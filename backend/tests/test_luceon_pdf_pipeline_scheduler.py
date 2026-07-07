from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "luceon_pdf_pipeline.py"
SPEC = importlib.util.spec_from_file_location("luceon_pdf_pipeline", MODULE_PATH)
pipeline = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = pipeline
SPEC.loader.exec_module(pipeline)


def write_lineage(tmp_path: Path, items: list[dict], active_marker_count: int = 0) -> str:
    path = tmp_path / "lineage.json"
    path.write_text(
        json.dumps(
            {
                "command": "lineage-audit",
                "scope": "test",
                "items": items,
                "scheduler_state_counts": {},
                "state_counts": {},
                "active_marker_count": active_marker_count,
                "active_marker_samples": [],
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_plan_next_can_be_limited_to_explicit_input_object(tmp_path):
    lineage_file = write_lineage(
        tmp_path,
        [
            {
                "input_object": "uat-input-only-20260702095009.pdf",
                "input_size_bytes": 560,
                "material_id": "pdf-uat",
                "scheduler_state": "eligible_for_submit",
            },
            {
                "input_object": "cambridge-igcse.pdf",
                "input_size_bytes": 166331327,
                "material_id": "pdf-d38fd83ffd5a7f6a",
                "scheduler_state": "eligible_for_submit",
            },
        ],
    )

    plan = pipeline.build_next_batch_plan(
        None,
        None,
        limit=5,
        sort_by="smallest",
        with_sha=False,
        lineage_file=lineage_file,
        input_objects=("cambridge-igcse.pdf",),
    )

    assert plan["status"] == "READY"
    assert plan["selected_count"] == 1
    assert plan["selected"][0]["input_object"] == "cambridge-igcse.pdf"


def test_existing_recovery_can_select_active_marker_items(tmp_path):
    lineage_file = write_lineage(
        tmp_path,
        [
            {
                "input_object": "cambridge-igcse.pdf",
                "input_size_bytes": 166331327,
                "material_id": "pdf-d38fd83ffd5a7f6a",
                "scheduler_state": "active_or_stale",
            }
        ],
        active_marker_count=1,
    )

    blocked = pipeline.build_next_batch_plan(
        None,
        None,
        limit=5,
        sort_by="smallest",
        with_sha=False,
        lineage_file=lineage_file,
    )
    recovery = pipeline.build_next_batch_plan(
        None,
        None,
        limit=5,
        sort_by="smallest",
        with_sha=False,
        lineage_file=lineage_file,
        allow_active=True,
        candidate_states={"active_or_stale"},
    )

    assert blocked["status"] == "BLOCKED_ACTIVE_MARKERS"
    assert recovery["status"] == "READY"
    assert recovery["selected"][0]["input_object"] == "cambridge-igcse.pdf"


class FakeS3:
    def __init__(self, objects: dict[str, bytes]):
        self.objects = objects

    def list_objects(self, bucket: str, max_keys: int = 1000, prefix: str = "") -> list[dict[str, str]]:
        return [
            {"Key": key, "Size": str(len(data))}
            for key, data in self.objects.items()
            if key.startswith(prefix)
        ]

    def get_bytes(self, bucket: str, obj: str, max_bytes: int | None = None) -> bytes:
        data = self.objects[obj]
        if max_bytes is not None and len(data) > max_bytes:
            raise ValueError("too large")
        return data

    def presign_get(self, public_endpoint: str, bucket: str, obj: str, expires: int = 86400) -> str:
        return f"{public_endpoint}/{bucket}/{obj}?expires={expires}"


def test_existing_stage_status_maps_sanitized_filename_by_sha():
    data = b"%PDF-1.7 actual target bytes"
    source_sha = hashlib.sha256(data).hexdigest()
    s3 = FakeS3({"original/cambridge-igcse-long-name.pdf": data})
    cfg = SimpleNamespace(
        input_bucket="eduassets-input",
        minio_public_endpoint="http://minio.local",
        presign_expires=3600,
        max_file_bytes=1024,
    )
    doc_status = {
        "doc_id": "remote-doc-003",
        "source": {
            "filename": "sanitized.pdf",
            "sha256": source_sha,
            "size_bytes": len(data),
        },
    }

    doc = pipeline.existing_stage_status_to_submit_doc(s3, cfg, doc_status, 2)

    assert doc["object"] == "original/cambridge-igcse-long-name.pdf"
    assert doc["doc_id"] == "remote-doc-003"
    assert doc["source_pdf_sha256"] == source_sha
    assert doc["material_id"] == "pdf-" + source_sha[:16]
