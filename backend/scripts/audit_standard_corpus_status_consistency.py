#!/usr/bin/env python3
"""Audit Standard Basic Print corpus case/run/golden status consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


PROFILE_CHOICES = {"reading_textbook", "grammar_workbook", "exercise_workbook", "math_textbook"}

STATUS_POLICY = {
    "basic_print_accepted": {
        "expected_candidate": True,
        "expected_golden": True,
        "layer": "basic_print_accepted",
    },
    "basic_print_candidate": {
        "expected_candidate": True,
        "expected_golden": False,
        "layer": "basic_print_candidate",
    },
    "standard_review_pressure_run": {
        "expected_candidate": False,
        "expected_golden": False,
        "layer": "standard_review_draft",
    },
    "math_profile_blocked_review": {
        "expected_candidate": False,
        "expected_golden": False,
        "layer": "blocked_needs_reconstruction",
    },
    "standard_review_draft": {
        "expected_candidate": False,
        "expected_golden": False,
        "layer": "standard_review_draft",
    },
    "blocked_needs_reconstruction": {
        "expected_candidate": False,
        "expected_golden": False,
        "layer": "blocked_needs_reconstruction",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def rel_exists(base: Path, ref: str) -> bool:
    if not ref:
        return False
    return (base / ref).resolve().exists()


def audit_corpus(corpus_dir: Path) -> dict[str, Any]:
    cases_dir = corpus_dir / "cases"
    runs_dir = corpus_dir / "runs"
    candidates_dir = corpus_dir / "golden" / "candidates"
    accepted_dir = corpus_dir / "golden" / "accepted"
    candidates = {read_json(path).get("material_id"): path for path in candidates_dir.glob("*.json")}
    accepted = {read_json(path).get("material_id"): path for path in accepted_dir.glob("*.json")}
    runs_by_material: dict[str, list[Path]] = {}
    for path in runs_dir.glob("*.json"):
        material_id = str(read_json(path).get("material_id") or "")
        runs_by_material.setdefault(material_id, []).append(path)

    issues: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    for path in sorted(cases_dir.glob("*.case.json")):
        case = read_json(path)
        material_id = str(case.get("material_id") or "")
        current_status = str(case.get("current_status") or "")
        expected = STATUS_POLICY.get(current_status, {})
        latest_ref = str(case.get("latest_run_record") or "")
        candidate_ref = str(case.get("candidate_record") or "")
        golden_ref = str(case.get("accepted_golden_record") or "")
        item = {
            "material_id": material_id,
            "case_file": str(path),
            "profile": case.get("profile"),
            "role": case.get("role"),
            "current_status": current_status,
            "latest_run_record": latest_ref,
            "candidate_record": candidate_ref,
            "accepted_golden_record": golden_ref,
            "runs_count": len(runs_by_material.get(material_id, [])),
            "candidate_exists": material_id in candidates,
            "accepted_golden_exists": material_id in accepted,
            "expected": expected,
        }
        item_issues: list[str] = []
        if case.get("profile") not in PROFILE_CHOICES:
            item_issues.append("profile_unknown")
        if not expected:
            item_issues.append("unknown_current_status")
        else:
            if bool(candidate_ref) != bool(expected.get("expected_candidate")):
                item_issues.append("candidate_ref_presence_mismatch")
            if bool(golden_ref) != bool(expected.get("expected_golden")):
                item_issues.append("golden_ref_presence_mismatch")
            if bool(case.get("golden")) != bool(expected.get("expected_golden")):
                item_issues.append("golden_flag_mismatch")
            if bool(case.get("basic_print_candidate")) and not expected.get("expected_candidate"):
                item_issues.append("candidate_flag_not_allowed_for_status")
        if runs_by_material.get(material_id) and not latest_ref:
            item_issues.append("missing_latest_run_record")
        if latest_ref and not rel_exists(path.parent, latest_ref):
            item_issues.append("latest_run_record_missing_file")
        if candidate_ref and not rel_exists(path.parent, candidate_ref):
            item_issues.append("candidate_record_missing_file")
        if golden_ref and not rel_exists(path.parent, golden_ref):
            item_issues.append("accepted_golden_record_missing_file")
        item["issues"] = item_issues
        items.append(item)
        for issue in item_issues:
            issues.append({"material_id": material_id, "issue": issue, "case_file": str(path)})

    schema_warnings: list[dict[str, Any]] = []
    for path in sorted(candidates_dir.glob("*.json")) + sorted(accepted_dir.glob("*.json")):
        data = read_json(path)
        if "profile" not in data:
            schema_warnings.append({"file": str(path), "warning": "missing_profile_field"})
        if "run_record" in data and not rel_exists(path.parent, str(data.get("run_record") or "")):
            schema_warnings.append({"file": str(path), "warning": "run_record_missing_file"})

    return {
        "schema": "luceon-standard-corpus-status-consistency-audit/v1",
        "corpus_dir": str(corpus_dir),
        "policy": "audit_only_no_status_promotion",
        "decision_boundary": (
            "This audit checks corpus manifest consistency from declared status semantics only. "
            "It does not promote candidates, change acceptance status, infer profile readiness "
            "from Standard pass artifacts, or special-case known sample material ids."
        ),
        "case_count": len(items),
        "issue_count": len(issues),
        "schema_warning_count": len(schema_warnings),
        "issues": issues,
        "schema_warnings": schema_warnings,
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=Path("docs/standard-research/corpus"))
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_corpus(args.corpus_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "corpus_status_consistency_audit.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "items"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
