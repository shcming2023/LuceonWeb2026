from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import zipfile
import signal
import threading
import time
import urllib.error
import urllib.request
from collections import deque
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
TOC_VIEW_DROP_TITLE_PREFIXES = (
    "tip",
    "link",
    "keyword",
    "keywords",
    "getting started",
    "in this chapter",
    "worked example",
    "answer",
    "answers",
    "apply your skills",
    "applyyourskills",
    "reflection",
    "investigation",
    "discussion",
    "self assessment",
    "selfassessment",
    "self/peer assessment",
    "peer assessment",
    "peerassessment",
    "mathematical connection",
    "mathematicalconnection",
    "summary",
    "summarycontinued",
    "go further",
    "extended content",
    "tp",
)
TOC_VIEW_FRONT_MATTER_PREFIXES = (
    "default title",
    "notice to teachers",
    "cambridge dedicated teacher awards",
    "congratulations to our incredible winners",
    "endorsement statement",
    "> contents",
    "> introduction",
    "introduction",
    "how to use this book",
    ">how to use this series",
    "> how to use this series",
    "> acknowledgements",
    "acknowledgements",
)
TOC_VIEW_KEEP_TITLE_PREFIXES = (
    "unit",
    "> unit",
    "exercise",
    "practice question",
    "past paper question",
    "> glossary",
    "glossary",
    "> index",
    "index",
)


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
FULL_BACKGROUND_STALL_TIMEOUT_SECONDS = int(os.environ.get("POPO_FULL_BACKGROUND_STALL_TIMEOUT_SECONDS", 3600))
FULL_BACKGROUND_POLL_SECONDS = float(os.environ.get("POPO_FULL_BACKGROUND_POLL_SECONDS", 30))
FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS = int(os.environ.get("POPO_FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS", 18000))
FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS = int(os.environ.get("POPO_FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS", 18000))


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
            timer = threading.Timer(2.0, self._persist_mps_worker_release, args=(job_id, release))
            timer.daemon = True
            timer.start()
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
        "long_run_policy": job_state.get("long_run_policy"),
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


def _copy_mineru_markdown(extract_root: Path, dest: Path) -> Path | None:
    matches = sorted(
        path
        for path in extract_root.rglob("*")
        if path.is_file() and path.suffix.lower() == ".md"
    )
    if not matches:
        return None
    preferred = sorted(
        matches,
        key=lambda path: (
            0 if path.name.lower() == "full.md" else 1,
            -path.stat().st_size,
            str(path),
        ),
    )[0]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(preferred, dest)
    return preferred


def _prepare_inputs(client, payload: dict[str, Any], work_dir: Path, material_id: str) -> tuple[bytes, bytes, ObjectRef, bytes, str | None]:
    content_path = work_dir / "post-process/mineru" / material_id / "vlm" / f"{material_id}_content_list.json"
    pdf_path = work_dir / "eval_pdf_dir" / f"{material_id}.pdf"
    markdown_path = work_dir / "input" / "full.md"
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
        extracted_markdown = _copy_mineru_markdown(extract_root, markdown_path)
        extracted_pdf = _find_one(extract_root, ".pdf", "source-pdf")
        shutil.copyfile(extracted_pdf, pdf_path)
        markdown_text = markdown_path.read_text(encoding="utf-8", errors="replace") if extracted_markdown else None
        return content_path.read_bytes(), pdf_path.read_bytes(), zip_ref, zip_bytes, markdown_text

    mineru_ref = _primary_input(payload)
    pdf_ref = _find_pdf(client, payload)
    content_bytes = _download(client, mineru_ref, content_path)
    pdf_bytes = _download(client, pdf_ref, pdf_path)
    return content_bytes, pdf_bytes, mineru_ref, content_bytes, None


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

    if _should_use_progress_aware_wait(job_state, step_name, timeout_seconds):
        return _wait_with_progress_aware_timeout(process, job_state, step_name)

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


def _should_use_progress_aware_wait(job_state: dict[str, Any], step_name: str, timeout_seconds: float | None) -> bool:
    invocation = job_state.get("invocation") if isinstance(job_state.get("invocation"), dict) else {}
    return (
        timeout_seconds is None
        and step_name == "running_inference"
        and invocation.get("mode") == "full-background"
        and invocation.get("recoverable") is True
    )


def _progress_signature(progress: dict[str, Any], mps_health: dict[str, Any] | None = None) -> tuple[Any, ...]:
    health = mps_health or {}
    return (
        progress.get("inference_chunks_completed"),
        progress.get("inference_blocks_validated"),
        progress.get("last_completed_chunk"),
        progress.get("active_chunk"),
        json.dumps(progress.get("chunks_by_task") or {}, sort_keys=True),
        health.get("generation_count"),
    )


def _host_mps_worker_health() -> dict[str, Any]:
    url = os.environ.get("POPO_GENERATE_URL", "").rstrip("/")
    if not url:
        return {"ok": False, "status": "not-configured"}
    try:
        with urllib.request.urlopen(f"{url}/health", timeout=5) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            if isinstance(data, dict):
                return data
            return {"ok": False, "status": "invalid-response"}
    except Exception as exc:
        return {"ok": False, "status": "request-failed", "error": str(exc)}


def _wait_with_progress_aware_timeout(process: subprocess.Popen, job_state: dict[str, Any], step_name: str) -> str:
    stdout_lines: deque[str] = deque(maxlen=500)

    def read_stdout() -> None:
        if process.stdout is None:
            return
        for line in process.stdout:
            stdout_lines.append(line)

    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()

    started_at = time.time()
    last_progress_at = started_at
    last_generation_started_at = None
    soft_checkpoint_recorded = False
    progress = _get_live_progress(job_state)
    mps_health = _host_mps_worker_health()
    last_signature = _progress_signature(progress, mps_health)
    job_state["long_run_policy"] = {
        "mode": "progress-aware",
        "stall_timeout_seconds": FULL_BACKGROUND_STALL_TIMEOUT_SECONDS,
        "poll_seconds": FULL_BACKGROUND_POLL_SECONDS,
        "soft_checkpoint_seconds": FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS,
        "single_generation_timeout_seconds": FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS,
        "started_at": started_at,
        "last_progress_at": last_progress_at,
        "last_signature": list(last_signature),
    }

    while True:
        if job_state.get("canceled"):
            try:
                os.killpg(job_state["pgid"], signal.SIGTERM)
            except Exception:
                pass
            process.wait(timeout=KILL_GRACE_SECONDS)
            raise AdapterError("canceled", "Job was canceled")

        returncode = process.poll()
        now = time.time()
        progress = _get_live_progress(job_state)
        mps_health = _host_mps_worker_health()
        signature = _progress_signature(progress, mps_health)
        active_generations = int(mps_health.get("active_generations") or 0)
        generation_count = mps_health.get("generation_count")

        if signature != last_signature:
            last_signature = signature
            last_progress_at = now
            last_generation_started_at = now if active_generations > 0 else None
        elif active_generations > 0 and last_generation_started_at is None:
            last_generation_started_at = now
        elif active_generations == 0:
            last_generation_started_at = None

        policy = job_state.setdefault("long_run_policy", {})
        policy.update({
            "mode": "progress-aware",
            "stall_timeout_seconds": FULL_BACKGROUND_STALL_TIMEOUT_SECONDS,
            "poll_seconds": FULL_BACKGROUND_POLL_SECONDS,
            "soft_checkpoint_seconds": FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS,
            "single_generation_timeout_seconds": FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS,
            "last_progress_at": last_progress_at,
            "seconds_since_progress": int(now - last_progress_at),
            "last_signature": list(last_signature),
            "mps_active_generations": active_generations,
            "mps_generation_count": generation_count,
        })

        if not soft_checkpoint_recorded and now - started_at >= FULL_BACKGROUND_SOFT_CHECKPOINT_SECONDS:
            policy["soft_checkpoint_reached"] = True
            policy["soft_checkpoint_at"] = now
            soft_checkpoint_recorded = True

        single_generation_stalled = (
            active_generations > 0
            and last_generation_started_at is not None
            and now - last_generation_started_at >= FULL_BACKGROUND_SINGLE_GENERATION_TIMEOUT_SECONDS
        )
        no_progress_stalled = active_generations == 0 and now - last_progress_at >= FULL_BACKGROUND_STALL_TIMEOUT_SECONDS

        if single_generation_stalled or no_progress_stalled:
            try:
                os.killpg(job_state["pgid"], signal.SIGTERM)
            except Exception:
                pass
            process.wait(timeout=KILL_GRACE_SECONDS)
            job_state["stage_finished_at"] = time.time()
            reason = "job-single-generation-stalled-timeout" if single_generation_stalled else "job-stalled-timeout"
            job_state["mps_worker_release"] = _release_host_mps_worker(reason, force_terminate_if_busy=True)
            raise AdapterError("timeout", f"{step_name} stalled without progress for {int(now - last_progress_at)}s")

        if returncode is not None:
            reader.join(timeout=2)
            job_state["stage_finished_at"] = time.time()
            stdout = "".join(stdout_lines)
            if job_state.get("canceled"):
                raise AdapterError("canceled", "Job was canceled")
            if returncode != 0:
                raise AdapterError("popo-command-failed", f"{step_name} failed:\n{stdout[-4000:]}")
            return stdout

        time.sleep(max(1.0, FULL_BACKGROUND_POLL_SECONDS))


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
        title = str(node.get("title") or "").strip()
        content = str(node.get("content") or "")
        data_preview = content[:30] + ("..." if len(content) > 30 else "")
        if title or data_preview:
            if data_preview:
                lines.append(f"{indent}{title}|{data_preview}")
            else:
                lines.append(f"{indent}{title}")
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, depth + 1)

    visit(tree, 0)
    return "\n".join(lines) + "\n"


def _toc_text(value: Any) -> str:
    return " ".join(str(value or "").replace("<|txt_split|>", " ").replace("<|txt_contd|>", " ").split())


def _toc_compact(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _toc_title_kind(title: str) -> str | None:
    clean = _toc_text(title).strip(" >")
    lower = clean.lower()
    compact = _toc_compact(clean)
    if not clean:
        return None
    if lower.startswith(TOC_VIEW_KEEP_TITLE_PREFIXES):
        return "toc"
    if compact.startswith("unit") and any(ch.isdigit() for ch in compact[:8]):
        return "toc"
    if compact in {"glossary", "index"}:
        return "toc"
    if compact.endswith("project") and "unit" in compact:
        return "toc"
    if "practicequestions" in compact or "pastpaperquestions" in compact:
        return "toc"
    if "exercise" in compact and any(ch.isdigit() for ch in compact):
        return "toc"
    if re.match(r"^\d{1,2}(?:\.\d+){1,3}\b", lower):
        return "toc"
    if re.match(r"^\d{1,2}\s+[A-Za-z]", clean):
        return "toc"
    return None


def _toc_should_promote_title(title: str) -> bool:
    lower = _toc_text(title).strip().lower()
    compact = _toc_compact(title)
    if not lower:
        return True
    if lower.startswith(TOC_VIEW_DROP_TITLE_PREFIXES):
        return True
    if lower.startswith(TOC_VIEW_FRONT_MATTER_PREFIXES):
        return True
    if compact.startswith("mathematicalconnection"):
        return True
    if compact.startswith("workedexample"):
        return True
    if compact.startswith("applyyourskills"):
        return True
    return False


def _filter_toc_view_tree(tree: dict[str, Any]) -> dict[str, Any]:
    def should_promote(node: dict[str, Any]) -> bool:
        node_type = str(node.get("type") or "").strip()
        if node_type in TOC_VIEW_SUPPLEMENT_TYPES:
            return True
        return _toc_should_promote_title(str(node.get("title") or ""))

    def visit(node: dict[str, Any]) -> list[dict[str, Any]]:
        children: list[dict[str, Any]] = []
        for child in node.get("children") or []:
            if not isinstance(child, dict):
                continue
            children.extend(visit(child))

        title = _toc_text(node.get("title"))
        promote_current = should_promote(node)
        keep_current = _toc_title_kind(title) is not None or (bool(children) and not promote_current)
        if promote_current:
            return children
        if not keep_current:
            return []

        filtered = {key: value for key, value in node.items() if key not in {"children", "content"}}
        filtered["title"] = title
        filtered["content"] = ""
        filtered["toc_view_role"] = "review-heading"
        filtered["children"] = children
        return [filtered]

    children = visit(tree)
    return {
        "schema": "luceon-toc-review-tree/v1",
        "type": "root",
        "title": "TOC Review View",
        "metadata": "",
        "content": "",
        "level": 0,
        "location": [],
        "block_ids": [],
        "children": children,
    }


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


def _source_pages_from_node(node: dict[str, Any]) -> list[int]:
    pages: set[int] = set()
    for key in ("page", "page_number", "pageNumber"):
        value = node.get(key)
        if isinstance(value, int):
            pages.add(value)
        elif isinstance(value, str) and value.isdigit():
            pages.add(int(value))
    raw_pages = node.get("pages")
    if isinstance(raw_pages, list):
        for value in raw_pages:
            if isinstance(value, int):
                pages.add(value)
            elif isinstance(value, str) and value.isdigit():
                pages.add(int(value))
    location = node.get("location") or node.get("locations")
    if isinstance(location, list):
        for item in location:
            if isinstance(item, dict):
                for key in ("page", "page_number", "pageNumber"):
                    value = item.get(key)
                    if isinstance(value, int):
                        pages.add(value)
                    elif isinstance(value, str) and value.isdigit():
                        pages.add(int(value))
            elif isinstance(item, int):
                pages.add(item)
    return sorted(page for page in pages if page > 0)


def _source_block_ids_from_node(node: dict[str, Any]) -> list[str]:
    block_ids: list[str] = []
    raw = node.get("block_ids") or node.get("blockIds") or []
    if isinstance(raw, list):
        block_ids.extend(str(value) for value in raw if value is not None)
    for key in ("id", "source_id", "sourceId"):
        value = node.get(key)
        if value is not None:
            block_ids.append(str(value))
    seen: set[str] = set()
    unique: list[str] = []
    for value in block_ids:
        if value and value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _canonical_title_kind(title: str) -> tuple[str, dict[str, Any], list[str]]:
    clean = _toc_text(title).strip()
    compact = _toc_compact(clean)
    lower = clean.lower()
    warnings: list[str] = []
    metadata: dict[str, Any] = {}

    if not clean:
        return "unknown_heading", metadata, ["empty-title"]
    if compact in {"glossary", "glossary"} or lower.strip(" >〉") == "glossary":
        return "glossary", metadata, warnings
    if compact == "index" or lower.strip(" >〉") == "index":
        return "index", metadata, warnings
    if "pastpaperquestions" in compact:
        return "past_paper", metadata, warnings
    if "practicequestions" in compact:
        return "practice", metadata, warnings

    exercise = re.match(r"^exercise\s*([0-9]+(?:\.[0-9]+)*)", lower)
    if exercise:
        metadata["number"] = exercise.group(1)
        metadata["major"] = int(exercise.group(1).split(".")[0])
        return "exercise", metadata, warnings

    unit = re.match(r"^[>〉]?\s*unit\s*([0-9]+)\b", lower)
    if unit:
        metadata["number"] = unit.group(1)
        if compact.endswith("project"):
            warnings.append("unit-project-treated-as-unit-boundary")
        return "unit", metadata, warnings

    section = re.match(r"^([0-9]{1,2})\.([0-9]{1,2})(?:\.([0-9]{1,2}))?", clean)
    if section:
        metadata["number"] = f"{int(section.group(1))}.{int(section.group(2))}"
        metadata["major"] = int(section.group(1))
        metadata["minor"] = int(section.group(2))
        return "section", metadata, warnings

    numbered = re.match(r"^([0-9]{1,2})\s*[A-Za-z]", clean)
    if numbered:
        metadata["number"] = str(int(numbered.group(1)))
        metadata["major"] = int(numbered.group(1))
        return "chapter", metadata, warnings

    if len(clean) > 90:
        warnings.append("long-heading-needs-review")
    if re.search(r"[a-z]{12,}", clean):
        warnings.append("possible-ocr-merged-word")
    return "chapter", metadata, warnings


def _strip_contents_page_number(text: str) -> str:
    return re.sub(r"\s+\d{1,4}\s*$", "", text).strip()


def _contents_line(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"^#+\s*", "", text.strip())
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_contents_excerpt(markdown_text: str | None) -> str:
    if not markdown_text:
        return ""
    match = re.search(r"(?im)^#{1,3}\s*>?\s*contents\s*$", markdown_text)
    if not match:
        match = re.search(r"(?i)\bcontents\b", markdown_text)
    if not match:
        return ""
    start = match.start()
    tail = markdown_text[match.end():]
    end_match = re.search(r"(?im)^#{1,3}\s*>?\s*(introduction|how\s*to\s*use|acknowledgements?)\b", tail)
    if end_match:
        return markdown_text[start:match.end() + end_match.start()]
    glossary = re.search(r"(?im)^.*\bindex\s+\d{1,4}\s*$", tail[:40000])
    if glossary:
        return markdown_text[start:match.end() + glossary.end()]
    return markdown_text[start:start + 40000]


def _parse_contents_outline(markdown_text: str | None) -> list[dict[str, Any]]:
    excerpt = _extract_contents_excerpt(markdown_text)
    if not excerpt:
        return []
    raw_lines = [_contents_line(line) for line in excerpt.splitlines()]
    lines = [line for line in raw_lines if line]
    entries: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    heading_buffer: list[str] = []
    seen_chapter_numbers: set[int] = set()

    def append_entry(entry: dict[str, Any]) -> None:
        entries.append(entry)
        if entry.get("kind") == "chapter" and isinstance(entry.get("major"), int):
            seen_chapter_numbers.add(entry["major"])

    def flush_pending() -> None:
        nonlocal pending
        if pending:
            pending["title"] = _strip_contents_page_number(pending["title"])
            if pending["title"]:
                append_entry(pending)
        pending = None

    def reset_heading_buffer() -> None:
        heading_buffer.clear()

    def remember_heading(line: str) -> None:
        title = _strip_contents_page_number(line)
        lower = _toc_compact(title)
        if not title:
            return
        if lower in {"contents", "introduction", "howtousethisbook", "howtousethisseries", "acknowledgements"}:
            return
        if re.match(r"^(pastpaperquestions|unit[0-9]+project|glossary|index)\b", lower, re.I):
            return
        heading_buffer.append(title)
        del heading_buffer[:-3]

    def infer_chapter_before_section(major: int) -> None:
        if major in seen_chapter_numbers or not heading_buffer:
            return
        title = " ".join(heading_buffer).strip()
        if not title:
            return
        append_entry({
            "kind": "chapter",
            "title": f"{major} {title}".strip(),
            "number": str(major),
            "major": major,
            "source": "contents",
            "metadata": {
                "inferred": True,
                "inference": "following-section-major",
                "source_lines": list(heading_buffer),
            },
            "warnings": ["inferred_chapter_from_following_section"],
        })
        reset_heading_buffer()

    for line in lines:
        lower = line.lower()
        if lower in {"contents", "> contents"}:
            continue
        if lower in {"introduction", "howtouse thisbook", "howto use this series", "acknowledgements"}:
            continue

        unit = re.match(r"^(?:##\s*)?unit\s*([1-9][0-9]*)\b", line, re.I)
        project = re.match(r"^unit\s*([1-9][0-9]*)\s*project\b", line, re.I)
        section = re.match(r"^([0-9]{1,2})\.([0-9]{1,2})\s*(.*)$", line)
        chapter = re.match(r"^([0-9]{1,2})\s*([^\d].*)$", line)
        past = re.match(r"^past\s*paper\s*questions\s*for\s*unit\s*([0-9]+)", line, re.I)
        glossary = re.match(r"^glossary\b", line, re.I)
        index = re.match(r"^index\b", line, re.I)

        starts_new = bool(unit or project or section or chapter or past or glossary or index)
        if starts_new:
            flush_pending()

        if unit and not project:
            reset_heading_buffer()
            append_entry({
                "kind": "unit",
                "title": f"Unit {int(unit.group(1))}",
                "number": str(int(unit.group(1))),
                "source": "contents",
            })
        elif project:
            reset_heading_buffer()
            append_entry({
                "kind": "chapter",
                "title": f"Unit {int(project.group(1))} Project",
                "number": f"project-{int(project.group(1))}",
                "source": "contents",
                "metadata": {"project_unit": int(project.group(1))},
            })
        elif section:
            infer_chapter_before_section(int(section.group(1)))
            pending = {
                "kind": "section",
                "title": f"{int(section.group(1))}.{int(section.group(2))} {_strip_contents_page_number(section.group(3))}".strip(),
                "number": f"{int(section.group(1))}.{int(section.group(2))}",
                "major": int(section.group(1)),
                "minor": int(section.group(2)),
                "source": "contents",
            }
            if re.search(r"\s+\d{1,4}\s*$", line):
                flush_pending()
        elif chapter and 1 <= int(chapter.group(1)) <= 99:
            reset_heading_buffer()
            pending = {
                "kind": "chapter",
                "title": f"{int(chapter.group(1))} {_strip_contents_page_number(chapter.group(2))}".strip(),
                "number": str(int(chapter.group(1))),
                "major": int(chapter.group(1)),
                "source": "contents",
            }
            if re.search(r"\s+\d{1,4}\s*$", line):
                flush_pending()
        elif past:
            reset_heading_buffer()
            append_entry({
                "kind": "past_paper",
                "title": f"Past paper questions for Unit {int(past.group(1))}",
                "number": str(int(past.group(1))),
                "source": "contents",
            })
        elif glossary:
            reset_heading_buffer()
            append_entry({"kind": "glossary", "title": "Glossary", "source": "contents"})
        elif index:
            reset_heading_buffer()
            append_entry({"kind": "index", "title": "Index", "source": "contents"})
        elif pending:
            pending["title"] = f"{pending['title']} {_strip_contents_page_number(line)}".strip()
        else:
            remember_heading(line)

    flush_pending()
    return entries


def _canonical_node_id(index: int) -> str:
    return f"toc-{index:04d}"


def _rawlatex_path_for(node_id: str, kind: str, title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        slug = "untitled"
    return f"rawlatex/{node_id}_{kind}_{slug[:64]}.tex"


def _collect_review_candidates(review_tree: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def collect(node: dict[str, Any], depth: int) -> None:
        title = _toc_text(node.get("title")).strip()
        if depth > 0 and title:
            order = len(candidates) + 1
            kind, kind_meta, warnings = _canonical_title_kind(title)
            block_ids = _source_block_ids_from_node(node)
            pages = _source_pages_from_node(node)
            if not block_ids:
                warnings = [*warnings, "missing-source-block-ids"]
            if not pages:
                warnings = [*warnings, "missing-source-page-range"]
            candidates.append({
                "node_id": _canonical_node_id(order),
                "kind": kind,
                "title": title,
                "original_title": str(node.get("title") or ""),
                "source_order": order,
                "source_depth": depth,
                "source_block_ids": block_ids,
                "source_page_range": [pages[0], pages[-1]] if pages else [],
                "source_pages": pages,
                "confidence": 0.9 if not warnings else 0.65,
                "warnings": warnings,
                "metadata": kind_meta,
                "children": [],
            })
        for child in node.get("children") or []:
            if isinstance(child, dict):
                collect(child, depth + 1)

    collect(review_tree, 0)
    return candidates


def _best_candidate_for_entry(entry: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    kind = entry.get("kind")
    number = str(entry.get("number") or "")
    title_compact = _toc_compact(entry.get("title") or "")
    ranked: list[tuple[int, dict[str, Any]]] = []
    for candidate in candidates:
        c_kind = candidate.get("kind")
        c_number = str(candidate.get("metadata", {}).get("number") or "")
        c_title_compact = _toc_compact(candidate.get("title") or "")
        if kind in {"chapter", "section", "exercise"} and c_kind != kind:
            continue
        if number and kind in {"chapter", "section", "exercise"} and c_number != number:
            continue
        score = 0
        if number and c_number == number:
            score += 100
        if kind == c_kind:
            score += 25
        if title_compact and (title_compact in c_title_compact or c_title_compact in title_compact):
            score += 10
        if kind in {"glossary", "index"} and c_kind == kind:
            score += 80
        if kind == "past_paper" and c_kind == "past_paper" and number in c_title_compact:
            score += 80
        if score > 0:
            ranked.append((score, candidate))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1].get("source_order") or 0))
    return ranked[0][1]


def _make_canonical_node_from_contents(entry: dict[str, Any], index: int, candidate: dict[str, Any] | None) -> dict[str, Any]:
    warnings = ["source:contents", *(entry.get("warnings") or [])]
    source_block_ids: list[str] = []
    source_page_range: list[int] = []
    source_pages: list[int] = []
    if candidate:
        source_block_ids = list(candidate.get("source_block_ids") or [])
        source_page_range = list(candidate.get("source_page_range") or [])
        source_pages = list(candidate.get("source_pages") or [])
        warnings.extend(candidate.get("warnings") or [])
    else:
        warnings.append("missing-body-tree-match")
    if not source_block_ids:
        warnings.append("missing-source-block-ids")
    if not source_page_range:
        warnings.append("missing-source-page-range")
    metadata = dict(entry.get("metadata") or {})
    for key in ("number", "major", "minor"):
        if entry.get(key) is not None:
            metadata[key] = entry.get(key)
    return {
        "node_id": _canonical_node_id(index),
        "kind": entry["kind"],
        "title": entry["title"],
        "original_title": entry["title"],
        "source_order": index,
        "source_depth": 1,
        "source_block_ids": source_block_ids,
        "source_page_range": source_page_range,
        "source_pages": source_pages,
        "confidence": 0.85 if candidate else 0.55,
        "warnings": warnings,
        "metadata": metadata,
        "children": [],
    }


def _compile_canonical_toc_from_contents(review_tree: dict[str, Any], contents_outline: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = _collect_review_candidates(review_tree)
    root = {
        "node_id": "toc-root",
        "kind": "root",
        "title": "Canonical TOC",
        "original_title": review_tree.get("title") or "",
        "source_order": 0,
        "source_depth": 0,
        "source_block_ids": [],
        "source_page_range": [],
        "source_pages": [],
        "confidence": 1.0,
        "warnings": ["contents-first"],
        "metadata": {},
        "children": [],
    }

    nodes: list[dict[str, Any]] = []
    nodes_by_id: dict[str, dict[str, Any]] = {"toc-root": root}
    current_unit: dict[str, Any] | None = None
    current_chapter: dict[str, Any] | None = None
    section_by_number: dict[str, dict[str, Any]] = {}

    def attach(parent: dict[str, Any], child: dict[str, Any]) -> None:
        child["parent_id"] = parent["node_id"]
        parent["children"].append(child)
        nodes_by_id[child["node_id"]] = child
        nodes.append(child)

    for entry in contents_outline:
        node = _make_canonical_node_from_contents(entry, len(nodes) + 1, _best_candidate_for_entry(entry, candidates))
        kind = node["kind"]
        if kind == "unit":
            attach(root, node)
            current_unit = node
            current_chapter = None
        elif kind in {"glossary", "index"}:
            attach(root, node)
            current_chapter = None
        elif kind == "chapter":
            attach(current_unit or root, node)
            current_chapter = node
        elif kind == "section":
            major = node.get("metadata", {}).get("major")
            if current_chapter is None or (isinstance(major, int) and str(current_chapter.get("metadata", {}).get("number")) != str(major)):
                chapter_match = next(
                    (
                        existing for existing in reversed(nodes)
                        if existing.get("kind") == "chapter"
                        and str(existing.get("metadata", {}).get("number")) == str(major)
                    ),
                    None,
                )
                current_chapter = chapter_match
            attach(current_chapter or current_unit or root, node)
            if node.get("metadata", {}).get("number"):
                section_by_number[str(node["metadata"]["number"])] = node
        elif kind in {"past_paper", "practice"}:
            attach(current_unit or root, node)
        else:
            attach(current_chapter or current_unit or root, node)

    existing_exercises: set[str] = set()
    for candidate in candidates:
        if candidate.get("kind") != "exercise":
            continue
        number = str(candidate.get("metadata", {}).get("number") or "")
        if not number or number in existing_exercises:
            continue
        parent = section_by_number.get(number)
        if not parent:
            major = number.split(".")[0]
            parent = next(
                (
                    existing for existing in reversed(nodes)
                    if existing.get("kind") == "chapter"
                    and str(existing.get("metadata", {}).get("number")) == major
                ),
                None,
            )
        exercise = {
            **candidate,
            "node_id": _canonical_node_id(len(nodes) + 1),
            "warnings": [*(candidate.get("warnings") or []), "source:body-tree-exercise"],
        }
        attach(parent or current_unit or root, exercise)
        existing_exercises.add(number)

    return {
        "schema": "luceon-canonical-toc/v1",
        "source_schema": review_tree.get("schema") or "unknown",
        "compiler": "luceon-layer3-deterministic-rules/contents-first",
        "root": root,
        "stats": {
            "node_count": len(nodes),
            "warning_count": sum(len(node.get("warnings") or []) for node in nodes),
            "kind_counts": {
                kind: sum(1 for node in nodes if node["kind"] == kind)
                for kind in sorted({node["kind"] for node in nodes})
            },
            "contents_outline_count": len(contents_outline),
        },
    }


def _compile_canonical_toc(review_tree: dict[str, Any], contents_markdown: str | None = None) -> dict[str, Any]:
    contents_outline = _parse_contents_outline(contents_markdown)
    if contents_outline:
        return _compile_canonical_toc_from_contents(review_tree, contents_outline)

    candidates = _collect_review_candidates(review_tree)

    root = {
        "node_id": "toc-root",
        "kind": "root",
        "title": "Canonical TOC",
        "original_title": review_tree.get("title") or "",
        "source_order": 0,
        "source_depth": 0,
        "source_block_ids": [],
        "source_page_range": [],
        "source_pages": [],
        "confidence": 1.0,
        "warnings": [],
        "metadata": {},
        "children": [],
    }

    nodes_by_id: dict[str, dict[str, Any]] = {"toc-root": root}
    current_unit: dict[str, Any] | None = None
    current_chapter: dict[str, Any] | None = None
    current_section: dict[str, Any] | None = None
    last_major: int | None = None

    def attach(parent: dict[str, Any], child: dict[str, Any]) -> None:
        child["parent_id"] = parent["node_id"]
        parent["children"].append(child)
        nodes_by_id[child["node_id"]] = child

    for node in candidates:
        kind = node["kind"]
        major = node["metadata"].get("major")
        if isinstance(major, int) and last_major is not None and major < last_major:
            node["warnings"].append("numbering-regression")
            node["confidence"] = min(node["confidence"], 0.55)
        if isinstance(major, int):
            last_major = max(last_major or major, major)

        if kind == "unit":
            attach(root, node)
            current_unit = node
            current_chapter = None
            current_section = None
        elif kind in {"glossary", "index"}:
            attach(root, node)
            current_chapter = None
            current_section = None
        elif kind == "chapter":
            parent = current_unit or root
            attach(parent, node)
            current_chapter = node
            current_section = None
        elif kind == "section":
            parent = current_chapter or current_unit or root
            attach(parent, node)
            current_section = node
        elif kind in {"exercise", "practice", "past_paper"}:
            parent = current_section or current_chapter or current_unit or root
            attach(parent, node)
        else:
            parent = current_section or current_chapter or current_unit or root
            attach(parent, node)

    return {
        "schema": "luceon-canonical-toc/v1",
        "source_schema": review_tree.get("schema") or "unknown",
        "compiler": "luceon-layer3-deterministic-rules",
        "root": root,
        "stats": {
            "node_count": len(candidates),
            "warning_count": sum(len(node.get("warnings") or []) for node in candidates),
            "kind_counts": {
                kind: sum(1 for node in candidates if node["kind"] == kind)
                for kind in sorted({node["kind"] for node in candidates})
            },
        },
    }


def _iter_canonical_nodes(canonical_toc: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []

    def visit(node: dict[str, Any]) -> None:
        nodes.append(node)
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child)

    root = canonical_toc.get("root")
    if isinstance(root, dict):
        visit(root)
    return nodes


def _compile_chapter_spans(canonical_toc: dict[str, Any]) -> dict[str, Any]:
    spans: list[dict[str, Any]] = []

    def subtree_trace(node: dict[str, Any]) -> tuple[list[int], list[str], list[int]]:
        orders: list[int] = []
        block_ids: list[str] = []
        pages: list[int] = []

        def visit(current: dict[str, Any]) -> None:
            order = current.get("source_order")
            if isinstance(order, int) and order > 0:
                orders.append(order)
            block_ids.extend(str(value) for value in current.get("source_block_ids") or [])
            pages.extend(value for value in current.get("source_pages") or [] if isinstance(value, int))
            for child in current.get("children") or []:
                if isinstance(child, dict):
                    visit(child)

        visit(node)
        return orders, sorted(set(block_ids)), sorted(set(pages))

    for node in _iter_canonical_nodes(canonical_toc):
        if node.get("node_id") == "toc-root":
            continue
        orders, block_ids, pages = subtree_trace(node)
        warnings = list(node.get("warnings") or [])
        if node.get("children"):
            warnings.append("hierarchical-span-contains-child-spans")
        if not orders:
            warnings.append("missing-source-order-range")
        spans.append({
            "node_id": node["node_id"],
            "kind": node["kind"],
            "title": node["title"],
            "parent_id": node.get("parent_id"),
            "source_order_range": [min(orders), max(orders)] if orders else [],
            "source_page_range": [pages[0], pages[-1]] if pages else [],
            "source_block_ids": block_ids,
            "asset_refs": [],
            "formula_refs": [],
            "table_refs": [],
            "image_refs": [],
            "warnings": warnings,
            "confidence": node.get("confidence", 0.5),
        })

    return {
        "schema": "luceon-chapter-spans/v1",
        "span_semantics": "hierarchical; parent spans may contain child spans and are explicitly warned",
        "spans": spans,
        "stats": {
            "span_count": len(spans),
            "warning_count": sum(len(span.get("warnings") or []) for span in spans),
        },
    }


def _compile_rawlatex_scaffold(canonical_toc: dict[str, Any], chapter_spans: dict[str, Any]) -> dict[str, Any]:
    span_by_id = {span["node_id"]: span for span in chapter_spans.get("spans") or []}
    files: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    container_kinds = {"unit", "chapter", "section", "exercise", "practice", "past_paper", "glossary", "index"}
    for node in _iter_canonical_nodes(canonical_toc):
        if node.get("node_id") == "toc-root" or node.get("kind") not in container_kinds:
            continue
        span = span_by_id.get(node["node_id"], {})
        path = _rawlatex_path_for(node["node_id"], node["kind"], node["title"])
        tex = "\n".join([
            f"% Luceon RawLaTeX scaffold: {node['node_id']}",
            f"% kind: {node['kind']}",
            f"% title: {node['title']}",
            f"% source_order_range: {span.get('source_order_range') or []}",
            f"% source_page_range: {span.get('source_page_range') or []}",
            f"% source_block_ids: {span.get('source_block_ids') or []}",
            f"% warnings: {span.get('warnings') or []}",
            f"\\section*{{{node['title']}}}",
            "% TODO(cleanlatex): clean only within the source span above. Do not move chapter boundaries.",
            "",
        ])
        files.append({
            "path": path,
            "node_id": node["node_id"],
            "kind": node["kind"],
            "title": node["title"],
            "content": tex,
            "source_span": span,
        })
        manifest_entries.append({
            "path": path,
            "node_id": node["node_id"],
            "kind": node["kind"],
            "title": node["title"],
        })

    return {
        "schema": "luceon-rawlatex-scaffold/v1",
        "compiler": "luceon-layer3-deterministic-rules",
        "manifest": {
            "entrypoint": "rawlatex/manifest.json",
            "file_count": len(files),
            "files": manifest_entries,
        },
        "files": files,
        "rules": [
            "No LLM call was used to decide whole-book structure.",
            "No new textbook content is invented by this scaffold.",
            "Later CleanLaTeX must clean only inside source-bound chapter containers.",
        ],
    }


def _cleanlatex_pack_selection_policy() -> dict[str, Any]:
    return {
        "schema": "luceon-cleanlatex-pack-selection-policy/v1",
        "primary_candidate_levels": [3, 4],
        "assembly_levels": [1, 2],
        "inline_child_levels": [4, 5],
        "hard_limits": {
            "max_pages": 8,
            "max_blocks": 120,
            "max_chars": 18000,
            "max_images": 12,
            "max_tables": 8,
            "max_formulas": 80,
        },
        "soft_targets": {
            "target_pages": 1,
            "target_blocks": 40,
            "target_chars": 6000,
        },
        "selection_order": [
            "source_span_continuity",
            "stable_parent_boundary",
            "content_size",
            "child_count",
            "asset_density",
            "semantic_hint",
        ],
    }


def _source_hash(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _source_nodes_by_block_id(source_tree: dict[str, Any], asset_index: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}

    def visit(node: dict[str, Any], path: list[str]) -> None:
        title = _toc_text(node.get("title")).strip()
        content = str(node.get("content") or "").strip()
        order = len(by_id) + 1
        pages = _source_pages_from_node(node)
        block_ids = _source_block_ids_from_node(node)
        row = {
            "source_order": order,
            "title": title,
            "content": content,
            "type": str(node.get("type") or "text"),
            "source_block_ids": block_ids,
            "page": pages[0] if pages else None,
            "pages": pages,
            "bbox": node.get("bbox") or node.get("box") or [],
            "location": node.get("location") or [],
            "path": [*path, *([title] if title else [])],
            "source_hash": _source_hash({
                "title": title,
                "content": content,
                "block_ids": block_ids,
                "page": pages,
                "bbox": node.get("bbox") or node.get("box") or [],
            }),
        }
        asset = _asset_for_source_node(node, asset_index)
        if asset:
            row["asset_refs"] = [{
                "kind": asset.get("kind"),
                "asset_hash_name": asset.get("asset_hash_name"),
                "raw_ref": asset.get("raw_ref"),
                "source_page": asset.get("page"),
                "bbox": asset.get("bbox") or [],
            }]
            row["asset_hash_names"] = [asset.get("asset_hash_name")]
        for block_id in block_ids:
            by_id.setdefault(str(block_id), row)
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, row["path"])

    visit(source_tree, [])
    return by_id


def _cleanlatex_block_type(source_row: dict[str, Any]) -> str:
    raw_type = _toc_compact(source_row.get("type") or "")
    text = f"{source_row.get('title') or ''}\n{source_row.get('content') or ''}"
    if "image" in raw_type:
        return "image"
    if "table" in raw_type:
        return "table"
    if "formula" in raw_type or re.search(r"\$[^$]+\$|\\begin\{(?:equation|align|gather)", text):
        return "formula"
    if re.search(r"(?i)^exercise\s*\d|^\(?[0-9]+\)?[.)]", str(source_row.get("title") or "").strip()):
        return "question_like"
    if re.search(r"(?i)worked\s*example|example\s*\d", str(source_row.get("title") or "")):
        return "example_like"
    if source_row.get("title") and not source_row.get("content"):
        return "title"
    return "text"


def _asset_hash_names_from_text(text: str) -> list[str]:
    matches = re.findall(r"\b[0-9a-fA-F]{16,}\.(?:png|jpe?g|webp|gif|svg)\b", text or "")
    seen: set[str] = set()
    result: list[str] = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            result.append(match)
    return result


def _asset_hash_name_from_path(value: Any) -> str | None:
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        return None
    name = text.rsplit("/", 1)[-1]
    if re.match(r"^[0-9a-fA-F]{16,}\.(?:png|jpe?g|webp|gif|svg)$", name):
        return name
    return None


def _visual_reference_terms(text: str) -> list[str]:
    terms = [
        "flow diagram",
        "diagram",
        "figure",
        "chart",
        "graph",
        "illustration",
        "image",
        "picture",
    ]
    found: list[str] = []
    for term in terms:
        pattern = r"\b" + re.escape(term).replace(r"\ ", r"\s*") + r"\b"
        if re.search(pattern, text or "", flags=re.IGNORECASE):
            found.append(term)
    return found


def _mineru_asset_index_from_content_bytes(content_bytes: bytes | None) -> dict[str, list[dict[str, Any]]]:
    if not content_bytes:
        return {"images": [], "tables": []}
    try:
        payload = json.loads(content_bytes.decode("utf-8", errors="replace"))
    except Exception:
        return {"images": [], "tables": []}
    if not isinstance(payload, list):
        return {"images": [], "tables": []}

    assets = {"images": [], "tables": []}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "").lower()
        if item_type not in {"image", "table"}:
            continue
        raw_path = item.get("img_path") or item.get("image_path") or item.get("path")
        asset_hash_name = _asset_hash_name_from_path(raw_path)
        if not asset_hash_name:
            continue
        page = None
        if isinstance(item.get("page"), int):
            page = item.get("page")
        elif isinstance(item.get("page_idx"), int):
            page = int(item.get("page_idx")) + 1
        asset = {
            "kind": "image" if item_type == "image" else "table",
            "asset_hash_name": asset_hash_name,
            "raw_ref": str(raw_path or ""),
            "source_index": index,
            "source_order": index + 1,
            "page": page,
            "bbox": item.get("bbox") or [],
        }
        assets["images" if item_type == "image" else "tables"].append(asset)
    return assets


def _asset_for_source_node(node: dict[str, Any], asset_index: dict[str, list[dict[str, Any]]] | None) -> dict[str, Any] | None:
    if not asset_index:
        return None
    node_type = str(node.get("type") or node.get("source_label") or "").lower()
    candidates = asset_index.get("images" if "image" in node_type else "tables" if "table" in node_type else "") or []
    if not candidates:
        return None
    source_id = str(node.get("source_id") or "")
    source_index = None
    match = re.search(r":(\d+)$", source_id)
    if match:
        source_index = int(match.group(1))
    pages = _source_pages_from_node(node)
    bbox = node.get("bbox") or node.get("box") or []
    for asset in candidates:
        if source_index is not None and asset.get("source_index") == source_index:
            return asset
    for asset in candidates:
        if pages and asset.get("page") not in pages:
            continue
        if bbox and _bbox_equivalent(asset.get("bbox"), bbox):
            return asset
    return None


def _normalized_bbox(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) < 4:
        return []
    numbers: list[float] = []
    for item in value[:4]:
        try:
            numbers.append(float(item))
        except Exception:
            return []
    scale = 1000.0 if max(abs(item) for item in numbers) > 10 else 1.0
    return [item / scale for item in numbers]


def _bbox_equivalent(left: Any, right: Any, tolerance: float = 0.005) -> bool:
    left_box = _normalized_bbox(left)
    right_box = _normalized_bbox(right)
    if len(left_box) != 4 or len(right_box) != 4:
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(left_box, right_box))


def _content_block_from_source_row(block_id: str, source_row: dict[str, Any]) -> dict[str, Any]:
    raw_text = "\n".join(
        value for value in [str(source_row.get("title") or "").strip(), str(source_row.get("content") or "").strip()]
        if value
    )
    block_type = _cleanlatex_block_type(source_row)
    block = {
        "block_id": str(block_id),
        "source_block_ids": list(source_row.get("source_block_ids") or [str(block_id)]),
        "source_order": source_row.get("source_order"),
        "page": source_row.get("page"),
        "pages": source_row.get("pages") or [],
        "bbox": source_row.get("bbox") or [],
        "type": block_type,
        "raw_text": raw_text,
        "normalized_text": None,
        "source_hash": source_row.get("source_hash"),
        "warnings": [],
    }
    if block_type == "image":
        block["asset_hash_names"] = list(source_row.get("asset_hash_names") or _asset_hash_names_from_text(raw_text))
        block["asset_refs"] = list(source_row.get("asset_refs") or [])
    if block_type == "formula":
        block["latex"] = raw_text
        block["source_format"] = "mineru-popo"
    if block_type == "table":
        block["asset_hash_names"] = list(source_row.get("asset_hash_names") or _asset_hash_names_from_text(raw_text))
        block["asset_refs"] = list(source_row.get("asset_refs") or [])
        block["raw_markdown"] = raw_text
        block["raw_html"] = None
        block["cells"] = []
    return block


def _iter_source_nodes(source_tree: dict[str, Any]):
    def visit(node: dict[str, Any]):
        yield node
        for child in node.get("children") or []:
            if isinstance(child, dict):
                yield from visit(child)

    yield from visit(source_tree)


def _related_asset_blocks_for_span(
    source_tree: dict[str, Any],
    source_block_ids: list[str],
    source_by_block_id: dict[str, dict[str, Any]],
    asset_index: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    source_id_set = {str(value) for value in source_block_ids}
    blocks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in _iter_source_nodes(source_tree):
        node_type = str(node.get("type") or node.get("source_label") or "").lower()
        if "image" not in node_type and "table" not in node_type:
            continue
        node_ids = _source_block_ids_from_node(node)
        linked_values: list[str] = []
        for key in ("image", "table", "contd"):
            value = node.get(key)
            if isinstance(value, int) and value >= 0:
                linked_values.append(str(value))
            elif isinstance(value, str) and value:
                linked_values.append(value)
        if not (source_id_set.intersection(node_ids) or source_id_set.intersection(linked_values)):
            continue
        asset = _asset_for_source_node(node, asset_index)
        if not asset:
            continue
        block_id = node_ids[0] if node_ids else f"{asset.get('kind')}-{asset.get('source_order')}"
        asset_hash_name = asset.get("asset_hash_name")
        key = f"{block_id}:{asset_hash_name}"
        if key in seen:
            continue
        seen.add(key)
        source_row = source_by_block_id.get(str(block_id)) or {
            "source_block_ids": node_ids or [str(block_id)],
            "source_order": asset.get("source_order"),
            "page": asset.get("page"),
            "pages": [asset.get("page")] if asset.get("page") else [],
            "bbox": asset.get("bbox") or [],
            "type": node_type,
            "title": "",
            "content": "",
            "source_hash": _source_hash({
                "asset_hash_name": asset_hash_name,
                "page": asset.get("page"),
                "bbox": asset.get("bbox") or [],
            }),
        }
        enriched = {
            **source_row,
            "type": "image" if asset.get("kind") == "image" else "table",
            "asset_hash_names": [asset_hash_name],
            "asset_refs": [{
                "kind": asset.get("kind"),
                "asset_hash_name": asset_hash_name,
                "raw_ref": asset.get("raw_ref"),
                "source_page": asset.get("page"),
                "bbox": asset.get("bbox") or [],
            }],
        }
        blocks.append(_content_block_from_source_row(str(block_id), enriched))
    return blocks


def _canonical_node_depths(canonical_toc: dict[str, Any]) -> dict[str, int]:
    depths: dict[str, int] = {}

    def visit(node: dict[str, Any], depth: int) -> None:
        node_id = str(node.get("node_id") or "")
        if node_id:
            depths[node_id] = depth
        for child in node.get("children") or []:
            if isinstance(child, dict):
                visit(child, depth + 1)

    root = canonical_toc.get("root")
    if isinstance(root, dict):
        visit(root, 0)
    return depths


def _ancestor_path_for_node(node: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    path: list[dict[str, Any]] = []
    current = node
    while current.get("parent_id"):
        parent = nodes_by_id.get(str(current.get("parent_id")))
        if not parent or parent.get("node_id") == "toc-root":
            break
        path.append({
            "node_id": parent.get("node_id"),
            "canonical_kind": parent.get("kind"),
            "title": parent.get("title"),
        })
        current = parent
    return list(reversed(path))


def _build_cleanlatex_prompt(pack: dict[str, Any]) -> str:
    lines = [
        "# CleanLaTeX Cleaning Unit Pack",
        "",
        "## Identity",
        "You clean exactly one source-bound structural cleaning unit.",
        "The semantic label is guidance only; it does not define or change the boundary.",
        "",
        "## Structural Boundary",
        f"- Pack id: {pack['pack_id']}",
        f"- Node id: {pack['node']['node_id']}",
        f"- Pack level: {pack['pack_boundary']['pack_level']}",
        f"- Canonical kind: {pack['node']['canonical_kind']}",
        f"- Title: {pack['node']['title']}",
        f"- Parent: {pack['node'].get('parent_title') or ''}",
        f"- Source pages: {pack['source_span'].get('source_page_range') or []}",
        f"- Source block ids: {pack['source_span'].get('source_block_ids') or []}",
        "",
        "## Non-Negotiable Rules",
        "- Do not create, delete, reorder, or rename book structure.",
        "- Do not move content outside this pack.",
        "- Do not invent textbook content.",
        "- Preserve image hash names exactly.",
        "- Preserve source block id references.",
        "- Return JSON matching luceon-cleanlatex-output/v1.",
        "",
        "## Source Blocks",
    ]
    for block in pack.get("content_blocks") or []:
        lines.extend([
            "",
            f"### {block.get('block_id')} [{block.get('type')}]",
            f"- page: {block.get('page')}",
            f"- source_order: {block.get('source_order')}",
            f"- asset_hash_names: {block.get('asset_hash_names') or []}",
            "",
            str(block.get("raw_text") or ""),
        ])
    lines.extend([
        "",
        "## Assets",
    ])
    for image in pack.get("assets", {}).get("images") or []:
        lines.append(
            f"- image: {image.get('asset_hash_name')} page={image.get('source_page')} "
            f"source_blocks={image.get('source_block_ids') or []}"
        )
    for table in pack.get("assets", {}).get("tables") or []:
        if isinstance(table, dict):
            lines.append(
                f"- table: {table.get('asset_hash_name') or table.get('block_id')} "
                f"page={table.get('source_page') or table.get('page')} "
                f"source_blocks={table.get('source_block_ids') or []}"
            )
    lines.extend([
        "",
        "## Visual Evidence Requirements",
    ])
    for requirement in pack.get("visual_evidence_requirements") or []:
        lines.append(
            f"- terms={requirement.get('terms') or []}; status={requirement.get('status')}; "
            f"linked_asset_hash_names={requirement.get('linked_asset_hash_names') or []}; "
            f"required_action={requirement.get('required_action')}"
        )
    lines.extend([
        "",
        "## Required Output",
        "Return only a JSON object that conforms to luceon-cleanlatex-output/v1.",
    ])
    return "\n".join(lines)


def _compile_cleanlatex_pilot_packs(
    canonical_toc: dict[str, Any],
    chapter_spans: dict[str, Any],
    source_tree: dict[str, Any],
    material_id: str,
    asset_version: str,
    asset_index: dict[str, list[dict[str, Any]]] | None = None,
    pilot_numbers: tuple[str, ...] = ("1.1", "4.1"),
) -> dict[str, Any]:
    policy = _cleanlatex_pack_selection_policy()
    nodes = [node for node in _iter_canonical_nodes(canonical_toc) if node.get("node_id") != "toc-root"]
    nodes_by_id = {str(node.get("node_id")): node for node in nodes}
    depths = _canonical_node_depths(canonical_toc)
    span_by_node_id = {str(span.get("node_id")): span for span in chapter_spans.get("spans") or []}
    source_by_block_id = _source_nodes_by_block_id(source_tree, asset_index)

    selected_nodes: list[dict[str, Any]] = []
    for number in pilot_numbers:
        node = next(
            (
                item for item in nodes
                if item.get("kind") not in {"unit", "chapter", "root"}
                and str(item.get("metadata", {}).get("number") or "") == number
            ),
            None,
        )
        if node:
            selected_nodes.append(node)

    packs: list[dict[str, Any]] = []
    prompts: dict[str, str] = {}
    validations: list[dict[str, Any]] = []
    for node in selected_nodes:
        node_id = str(node.get("node_id"))
        span = span_by_node_id.get(node_id, {})
        source_block_ids = [str(value) for value in span.get("source_block_ids") or node.get("source_block_ids") or []]
        content_blocks: list[dict[str, Any]] = []
        unresolved_block_ids: list[str] = []
        for block_id in source_block_ids:
            source_row = source_by_block_id.get(block_id)
            if source_row:
                content_blocks.append(_content_block_from_source_row(block_id, source_row))
            else:
                unresolved_block_ids.append(block_id)
        content_blocks.extend(_related_asset_blocks_for_span(source_tree, source_block_ids, source_by_block_id, asset_index))
        content_blocks.sort(key=lambda block: (block.get("source_order") or 0, block.get("block_id") or ""))

        image_assets: dict[str, dict[str, Any]] = {}
        table_assets: dict[str, dict[str, Any]] = {}
        for block in content_blocks:
            for ref in block.get("asset_refs") or []:
                name = ref.get("asset_hash_name")
                if not name:
                    continue
                target = image_assets if ref.get("kind") == "image" else table_assets
                target.setdefault(name, {
                    "asset_hash_name": name,
                    "source_page": ref.get("source_page"),
                    "bbox": ref.get("bbox") or [],
                    "raw_ref": ref.get("raw_ref"),
                    "source_block_ids": block.get("source_block_ids") or [block.get("block_id")],
                })
            for name in block.get("asset_hash_names") or _asset_hash_names_from_text(block.get("raw_text") or ""):
                if not name:
                    continue
                image_assets.setdefault(name, {
                    "asset_hash_name": name,
                    "source_page": block.get("page"),
                    "bbox": block.get("bbox") or [],
                    "raw_ref": f"images/{name}",
                    "source_block_ids": block.get("source_block_ids") or [block.get("block_id")],
                })
        combined_text = "\n".join(str(block.get("raw_text") or "") for block in content_blocks)
        visual_terms = _visual_reference_terms(combined_text)
        visual_requirements: list[dict[str, Any]] = []
        if visual_terms or image_assets:
            visual_requirements.append({
                "terms": visual_terms,
                "status": "asset-linked" if image_assets else "asset-missing",
                "required_action": "preserve_asset_reference_or_report_unresolved",
                "source_block_ids": source_block_ids,
                "linked_asset_hash_names": sorted(image_assets.keys()),
            })
        parent = nodes_by_id.get(str(node.get("parent_id")))
        pack_level = depths.get(node_id, 0)
        block_chars = sum(len(str(block.get("raw_text") or "")) for block in content_blocks)
        pack_id = f"cleaning-unit:{node_id}"
        pack = {
            "schema": "luceon-cleanlatex-cleaning-unit-pack/v1",
            "pack_id": pack_id,
            "material_id": material_id,
            "asset_version": asset_version,
            "node": {
                "node_id": node_id,
                "canonical_kind": node.get("kind"),
                "semantic_label": node.get("kind"),
                "title": node.get("title"),
                "number": node.get("metadata", {}).get("number"),
                "parent_id": node.get("parent_id"),
                "parent_title": parent.get("title") if parent else None,
                "ancestor_path": _ancestor_path_for_node(node, nodes_by_id),
            },
            "pack_boundary": {
                "pack_level": pack_level,
                "pack_role": "primary_cleaning_unit",
                "boundary_basis": "structure-level",
                "selection_reason": [
                    "stable_parent",
                    "continuous_source_span",
                    "content_size_within_limit" if block_chars <= policy["hard_limits"]["max_chars"] else "content_size_exceeds_limit",
                    "pilot_requested",
                ],
                "semantic_kind_is_boundary_driver": False,
            },
            "source_span": {
                "source_order_range": span.get("source_order_range") or [],
                "source_page_range": span.get("source_page_range") or [],
                "source_block_ids": source_block_ids,
                "unresolved_source_block_ids": unresolved_block_ids,
            },
            "content_blocks": content_blocks,
            "child_units": [
                {
                    "node_id": child.get("node_id"),
                    "canonical_kind": child.get("kind"),
                    "title": child.get("title"),
                    "source_block_ids": child.get("source_block_ids") or [],
                }
                for child in node.get("children") or []
                if isinstance(child, dict)
            ],
            "assets": {
                "images": [image_assets[name] for name in sorted(image_assets)],
                "tables": [*([table_assets[name] for name in sorted(table_assets)]), *[block for block in content_blocks if block.get("type") == "table" and not block.get("asset_hash_names")]],
                "formulas": [block for block in content_blocks if block.get("type") == "formula"],
                "audio": [],
            },
            "visual_evidence_requirements": visual_requirements,
            "cleaning_contract": {
                "unit": "cleaning_unit",
                "may_clean_ocr_text": True,
                "may_normalize_math_latex": True,
                "may_reorder_within_pack": True,
                "must_not_change_node_id": True,
                "must_not_change_parent_id": True,
                "must_not_create_or_delete_book_structure": True,
                "must_not_move_blocks_outside_pack": True,
                "must_preserve_source_block_ids": True,
                "must_preserve_asset_hash_names": True,
                "must_report_unresolved_items": True,
                "semantic_guidance": {
                    "canonical_kind": node.get("kind"),
                    "do_not_answer_questions": node.get("kind") == "exercise",
                },
            },
            "expected_output": {
                "schema": "luceon-cleanlatex-output/v1",
                "output_role": "cleaning_unit_cleanlatex",
                "path": _rawlatex_path_for(node_id, str(node.get("kind") or "unit"), str(node.get("title") or "")),
            },
            "warnings": [*(node.get("warnings") or []), *([] if content_blocks else ["empty-pack-content-blocks"])],
        }
        prompts[pack_id] = _build_cleanlatex_prompt(pack)
        validations.append({
            "schema": "luceon-cleanlatex-validation-manifest/v1",
            "pack_id": pack_id,
            "pack_level": pack_level,
            "selection_policy": policy["schema"],
            "input_counts": {
                "blocks": len(content_blocks),
                "images": len(pack["assets"]["images"]),
                "formulas": len(pack["assets"]["formulas"]),
                "tables": len(pack["assets"]["tables"]),
                "unresolved_source_blocks": len(unresolved_block_ids),
            },
            "output_checks": {
                "source_block_coverage": "pending",
                "asset_hash_preservation": "pending",
                "latex_parse": "pending",
                "forbidden_custom_commands": "pending",
                "structure_boundary": "pending",
            },
        })
        packs.append(pack)

    return {
        "schema": "luceon-cleanlatex-pack-manifest/v1",
        "compiler": "luceon-layer3-deterministic-rules/cleanlatex-pack-generator-pilot",
        "selection_policy": policy,
        "pilot_numbers": list(pilot_numbers),
        "packs": packs,
        "prompts": prompts,
        "validation_manifests": validations,
        "stats": {
            "pack_count": len(packs),
            "content_block_count": sum(len(pack.get("content_blocks") or []) for pack in packs),
            "unresolved_source_block_count": sum(len(pack.get("source_span", {}).get("unresolved_source_block_ids") or []) for pack in packs),
            "asset_hash_count": sum(len(pack.get("assets", {}).get("images") or []) for pack in packs),
        },
    }


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

    content_bytes, pdf_bytes, provenance_input_ref, provenance_input_bytes, markdown_text = _prepare_inputs(client, payload, work_dir, material_id)

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
    canonical_toc = _compile_canonical_toc(toc_view_tree, markdown_text)
    chapter_spans = _compile_chapter_spans(canonical_toc)
    rawlatex_scaffold = _compile_rawlatex_scaffold(canonical_toc, chapter_spans)
    mineru_asset_index = _mineru_asset_index_from_content_bytes(content_bytes)
    cleanlatex_pack_manifest = _compile_cleanlatex_pilot_packs(
        canonical_toc,
        chapter_spans,
        tree,
        material_id,
        asset_version,
        mineru_asset_index,
    )
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
        "mineru_asset_index": {
            "images": len(mineru_asset_index.get("images") or []),
            "tables": len(mineru_asset_index.get("tables") or []),
        },
        "unresolved_anchor_count": 0,
        "cost_cny_actual": 0,
        "canonical_toc": canonical_toc.get("stats", {}),
        "chapter_spans": chapter_spans.get("stats", {}),
        "rawlatex_scaffold": {
            "file_count": rawlatex_scaffold.get("manifest", {}).get("file_count", 0),
        },
        "cleanlatex_packs": cleanlatex_pack_manifest.get("stats", {}),
        "contents_first": {
            "enabled": bool(markdown_text and canonical_toc.get("stats", {}).get("contents_outline_count")),
            "outline_count": canonical_toc.get("stats", {}).get("contents_outline_count", 0),
        },
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
        "output_views": {
            "raw_tree": "official_popo_tree.json",
            "review_tree": "toc_view.json",
            "canonical_toc": "canonical_toc.json",
            "chapter_spans": "chapter_spans.json",
            "rawlatex_scaffold": "rawlatex_scaffold.json",
            "cleanlatex_pack_manifest": "cleanlatex_pack_manifest.json",
            "cleaning_unit_packs": "cleaning_unit_packs.json",
            "cleaning_unit_prompts": "cleaning_unit_prompts.json",
            "compat_logic_tree": "logic_tree.json",
        },
        "contents_first": {
            "enabled": bool(markdown_text and canonical_toc.get("stats", {}).get("contents_outline_count")),
            "outline_count": canonical_toc.get("stats", {}).get("contents_outline_count", 0),
        },
    }

    artifacts = {
        "flooded_content": _put_json(client, sink_bucket, f"{sink_prefix}flooded_content.json", flooded_content),
        "logic_tree": _put_json(client, sink_bucket, f"{sink_prefix}logic_tree.json", toc_view_tree),
        "readable_tree": _put_text(client, sink_bucket, f"{sink_prefix}readable_tree.md", readable, "text/markdown"),
        "toc_view": _put_json(client, sink_bucket, f"{sink_prefix}toc_view.json", toc_view_tree),
        "review_tree": _put_json(client, sink_bucket, f"{sink_prefix}review_tree.json", toc_view_tree),
        "canonical_toc": _put_json(client, sink_bucket, f"{sink_prefix}canonical_toc.json", canonical_toc),
        "chapter_spans": _put_json(client, sink_bucket, f"{sink_prefix}chapter_spans.json", chapter_spans),
        "rawlatex_scaffold": _put_json(client, sink_bucket, f"{sink_prefix}rawlatex_scaffold.json", rawlatex_scaffold),
        "cleanlatex_pack_manifest": _put_json(client, sink_bucket, f"{sink_prefix}cleanlatex_pack_manifest.json", {
            key: value for key, value in cleanlatex_pack_manifest.items()
            if key not in {"packs", "prompts", "validation_manifests"}
        }),
        "cleaning_unit_packs": _put_json(client, sink_bucket, f"{sink_prefix}cleaning_unit_packs.json", cleanlatex_pack_manifest.get("packs") or []),
        "cleaning_unit_prompts": _put_json(client, sink_bucket, f"{sink_prefix}cleaning_unit_prompts.json", cleanlatex_pack_manifest.get("prompts") or {}),
        "cleanlatex_validation_manifests": _put_json(client, sink_bucket, f"{sink_prefix}cleanlatex_validation_manifests.json", cleanlatex_pack_manifest.get("validation_manifests") or []),
        "official_popo_tree": _put_json(client, sink_bucket, f"{sink_prefix}official_popo_tree.json", tree),
        "raw_tree": _put_json(client, sink_bucket, f"{sink_prefix}raw_tree.json", tree),
        "skeleton": _put_json(client, sink_bucket, f"{sink_prefix}skeleton.json", {
            "source": "mineru-popo",
            "normalized_input": f"outputs/label_normalization/mineru/{material_id}.json",
            "review_view": f"{sink_prefix}toc_view.json",
            "canonical_toc": f"{sink_prefix}canonical_toc.json",
            "chapter_spans": f"{sink_prefix}chapter_spans.json",
            "rawlatex_scaffold": f"{sink_prefix}rawlatex_scaffold.json",
            "cleanlatex_pack_manifest": f"{sink_prefix}cleanlatex_pack_manifest.json",
            "cleaning_unit_packs": f"{sink_prefix}cleaning_unit_packs.json",
            "raw_tree": f"{sink_prefix}official_popo_tree.json",
        }),
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
