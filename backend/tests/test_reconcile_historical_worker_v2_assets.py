from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_historical_worker_v2_assets.py"
SPEC = importlib.util.spec_from_file_location("reconcile_historical_worker_v2_assets", SCRIPT)
subject = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(subject)


def material(**overrides):
    values = {
        "material_id": "pdf-1234567890abcdef",
        "input_sha256": "1234567890abcdef" + "0" * 48,
        "popo_manifest_bucket": "eduassets-minerupopo",
        "popo_manifest_object": "minerupopo/pdf-1234567890abcdef/run-popo/manifest.json",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def combined_manifest(**overrides):
    def ref(name):
        return {
            "bucket": "eduassets-mineru",
            "object": f"mineru/pdf-1234567890abcdef/run-mineru/{name}",
            "sha256": "a" * 64,
            "size_bytes": 1,
        }

    value = {
        "run_id": "run-popo",
        "source_pdf": {"sha256": "1234567890abcdef" + "0" * 48},
        "stage_prefixes": {
            "mineru": {
                "bucket": "eduassets-mineru",
                "prefix": "mineru/pdf-1234567890abcdef/run-mineru/",
            }
        },
        "objects": {
            "content_list": ref("content_list.json"),
            "middle": ref("middle.json"),
            "model": ref("model.json"),
            "full_md": ref("full.md"),
            "images": [ref("images/a.jpg"), {"bucket": "eduassets-minerupopo", "object": "ignored.jpg"}],
        },
    }
    value.update(overrides)
    return value


def test_build_recovered_manifest_uses_verified_existing_mineru_objects(monkeypatch):
    monkeypatch.setattr(subject, "object_exists", lambda bucket, object_name: True)

    object_name, manifest = subject.build_recovered_mineru_manifest(material(), combined_manifest())

    assert object_name == "mineru/pdf-1234567890abcdef/run-mineru/manifest.json"
    assert manifest["status"] == "mineru_done_frozen"
    assert manifest["lineage"]["mode"] == "recovered_from_combined_popo_manifest"
    assert manifest["lineage"]["content_objects_copied"] is False
    assert manifest["reference_count"] == 5
    assert len(manifest["objects"]["images"]) == 1


def test_build_recovered_manifest_rejects_incomplete_combined_manifest(monkeypatch):
    monkeypatch.setattr(subject, "object_exists", lambda bucket, object_name: True)
    value = combined_manifest()
    del value["objects"]["middle"]

    with pytest.raises(ValueError, match="lacks MinerU objects: middle"):
        subject.build_recovered_mineru_manifest(material(), value)


def test_uat_alias_pattern_extracts_canonical_hash_prefix():
    match = subject.UAT_ALIAS_RE.fullmatch("pdf-uatlatex-20260706065844-03-43101368")

    assert match
    assert match.group("sha") == "43101368"
