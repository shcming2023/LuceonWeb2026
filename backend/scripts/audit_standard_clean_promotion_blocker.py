#!/usr/bin/env python3
"""Audit whether Clean review gates still block Standard Basic Print promotion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def gate_names(gates: list[Any]) -> list[str]:
    names: list[str] = []
    for gate in gates:
        if isinstance(gate, dict):
            names.append(str(gate.get("name") or gate.get("gate") or ""))
        else:
            names.append(str(gate))
    return [name for name in names if name]


def build_audit(clean_dir: Path, standard_dir: Path) -> dict[str, Any]:
    clean_acceptance = read_json(clean_dir / "acceptance_report.json")
    clean_manifest = read_json(clean_dir / "manifest.json")
    clean_scope = read_json(standard_dir / "clean_review_scope_report.json")
    standard_acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    workbook_profile = read_json(standard_dir / "workbook_profile_report.json")
    standard_gates = standard_acceptance.get("gates") or {}
    clean_review_gates = gate_names(clean_acceptance.get("review_gates") or [])
    unscoped = clean_scope.get("unscoped_clean_review_gates") or []
    scoped_gate_names = [str(item.get("gate") or "") for item in clean_scope.get("clean_review_gate_scope") or []]
    standard_pass = standard_acceptance.get("status") == "pass"
    clean_review = clean_acceptance.get("status") == "review"
    scope_contained = clean_scope.get("status") == "review_scoped_not_promoted" and not unscoped
    promotion_candidate = bool(clean_scope.get("promotion_candidate"))
    blockers: list[str] = []
    if clean_review:
        blockers.append("clean_acceptance_status_review")
    for gate in clean_review_gates:
        blockers.append(f"clean_review_gate_open:{gate}")
    if not promotion_candidate:
        blockers.append("clean_scope_report_not_promotion_candidate")
    return {
        "schema": "luceon-standard-clean-promotion-blocker-audit/v1",
        "clean_dir": str(clean_dir),
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_clean_status_mutation_no_standard_promotion",
        "decision_boundary": (
            "This audit distinguishes Standard artifact risk containment from Clean acceptance promotion. "
            "A Standard pass plus scoped Clean review does not make Clean pass and does not promote the sample."
        ),
        "clean_acceptance": {
            "status": clean_acceptance.get("status"),
            "hard_failure_count": clean_acceptance.get("hard_failure_count"),
            "review_gate_count": clean_acceptance.get("review_gate_count"),
            "review_gates": clean_review_gates,
        },
        "clean_manifest": {
            "pipeline_node": clean_manifest.get("pipeline_node"),
            "llm": clean_manifest.get("llm") or {},
            "media": clean_manifest.get("media") or {},
            "fidelity": clean_manifest.get("fidelity") or {},
        },
        "scope_report": {
            "status": clean_scope.get("status"),
            "promotion_candidate": promotion_candidate,
            "scoped_gate_names": scoped_gate_names,
            "unscoped_clean_review_gates": unscoped,
        },
        "standard_evidence": {
            "acceptance_status": standard_acceptance.get("status"),
            "quality_score": (standard_acceptance.get("quality_score") or {}).get("score")
            if isinstance(standard_acceptance.get("quality_score"), dict)
            else standard_acceptance.get("quality_score"),
            "source_fidelity_status": (standard_gates.get("source_fidelity") or {}).get("status"),
            "review_outcomes_status": (standard_gates.get("review_outcomes") or {}).get("status"),
            "review_outcome_open_blocking_count": (standard_gates.get("review_outcomes") or {}).get("open_blocking_count"),
            "print_render_status": (standard_gates.get("print_render") or {}).get("status"),
            "workbook_profile_status": workbook_profile.get("status"),
            "workbook_basic_print_blockers": workbook_profile.get("basic_print_blockers") or [],
        },
        "risk_containment": {
            "standard_pass": standard_pass,
            "clean_review_scope_contained_for_this_standard_artifact": scope_contained,
            "can_use_as_standard_risk_evidence": standard_pass and scope_contained,
        },
        "promotion": {
            "can_promote_clean_to_pass": False,
            "can_promote_standard_to_candidate": False,
            "can_count_as_profile_ready_evidence": False,
            "blockers": blockers,
            "required_next_action": "define_reusable_clean_media_and_llm_revert_closure_policy_or_run_clean_review_to_pass",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_audit(args.clean_dir, args.standard_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "clean_promotion_blocker_audit.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
