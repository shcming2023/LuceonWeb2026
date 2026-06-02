from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import zipfile
import signal
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3


REPO_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = Path(os.environ.get("POPO_WORK_ROOT", REPO_ROOT / "runtime/work")).resolve()
DEFAULT_SOURCE_BUCKET = os.environ.get("POPO_SOURCE_BUCKET", "eduassets")
DEFAULT_CLEAN_BUCKET = os.environ.get("POPO_CLEAN_BUCKET", "eduassets-clean")
DEFAULT_INVOCATION_MODE = os.environ.get("POPO_TOC_REBUILD_DEFAULT_MODE", "bounded-preview")
BOUNDED_CHUNK_LIMIT = int(os.environ.get("POPO_BOUNDED_CHUNK_LIMIT", 3))
BOUNDED_PAGE_LIMIT = int(os.environ.get("POPO_BOUNDED_PAGE_LIMIT", 10))
CHUNK_SECONDS_ESTIMATE = float(os.environ.get("POPO_MPS_CHUNK_SECONDS_ESTIMATE", 780))
TOC_VIEW_SUPPLEMENT_TYPES = {
    "page_number",
    "header",
    "footer",
    "page_footnote",
    "page_title",
    "aside_text",
}


class AdapterError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class JobStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, job_id: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in job_id)
        return self.root / f"{safe}.json"

    def exists(self, job_id: str) -> bool:
        return self.path_for(job_id).exists()

    def read(self, job_id: str) -> dict[str, Any]:
        return json.loads(self.path_for(job_id).read_text(encoding="utf-8"))

    def write(self, job_id: str, payload: dict[str, Any]) -> None:
        self.path_for(job_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_ids(self) -> list[str]:
        return sorted(path.stem for path in self.root.glob("*.json"))

MAX_CONCURRENT_JOBS = int(os.environ.get("POPO_MAX_CONCURRENT_JOBS", 1))
JOB_TIMEOUT_SECONDS = int(os.environ.get("POPO_JOB_TIMEOUT_SECONDS", 600))
KILL_GRACE_SECONDS = int(os.environ.get("POPO_KILL_GRACE_SECONDS", 10))


def _page_sort_key(value: Any) -> tuple[int, str]:
    text = str(value)
    try:
        return (int(text), text)
    except ValueError:
        return (10**9, text)


def _coerce_pages(normalized_payload: Any) -> dict[str, list[dict[str, Any]]]:
    if isinstance(normalized_payload, dict) and isinstance(normalized_payload.get("pages"), dict):
        source = normalized_payload["pages"]
    elif isinstance(normalized_payload, dict):
        source = normalized_payload
    else:
        return {}

    pages: dict[str, list[dict[str, Any]]] = {}
    for page, blocks in source.items():
        if not isinstance(blocks, list):
            continue
        normalized_blocks = [block for block in blocks if isinstance(block, dict)]
        pages[str(page)] = normalized_blocks
    return pages


def _block_text(block: dict[str, Any]) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(str(item).strip() for item in content if str(item).strip())
    if isinstance(content, dict):
        for key in ("text", "content", "caption", "html"):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return str(block.get("text") or "").strip()


def _estimate_items(pages: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    items = {"contd": [], "title": [], "image": []}
    for page_key, blocks in pages.items():
        try:
            page_num = int(page_key)
        except ValueError:
            continue
        for block in blocks:
            block_type = str(block.get("type") or block.get("popo_type") or "text")
            if block_type in TOC_VIEW_SUPPLEMENT_TYPES:
                continue
            if not _block_text(block):
                continue
            item = {"page": page_num}
            # MinerU-Popo runs three families. This preflight is intentionally
            # conservative: all meaningful blocks can affect each family.
            items["contd"].append(item)
            items["title"].append(item)
            items["image"].append(item)
    return items


def _adaptive_chunk_ranges(items: list[dict[str, Any]], chunk_size: int, overlap: int = 1) -> list[list[int]]:
    chunk_size = max(1, int(chunk_size))
    if not items:
        return []

    sorted_items = sorted(items, key=lambda item: item["page"])
    pages = [item["page"] for item in sorted_items]
    unique_pages = sorted(set(pages))
    boundaries = []
    current_min = unique_pages[0]

    while current_min < unique_pages[-1]:
        target = current_min + chunk_size
        search_range = range(max(unique_pages[0], target - 5), min(unique_pages[-1], target + 5) + 1)
        freq = {}
        for page in search_range:
            if page in unique_pages:
                freq[page] = pages.count(page)
        if freq:
            boundary = max(freq, key=freq.get)
        else:
            boundary = min((page for page in unique_pages if page > target), default=unique_pages[-1])
        boundaries.append(boundary)
        current_min = boundary

    ranges = []
    prev_boundary = unique_pages[0]
    for boundary in boundaries:
        chunk_items = [
            item for item in sorted_items
            if prev_boundary - overlap <= item["page"] <= boundary + overlap
        ]
        if chunk_items:
            start = prev_boundary if prev_boundary == unique_pages[0] else prev_boundary - overlap
            end = min(unique_pages[-1], boundary + overlap)
            ranges.append([start, end])
        prev_boundary = boundary

    last_chunk = [
        item for item in sorted_items
        if prev_boundary - overlap <= item["page"] <= unique_pages[-1]
    ]
    if last_chunk:
        start = prev_boundary if prev_boundary == unique_pages[0] else prev_boundary - overlap
        if unique_pages[-1] - start > 2:
            ranges.append([start, unique_pages[-1]])

    return ranges


def _estimate_ranges_from_pages(page_numbers: list[int], chunk_size: int, overlap: int = 1) -> list[list[int]]:
    if not page_numbers:
        return []
    pages = sorted(set(page_numbers))
    ranges = []
    start_index = 0
    while start_index < len(pages):
        end_index = min(len(pages) - 1, start_index + max(1, chunk_size) - 1)
        start_page = pages[start_index]
        end_page = pages[end_index]
        if ranges:
            start_page = max(pages[0], start_page - overlap)
        if end_index < len(pages) - 1:
            end_page = min(pages[-1], end_page + overlap)
        ranges.append([start_page, end_page])
        start_index += max(1, chunk_size)
    return ranges


def _estimate_toc_rebuild(normalized_payload: Any, chunk_size: int | None = None) -> dict[str, Any]:
    chunk_size = int(chunk_size or os.environ.get("POPO_MPS_CHUNK_SIZE", 10))
    pages = _coerce_pages(normalized_payload)
    ordered_page_keys = sorted(pages.keys(), key=_page_sort_key)
    normalized_blocks = sum(len(blocks) for blocks in pages.values())
    items_by_task = _estimate_items(pages)
    ranges_by_task = {}
    for task, items in items_by_task.items():
        page_numbers = [int(item["page"]) for item in items if isinstance(item.get("page"), int)]
        ranges_by_task[task] = _estimate_ranges_from_pages(page_numbers, chunk_size)
    chunks_by_task = {task: len(ranges) for task, ranges in ranges_by_task.items()}
    total_chunks = sum(chunks_by_task.values())
    return {
        "schema": "luceon-popo-preflight/v1",
        "chunk_size": chunk_size,
        "normalized_pages": len(ordered_page_keys),
        "normalized_blocks": normalized_blocks,
        "page_start": ordered_page_keys[0] if ordered_page_keys else None,
        "page_end": ordered_page_keys[-1] if ordered_page_keys else None,
        "chunks_by_task": chunks_by_task,
        "ranges_by_task_sample": {task: ranges[:3] for task, ranges in ranges_by_task.items()},
        "inference_chunks_total": total_chunks,
        "estimated_seconds": int(math.ceil(total_chunks * CHUNK_SECONDS_ESTIMATE)),
        "risk_class": "large-mps" if total_chunks > BOUNDED_CHUNK_LIMIT else "interactive",
    }


def _slice_normalized_payload(normalized_payload: Any, max_pages: int) -> Any:
    pages = _coerce_pages(normalized_payload)
    selected_keys = sorted(pages.keys(), key=_page_sort_key)[:max(1, int(max_pages))]
    selected_pages = {key: pages[key] for key in selected_keys}
    if isinstance(normalized_payload, dict) and isinstance(normalized_payload.get("pages"), dict):
        return {**normalized_payload, "pages": selected_pages}
    return selected_pages


def _build_bounded_payload(normalized_payload: Any, chunk_size: int) -> tuple[Any, dict[str, Any]]:
    original_estimate = _estimate_toc_rebuild(normalized_payload, chunk_size)
    max_pages = min(
        max(1, BOUNDED_PAGE_LIMIT),
        max(1, int(original_estimate["normalized_pages"] or 1)),
    )
    bounded_payload = _slice_normalized_payload(normalized_payload, max_pages)
    bounded_estimate = _estimate_toc_rebuild(bounded_payload, chunk_size)
    while (
        max_pages > 1
        and bounded_estimate["inference_chunks_total"] > BOUNDED_CHUNK_LIMIT
    ):
        max_pages = max(1, max_pages - max(1, max_pages // 4))
        bounded_payload = _slice_normalized_payload(normalized_payload, max_pages)
        bounded_estimate = _estimate_toc_rebuild(bounded_payload, chunk_size)
    if isinstance(bounded_payload, dict) and isinstance(bounded_payload.get("pages"), dict):
        bounded_payload = {
            **bounded_payload,
            "luceon_invocation": {
                "mode": "bounded-preview",
                "bounded_page_limit": max_pages,
                "bounded_chunk_limit": BOUNDED_CHUNK_LIMIT,
                "source_pages": original_estimate["normalized_pages"],
                "selected_pages": bounded_estimate["normalized_pages"],
            },
        }
    return bounded_payload, {
        "mode": "bounded-preview",
        "bounded_page_limit": max_pages,
        "bounded_chunk_limit": BOUNDED_CHUNK_LIMIT,
        "original": original_estimate,
        "selected": bounded_estimate,
    }

class JobManager:
    def __init__(self, job_store: JobStore):
        self.job_store = job_store
        self.active_jobs: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def is_busy(self) -> bool:
        with self.lock:
            return len(self.active_jobs) >= MAX_CONCURRENT_JOBS

    def start_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = payload["job_id"]
        with self.lock:
            if len(self.active_jobs) >= MAX_CONCURRENT_JOBS:
                raise RuntimeError("Too many concurrent jobs")

            start_t = time.time()
            initial_state = {
                "job_id": job_id,
                "status": "running",
                "service_name": payload.get("service_name") or "toc-rebuild",
                "protocol_version": payload.get("protocol_version") or "v1",
                "material_id": payload.get("material_id"),
                "parse_task_id": payload.get("parse_task_id"),
                "asset_version": payload.get("asset_version"),
                "start_time": start_t,
                "current_step": "init",
            }
            self.job_store.write(job_id, initial_state)

            job_state = {"process": None, "pgid": None, "canceled": False, "payload": payload, "start_time": start_t}
            self.active_jobs[job_id] = job_state

        thread = threading.Thread(target=self._run_job_background, args=(job_id, job_state))
        thread.daemon = True
        thread.start()

        return initial_state

    def cancel_job(self, job_id: str) -> bool:
        with self.lock:
            if job_id not in self.active_jobs:
                return False
            job_state = self.active_jobs[job_id]
            job_state["canceled"] = True

            pgid = job_state.get("pgid")
            if pgid:
                try:
                    os.killpg(pgid, signal.SIGTERM)
                except Exception:
                    pass
            job_state["mps_worker_release"] = {
                "ok": None,
                "status": "release-requested",
                "reason": "job-canceled",
            }
            release = _release_host_mps_worker("job-canceled", force_terminate_if_busy=True)
            job_state["mps_worker_release"] = release
            self._persist_mps_worker_release(job_id, release)
            return True

    def _persist_mps_worker_release(self, job_id: str, release: dict[str, Any]) -> None:
        try:
            existing = self.job_store.read(job_id)
            progress = existing.get("progress") if isinstance(existing.get("progress"), dict) else {}
            progress["mps_worker_release"] = release
            existing["progress"] = progress
            self.job_store.write(job_id, existing)
        except Exception:
            pass

    def _run_job_background(self, job_id: str, job_state: dict[str, Any]):
        try:
            result = run_luceon_job(job_state["payload"], job_state)
            result["progress"] = _get_live_progress(job_state)
            result["current_step"] = "succeeded"
        except Exception as exc:
            if job_state.get("canceled"):
                result = self._make_error_result(job_state["payload"], "canceled", "Job canceled by operator", "canceled", job_state)
            elif getattr(exc, "code", "") == "timeout":
                result = self._make_error_result(job_state["payload"], "timeout", str(exc), "timeout", job_state)
            else:
                result = self._make_error_result(job_state["payload"], getattr(exc, "code", "mineru_popo_adapter_error"), str(exc), "failed", job_state)

        self.job_store.write(job_id, result)
        with self.lock:
            self.active_jobs.pop(job_id, None)

    def _make_error_result(self, payload, code, message, status, job_state=None):
        res = {
            "job_id": payload["job_id"],
            "status": status,
            "service_name": payload.get("service_name") or "toc-rebuild",
            "protocol_version": payload.get("protocol_version") or "v1",
            "material_id": payload.get("material_id"),
            "parse_task_id": payload.get("parse_task_id"),
            "asset_version": payload.get("asset_version"),
            "error": {
                "code": code,
                "message": message,
                "retriable": False,
            },
            "stats": {
                "engine": "mineru-popo",
                "cost_cny_actual": 0,
                "unresolved_anchor_count": 0,
                "tokens": {"total": 0},
            },
        }
        if job_state:
            res["progress"] = _get_live_progress(job_state)
            if code == "timeout":
                res["current_step"] = "timeout"
            elif code == "canceled":
                res["current_step"] = "canceled"
            else:
                res["current_step"] = "failed"
        return res

def _get_live_progress(job_state: dict[str, Any]) -> dict[str, Any]:
    import re
    progress = {
        "current_step": job_state.get("current_step", "queued"),
        "stage_started_at": job_state.get("stage_started_at"),
        "stage_finished_at": job_state.get("stage_finished_at"),
        "elapsed_seconds": int(time.time() - job_state.get("start_time", time.time())),
        "output_files_present": [],
        "normalized_pages": 0,
        "normalized_blocks": 0,
        "inference_chunks_total": 0,
        "inference_chunks_completed": 0,
        "inference_blocks_validated": 0,
        "active_chunk": None,
        "last_completed_chunk": None,
        "last_error": None,
        "chunks_by_task": {},
        "preflight": job_state.get("preflight"),
        "invocation": job_state.get("invocation"),
        "chunk_checkpoint": job_state.get("chunk_checkpoint"),
        "mps_worker_release": job_state.get("mps_worker_release"),
    }

    payload = job_state.get("payload", {})
    job_id = payload.get("job_id", "unknown")
    material_id = str(payload.get("material_id") or "")
    work_dir = WORK_ROOT / job_id
    outputs = work_dir / "outputs"
    chunk_size = int(os.environ.get("POPO_MPS_CHUNK_SIZE", 10))

    try:
        if outputs.exists():
            files = [str(p.relative_to(outputs)) for p in outputs.glob("**/*") if p.is_file()]
            progress["output_files_present"] = files[:50]  # cap to prevent huge JSON

        norm_dir = outputs / "label_normalization/mineru"
        if norm_dir.exists():
            for f in norm_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    estimate = _estimate_toc_rebuild(data, chunk_size)
                    progress["normalized_pages"] = estimate["normalized_pages"]
                    progress["normalized_blocks"] = estimate["normalized_blocks"]
                    progress["inference_chunks_total"] = estimate["inference_chunks_total"]
                    if not progress.get("preflight"):
                        progress["preflight"] = {"original": estimate}
                except Exception:
                    pass
                break

        # Derive progress from outputs/inference_raw/mineru/<material_id>/*_chunk_*.json
        inf_raw_dir = outputs / "inference_raw"
        target_dir = None
        if material_id:
            target_dir = inf_raw_dir / "mineru" / material_id
            if not target_dir.exists():
                target_dir = None

        if not target_dir:
            # Fallback path if exact material_id folder is not present yet
            mineru_dir = inf_raw_dir / "mineru"
            if mineru_dir.exists():
                for sub in mineru_dir.iterdir():
                    if sub.is_dir():
                        target_dir = sub
                        break

        if not target_dir:
            target_dir = inf_raw_dir

        completed_chunks = []
        chunks_by_task = {}
        completed_records = []

        if target_dir.exists():
            checkpoint_path = target_dir / "checkpoint.json"
            if checkpoint_path.exists():
                try:
                    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                    if isinstance(checkpoint, dict):
                        progress["chunk_checkpoint"] = checkpoint
                except Exception:
                    pass
            for f in target_dir.glob("**/*_chunk_*.json"):
                rel_parts = f.relative_to(target_dir).parts
                if "profile_archive" in rel_parts:
                    continue
                try:
                    data = json.loads(f.read_text())
                    if isinstance(data, dict):
                        task = str(data.get("task") or "unknown")
                        chunk_index = data.get("chunk_index")
                        # Register completed chunk filename and task family count
                        completed_chunks.append(f.name)
                        chunks_by_task[task] = chunks_by_task.get(task, 0) + 1
                        completed_records.append({
                            "file": f.name,
                            "task": task,
                            "chunk_index": chunk_index if isinstance(chunk_index, int) else None,
                            "range": data.get("range"),
                            "pages": data.get("pages"),
                        })

                        # Validate blocks from internal 'parsed' page list
                        parsed_pages = data.get("parsed") or []
                        if isinstance(parsed_pages, list):
                            progress["inference_blocks_validated"] += sum(
                                len(page) if isinstance(page, list) else 0 for page in parsed_pages
                            )
                except Exception:
                    pass

        completed_chunks = sorted(list(set(completed_chunks)))
        progress["inference_chunks_completed"] = len(completed_chunks)
        progress["chunks_by_task"] = chunks_by_task

        completed_records = sorted(
            completed_records,
            key=lambda item: (str(item.get("task") or ""), int(item.get("chunk_index") or 0), str(item.get("file") or "")),
        )
        if completed_records:
            last_record = completed_records[-1]
            progress["last_completed_chunk"] = last_record["file"]
            # Safely capture next chunk with same family prefix and correct padding length
            m = re.match(r'^(.+)_chunk_(\d+)\.json$', last_record["file"])
            if m:
                prefix = m.group(1)
                idx_str = m.group(2)
                next_idx = int(last_record.get("chunk_index") if last_record.get("chunk_index") is not None else idx_str) + 1
                progress["active_chunk"] = f"{prefix}_chunk_{next_idx:0{len(idx_str)}d}.json"
            else:
                progress["active_chunk"] = "title_chunk_0000.json"
        elif progress["inference_chunks_total"] > 0 and progress["current_step"] == "running_inference":
            progress["active_chunk"] = "contd_chunk_0000.json"

    except Exception as e:
        progress["last_error"] = str(e)

    return progress


@dataclass
class ObjectRef:
    bucket: str
    object: str


def _s3_client(endpoint: str | None = None, use_ssl: bool = False):
    endpoint_url = _endpoint_url(endpoint or os.environ.get("MINIO_ENDPOINT") or "127.0.0.1:9000", use_ssl)
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("MINIO_ROOT_USER") or "minioadmin",
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY") or os.environ.get("MINIO_ROOT_PASSWORD") or "minioadmin",
    )


def _endpoint_url(endpoint: str, use_ssl: bool) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"{'https' if use_ssl else 'http'}://{endpoint}"


def _input_by_role(payload: dict[str, Any], role: str) -> ObjectRef | None:
    for item in payload.get("inputs") or []:
        if item.get("role") != role:
            continue
        source = item.get("source") or {}
        bucket = source.get("bucket")
        obj = source.get("object")
        if bucket and obj:
            return ObjectRef(bucket=bucket, object=obj)
    return None


def _primary_input(payload: dict[str, Any]) -> ObjectRef:
    source = _input_by_role(payload, "mineru-content")
    if not source:
        raise AdapterError("missing-mineru-content-input", "inputs[] must include role=mineru-content ObjectRef")
    return source


def _zip_input(payload: dict[str, Any]) -> ObjectRef | None:
    return _input_by_role(payload, "mineru-result-zip")


def _find_pdf(client, payload: dict[str, Any]) -> ObjectRef:
    explicit = _input_by_role(payload, "source-pdf")
    if explicit:
        return explicit

    material_id = str(payload.get("material_id") or "").strip()
    if not material_id:
        raise AdapterError("missing-material-id", "material_id is required to discover the source PDF")

    bucket = os.environ.get("POPO_SOURCE_BUCKET", DEFAULT_SOURCE_BUCKET)
    prefix = f"originals/{material_id}/"
    resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=50)
    candidates = [
        item["Key"]
        for item in resp.get("Contents", [])
        if item.get("Key", "").lower().endswith(".pdf")
    ]
    if not candidates:
        raise AdapterError(
            "source-pdf-not-found",
            f"no PDF found under s3://{bucket}/{prefix}; pass inputs[] role=source-pdf or preserve originals/{{materialId}} PDF",
        )
    return ObjectRef(bucket=bucket, object=sorted(candidates)[0])


def _download(client, ref: ObjectRef, dest: Path) -> bytes:
    dest.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(ref.bucket, ref.object, str(dest))
    return dest.read_bytes()


def _find_one(root: Path, suffix: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob("*") if path.is_file() and path.name.lower().endswith(suffix))
    if not matches:
        raise AdapterError(f"{label}-not-found-in-zip", f"no *{suffix} file found in mineru-result zip")
    return matches[0]


def _content_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_content_text(item) for item in value)
    if not isinstance(value, dict):
        return ""

    parts: list[str] = []
    for key in (
        "content",
        "text",
        "paragraph_content",
        "title_content",
        "page_header_content",
        "page_footer_content",
        "table_body",
        "image_caption",
        "image_footnote",
        "table_caption",
        "table_footnote",
    ):
        if key in value:
            parts.append(_content_text(value[key]))
    return "".join(parts)


def _flatten_content_list_v2(source: Path, dest: Path) -> None:
    pages = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(pages, list):
        raise AdapterError("content-list-v2-invalid", f"{source} must contain a page list")

    type_map = {
        "paragraph": "text",
        "title": "title",
        "page_header": "header",
        "page_footer": "footer",
        "table": "table",
        "image": "image",
        "interline_equation": "display_formula",
        "isolated_formula": "display_formula",
    }
    rows: list[dict[str, Any]] = []
    for page_idx, page in enumerate(pages):
        if not isinstance(page, list):
            continue
        for block in page:
            if not isinstance(block, dict) or block.get("bbox") is None:
                continue
            text = _content_text(block.get("content")).strip()
            if not text:
                continue
            block_type = str(block.get("type") or "text")
            row: dict[str, Any] = {
                "type": type_map.get(block_type, "text"),
                "text": text,
                "bbox": block.get("bbox"),
                "page_idx": page_idx,
            }
            if block_type == "title":
                row["text_level"] = block.get("level") or block.get("text_level") or 1
            rows.append(row)

    if not rows:
        raise AdapterError("content-list-v2-empty", f"{source} did not yield any text blocks")
    dest.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def _copy_mineru_content_list(extract_root: Path, dest: Path) -> Path:
    flat_matches = sorted(
        path
        for path in extract_root.rglob("*")
        if path.is_file()
        and path.name.lower().endswith("_content_list.json")
        and not path.name.lower().endswith("_content_list_v2.json")
    )
    if flat_matches:
        shutil.copyfile(flat_matches[0], dest)
        return flat_matches[0]

    v2_matches = sorted(
        path
        for path in extract_root.rglob("*")
        if path.is_file() and path.name.lower().endswith("_content_list_v2.json")
    )
    if not v2_matches:
        raise AdapterError("content-list-not-found-in-zip", "no *_content_list.json or *_content_list_v2.json file found in mineru-result zip")
    _flatten_content_list_v2(v2_matches[0], dest)
    return v2_matches[0]


def _prepare_inputs(client, payload: dict[str, Any], work_dir: Path, material_id: str) -> tuple[bytes, bytes, ObjectRef, bytes]:
    content_path = work_dir / "post-process/mineru" / material_id / "vlm" / f"{material_id}_content_list.json"
    pdf_path = work_dir / "eval_pdf_dir" / f"{material_id}.pdf"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    zip_ref = _zip_input(payload)
    if zip_ref:
        zip_path = work_dir / "input" / "mineru-result.zip"
        zip_bytes = _download(client, zip_ref, zip_path)
        extract_root = work_dir / "input" / "mineru-result"
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)

        extracted_content = _copy_mineru_content_list(extract_root, content_path)
        extracted_pdf = _find_one(extract_root, ".pdf", "source-pdf")
        shutil.copyfile(extracted_pdf, pdf_path)
        return content_path.read_bytes(), pdf_path.read_bytes(), zip_ref, zip_bytes

    mineru_ref = _primary_input(payload)
    pdf_ref = _find_pdf(client, payload)
    content_bytes = _download(client, mineru_ref, content_path)
    pdf_bytes = _download(client, pdf_ref, pdf_path)
    return content_bytes, pdf_bytes, mineru_ref, content_bytes


def _put_text(client, bucket: str, key: str, text: str, content_type: str) -> dict[str, Any]:
    data = text.encode("utf-8")
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return _object_ref(bucket, key, data, content_type)


def _put_json(client, bucket: str, key: str, payload: Any) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    return _put_text(client, bucket, key, text, "application/json")


def _object_ref(bucket: str, key: str, data: bytes, content_type: str) -> dict[str, Any]:
    return {
        "bucket": bucket,
        "object": key,
        "size_bytes": len(data),
        "content_type": content_type,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _run_with_state(args: list[str], cwd: Path, job_state: dict[str, Any], step_name: str, timeout_seconds: float | None = None) -> str:
    if job_state.get("canceled"):
        raise AdapterError("canceled", "Job was canceled")

    # Update state
    job_id = job_state["payload"]["job_id"]
    job_state["current_step"] = step_name
    job_state["stage_started_at"] = time.time()

    if timeout_seconds is None:
        time_elapsed = time.time() - job_state.get("start_time", time.time())
        timeout = max(1.0, float(JOB_TIMEOUT_SECONDS) - time_elapsed)
    else:
        timeout = max(1.0, float(timeout_seconds))

    process = subprocess.Popen(
        args, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        start_new_session=True
    )
    job_state["process"] = process
    job_state["pgid"] = os.getpgid(process.pid)

    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(job_state["pgid"], signal.SIGTERM)
        process.communicate()
        job_state["stage_finished_at"] = time.time()
        if step_name == "running_inference":
            job_state["mps_worker_release"] = _release_host_mps_worker("job-timeout", force_terminate_if_busy=True)
        raise AdapterError("timeout", f"{step_name} exceeded maximum execution time")

    job_state["stage_finished_at"] = time.time()
    if job_state.get("canceled"):
        raise AdapterError("canceled", "Job was canceled")

    if process.returncode != 0:
        raise AdapterError("popo-command-failed", f"{' '.join(args)} failed:\n{stdout[-4000:]}")

    return stdout or ""


def _release_host_mps_worker(reason: str, force_terminate_if_busy: bool = False) -> dict[str, Any]:
    url = os.environ.get("POPO_GENERATE_URL", "").rstrip("/")
    if not url:
        return {"ok": False, "status": "not-configured", "reason": reason}

    payload = json.dumps({
        "reason": reason,
        "force_terminate_if_busy": force_terminate_if_busy,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{url}/release",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            if isinstance(data, dict):
                return data
            return {"ok": False, "status": "invalid-response", "reason": reason}
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = ""
        return {"ok": False, "status": "http-error", "reason": reason, "status_code": exc.code, "detail": detail[:1000]}
    except Exception as exc:
        return {"ok": False, "status": "request-failed", "reason": reason, "error": str(exc)}



def _render_tree_markdown(tree: dict[str, Any]) -> str:
    lines: list[str] = []

    def visit(node: dict[str, Any], depth: int) -> None:
        title = str(node.get("title") or "").strip()
        content = str(node.get("content") or "").replace("<|txt_split|>", "\n\n").replace("<|txt_contd|>", "")
        if title:
            level = min(max(depth, 1), 6)
            lines.append(f"{'#' * level} {title}")
            lines.append("")
        if content.strip():
            lines.append(content.strip())
            lines.append("")
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, depth + 1 if title else depth)

    visit(tree, 1)
    return "\n".join(lines).strip() + "\n"


def _render_tree_preview(tree: dict[str, Any]) -> str:
    lines: list[str] = []

    def visit(node: dict[str, Any], depth: int) -> None:
        indent = " " * (depth * 4)
        title = str(node.get("title") or "")
        content = str(node.get("content") or "")
        data_preview = content[:30] + ("..." if len(content) > 30 else "")
        lines.append(f"{indent}{title}|{data_preview}")
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, depth + 1)

    visit(tree, 0)
    return "\n".join(lines) + "\n"


def _filter_toc_view_tree(tree: dict[str, Any]) -> dict[str, Any]:
    def should_drop(node: dict[str, Any]) -> bool:
        node_type = str(node.get("type") or "").strip()
        return node_type in TOC_VIEW_SUPPLEMENT_TYPES

    def visit(node: dict[str, Any]) -> dict[str, Any] | None:
        if should_drop(node):
            return None
        filtered = {key: value for key, value in node.items() if key != "children"}
        children = []
        for child in node.get("children") or []:
            if not isinstance(child, dict):
                continue
            filtered_child = visit(child)
            if filtered_child is not None:
                children.append(filtered_child)
        filtered["children"] = children
        return filtered

    return visit(tree) or {"type": "root", "title": "", "metadata": "", "content": "", "level": 0, "location": [], "block_ids": [], "children": []}


def _flatten_tree(tree: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(node: dict[str, Any], path: list[str]) -> None:
        title = str(node.get("title") or "").strip()
        current_path = path + ([title] if title else [])
        content = str(node.get("content") or "").strip()
        if title or content:
            rows.append({
                "id": "node-" + str(len(rows) + 1),
                "title": title,
                "path": current_path,
                "content": content,
                "type": node.get("type") or "text",
                "block_ids": node.get("block_ids") or [],
                "location": node.get("location") or [],
            })
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, current_path)

    visit(tree, [])
    return rows


def _assert_usable_outputs(tree: dict[str, Any], readable: str, rebuilt_markdown: str, flooded_content: list[dict[str, Any]]) -> None:
    title = str(tree.get("title") or "").strip().lower()
    has_children = bool(tree.get("children"))
    markdown_body = rebuilt_markdown.strip()
    readable_body = readable.strip()
    if (
        not flooded_content
        or not has_children
        or markdown_body == "# default title"
        or title == "default title"
        or len(markdown_body) < 200
        or len(readable_body) < 50
    ):
        raise AdapterError(
            "popo-empty-output",
            "MinerU-Popo produced an unusable tree; normalized input likely had no pages or inference returned no content",
        )


def run_luceon_job(payload: dict[str, Any], job_state: dict[str, Any] = None) -> dict[str, Any]:
    if job_state is None:
        job_state = {"payload": payload, "canceled": False}

    job_id = payload["job_id"]
    material_id = str(payload.get("material_id") or "")
    asset_version = str(payload.get("asset_version") or "v1")
    service_name = payload.get("service_name") or "toc-rebuild"
    options = payload.get("options") if isinstance(payload.get("options"), dict) else {}
    requested_mode = str(
        options.get("toc_rebuild_mode")
        or options.get("invocation_mode")
        or options.get("mode")
        or DEFAULT_INVOCATION_MODE
    ).strip().lower()
    invocation_mode = "full-background" if requested_mode in {"full", "recoverable-full", "background-full", "full-background"} else "bounded-preview"
    sink = payload.get("sink") or {}
    sink_bucket = sink.get("bucket") or DEFAULT_CLEAN_BUCKET
    sink_prefix = sink.get("prefix") or f"{service_name}/{material_id}/{asset_version}/"
    storage_endpoint = sink.get("endpoint") or payload.get("inputs", [{}])[0].get("source", {}).get("endpoint")
    storage_use_ssl = bool(sink.get("use_ssl") or sink.get("useSsl"))

    model_path = os.environ.get("POPO_MODEL_PATH", "").strip()
    if not model_path or not Path(model_path).exists():
        raise AdapterError("popo-model-not-configured", "POPO_MODEL_PATH must point to downloaded MinerU-Popo model weights")

    client = _s3_client(storage_endpoint, storage_use_ssl)
    work_dir = WORK_ROOT / job_id
    recoverable_full = invocation_mode == "full-background"
    if work_dir.exists() and not recoverable_full:
        shutil.rmtree(work_dir)
    (work_dir / "post-process/mineru" / material_id / "vlm").mkdir(parents=True, exist_ok=True)
    (work_dir / "eval_pdf_dir").mkdir(parents=True, exist_ok=True)

    content_bytes, pdf_bytes, provenance_input_ref, provenance_input_bytes = _prepare_inputs(client, payload, work_dir, material_id)

    outputs = work_dir / "outputs"
    _run_with_state([
        sys.executable,
        str(REPO_ROOT / "post_processing/label_normalization.py"),
        "--model", "mineru",
        "--input-dir", str(work_dir / "post-process/mineru"),
        "--doc-id", material_id,
        "--output-dir", str(outputs / "label_normalization"),
        "--pdf-dir", str(work_dir / "eval_pdf_dir"),
    ], REPO_ROOT, job_state, "running_normalization")

    chunk_size = int(os.environ.get("POPO_MPS_CHUNK_SIZE", 10))
    normalized_path = outputs / "label_normalization/mineru" / f"{material_id}.json"
    normalized_payload = json.loads(normalized_path.read_text(encoding="utf-8"))
    original_preflight = _estimate_toc_rebuild(normalized_payload, chunk_size)
    selected_input_dir = outputs / "label_normalization/mineru"
    selected_preflight = original_preflight
    invocation = {
        "mode": invocation_mode,
        "requested_mode": requested_mode or DEFAULT_INVOCATION_MODE,
        "recoverable": recoverable_full,
        "bounded": invocation_mode == "bounded-preview",
        "resume": recoverable_full,
    }

    if invocation_mode == "bounded-preview":
        bounded_payload, bounded_plan = _build_bounded_payload(normalized_payload, chunk_size)
        selected_input_dir = outputs / "label_normalization_bounded/mineru"
        selected_input_dir.mkdir(parents=True, exist_ok=True)
        (selected_input_dir / f"{material_id}.json").write_text(
            json.dumps(bounded_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        selected_preflight = bounded_plan["selected"]
        invocation.update({
            "bounded_page_limit": bounded_plan["bounded_page_limit"],
            "bounded_chunk_limit": bounded_plan["bounded_chunk_limit"],
            "bounded_reason": "Popo preflight uses bounded-preview Home Mac mini MPS profile",
        })

    job_state["preflight"] = {
        "original": original_preflight,
        "selected": selected_preflight,
    }
    job_state["invocation"] = invocation

    inference_output_dir = outputs / "inference/mineru"
    inference_args = [
        sys.executable,
        str(REPO_ROOT / "post_processing/run_inference.py"),
        "--input-dir", str(selected_input_dir),
        "--model-path", model_path,
        "--output-dir", str(inference_output_dir),
        "--raw-output-root", str(outputs / "inference_raw"),
        "--limit", "1",
    ]
    if recoverable_full:
        inference_args.append("--resume")
    _run_with_state(inference_args, REPO_ROOT, job_state, "running_inference")
    _run_with_state([
        sys.executable,
        str(REPO_ROOT / "post_processing/get_json_tree.py"),
        "--input-dir", str(outputs / "inference/mineru"),
        "--output-dir", str(outputs / "build_tree/mineru"),
        "--txt-dir", str(outputs / "build_tree_txt/mineru"),
    ], REPO_ROOT, job_state, "running_build_tree")

    tree_path = outputs / "build_tree/mineru" / f"{material_id}.json"
    tree = json.loads(tree_path.read_text(encoding="utf-8"))
    toc_view_tree = _filter_toc_view_tree(tree)
    readable = _render_tree_preview(toc_view_tree)
    rebuilt_markdown = _render_tree_markdown(toc_view_tree)
    flooded_content = _flatten_tree(toc_view_tree)
    _assert_usable_outputs(toc_view_tree, readable, rebuilt_markdown, flooded_content)
    unresolved: list[dict[str, Any]] = []
    metrics = {
        "engine": "mineru-popo",
        "model_path": model_path,
        "invocation": invocation,
        "preflight": {
            "original": original_preflight,
            "selected": selected_preflight,
        },
        "tokens": {"total": max(1, len(content_bytes) // 4)},
        "input_bytes": {"content_list_v2": len(content_bytes), "pdf": len(pdf_bytes)},
        "unresolved_anchor_count": 0,
        "cost_cny_actual": 0,
    }
    provenance = {
        "schema": "luceon-provenance/v1",
        "service": {"name": service_name, "version": "mineru-popo-adapter.v0.1", "protocol_version": "v1", "engine": "mineru-popo"},
        "asset": {"material_id": material_id, "asset_version": asset_version},
        "job": {"job_id": job_id, "parse_task_id": payload.get("parse_task_id")},
        "invocation": invocation,
        "preflight": {
            "original": original_preflight,
            "selected": selected_preflight,
        },
        "inputs": [
            {
                "bucket": provenance_input_ref.bucket,
                "object": provenance_input_ref.object,
                "sha256": hashlib.sha256(provenance_input_bytes).hexdigest(),
                "size_bytes": len(provenance_input_bytes),
            },
        ],
        "outputs": {"bucket": sink_bucket, "prefix": sink_prefix},
    }

    artifacts = {
        "flooded_content": _put_json(client, sink_bucket, f"{sink_prefix}flooded_content.json", flooded_content),
        "logic_tree": _put_json(client, sink_bucket, f"{sink_prefix}logic_tree.json", toc_view_tree),
        "readable_tree": _put_text(client, sink_bucket, f"{sink_prefix}readable_tree.md", readable, "text/markdown"),
        "skeleton": _put_json(client, sink_bucket, f"{sink_prefix}skeleton.json", {"source": "mineru-popo", "normalized_input": f"outputs/label_normalization/mineru/{material_id}.json"}),
        "unresolved_anchors": _put_json(client, sink_bucket, f"{sink_prefix}unresolved_anchors.json", unresolved),
        "metrics": _put_json(client, sink_bucket, f"{sink_prefix}metrics.json", metrics),
        "rebuilt_markdown": _put_text(client, sink_bucket, f"{sink_prefix}rebuilt_markdown.md", rebuilt_markdown, "text/markdown"),
    }
    artifacts["provenance"] = _put_json(client, sink_bucket, f"{sink_prefix}provenance.json", provenance)

    return {
        "job_id": job_id,
        "status": "completed",
        "service_name": service_name,
        "service_version": "mineru-popo-adapter.v0.1",
        "protocol_version": "v1",
        "material_id": material_id,
        "parse_task_id": payload.get("parse_task_id"),
        "asset_version": asset_version,
        "sink": {"bucket": sink_bucket, "prefix": sink_prefix},
        "artifacts": artifacts,
        "provenance": provenance,
        "stats": {
            "engine": "mineru-popo",
            "invocation": invocation,
            "preflight": {
                "original": original_preflight,
                "selected": selected_preflight,
            },
            "tokens": metrics["tokens"],
            "cost_cny_actual": 0,
            "unresolved_anchor_count": 0,
        },
        "error": None,
    }
