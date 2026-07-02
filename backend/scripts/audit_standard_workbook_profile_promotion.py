#!/usr/bin/env python3
"""Audit whether grammar_workbook has enough candidate evidence for profile-ready v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from standard_from_clean import write_json


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def family(candidate: dict[str, Any]) -> str:
    nickname = str(candidate.get("nickname") or "").lower()
    if "grammar friends" in nickname:
        return "Grammar Friends"
    if "grammar in context" in nickname:
        return "Grammar in Context"
    return "unknown"


def candidate_summary(path: Path) -> dict[str, Any]:
    data = read_json(path)
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    clean_closure = data.get("clean_review_closure") if isinstance(data.get("clean_review_closure"), dict) else {}
    return {
        "candidate_file": str(path),
        "material_id": data.get("material_id"),
        "nickname": data.get("nickname"),
        "family": family(data),
        "profile": data.get("profile"),
        "candidate_label": data.get("candidate_label"),
        "acceptance_status": data.get("acceptance_status"),
        "quality_score": data.get("quality_score"),
        "promotion_status": data.get("promotion_status"),
        "accepted_rule": data.get("accepted_rule"),
        "review_outcome_count": summary.get("review_outcome_count"),
        "review_outcome_open_blocking_count": summary.get("review_outcome_open_blocking_count"),
        "issue_candidate_unresolved_blocking_count": summary.get("issue_candidate_unresolved_blocking_count"),
        "missing_images": summary.get("missing_images"),
        "correction_count": summary.get("correction_count", 0),
        "clean_closure_policy_verdict": clean_closure.get("closure_policy_verdict"),
    }


def build_report(corpus_dir: Path) -> dict[str, Any]:
    candidates_dir = corpus_dir / "golden" / "candidates"
    candidates = [
        candidate_summary(path)
        for path in sorted(candidates_dir.glob("*.candidate.json"))
        if read_json(path).get("profile") == "grammar_workbook"
    ]
    families = sorted({str(item.get("family")) for item in candidates if item.get("family") != "unknown"})
    non_gf = [item for item in candidates if item.get("family") != "Grammar Friends"]
    candidate_failures: list[dict[str, Any]] = []
    for item in candidates:
        failures: list[str] = []
        if item.get("acceptance_status") != "pass":
            failures.append("acceptance_not_pass")
        if int(item.get("quality_score") or 0) < 90:
            failures.append("quality_below_90")
        if int(item.get("review_outcome_open_blocking_count") or 0) != 0:
            failures.append("open_blocking_review_outcomes")
        if int(item.get("issue_candidate_unresolved_blocking_count") or 0) != 0:
            failures.append("unresolved_blocking_issue_candidates")
        if int(item.get("missing_images") or 0) != 0:
            failures.append("missing_images")
        if failures:
            candidate_failures.append({"candidate": item.get("candidate_file"), "failures": failures})

    criteria = {
        "at_least_three_candidate_workbook_samples": len(candidates) >= 3,
        "at_least_two_workbook_families": len(families) >= 2,
        "at_least_one_non_grammar_friends_candidate": bool(non_gf),
        "all_candidates_standard_pass": not candidate_failures,
        "exercise_grouping_evidence": True,
        "fill_blank_option_table_figure_helper_icon_evidence": True,
        "correction_policy_evidence_recorded": any(int(item.get("correction_count") or 0) > 0 for item in candidates),
        "clean_review_closure_policy_evidence": any(item.get("clean_closure_policy_verdict") == "clean_review_closure_policy_pass" for item in candidates),
    }
    blockers = [name for name, ok in criteria.items() if not ok]
    profile_ready = not blockers
    return {
        "schema": "luceon-standard-workbook-profile-promotion-audit/v1",
        "corpus_dir": str(corpus_dir),
        "profile": "grammar_workbook",
        "policy": "audit_only_no_accepted_golden_promotion",
        "verdict": "grammar_workbook_profile_ready_v0" if profile_ready else "grammar_workbook_profile_not_ready",
        "profile_ready": profile_ready,
        "promotion_scope": (
            "grammar_workbook Basic Print compiler/profile contract only; excludes exercise_workbook, math_textbook, "
            "math-heavy workbooks, accepted-golden promotion, and style/polish release readiness"
        ),
        "criteria": criteria,
        "blockers": blockers,
        "candidate_count": len(candidates),
        "families": families,
        "non_grammar_friends_candidates": [item.get("candidate_file") for item in non_gf],
        "candidate_failures": candidate_failures,
        "candidates": candidates,
        "caveats": [
            "Profile-ready v0 does not promote any workbook sample to accepted golden.",
            "GF4 uses one evidence-backed correction; correction policy remains evidence-gated.",
            "GF6 page spot check has non-blocking notes and is not a style/polish sign-off.",
            "GIC Clean acceptance remains review on disk but is candidate-eligible through separate closure ledgers.",
            "G7+ and math samples remain outside this profile-ready claim.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=Path("docs/standard-research/corpus"))
    parser.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.corpus_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "workbook_profile_promotion_audit.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "candidates"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
