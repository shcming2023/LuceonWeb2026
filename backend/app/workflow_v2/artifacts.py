from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import os
import zipfile
from datetime import datetime
from pathlib import Path

from PIL import Image

from sqlalchemy.orm import Session

from app.workflow_v2.models import ArtifactVersion, StageRun, WorkflowJob


ARTIFACT_BUCKET = os.getenv("WORKFLOW_ARTIFACT_BUCKET", "eduassets-elegantbook")
ARTIFACT_ROOT = "worker-v2"
DELIVERY_IMAGE_MAX_BYTES = 1_000_000
DELIVERY_ZIP_MAX_BYTES = 50_000_000


class ArtifactIntegrityError(RuntimeError):
    pass


def publish_stage_directory(
    db: Session,
    client,
    *,
    job: WorkflowJob,
    stage: StageRun,
    source_dir: Path,
    artifact_kind: str,
    contract: dict,
) -> ArtifactVersion:
    files = _inventory(source_dir)
    if not files:
        raise ArtifactIntegrityError("stage output directory is empty")
    manifest = {
        "schema": "luceon.workflow.artifact-manifest/v1",
        "workflow_job_id": job.public_id,
        "material_id": job.material_id,
        "workflow_version": job.workflow_version,
        "stage": {"key": stage.stage_key, "version": stage.stage_version, "attempt": stage.attempt},
        "contract": contract,
        "source_popo_manifest": {"bucket": job.source_popo_bucket, "object": job.source_popo_object},
        "files": files,
    }
    manifest_bytes = canonical_json_bytes(manifest)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    prefix = f"{ARTIFACT_ROOT}/{job.material_id}/{job.public_id}/{stage.stage_key}/attempt-{stage.attempt}/{manifest_sha256}"
    for entry in files:
        path = source_dir / entry["path"]
        _put_immutable(client, ARTIFACT_BUCKET, f"{prefix}/files/{entry['path']}", path.read_bytes(), entry["sha256"], entry["content_type"])
    manifest_object = f"{prefix}/manifest.json"
    _put_immutable(client, ARTIFACT_BUCKET, manifest_object, manifest_bytes, manifest_sha256, "application/json")
    identity_hash = hashlib.sha256(f"{ARTIFACT_BUCKET}\n{manifest_object}".encode()).hexdigest()
    existing = db.query(ArtifactVersion).filter(ArtifactVersion.object_identity_hash == identity_hash).first()
    if existing:
        if existing.sha256 != manifest_sha256:
            raise ArtifactIntegrityError("registered artifact identity has a different digest")
        return existing
    artifact = ArtifactVersion(
        workflow_job_id=job.id,
        stage_run_id=stage.id,
        artifact_kind=artifact_kind,
        bucket=ARTIFACT_BUCKET,
        object_name=manifest_object,
        object_identity_hash=identity_hash,
        sha256=manifest_sha256,
        size_bytes=len(manifest_bytes),
        content_type="application/json",
        status="candidate",
        immutable=True,
        metadata_json=ArtifactVersion.dump({"file_count": len(files), "created_at": datetime.utcnow().isoformat()}),
    )
    db.add(artifact)
    db.flush()
    return artifact


def canonical_json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_reproducible_zip(
    source_dir: Path,
    destination: Path,
    *,
    max_size_bytes: int | None = None,
    exclude_paths: set[str] | None = None,
) -> dict:
    source_root = source_dir.resolve()
    destination = destination.resolve()
    excluded = {Path(path).as_posix() for path in (exclude_paths or set())}
    files = sorted(
        path for path in source_root.rglob("*")
        if path.is_file()
        and path.resolve() != destination
        and path.relative_to(source_root).as_posix() not in excluded
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    content = destination.read_bytes()
    result = {
        "path": destination.name,
        "file_count": len(files),
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if max_size_bytes is not None and result["size_bytes"] > max_size_bytes:
        raise ArtifactIntegrityError(
            f"delivery ZIP exceeds size limit: {result['size_bytes']} > {max_size_bytes} bytes"
        )
    return result


LATEX_DELIVERY_ROOT_FILES = ("main.tex", "elegantbook.cls")
LATEX_DELIVERY_FIGURE_FILES = ("figure/logo.jpg", "figure/cover.jpg")


def write_latex_delivery_zip(
    source_dir: Path,
    destination: Path,
    *,
    max_size_bytes: int | None = DELIVERY_ZIP_MAX_BYTES,
) -> dict:
    """Write the locked four-entry LaTeX delivery shape and reject any drift."""
    source_root = source_dir.resolve()
    destination = destination.resolve()
    required_files = (*LATEX_DELIVERY_ROOT_FILES, *LATEX_DELIVERY_FIGURE_FILES)
    missing = [name for name in required_files if not (source_root / name).is_file()]
    if not (source_root / "images").is_dir():
        missing.append("images/")
    if not (source_root / "figure").is_dir():
        missing.append("figure/")
    if missing:
        raise ArtifactIntegrityError(f"LaTeX delivery is missing required paths: {', '.join(missing)}")

    unexpected_figure_files = sorted(
        path.relative_to(source_root).as_posix()
        for path in (source_root / "figure").rglob("*")
        if path.is_file() and path.relative_to(source_root).as_posix() not in LATEX_DELIVERY_FIGURE_FILES
    )
    if unexpected_figure_files:
        raise ArtifactIntegrityError(
            "LaTeX delivery figure/ contains files other than logo.jpg and cover.jpg: "
            + ", ".join(unexpected_figure_files)
        )

    image_files = sorted(path for path in (source_root / "images").rglob("*") if path.is_file())
    files = [*(source_root / name for name in LATEX_DELIVERY_ROOT_FILES)]
    files.extend(source_root / name for name in LATEX_DELIVERY_FIGURE_FILES)
    files.extend(image_files)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for directory in ("images/", "figure/"):
            info = zipfile.ZipInfo(directory, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = (0o40755 << 16) | 0x10
            info.create_system = 3
            archive.writestr(info, b"")
        for path in sorted(files, key=lambda item: item.relative_to(source_root).as_posix()):
            relative = path.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(destination) as archive:
        names = archive.namelist()
    allowed = {"images/", "figure/", *LATEX_DELIVERY_ROOT_FILES, *LATEX_DELIVERY_FIGURE_FILES}
    unexpected = sorted(
        name for name in names
        if name not in allowed and not name.startswith("images/")
    )
    if unexpected:
        destination.unlink(missing_ok=True)
        raise ArtifactIntegrityError(f"LaTeX delivery ZIP contains forbidden paths: {', '.join(unexpected)}")

    content = destination.read_bytes()
    result = {
        "path": destination.name,
        "file_count": len(files),
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "root_entries": ["images/", "figure/", "main.tex", "elegantbook.cls"],
    }
    if max_size_bytes is not None and result["size_bytes"] > max_size_bytes:
        raise ArtifactIntegrityError(
            f"delivery ZIP exceeds size limit: {result['size_bytes']} > {max_size_bytes} bytes"
        )
    return result


def optimize_delivery_images(
    project_dir: Path,
    *,
    max_image_bytes: int = DELIVERY_IMAGE_MAX_BYTES,
    max_zip_bytes: int = DELIVERY_ZIP_MAX_BYTES,
) -> dict:
    """Compress delivery copies in place while preserving image names and count."""
    image_dir = project_dir / "images"
    images = sorted(
        (
            path for path in image_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        ),
        key=lambda path: (-path.stat().st_size, path.as_posix()),
    ) if image_dir.exists() else []
    before = {path.relative_to(project_dir).as_posix(): path.stat().st_size for path in images}
    for path in images:
        _compress_image_to_limit(path, max_image_bytes)

    temporary_zip = project_dir / ".latex-size-check.zip"
    try:
        for _ in range(20):
            archive = write_latex_delivery_zip(project_dir, temporary_zip, max_size_bytes=None)
            if archive["size_bytes"] <= max_zip_bytes and all(
                path.stat().st_size <= max_image_bytes for path in images
            ):
                break
            for path in images:
                _resize_and_reencode(path, scale=0.9, quality=70)
        else:
            archive = write_latex_delivery_zip(project_dir, temporary_zip, max_size_bytes=None)
            raise ArtifactIntegrityError(
                f"delivery ZIP remains over size limit after image compression: "
                f"{archive['size_bytes']} > {max_zip_bytes} bytes"
            )
    finally:
        temporary_zip.unlink(missing_ok=True)

    after = {path.relative_to(project_dir).as_posix(): path.stat().st_size for path in images}
    return {
        "image_count": len(images),
        "filenames_preserved": set(before) == set(after),
        "before_bytes": sum(before.values()),
        "after_bytes": sum(after.values()),
        "max_image_bytes": max(after.values(), default=0),
        "max_image_limit_bytes": max_image_bytes,
        "max_zip_limit_bytes": max_zip_bytes,
    }


def _compress_image_to_limit(path: Path, max_bytes: int) -> None:
    if path.stat().st_size <= max_bytes:
        return
    for quality in (90, 80, 70, 60, 50, 40, 30, 20):
        _resize_and_reencode(path, scale=1.0, quality=quality)
        if path.stat().st_size <= max_bytes:
            return
    for _ in range(20):
        _resize_and_reencode(path, scale=0.85, quality=20)
        if path.stat().st_size <= max_bytes:
            return
    raise ArtifactIntegrityError(f"image remains over size limit after compression: {path}")


def _resize_and_reencode(path: Path, *, scale: float, quality: int) -> None:
    with Image.open(path) as source:
        image = source.convert("RGB") if path.suffix.lower() in {".jpg", ".jpeg"} else source.copy()
        if scale != 1.0:
            width = max(1, round(image.width * scale))
            height = max(1, round(image.height * scale))
            image = image.resize((width, height), Image.Resampling.LANCZOS)
        temporary = path.with_suffix(path.suffix + ".tmp")
        save_kwargs = {"optimize": True}
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            save_kwargs.update(format="JPEG", quality=quality, subsampling=0)
        else:
            save_kwargs.update(format="PNG")
        image.save(temporary, **save_kwargs)
    temporary.replace(path)


def materialize_artifact(client, artifact: ArtifactVersion, destination: Path) -> dict:
    manifest_bytes = _read_object(client, artifact.bucket, artifact.object_name)
    if hashlib.sha256(manifest_bytes).hexdigest() != artifact.sha256:
        raise ArtifactIntegrityError("artifact manifest digest mismatch")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    prefix = artifact.object_name.rsplit("/manifest.json", 1)[0]
    destination.mkdir(parents=True, exist_ok=True)
    for entry in manifest.get("files") or []:
        relative = Path(str(entry.get("path") or ""))
        if not relative.parts or relative.is_absolute() or ".." in relative.parts:
            raise ArtifactIntegrityError("unsafe artifact path")
        content = _read_object(client, artifact.bucket, f"{prefix}/files/{relative.as_posix()}")
        if hashlib.sha256(content).hexdigest() != entry.get("sha256"):
            raise ArtifactIntegrityError(f"artifact file digest mismatch: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return manifest


def _inventory(source_dir: Path) -> list[dict]:
    root = source_dir.resolve()
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        rows.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
                "content_type": mimetypes.guess_type(relative)[0] or "application/octet-stream",
            }
        )
    return rows


def _put_immutable(client, bucket: str, object_name: str, content: bytes, sha256: str, content_type: str) -> None:
    try:
        existing = client.stat_object(bucket, object_name)
    except Exception as exc:
        if not _is_not_found(exc):
            raise
    else:
        metadata = {str(key).lower(): str(value) for key, value in (getattr(existing, "metadata", {}) or {}).items()}
        existing_hash = metadata.get("x-amz-meta-sha256") or metadata.get("sha256")
        if existing_hash == sha256 and int(getattr(existing, "size", -1)) == len(content):
            return
        raise ArtifactIntegrityError(f"immutable object already exists with different content: {bucket}/{object_name}")
    client.put_object(
        bucket,
        object_name,
        io.BytesIO(content),
        len(content),
        content_type=content_type,
        metadata={"sha256": sha256},
    )


def _is_not_found(exc: Exception) -> bool:
    code = str(getattr(exc, "code", ""))
    return code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket", "NotFound", "XMinioInvalidObjectName"} or isinstance(exc, FileNotFoundError)


def _read_object(client, bucket: str, object_name: str) -> bytes:
    response = client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        if hasattr(response, "close"):
            response.close()
        if hasattr(response, "release_conn"):
            response.release_conn()
