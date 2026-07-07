from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.models.material import Material
from app.services.luceon_review import ObjectRef, clean_path, is_missing_object_error, minio_client, object_exists, read_object


ELEGANTBOOK_BUCKET = os.getenv("LUCEON_ELEGANTBOOK_BUCKET", "eduassets-elegantbook")
ELEGANTBOOK_PREFIX = clean_path(os.getenv("LUCEON_ELEGANTBOOK_PREFIX", "elegantbook")).rstrip("/") + "/"
LEGACY_LATEX_BUCKET = os.getenv("LUCEON_LEGACY_LATEX_BUCKET", "eduassets-latex")


@dataclass(frozen=True)
class ElegantBookOutput:
    manifest_ref: ObjectRef
    manifest: dict[str, Any]
    material_id: str
    popo_run_id: str
    output_run_id: str
    origin: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest_ref.as_dict(),
            "material_id": self.material_id,
            "popo_run_id": self.popo_run_id,
            "output_run_id": self.output_run_id,
            "origin": self.origin,
            "created_at": self.created_at,
        }


def parse_manifest_ref(ref: ObjectRef) -> dict[str, Any] | None:
    try:
        value = json.loads(read_object(ref.bucket, ref.object).decode("utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def list_codex_elegantbook_manifest_refs(material: Material, *, limit: int = 100) -> list[ObjectRef]:
    material_id = str(material.material_id or "").strip()
    popo_run_id = str(material.popo_run_id or "").strip()
    if not material_id:
        return []
    prefixes = [f"{ELEGANTBOOK_PREFIX}{material_id}/"]
    if popo_run_id:
        prefixes.insert(0, f"{ELEGANTBOOK_PREFIX}{material_id}/{popo_run_id}/")
    refs: list[ObjectRef] = []
    seen: set[tuple[str, str]] = set()
    for prefix in prefixes:
        try:
            items = minio_client.list_objects(ELEGANTBOOK_BUCKET, prefix=prefix, recursive=True)
            for item in items:
                object_name = clean_path(getattr(item, "object_name", ""))
                if not object_name.endswith("/manifest.json"):
                    continue
                key = (ELEGANTBOOK_BUCKET, object_name)
                if key in seen:
                    continue
                seen.add(key)
                refs.append(ObjectRef(ELEGANTBOOK_BUCKET, object_name))
                if len(refs) >= limit:
                    return refs
        except Exception as exc:
            if is_missing_object_error(exc):
                continue
            continue
    return refs


def list_all_codex_elegantbook_manifest_refs(*, limit: int | None = None) -> list[ObjectRef]:
    refs: list[ObjectRef] = []
    try:
        items = minio_client.list_objects(ELEGANTBOOK_BUCKET, prefix=ELEGANTBOOK_PREFIX, recursive=True)
        for item in items:
            object_name = clean_path(getattr(item, "object_name", ""))
            if not object_name.endswith("/manifest.json"):
                continue
            refs.append(ObjectRef(ELEGANTBOOK_BUCKET, object_name))
            if limit and len(refs) >= limit:
                break
    except Exception:
        return []
    return refs


def legacy_latex_manifest_ref(material: Material) -> ObjectRef | None:
    if material.latex_manifest_bucket and material.latex_manifest_object:
        return ObjectRef(material.latex_manifest_bucket, material.latex_manifest_object)
    material_id = str(material.material_id or "").strip()
    popo_run_id = str(material.popo_run_id or "").strip()
    if not material_id or not popo_run_id:
        return None
    ref = ObjectRef(LEGACY_LATEX_BUCKET, f"latex/{material_id}/{popo_run_id}/manifest.json")
    try:
        return ref if object_exists(ref.bucket, ref.object) else None
    except Exception:
        return None


def output_from_ref(ref: ObjectRef, material: Material, manifest: dict[str, Any] | None = None) -> ElegantBookOutput | None:
    manifest = manifest if isinstance(manifest, dict) else parse_manifest_ref(ref)
    if not isinstance(manifest, dict):
        return None
    material_id, popo_run_id, output_run_id = infer_ids(ref.object, manifest, material)
    return ElegantBookOutput(
        manifest_ref=ref,
        manifest=manifest,
        material_id=material_id,
        popo_run_id=popo_run_id,
        output_run_id=output_run_id,
        origin=classify_output(ref, manifest),
        created_at=str(manifest.get("created_at") or manifest.get("updated_at") or ""),
    )


def infer_ids(object_name: str, manifest: dict[str, Any], material: Material) -> tuple[str, str, str]:
    parts = clean_path(object_name).split("/")
    material_id = str(manifest.get("material_id") or material.material_id or "").strip()
    popo_run_id = str(manifest.get("popo_run_id") or material.popo_run_id or "").strip()
    output_run_id = str(manifest.get("codex_run_id") or manifest.get("output_run_id") or manifest.get("run_id") or "").strip()
    if len(parts) >= 5 and parts[-1] == "manifest.json":
        material_id = material_id or parts[-4]
        popo_run_id = popo_run_id or parts[-3]
        output_run_id = output_run_id or parts[-2]
    elif len(parts) >= 4 and parts[-1] == "manifest.json":
        material_id = material_id or parts[-3]
        popo_run_id = popo_run_id or str(manifest.get("run_id") or parts[-2]).strip()
    if not output_run_id:
        output_run_id = popo_run_id
    return material_id, popo_run_id, output_run_id


def classify_output(ref: ObjectRef, manifest: dict[str, Any]) -> str:
    text = json.dumps(manifest, ensure_ascii=False).lower()
    bucket = ref.bucket.lower()
    object_name = ref.object.lower()
    if "legacy_selfloop" in text or bucket == LEGACY_LATEX_BUCKET.lower() or object_name.startswith("latex/"):
        return "legacy_selfloop"
    if "refine-elegantbook-latex" in text or "latex_polish_report" in text or "editorial_decisions" in text:
        return "codex_refined"
    return "codex_elegantbook"


def output_priority(output: ElegantBookOutput) -> tuple[int, str, str]:
    origin_priority = {
        "codex_refined": 30,
        "codex_elegantbook": 20,
        "legacy_selfloop": 10,
    }.get(output.origin, 0)
    return (origin_priority, sortable_time(output.created_at), output.manifest_ref.object)


def sortable_time(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return raw


def list_elegantbook_outputs(material: Material) -> list[ElegantBookOutput]:
    outputs: list[ElegantBookOutput] = []
    seen: set[tuple[str, str]] = set()
    for ref in list_codex_elegantbook_manifest_refs(material):
        output = output_from_ref(ref, material)
        if output:
            seen.add((ref.bucket, ref.object))
            outputs.append(output)
    legacy_ref = legacy_latex_manifest_ref(material)
    if legacy_ref and (legacy_ref.bucket, legacy_ref.object) not in seen:
        output = output_from_ref(legacy_ref, material)
        if output:
            outputs.append(output)
    return sorted(outputs, key=output_priority, reverse=True)


def select_elegantbook_output(material: Material) -> ElegantBookOutput | None:
    outputs = list_elegantbook_outputs(material)
    return outputs[0] if outputs else None


def object_path(manifest: dict[str, Any], keys: tuple[str, ...], default: str) -> str:
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for key in keys:
        value = objects.get(key)
        if isinstance(value, dict):
            raw = value.get("object") or value.get("key") or value.get("path")
        else:
            raw = value
        cleaned = clean_path(raw)
        if cleaned:
            return cleaned
    return default


def output_artifact_paths(output: ElegantBookOutput) -> dict[str, str]:
    manifest = output.manifest
    return {
        "compiled_pdf": object_path(manifest, ("compiled_pdf", "pdf", "main_pdf"), "compiled.pdf"),
        "package_zip": object_path(
            manifest,
            ("refined_overleaf_zip", "package_zip", "latex_project_zip", "source_zip", "overleaf_zip"),
            "latex-project.zip",
        ),
        "compile_report": object_path(manifest, ("compile_report",), "compile_report.json"),
        "latex_polish_report": object_path(manifest, ("latex_polish_report", "polish_report"), "latex_polish_report.md"),
        "latex_polish_report_json": object_path(manifest, ("latex_polish_report_json", "polish_report_json"), "latex_polish_report.json"),
        "final_review_report": object_path(manifest, ("final_review_report",), "final_review_report.md"),
        "final_review_report_json": object_path(manifest, ("final_review_report_json",), "final_review_report.json"),
        "render_review": object_path(manifest, ("render_review",), "render_review.md"),
        "render_review_json": object_path(manifest, ("render_review_json",), "render_review.json"),
        "run_state": object_path(manifest, ("run_state",), "run_state.json"),
    }
