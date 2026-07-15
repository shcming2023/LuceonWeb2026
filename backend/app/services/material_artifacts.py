from __future__ import annotations

import json
import mimetypes
from typing import Any

from sqlalchemy.orm import Session

from app.models.material import Material
from app.services.codex_elegantbook import output_artifact_paths
from app.services.luceon_review import ObjectRef, clean_path, minio_client, read_object
from app.services.material_outputs import list_material_outputs, output_from_material_output


INPUT_BUCKET = "eduassets-input"
MINERU_BUCKET = "eduassets-mineru"
POPO_BUCKET = "eduassets-minerupopo"


class ArtifactNotFoundError(RuntimeError):
    pass


def _stat(bucket: str, object_name: str) -> dict[str, Any]:
    try:
        value = minio_client.stat_object(bucket, object_name)
    except Exception:
        return {}
    return {
        "size_bytes": int(getattr(value, "size", 0) or 0),
        "content_type": str(getattr(value, "content_type", "") or ""),
        "etag": str(getattr(value, "etag", "") or "").strip('"'),
        "last_modified": getattr(value, "last_modified", None),
    }


def _read_json(bucket: str, object_name: str) -> dict[str, Any]:
    try:
        value = json.loads(read_object(bucket, object_name).decode("utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _exists(bucket: str, object_name: str) -> bool:
    return bool(bucket and object_name and _stat(bucket, object_name))


def _record(
    *,
    artifact_id: str,
    kind: str,
    stage: str,
    label: str,
    bucket: str,
    object_name: str,
    filename: str,
    status: str,
    sha256: str = "",
    run_id: str = "",
    output_id: str = "",
    current: bool = False,
    candidate: bool = False,
    frozen: bool = False,
    created_at: str = "",
    size_bytes: int | None = None,
    content_type: str = "",
) -> dict[str, Any]:
    stat = _stat(bucket, object_name)
    available = bool(stat)
    resolved_size = int(size_bytes if size_bytes is not None else stat.get("size_bytes") or 0)
    media_type = content_type or str(stat.get("content_type") or "") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "stage": stage,
        "label": label,
        "filename": filename,
        "status": status,
        "verification_status": "frozen" if frozen else status,
        "run_id": run_id,
        "output_id": output_id,
        "current": current,
        "historical": not current,
        "candidate": candidate,
        "frozen": frozen,
        "download_available": available,
        "size_bytes": resolved_size,
        "sha256": sha256,
        "etag": str(stat.get("etag") or ""),
        "content_type": media_type,
        "created_at": created_at,
        "_ref": {"bucket": bucket, "object": object_name},
    }


def _manifest_objects(bucket: str, prefix: str, fallback: str = "") -> list[str]:
    values: set[str] = {fallback} if fallback else set()
    try:
        for item in minio_client.list_objects(bucket, prefix=prefix, recursive=True):
            object_name = clean_path(getattr(item, "object_name", ""))
            if object_name.endswith("/manifest.json"):
                values.add(object_name)
    except Exception:
        pass
    return sorted(value for value in values if value)


def _archive_ref(manifest: dict[str, Any]) -> tuple[str, str]:
    stages = manifest.get("stage_prefixes") if isinstance(manifest.get("stage_prefixes"), dict) else {}
    archive = stages.get("archive") if isinstance(stages.get("archive"), dict) else {}
    if archive.get("bucket") and archive.get("object"):
        return str(archive["bucket"]), clean_path(archive["object"])
    objects = manifest.get("objects") if isinstance(manifest.get("objects"), dict) else {}
    archive = objects.get("archive") if isinstance(objects.get("archive"), dict) else {}
    return str(archive.get("bucket") or ""), clean_path(archive.get("object") or "")


def _stage_records(material: Material, stage: str) -> list[dict[str, Any]]:
    if not material.material_id:
        return []
    bucket = MINERU_BUCKET if stage == "mineru" else POPO_BUCKET
    prefix = f"{stage if stage == 'mineru' else 'minerupopo'}/{material.material_id}/"
    fallback = material.mineru_manifest_object if stage == "mineru" else material.popo_manifest_object
    current_run = material.mineru_run_id if stage == "mineru" else material.popo_run_id
    marker_status = "mineru_done_frozen" if stage == "mineru" else "popo_done_frozen"
    records: list[dict[str, Any]] = []
    for manifest_object in _manifest_objects(bucket, prefix, fallback or ""):
        manifest = _read_json(bucket, manifest_object)
        if str(manifest.get("material_id") or "") != material.material_id:
            continue
        run_id = str(manifest.get("run_id") or "")
        if not run_id:
            parts = manifest_object.split("/")
            run_id = parts[-2] if len(parts) >= 2 else ""
        marker_object = f"_status/{material.material_id}/{run_id}.{marker_status}.json"
        frozen = _exists(INPUT_BUCKET, marker_object) or str(manifest.get("status") or "") == marker_status
        status = "frozen" if frozen else "legacy_unverified"
        created_at = str(manifest.get("created_at") or "")
        archive_bucket, archive_object = _archive_ref(manifest)
        archive_name = f"{material.material_id}-{run_id}-{stage}.tar.gz"
        archive_record = _record(
                artifact_id=f"{stage}~{run_id}~archive",
                kind=f"{stage}_archive",
                stage=stage,
                label=f"{stage.upper()} 冻结包",
                bucket=archive_bucket,
                object_name=archive_object,
                filename=archive_name,
                status=status if archive_object else "unavailable",
                sha256=str(manifest.get("archive_sha256") or ""),
                run_id=run_id,
                current=run_id == current_run,
                frozen=frozen,
                created_at=created_at,
                size_bytes=int(manifest.get("archive_size_bytes") or 0) or None,
                content_type="application/gzip",
            )
        manifest_record = _record(
                artifact_id=f"{stage}~{run_id}~manifest",
                kind=f"{stage}_manifest",
                stage=stage,
                label=f"{stage.upper()} Manifest",
                bucket=bucket,
                object_name=manifest_object,
                filename=f"{material.material_id}-{run_id}-{stage}-manifest.json",
                status=status,
                run_id=run_id,
                current=run_id == current_run,
                frozen=frozen,
                created_at=created_at,
                content_type="application/json",
            )
        if not frozen:
            archive_record["download_available"] = False
            manifest_record["download_available"] = False
        records.extend([archive_record, manifest_record])
    return records


def _manifest_file_metadata(manifest: dict[str, Any], relative_path: str) -> dict[str, Any]:
    normalized = relative_path.removeprefix("files/")
    for row in manifest.get("files") or []:
        if not isinstance(row, dict) or clean_path(row.get("path") or "") != normalized:
            continue
        return {
            "sha256": str(row.get("sha256") or ""),
            "size_bytes": int(row.get("size_bytes") or row.get("size") or 0) or None,
        }
    return {}


def _output_records(db: Session, user_id: str, material: Material) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in list_material_outputs(db, user_id, material):
        output = output_from_material_output(row, material)
        if not output:
            continue
        base = output.manifest_ref.object.rsplit("/", 1)[0] + "/"
        paths = output_artifact_paths(output)
        accepted = row.quality_status == "passed"
        output_status = "accepted" if accepted else row.status
        for key, label, filename in (
            ("package_zip", "LaTeX ZIP", f"{material.material_id}-{row.output_run_id or row.id}.zip"),
            ("compiled_pdf", "编译 PDF", f"{material.material_id}-{row.output_run_id or row.id}.pdf"),
            ("compile_report", "编译报告", "compile-report.json"),
            ("final_review_report_json", "质量报告", "core-acceptance.json"),
        ):
            relative_path = clean_path(paths.get(key) or "")
            if not relative_path:
                continue
            object_name = clean_path(f"{base}{relative_path}")
            metadata = _manifest_file_metadata(output.manifest, relative_path)
            records.append(
                _record(
                    artifact_id=f"output~{row.id}~{key}",
                    kind=key,
                    stage="elegantbook",
                    label=label,
                    bucket=output.manifest_ref.bucket,
                    object_name=object_name,
                    filename=filename,
                    status=output_status,
                    sha256=str(metadata.get("sha256") or ""),
                    run_id=row.output_run_id or "",
                    output_id=str(row.id),
                    current=bool(row.is_current),
                    candidate=not accepted,
                    frozen=accepted,
                    created_at=str(row.created_at.isoformat() if row.created_at else output.created_at),
                    size_bytes=metadata.get("size_bytes"),
                )
            )
        records.append(
            _record(
                artifact_id=f"output~{row.id}~manifest",
                kind="worker_manifest",
                stage="elegantbook",
                label="Worker 输出 Manifest",
                bucket=output.manifest_ref.bucket,
                object_name=output.manifest_ref.object,
                filename=f"{material.material_id}-{row.output_run_id or row.id}-manifest.json",
                status=output_status,
                run_id=row.output_run_id or "",
                output_id=str(row.id),
                current=bool(row.is_current),
                candidate=not accepted,
                frozen=accepted,
                created_at=str(row.created_at.isoformat() if row.created_at else output.created_at),
                content_type="application/json",
            )
        )
    return records


def _candidate_records(user_id: str, material: Material) -> list[dict[str, Any]]:
    try:
        from app.workflow_v2.database import workflow_session_factory
        from app.workflow_v2.models import ArtifactVersion, WorkflowJob
    except Exception:
        return []
    db = workflow_session_factory()()
    try:
        jobs = (
            db.query(WorkflowJob)
            .filter(
                WorkflowJob.user_id == user_id,
                or_material_identity(WorkflowJob, material),
                WorkflowJob.status == "needs_review",
            )
            .order_by(WorkflowJob.created_at.desc(), WorkflowJob.id.desc())
            .all()
        )
        records: list[dict[str, Any]] = []
        for job in jobs:
            artifact = (
                db.query(ArtifactVersion)
                .filter(
                    ArtifactVersion.workflow_job_id == job.id,
                    ArtifactVersion.artifact_kind == "elegantbook-candidate",
                )
                .order_by(ArtifactVersion.id.desc())
                .first()
            )
            if not artifact:
                continue
            manifest = _read_json(artifact.bucket, artifact.object_name)
            base = artifact.object_name.rsplit("/", 1)[0] + "/files/"
            for key, filename, content_type in (
                ("pdf", "main.pdf", "application/pdf"),
                ("latex", "latex-project.zip", "application/zip"),
                ("validation", "elegantbook-validation.json", "application/json"),
                ("compile", "compile-report.json", "application/json"),
            ):
                metadata = _manifest_file_metadata(manifest, filename)
                records.append(
                    _record(
                        artifact_id=f"candidate~{job.public_id}~{key}",
                        kind=f"candidate_{key}",
                        stage="candidate",
                        label=f"待审阅 {filename}",
                        bucket=artifact.bucket,
                        object_name=clean_path(f"{base}{filename}"),
                        filename=f"{job.public_id}-{filename}",
                        status="needs_review",
                        sha256=str(metadata.get("sha256") or ""),
                        run_id=job.public_id,
                        candidate=True,
                        frozen=False,
                        created_at=artifact.created_at.isoformat() if artifact.created_at else "",
                        size_bytes=metadata.get("size_bytes"),
                        content_type=content_type,
                    )
                )
        return records
    except Exception:
        return []
    finally:
        db.close()


def or_material_identity(workflow_job_model, material: Material):
    from sqlalchemy import or_

    return or_(
        workflow_job_model.material_pk == material.id,
        workflow_job_model.material_id == (material.material_id or ""),
    )


def material_artifact_catalog(db: Session, user_id: str, material: Material) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if material.input_bucket and material.input_object:
        records.append(
            _record(
                artifact_id="source",
                kind="source_pdf",
                stage="source",
                label="源 PDF",
                bucket=material.input_bucket,
                object_name=material.input_object,
                filename=material.filename,
                status="available",
                sha256=material.input_sha256 or "",
                current=True,
                frozen=True,
                created_at=material.created_at.isoformat() if material.created_at else "",
                size_bytes=material.size_bytes,
                content_type=material.content_type or "application/pdf",
            )
        )
    records.extend(_stage_records(material, "mineru"))
    records.extend(_stage_records(material, "popo"))
    records.extend(_candidate_records(user_id, material))
    records.extend(_output_records(db, user_id, material))
    visible = []
    for record in records:
        clean = dict(record)
        clean.pop("_ref", None)
        visible.append(clean)
    return {
        "material": {
            "material_pk": str(material.id),
            "material_id": material.material_id or "",
            "filename": material.filename,
            "input_sha256": material.input_sha256 or "",
        },
        "artifacts": visible,
    }


def resolve_material_artifact(db: Session, user_id: str, material: Material, artifact_id: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if artifact_id == "source" and material.input_bucket and material.input_object:
        records = [
            _record(
                artifact_id="source",
                kind="source_pdf",
                stage="source",
                label="源 PDF",
                bucket=material.input_bucket,
                object_name=material.input_object,
                filename=material.filename,
                status="available",
                sha256=material.input_sha256 or "",
                current=True,
                frozen=True,
                size_bytes=material.size_bytes,
                content_type=material.content_type or "application/pdf",
            )
        ]
    elif artifact_id.startswith("mineru~"):
        records = _stage_records(material, "mineru")
    elif artifact_id.startswith("popo~"):
        records = _stage_records(material, "popo")
    elif artifact_id.startswith("candidate~"):
        records = _candidate_records(user_id, material)
    elif artifact_id.startswith("output~"):
        records = _output_records(db, user_id, material)
    for record in records:
        if record["artifact_id"] == artifact_id and record["download_available"]:
            return record
    raise ArtifactNotFoundError("数字资产不存在、未冻结或不可下载")


def open_artifact_stream(ref: ObjectRef, *, offset: int = 0, length: int | None = None):
    kwargs: dict[str, Any] = {"offset": offset}
    if length is not None:
        kwargs["length"] = length
    return minio_client.get_object(ref.bucket, ref.object, **kwargs)


def stream_response_body(response, chunk_size: int = 1024 * 1024):
    try:
        stream = getattr(response, "stream", None)
        if stream:
            yield from stream(chunk_size)
        else:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    finally:
        close = getattr(response, "close", None)
        if close:
            close()
        release_conn = getattr(response, "release_conn", None)
        if release_conn:
            release_conn()


def parse_single_range(value: str | None, size: int) -> tuple[int, int] | None:
    if not value:
        return None
    if not value.startswith("bytes=") or "," in value:
        raise ValueError("只支持单段 bytes Range")
    start_text, end_text = value.removeprefix("bytes=").split("-", 1)
    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("Range 无效")
        return max(0, size - suffix), size - 1
    start = int(start_text)
    end = int(end_text) if end_text else size - 1
    if start < 0 or start >= size or end < start:
        raise ValueError("Range 超出文件范围")
    return start, min(end, size - 1)
