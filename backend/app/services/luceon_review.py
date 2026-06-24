import json
import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.minio_client import get_presigned_url, minio_client

try:
    from minio.error import S3Error
except ImportError:  # pragma: no cover
    S3Error = None


_MISSING_CODES = {"NoSuchKey", "NoSuchObject", "NoSuchBucket", "NotFound"}


@dataclass(frozen=True)
class ObjectRef:
    bucket: str
    object: str

    def as_dict(self) -> dict[str, str]:
        return {"bucket": self.bucket, "object": self.object}


@dataclass(frozen=True)
class ResolvedReviewAsset:
    title: str
    input_filename: str
    review_stage: str
    material_id: str
    run_id: str
    manifest: dict[str, Any]
    manifest_ref: ObjectRef
    input_pdf: ObjectRef | None
    source_pdf: ObjectRef | None
    markdown: ObjectRef | None
    page_markdown: ObjectRef | None
    popo_markdown: ObjectRef | None
    middle_json: ObjectRef | None


def clean_path(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/").lstrip("/")
    parts = [part for part in path.split("/") if part and part not in {".", ".."}]
    return "/".join(parts)


def read_object(bucket: str, object_name: str) -> bytes:
    response = minio_client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        close = getattr(response, "close", None)
        if close:
            close()
        release_conn = getattr(response, "release_conn", None)
        if release_conn:
            release_conn()


def list_manifest_objects(
    bucket: str = "eduassets-minerupopo",
    prefix: str = "minerupopo/",
    limit: int | None = None,
) -> list[str]:
    normalized_prefix = clean_path(prefix).rstrip("/") + "/" if prefix else ""
    rows = []

    if normalized_prefix == "minerupopo/":
        for material_item in minio_client.list_objects(bucket, prefix=normalized_prefix, recursive=False):
            raw_material_prefix = str(getattr(material_item, "object_name", "") or "").replace("\\", "/").lstrip("/")
            if not raw_material_prefix.endswith("/") and not getattr(material_item, "is_dir", False):
                continue
            material_prefix = clean_path(raw_material_prefix).rstrip("/") + "/"
            for run_item in minio_client.list_objects(bucket, prefix=material_prefix, recursive=False):
                raw_run_prefix = str(getattr(run_item, "object_name", "") or "").replace("\\", "/").lstrip("/")
                if raw_run_prefix.endswith("/") or getattr(run_item, "is_dir", False):
                    run_prefix = clean_path(raw_run_prefix).rstrip("/") + "/"
                    rows.append(f"{run_prefix}manifest.json")
                    if limit and len(rows) >= limit:
                        return sorted(rows)
        return sorted(rows)

    for item in minio_client.list_objects(bucket, prefix=normalized_prefix, recursive=True):
        object_name = clean_path(getattr(item, "object_name", ""))
        if object_name.endswith("/manifest.json"):
            rows.append(object_name)
            if limit and len(rows) >= limit:
                break
    return sorted(rows)


def list_input_pdf_objects(bucket: str = "eduassets-input", prefix: str = "", limit: int | None = None) -> list[str]:
    rows = []
    for item in minio_client.list_objects(bucket, prefix=prefix, recursive=True):
        object_name = clean_path(getattr(item, "object_name", ""))
        if object_name.lower().endswith(".pdf"):
            rows.append(object_name)
            if limit and len(rows) >= limit:
                break
    return sorted(rows)


def object_exists(bucket: str, object_name: str) -> bool:
    try:
        minio_client.stat_object(bucket, object_name)
        return True
    except Exception as exc:
        if is_missing_object_error(exc):
            return False
        raise


def is_missing_object_error(exc: Exception) -> bool:
    if isinstance(exc, FileNotFoundError):
        return True
    if S3Error and isinstance(exc, S3Error):
        return exc.code in _MISSING_CODES
    return False


def parse_json_bytes(data: bytes) -> dict[str, Any]:
    parsed = json.loads(data.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("manifest must be a JSON object")
    return parsed


def ref_from_value(value: Any, default_bucket: str = "") -> ObjectRef | None:
    if isinstance(value, dict):
        bucket = str(value.get("bucket") or default_bucket or "").strip()
        object_name = clean_path(value.get("object") or value.get("key") or value.get("path"))
        if bucket and object_name:
            return ObjectRef(bucket=bucket, object=object_name)
    if isinstance(value, str) and default_bucket:
        object_name = clean_path(value)
        if object_name:
            return ObjectRef(bucket=default_bucket, object=object_name)
    return None


def pick_ref(manifest: dict[str, Any], keys: tuple[str, ...], default_bucket: str = "") -> ObjectRef | None:
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    for key in keys:
        ref = ref_from_value(objects.get(key), default_bucket)
        if ref:
            return ref
        ref = ref_from_value(manifest.get(key), default_bucket)
        if ref:
            return ref
    return None


def infer_review_stage(manifest: dict[str, Any], manifest_ref: ObjectRef) -> str:
    schema = str(manifest.get("schema") or "").lower()
    bucket = manifest_ref.bucket.lower()
    object_name = manifest_ref.object.lower()
    explicit = str(manifest.get("review_stage") or manifest.get("asset_stage") or manifest.get("stage") or "").lower()
    for value in (explicit, schema, bucket, object_name):
        if "clean" in value:
            return "clean"
        if "raw" in value:
            return "raw"
    return "parse"


def first_existing(candidates: list[ObjectRef | None]) -> ObjectRef | None:
    for ref in candidates:
        if ref and object_exists(ref.bucket, ref.object):
            return ref
    return None


def infer_ids_from_manifest_path(manifest_object: str) -> tuple[str, str]:
    parts = clean_path(manifest_object).split("/")
    if len(parts) >= 4 and parts[-1] == "manifest.json":
        return parts[-3], parts[-2]
    return "", ""


def stage_prefix(manifest: dict[str, Any], stage: str, bucket: str, fallback_prefix: str) -> tuple[str, str]:
    stages = manifest.get("stage_prefixes") if isinstance(manifest.get("stage_prefixes"), dict) else {}
    value = stages.get(stage) if isinstance(stages.get(stage), dict) else {}
    return (
        str(value.get("bucket") or bucket),
        clean_path(value.get("prefix") or fallback_prefix).rstrip("/") + "/",
    )


def official_prefix(manifest: dict[str, Any], stage: str, prefix: str) -> str:
    stages = manifest.get("stage_prefixes") if isinstance(manifest.get("stage_prefixes"), dict) else {}
    value = stages.get(stage) if isinstance(stages.get(stage), dict) else {}
    return clean_path(value.get("official_prefix") or posixpath.join(prefix, "official")).rstrip("/") + "/"


def resolve_manifest(bucket: str, object_name: str, title: str = "", check_fallbacks: bool = True) -> ResolvedReviewAsset:
    manifest_ref = ObjectRef(bucket=bucket, object=clean_path(object_name))
    manifest = parse_json_bytes(read_object(manifest_ref.bucket, manifest_ref.object))

    parsed_material_id, parsed_run_id = infer_ids_from_manifest_path(manifest_ref.object)
    material_id = str(manifest.get("material_id") or parsed_material_id or "").strip()
    run_id = str(manifest.get("run_id") or parsed_run_id or "").strip()

    mineru_bucket, mineru_prefix = stage_prefix(
        manifest,
        "mineru",
        "eduassets-mineru",
        f"mineru/{material_id}/{run_id}/" if material_id and run_id else "",
    )
    popo_bucket, popo_prefix = stage_prefix(
        manifest,
        "minerupopo",
        bucket,
        f"minerupopo/{material_id}/{run_id}/" if material_id and run_id else "",
    )
    mineru_official = official_prefix(manifest, "mineru", mineru_prefix)

    source_pdf = (
        ref_from_value(manifest.get("source_pdf"))
        or pick_ref(manifest, ("source_pdf",), "eduassets-parsed")
        or (
            ObjectRef("eduassets-parsed", f"source-pdf/{material_id}/{run_id}/source.pdf")
            if material_id and run_id
            else None
        )
    )
    source_pdf_meta = manifest.get("source_pdf") if isinstance(manifest.get("source_pdf"), dict) else {}
    input_pdf = (
        ref_from_value(
            {
                "bucket": source_pdf_meta.get("input_bucket"),
                "object": source_pdf_meta.get("input_object"),
            }
        )
        or pick_ref(manifest, ("input_pdf", "input"), "eduassets-input")
    )

    middle_json = pick_ref(manifest, ("middle", "middle_json", "middle_json_v2"), mineru_bucket)
    if check_fallbacks and not middle_json and material_id:
        stem = Path(material_id).name
        middle_json = first_existing(
            [
                ObjectRef(mineru_bucket, f"{mineru_official}{stem}_middle.json"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}{stem}_middle.json"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}middle.json"),
            ]
        )

    markdown = pick_ref(manifest, ("full_md", "markdown", "md", "raw_markdown"), mineru_bucket)
    if check_fallbacks and not markdown and material_id:
        stem = Path(material_id).name
        markdown = first_existing(
            [
                ObjectRef(mineru_bucket, f"{mineru_official}{stem}.md"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}{stem}.md"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}full.md"),
            ]
        )

    page_markdown = pick_ref(manifest, ("pages_md", "markdown_page", "page_markdown"), mineru_bucket)
    if check_fallbacks and not page_markdown and material_id:
        stem = Path(material_id).name
        page_markdown = first_existing(
            [
                ObjectRef(mineru_bucket, f"{mineru_official}{stem}_pages.md"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}{stem}_pages.md"),
                ObjectRef(mineru_bucket, f"{mineru_prefix}pages.md"),
            ]
        )

    popo_markdown = pick_ref(
        manifest,
        ("document_tree_txt", "rebuilt_markdown", "popo_markdown", "markdown_popo"),
        popo_bucket,
    )
    if check_fallbacks and not popo_markdown and popo_prefix:
        popo_markdown = first_existing(
            [
                ObjectRef(popo_bucket, f"{popo_prefix}document_tree.txt"),
                ObjectRef(popo_bucket, f"{popo_prefix}build_tree_txt.txt"),
            ]
        )

    input_filename = str(source_pdf_meta.get("filename") or "").strip()
    if not input_filename and input_pdf:
        input_filename = Path(input_pdf.object).name
    display_title = title.strip() or input_filename or material_id or Path(manifest_ref.object).parent.name

    return ResolvedReviewAsset(
        title=display_title,
        input_filename=input_filename,
        review_stage=infer_review_stage(manifest, manifest_ref),
        material_id=material_id,
        run_id=run_id,
        manifest=manifest,
        manifest_ref=manifest_ref,
        input_pdf=input_pdf,
        source_pdf=source_pdf,
        markdown=markdown,
        page_markdown=page_markdown,
        popo_markdown=popo_markdown,
        middle_json=middle_json,
    )


def presigned(ref: ObjectRef, expires: int = 3600) -> str:
    return get_presigned_url(ref.bucket, ref.object, expires=expires)
