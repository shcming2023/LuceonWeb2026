#!/usr/bin/env python3
"""Scope upstream Clean review gates against a Standard Basic Print artifact.

This script does not change Clean acceptance. It records whether a Standard
artifact has enough evidence to contain specific Clean review risks.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from standard_from_clean import read_json, write_json


def gate_names(acceptance_report: dict[str, Any], status: str) -> list[str]:
    gates = acceptance_report.get("gates") if isinstance(acceptance_report.get("gates"), list) else []
    return [str(gate.get("name") or "") for gate in gates if gate.get("status") == status and gate.get("name")]


def gate_by_name(acceptance_report: dict[str, Any], name: str) -> dict[str, Any]:
    gates = acceptance_report.get("gates") if isinstance(acceptance_report.get("gates"), list) else []
    for gate in gates:
        if gate.get("name") == name:
            return gate
    return {}


def count_status(report: dict[str, Any], key: str, status: str) -> int:
    items = report.get(key) if isinstance(report.get(key), list) else []
    return sum(1 for item in items if item.get("status") == status)


def clean_structure_summary(clean_dir: Path) -> dict[str, Any]:
    structure = read_json(clean_dir / "structure_report.json")
    loss = read_json(clean_dir / "loss_audit.json")
    render = read_json(clean_dir / "render_report.json")
    raw = structure.get("raw") if isinstance(structure.get("raw"), dict) else {}
    clean = structure.get("clean") if isinstance(structure.get("clean"), dict) else {}
    return {
        "structure_report_status": structure.get("status") or ("pass" if not structure.get("violations") else "review"),
        "structure_violations": len(structure.get("violations") or []),
        "raw_numbered_question_lines": raw.get("numbered_question_lines"),
        "clean_numbered_question_lines": clean.get("numbered_question_lines"),
        "raw_blank_marker_count": raw.get("blank_marker_count"),
        "clean_blank_marker_count": clean.get("blank_marker_count"),
        "raw_html_tables": raw.get("html_tables"),
        "clean_html_tables": clean.get("html_tables"),
        "raw_image_refs": raw.get("image_refs"),
        "clean_image_refs": clean.get("image_refs"),
        "raw_inline_math_delimiters": raw.get("inline_math_delimiters"),
        "clean_inline_math_delimiters": clean.get("inline_math_delimiters"),
        "loss_audit_status": loss.get("status"),
        "forbidden_losses": len(loss.get("forbidden_losses") or []),
        "render_pdf_ok": bool(render.get("pdf_ok")),
        "render_missing_images": len(render.get("missing_images") or []),
    }


def standard_evidence_summary(standard_dir: Path) -> dict[str, Any]:
    acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    workbook = read_json(standard_dir / "workbook_profile_report.json")
    closure = read_json(standard_dir / "basic_print_closure_report.json")
    summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    source_fidelity = gates.get("source_fidelity") if isinstance(gates.get("source_fidelity"), dict) else {}
    correction_evidence = gates.get("correction_evidence") if isinstance(gates.get("correction_evidence"), dict) else {}
    media_integrity = gates.get("media_integrity") if isinstance(gates.get("media_integrity"), dict) else {}
    image_relation = gates.get("image_relation_integrity") if isinstance(gates.get("image_relation_integrity"), dict) else {}
    exercise_relation = workbook.get("exercise_relation_contract") if isinstance(workbook.get("exercise_relation_contract"), dict) else {}
    image_relation_contract = workbook.get("image_relation_contract") if isinstance(workbook.get("image_relation_contract"), dict) else {}
    category_counts = image_relation.get("category_counts") if isinstance(image_relation.get("category_counts"), dict) else {}
    return {
        "acceptance_status": acceptance.get("status"),
        "quality_score": (acceptance.get("quality_score") or {}).get("score")
        if isinstance(acceptance.get("quality_score"), dict)
        else None,
        "source_fidelity_status": source_fidelity.get("status"),
        "standard_text_hash_equals_clean_text_hash": bool(
            source_fidelity.get("clean_text_hash")
            and source_fidelity.get("clean_text_hash") == source_fidelity.get("standard_text_hash")
        ),
        "correction_count": summary.get("correction_count", correction_evidence.get("correction_count", 0)),
        "corrections_without_evidence": correction_evidence.get("corrections_without_evidence", 0),
        "workbook_profile_status": workbook.get("status"),
        "exercise_relation_contract_status": exercise_relation.get("status"),
        "image_relation_contract_status": image_relation_contract.get("status"),
        "image_refs": summary.get("image_refs", media_integrity.get("image_refs")),
        "missing_images": len(media_integrity.get("missing_images") or []),
        "helper_icon_count": category_counts.get("helper_icon"),
        "issue_candidate_count": summary.get("issue_candidate_count"),
        "unresolved_blocking_issue_count": summary.get("issue_candidate_unresolved_blocking_count"),
        "review_outcome_count": summary.get("review_outcome_count", (closure.get("review_outcomes") or {}).get("count")),
        "review_outcome_closed_count": summary.get(
            "review_outcome_closed_count", (closure.get("review_outcomes") or {}).get("closed_count")
        ),
        "review_outcome_open_blocking_count": summary.get(
            "review_outcome_open_blocking_count", (closure.get("review_outcomes") or {}).get("open_blocking_count")
        ),
        "image_source_crop_count": summary.get("image_visual_confirmation_source_crop_count"),
        "visual_review_source_crop_count": summary.get("visual_review_source_crop_count"),
        "pdf_render_ok": bool(summary.get("pdf_page_count")),
        "pdf_page_count": summary.get("pdf_page_count"),
    }


def media_scope(
    clean_acceptance: dict[str, Any],
    clean_structure: dict[str, Any],
    standard_evidence: dict[str, Any],
) -> dict[str, Any]:
    gate = gate_by_name(clean_acceptance, "media_review_threshold")
    details = gate.get("details") if isinstance(gate.get("details"), dict) else {}
    clean_image_refs = clean_structure.get("clean_image_refs")
    acceptance_status = standard_evidence.get("acceptance_status")
    covered = (
        acceptance_status == "pass"
        and int(standard_evidence.get("review_outcome_open_blocking_count") or 0) == 0
        and int(standard_evidence.get("unresolved_blocking_issue_count") or 0) == 0
        and int(standard_evidence.get("missing_images") or 0) == 0
    )
    return {
        "gate": "media_review_threshold",
        "clean_trigger": {
            "review_image_count": details.get("review_image_count"),
            "reason": "generic_alt/raw_semantics_unavailable",
        },
        "standard_coverage": {
            "clean_image_refs": clean_image_refs,
            "standard_image_refs": standard_evidence.get("image_refs"),
            "missing_images": 0 if covered else None,
            "image_relation_contract_status": standard_evidence.get("image_relation_contract_status"),
            "key_figure_source_crops": standard_evidence.get("image_source_crop_count"),
            "helper_icon_compact_rendering": standard_evidence.get("helper_icon_count"),
            "image_review_outcome_open_blocking_count": standard_evidence.get("review_outcome_open_blocking_count"),
        },
        "scope_decision": "covered_for_standard_basic_print_review" if covered else "not_covered_for_standard_basic_print_review",
        "promotion_decision": "not_sufficient_to_promote_clean_pass",
        "reason": "Standard source evidence can close retained media use for this Standard artifact, but Clean needs its own media-purpose closure schema before promotion.",
    }


def llm_scope(clean_acceptance: dict[str, Any], clean_structure: dict[str, Any], standard_evidence: dict[str, Any]) -> dict[str, Any]:
    gate = gate_by_name(clean_acceptance, "llm_structure_revert_threshold")
    details = gate.get("details") if isinstance(gate.get("details"), dict) else {}
    covered = (
        clean_structure.get("structure_report_status") == "pass"
        and int(clean_structure.get("structure_violations") or 0) == 0
        and standard_evidence.get("source_fidelity_status") == "pass"
        and standard_evidence.get("standard_text_hash_equals_clean_text_hash") is True
    )
    return {
        "gate": "llm_structure_revert_threshold",
        "clean_trigger": {
            "reverted_structure_count": details.get("reverted_structure_count"),
            "llm_failures": None,
            "global_revert_reason": "see_clean_review_items",
        },
        "standard_coverage": {
            "clean_structure_report_status": clean_structure.get("structure_report_status"),
            "standard_source_fidelity": standard_evidence.get("source_fidelity_status"),
            "standard_text_hash_equals_clean_text_hash": standard_evidence.get("standard_text_hash_equals_clean_text_hash"),
            "standard_profile_coverage": standard_evidence.get("workbook_profile_status"),
        },
        "scope_decision": "risk_contained_for_standard_from_this_clean_candidate" if covered else "risk_not_contained",
        "promotion_decision": "not_sufficient_to_promote_clean_pass",
        "reason": "A preserved final Clean structure plus Standard source fidelity contains this artifact risk, but Clean LLM rollback review remains an upstream process-quality review.",
    }


def build_clean_review_scope_report(clean_dir: Path, standard_dir: Path) -> dict[str, Any]:
    clean_acceptance = read_json(clean_dir / "acceptance_report.json")
    clean_manifest = read_json(clean_dir / "manifest.json")
    standard_manifest = read_json(standard_dir / "manifest.json")
    clean_structure = clean_structure_summary(clean_dir)
    standard_evidence = standard_evidence_summary(standard_dir)
    review_gates = gate_names(clean_acceptance, "review")
    hard_failures = gate_names(clean_acceptance, "fail")
    scope_items: list[dict[str, Any]] = []
    if "media_review_threshold" in review_gates:
        scope_items.append(media_scope(clean_acceptance, clean_structure, standard_evidence))
    if "llm_structure_revert_threshold" in review_gates:
        scope_items.append(llm_scope(clean_acceptance, clean_structure, standard_evidence))
    unscoped = [gate for gate in review_gates if gate not in {"media_review_threshold", "llm_structure_revert_threshold"}]
    clean_status = str(clean_acceptance.get("status") or "")
    if hard_failures:
        status = "clean_fail_not_scoped"
    elif review_gates:
        status = "review_scoped_not_promoted"
    elif clean_status == "pass":
        status = "clean_pass_no_scope_needed"
    else:
        status = "clean_status_unknown_not_promoted"
    promotion_candidate = False
    decision = [
        "This report scopes upstream Clean review risks against the current Standard artifact.",
        "It does not change Clean acceptance status.",
        "It does not promote a Standard artifact to accepted golden or profile-ready status.",
    ]
    if status == "clean_pass_no_scope_needed":
        decision.append("The upstream Clean artifact is already pass, so no Clean review scope closure is needed for this Standard artifact.")
    elif status == "review_scoped_not_promoted":
        decision.append("A separate reusable Clean closure policy is required before Clean review gates can stop blocking promotion.")
    elif status == "clean_fail_not_scoped":
        decision.append("Clean has hard failures, so Standard promotion remains blocked and review scoping is not sufficient.")
    else:
        decision.append("Clean status is not a recognized pass/review/fail state, so promotion remains blocked.")
    return {
        "schema": "luceon-standard-clean-review-scope/v1",
        "material_id": clean_manifest.get("material_id") or standard_manifest.get("material_id"),
        "profile": standard_manifest.get("profile"),
        "clean_dir": str(clean_dir),
        "standard_dir": str(standard_dir),
        "status": status,
        "promotion_candidate": promotion_candidate,
        "clean_acceptance": {
            "status": clean_acceptance.get("status"),
            "hard_failure_count": len(hard_failures),
            "review_gate_count": len(review_gates),
            "review_gates": review_gates,
            "pass_gates": gate_names(clean_acceptance, "pass"),
        },
        "clean_structure_evidence": clean_structure,
        "standard_evidence": standard_evidence,
        "clean_review_gate_scope": scope_items,
        "unscoped_clean_review_gates": unscoped,
        "decision": decision,
        "evidence": {
            "clean_acceptance_report": str(clean_dir / "acceptance_report.json"),
            "clean_media_report": str(clean_dir / "media_report.json"),
            "clean_structure_report": str(clean_dir / "structure_report.json"),
            "clean_loss_audit": str(clean_dir / "loss_audit.json"),
            "clean_render_report": str(clean_dir / "render_report.json"),
            "standard_acceptance_report": str(standard_dir / "standard_acceptance_report.json"),
            "standard_review_outcomes": str(standard_dir / "standard_review_outcomes.json"),
            "standard_basic_print_closure_report": str(standard_dir / "basic_print_closure_report.json"),
        },
    }


def update_manifest(standard_dir: Path, report_name: str) -> None:
    manifest_path = standard_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if not manifest:
        return
    outputs = manifest.setdefault("outputs", {})
    if isinstance(outputs, dict):
        outputs["clean_review_scope_report"] = report_name
    write_json(manifest_path, manifest)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--output", default="clean_review_scope_report.json")
    parser.add_argument("--update-manifest", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    clean_dir = args.clean_dir
    standard_dir = args.standard_dir
    report = build_clean_review_scope_report(clean_dir, standard_dir)
    output_path = standard_dir / args.output
    write_json(output_path, report)
    if args.update_manifest:
        update_manifest(standard_dir, args.output)
    print(
        {
            "report": str(output_path),
            "status": report["status"],
            "promotion_candidate": report["promotion_candidate"],
            "review_gates": report["clean_acceptance"]["review_gates"],
            "unscoped_clean_review_gates": report["unscoped_clean_review_gates"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
