#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import SessionLocal  # noqa: E402
from app.models.material import Material, MaterialOutput  # noqa: E402
from app.services.luceon_review import minio_client, object_exists, parse_json_bytes, read_object  # noqa: E402


UAT_ALIAS_RE = re.compile(r"^pdf-uatlatex-\d{14}-\d{2}-(?P<sha>[0-9a-f]{8})$")
REQUIRED_MINERU_OBJECT_KEYS = ("content_list", "middle", "model", "full_md")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _metadata(output: MaterialOutput) -> dict[str, Any]:
    return output.metadata_dict()


def _alias_target(db, material: Material) -> Material:
    match = UAT_ALIAS_RE.fullmatch(material.material_id or "")
    if not match:
        raise ValueError(f"unsupported input-less historical material: {material.material_id}")
    prefix = f"pdf-{match.group('sha')}%"
    candidates = (
        db.query(Material)
        .filter(
            Material.user_id == material.user_id,
            Material.material_id.like(prefix),
            Material.input_bucket == "eduassets-input",
            Material.input_object.isnot(None),
            Material.input_object != "",
        )
        .all()
    )
    if len(candidates) != 1:
        raise ValueError(f"alias {material.material_id} matched {len(candidates)} canonical materials")
    return candidates[0]


def _object_refs(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _mineru_objects(popo_manifest: dict[str, Any]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key, value in (popo_manifest.get("objects") or {}).items():
        refs = [row for row in _object_refs(value) if row.get("bucket") == "eduassets-mineru"]
        if not refs:
            continue
        selected[key] = refs if isinstance(value, list) else refs[0]
    missing = [key for key in REQUIRED_MINERU_OBJECT_KEYS if key not in selected]
    if missing:
        raise ValueError(f"combined Popo manifest lacks MinerU objects: {', '.join(missing)}")
    return selected


def _verify_refs(objects: dict[str, Any]) -> int:
    count = 0
    for value in objects.values():
        for ref in _object_refs(value):
            bucket = str(ref.get("bucket") or "")
            object_name = str(ref.get("object") or "")
            if not bucket or not object_name or not object_exists(bucket, object_name):
                raise ValueError(f"missing referenced MinerU object: {bucket}/{object_name}")
            count += 1
    return count


def build_recovered_mineru_manifest(material: Material, popo_manifest: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    stage_prefixes = popo_manifest.get("stage_prefixes") or {}
    mineru_stage = stage_prefixes.get("mineru") or {}
    bucket = str(mineru_stage.get("bucket") or "")
    prefix = str(mineru_stage.get("prefix") or "").rstrip("/") + "/"
    if bucket != "eduassets-mineru" or not prefix.startswith(f"mineru/{material.material_id}/"):
        raise ValueError(f"invalid MinerU stage prefix for {material.material_id}")
    run_id = prefix.rstrip("/").rsplit("/", 1)[-1]
    objects = _mineru_objects(popo_manifest)
    reference_count = _verify_refs(objects)
    source_pdf = popo_manifest.get("source_pdf") or {}
    if source_pdf.get("sha256") and material.input_sha256 and source_pdf["sha256"] != material.input_sha256:
        raise ValueError(f"source PDF hash mismatch for {material.material_id}")
    manifest = {
        "schema": "luceon-recovered-mineru-manifest/v1",
        "status": "mineru_done_frozen",
        "material_id": material.material_id,
        "run_id": run_id,
        "stage_run_ids": {"mineru": run_id, "popo": str(popo_manifest.get("run_id") or "")},
        "lineage": {
            "join_key": "material_id",
            "stage_run_ids_can_differ": True,
            "mode": "recovered_from_combined_popo_manifest",
            "source_popo_manifest": {
                "bucket": material.popo_manifest_bucket,
                "object": material.popo_manifest_object,
            },
            "content_objects_copied": False,
        },
        "source_pdf": source_pdf,
        "stage_prefixes": {"mineru": mineru_stage},
        "objects": objects,
        "reference_count": reference_count,
        "created_at": _utc_now(),
    }
    return prefix + "manifest.json", manifest


def _accepted_worker_output(output: MaterialOutput) -> dict[str, Any]:
    prefix = output.manifest_object.rsplit("/", 1)[0]
    acceptance = parse_json_bytes(read_object(output.manifest_bucket, prefix + "/files/core-acceptance.json"))
    if acceptance.get("status") != "passed" or acceptance.get("sidecar_used") is not False:
        raise ValueError(f"Worker V2 output {output.id} is not core-accepted without Sidecar")
    if not all((acceptance.get("gates") or {}).values()):
        raise ValueError(f"Worker V2 output {output.id} has a failed core gate")
    return acceptance


def _adopt_worker_outputs(db, *, canonical: list[Material], target_user_id: str, source_user_id: str, apply: bool) -> list[dict[str, Any]]:
    canonical_by_id = {row.material_id: row for row in canonical}
    source_outputs = (
        db.query(MaterialOutput)
        .filter(
            MaterialOutput.user_id == source_user_id,
            MaterialOutput.origin == "worker_v2",
            MaterialOutput.is_current.is_(True),
            MaterialOutput.quality_status == "passed",
            MaterialOutput.material_id.in_(canonical_by_id),
        )
        .all()
    )
    rows = []
    for source in source_outputs:
        target = canonical_by_id[source.material_id]
        exists = (
            db.query(MaterialOutput)
            .filter(
                MaterialOutput.user_id == target_user_id,
                MaterialOutput.manifest_bucket == source.manifest_bucket,
                MaterialOutput.manifest_object == source.manifest_object,
            )
            .first()
        )
        if exists:
            continue
        source_material = db.query(Material).filter(Material.id == source.material_pk, Material.user_id == source_user_id).one()
        if not source_material.input_sha256 or source_material.input_sha256 != target.input_sha256:
            raise ValueError(f"cross-user source hash mismatch for {source.material_id}")
        acceptance = _accepted_worker_output(source)
        row = {
            "material_id": source.material_id,
            "target_material_pk": target.id,
            "source_material_pk": source_material.id,
            "source_output_id": source.id,
            "output_run_id": source.output_run_id,
            "manifest_bucket": source.manifest_bucket,
            "manifest_object": source.manifest_object,
            "core_acceptance_schema": acceptance.get("schema"),
        }
        rows.append(row)
        if not apply:
            continue
        db.query(MaterialOutput).filter(
            MaterialOutput.user_id == target_user_id,
            MaterialOutput.material_id == target.material_id,
            MaterialOutput.output_type == source.output_type,
            MaterialOutput.is_current.is_(True),
        ).update({MaterialOutput.is_current: False}, synchronize_session=False)
        metadata = source.metadata_dict()
        metadata["historical_adoption"] = {
            "source_user_id": source_user_id,
            "source_material_pk": source_material.id,
            "source_output_id": source.id,
            "reason": "same_input_sha256_core_accepted_worker_v2",
        }
        adopted = MaterialOutput(
            user_id=target_user_id,
            material_pk=target.id,
            material_id=target.material_id,
            review_asset_id=target.review_asset_id,
            output_type=source.output_type,
            origin=source.origin,
            status="promoted",
            quality_status="passed",
            is_current=True,
            manifest_bucket=source.manifest_bucket,
            manifest_object=source.manifest_object,
            output_run_id=source.output_run_id,
            popo_run_id=target.popo_run_id,
            skill_name=source.skill_name,
            skill_version=source.skill_version,
            codex_job_id=None,
            version_label=source.version_label,
            metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            promoted_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(adopted)
        target.latex_manifest_bucket = source.manifest_bucket
        target.latex_manifest_object = source.manifest_object
        target.latex_run_id = source.output_run_id
        target.promote_stage("latex_done")
    return rows


def reconcile(*, user_id: str, apply: bool, adopt_worker_from_user: str = "") -> dict[str, Any]:
    db = SessionLocal()
    report: dict[str, Any] = {
        "schema": "luceon-historical-worker-v2-reconciliation/v1",
        "mode": "apply" if apply else "audit",
        "user_id": user_id,
        "created_at": _utc_now(),
        "aliases": [],
        "lineage_backfills": [],
        "worker_output_adoptions": [],
        "errors": [],
    }
    try:
        outputs = db.query(MaterialOutput).filter(MaterialOutput.user_id == user_id, MaterialOutput.origin == "legacy_selfloop").all()
        material_ids = sorted({row.material_id for row in outputs})
        materials = db.query(Material).filter(Material.user_id == user_id, Material.material_id.in_(material_ids)).all()
        by_id = {row.material_id: row for row in materials}
        if len(by_id) != len(material_ids):
            raise ValueError("historical outputs do not map one-to-one to Material rows")

        canonical: list[Material] = []
        for material_id in material_ids:
            material = by_id[material_id]
            if material.input_bucket and material.input_object:
                canonical.append(material)
                continue
            try:
                target = _alias_target(db, material)
                alias_row = {
                    "alias_material_pk": material.id,
                    "alias_material_id": material.material_id,
                    "canonical_material_pk": target.id,
                    "canonical_material_id": target.material_id,
                    "reason": "uat_hash_alias",
                }
                report["aliases"].append(alias_row)
                if apply:
                    material.ignored = True
                    for output in [row for row in outputs if row.material_id == material.material_id]:
                        metadata = _metadata(output)
                        metadata["historical_alias"] = alias_row
                        output.metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
            except Exception as exc:
                report["errors"].append({"material_id": material_id, "stage": "alias", "error": str(exc)})

        for material in canonical:
            if material.mineru_manifest_bucket and material.mineru_manifest_object:
                continue
            try:
                popo_manifest = parse_json_bytes(read_object(material.popo_manifest_bucket, material.popo_manifest_object))
                manifest_object, manifest = build_recovered_mineru_manifest(material, popo_manifest)
                exists = object_exists("eduassets-mineru", manifest_object)
                if exists:
                    existing = parse_json_bytes(read_object("eduassets-mineru", manifest_object))
                    if existing.get("material_id") != material.material_id or existing.get("run_id") != manifest.get("run_id"):
                        raise ValueError("existing MinerU manifest has incompatible identity")
                row = {
                    "material_pk": material.id,
                    "material_id": material.material_id,
                    "manifest_bucket": "eduassets-mineru",
                    "manifest_object": manifest_object,
                    "run_id": manifest["run_id"],
                    "reference_count": manifest["reference_count"],
                    "manifest_already_existed": exists,
                }
                report["lineage_backfills"].append(row)
                if apply:
                    if not exists:
                        data = _json_bytes(manifest)
                        minio_client.put_object(
                            "eduassets-mineru",
                            manifest_object,
                            BytesIO(data),
                            length=len(data),
                            content_type="application/json",
                        )
                    material.mineru_manifest_bucket = "eduassets-mineru"
                    material.mineru_manifest_object = manifest_object
                    material.mineru_run_id = manifest["run_id"]
            except Exception as exc:
                report["errors"].append({"material_id": material.material_id, "stage": "mineru_lineage", "error": str(exc)})

        if adopt_worker_from_user:
            try:
                report["worker_output_adoptions"] = _adopt_worker_outputs(
                    db,
                    canonical=canonical,
                    target_user_id=user_id,
                    source_user_id=adopt_worker_from_user,
                    apply=apply,
                )
            except Exception as exc:
                report["errors"].append({"stage": "worker_output_adoption", "error": str(exc)})

        report["counts"] = {
            "legacy_output_materials": len(material_ids),
            "canonical_materials": len(canonical),
            "aliases": len(report["aliases"]),
            "lineage_backfills": len(report["lineage_backfills"]),
            "worker_output_adoptions": len(report["worker_output_adoptions"]),
            "errors": len(report["errors"]),
        }
        if apply and report["errors"]:
            raise ValueError(f"reconciliation has {len(report['errors'])} errors; refusing partial commit")
        if apply:
            db.commit()
        else:
            db.rollback()
        return report
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile historical Luceon assets before Worker V2 refresh.")
    parser.add_argument("--user-id", default="2")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--adopt-worker-from-user", default="")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = reconcile(user_id=args.user_id, apply=args.apply, adopt_worker_from_user=args.adopt_worker_from_user)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
