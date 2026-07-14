import json
from types import SimpleNamespace

import pytest

from app.workflow_v2.contracts import LEGACY_WORKFLOW_VERSION
from app.workflow_v2.runner import StageExecutionError, _semantic_markdown_for_elegantbook


def test_core_elegantbook_uses_only_passed_semantic_input(tmp_path):
    canonical = tmp_path / "canonical"
    annotation = tmp_path / "annotation"
    canonical.mkdir()
    annotation.mkdir()
    (canonical / "clean.md").write_text("# Old outline\n", encoding="utf-8")
    (annotation / "semantic-input.md").write_text("# Accepted outline\n", encoding="utf-8")
    (annotation / "semantic-validation.json").write_text(json.dumps({"status": "passed"}), encoding="utf-8")

    selected = _semantic_markdown_for_elegantbook(SimpleNamespace(workflow_version="worker-v2.1.0-core-convergence1"), canonical, annotation)

    assert selected == canonical / "semantic-input.md"
    assert selected.read_text(encoding="utf-8") == "# Accepted outline\n"


def test_core_elegantbook_rejects_unaccepted_semantic_input(tmp_path):
    canonical = tmp_path / "canonical"
    annotation = tmp_path / "annotation"
    canonical.mkdir()
    annotation.mkdir()
    (annotation / "semantic-input.md").write_text("# Candidate\n", encoding="utf-8")
    (annotation / "semantic-validation.json").write_text(json.dumps({"status": "review"}), encoding="utf-8")

    with pytest.raises(StageExecutionError, match="passed semantic gate"):
        _semantic_markdown_for_elegantbook(SimpleNamespace(workflow_version="worker-v2.1.0-core-convergence1"), canonical, annotation)


def test_legacy_elegantbook_keeps_canonical_input(tmp_path):
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    clean = canonical / "clean.md"
    clean.write_text("# Legacy\n", encoding="utf-8")

    selected = _semantic_markdown_for_elegantbook(SimpleNamespace(workflow_version=LEGACY_WORKFLOW_VERSION), canonical, tmp_path / "missing")

    assert selected == clean
