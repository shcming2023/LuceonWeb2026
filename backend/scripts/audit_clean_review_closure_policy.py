#!/usr/bin/env python3
"""Audit whether Clean review gates have reusable closure evidence.

This script is audit-only. It does not mutate Clean acceptance, does not
promote a Standard artifact, and does not mark a corpus case as golden.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from standard_from_clean import read_json, write_json


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def gate_by_name(report: dict[str, Any], name: str) -> dict[str, Any]:
    gates = report.get("gates") if isinstance(report.get("gates"), list) else []
    for gate in gates:
        if gate.get("name") == name:
            return gate
    return {}


def clean_structure_summary(clean_dir: Path) -> dict[str, Any]:
    structure = read_json(clean_dir / "structure_report.json")
    loss = read_json(clean_dir / "loss_audit.json")
    render = read_json(clean_dir / "render_report.json")
    readability = read_json(clean_dir / "readability_report.json")
    raw = structure.get("raw") if isinstance(structure.get("raw"), dict) else {}
    clean = structure.get("clean") if isinstance(structure.get("clean"), dict) else {}
    return {
        "structure_status": structure.get("status"),
        "structure_violations": len(structure.get("violations") or []),
        "loss_audit_status": loss.get("status"),
        "forbidden_losses": len(loss.get("forbidden_losses") or []),
        "readability_status": readability.get("status"),
        "render_pdf_ok": bool(render.get("pdf_ok")),
        "render_missing_images": len(render.get("missing_images") or []),
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
    }


def media_summary(clean_dir: Path) -> dict[str, Any]:
    media = read_json(clean_dir / "media_report.json")
    items = media.get("items") if isinstance(media.get("items"), list) else []
    decision_counts = Counter(str(item.get("decision") or "") for item in items)
    reason_counts = Counter(str(reason) for item in items for reason in item.get("reasons", []))
    raw_semantics_counts = Counter(
        "available" if (item.get("raw_semantics") or {}).get("available") else "unavailable" for item in items
    )
    review_items = [item for item in items if item.get("decision") == "review"]
    review_reason_sets = Counter(",".join(sorted(map(str, item.get("reasons", [])))) for item in review_items)
    return {
        "item_count": len(items),
        "decision_counts": dict(decision_counts),
        "reason_counts": dict(reason_counts),
        "raw_semantics_counts": dict(raw_semantics_counts),
        "review_reason_sets": dict(review_reason_sets),
        "sample_review_items": [
            {
                "path": item.get("path"),
                "line": item.get("line"),
                "alt": item.get("alt"),
                "width": item.get("width"),
                "height": item.get("height"),
                "reasons": item.get("reasons") or [],
                "raw_semantics_available": bool((item.get("raw_semantics") or {}).get("available")),
                "context_excerpt": item.get("context_excerpt"),
            }
            for item in review_items[:8]
        ],
    }


def llm_summary(clean_dir: Path) -> dict[str, Any]:
    usage = read_json(clean_dir / "llm_usage.json")
    progress = read_jsonl(clean_dir / "llm_progress.jsonl")
    review_items = read_json(clean_dir / "review_items.json")
    if not isinstance(review_items, list):
        review_items = []
    status_counts = Counter(str(record.get("status") or "") for record in progress)
    revert_records = [record for record in progress if record.get("status") == "reverted_structure_drift"]
    failed_records = [record for record in progress if record.get("status") == "failed"]
    violation_counts = Counter(
        str(violation.get("type") or "")
        for record in revert_records
        for violation in record.get("structure_violations", [])
    )
    return {
        "usage": {
            "enabled": usage.get("enabled"),
            "provider": usage.get("provider"),
            "chunks": usage.get("chunks"),
            "called": usage.get("called"),
            "applied": usage.get("applied"),
            "reverted_structure": usage.get("reverted_structure"),
            "failures": usage.get("failures"),
            "estimated_cost_usd": (usage.get("usage") or {}).get("estimated_cost_usd")
            if isinstance(usage.get("usage"), dict)
            else None,
        },
        "progress_record_count": len(progress),
        "status_counts": dict(status_counts),
        "revert_records": [
            {
                "chunk_index": record.get("chunk_index"),
                "title": record.get("title"),
                "structure_violations": record.get("structure_violations") or [],
            }
            for record in revert_records
        ],
        "failed_records": [
            {
                "chunk_index": record.get("chunk_index"),
                "title": record.get("title"),
                "message": record.get("message"),
            }
            for record in failed_records
        ],
        "violation_counts": dict(violation_counts),
        "review_items": review_items,
    }


def standard_summary(standard_dir: Path) -> dict[str, Any]:
    acceptance = read_json(standard_dir / "standard_acceptance_report.json")
    workbook = read_json(standard_dir / "workbook_profile_report.json")
    closure = read_json(standard_dir / "basic_print_closure_report.json")
    scope = read_json(standard_dir / "clean_review_scope_report.json")
    summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    source = gates.get("source_fidelity") if isinstance(gates.get("source_fidelity"), dict) else {}
    return {
        "acceptance_status": acceptance.get("status"),
        "quality_score": (acceptance.get("quality_score") or {}).get("score")
        if isinstance(acceptance.get("quality_score"), dict)
        else None,
        "workbook_profile_status": workbook.get("status"),
        "open_blocking_review_outcomes": summary.get("review_outcome_open_blocking_count"),
        "issue_candidate_unresolved_blocking_count": summary.get("issue_candidate_unresolved_blocking_count"),
        "missing_images": summary.get("missing_images"),
        "image_refs": summary.get("image_refs"),
        "visual_review_source_crop_count": summary.get("visual_review_source_crop_count"),
        "source_fidelity_status": source.get("status"),
        "standard_text_hash_equals_clean_text_hash": bool(
            source.get("clean_text_hash") and source.get("clean_text_hash") == source.get("standard_text_hash")
        ),
        "clean_review_scope_status": scope.get("status"),
        "unscoped_clean_review_gates": scope.get("unscoped_clean_review_gates") or [],
        "basic_print_closure_status": closure.get("status"),
        "promotion_candidate": closure.get("promotion_candidate"),
        "promotion_blockers": closure.get("promotion_blockers") or [],
    }


def media_policy_verdict(
    clean_acceptance: dict[str, Any],
    structure: dict[str, Any],
    media: dict[str, Any],
    standard: dict[str, Any],
    media_ledger: dict[str, Any],
) -> dict[str, Any]:
    gate = gate_by_name(clean_acceptance, "media_review_threshold")
    details = gate.get("details") if isinstance(gate.get("details"), dict) else {}
    review_count = int((media.get("decision_counts") or {}).get("review") or 0)
    raw_semantics_unavailable = int((media.get("raw_semantics_counts") or {}).get("unavailable") or 0)
    required = {
        "clean_media_conservative_retention_pass": gate_by_name(clean_acceptance, "media_conservative_retention").get("status")
        == "pass",
        "render_missing_images_zero": structure.get("render_missing_images") == 0,
        "standard_missing_images_zero": standard.get("missing_images") == 0,
        "standard_open_blocking_zero": standard.get("open_blocking_review_outcomes") == 0,
        "standard_visual_source_crops_present": int(standard.get("visual_review_source_crop_count") or 0) > 0,
        "raw_semantics_unavailable_for_all_review_items": raw_semantics_unavailable == int(media.get("item_count") or 0),
    }
    missing = [name for name, ok in required.items() if not ok]
    ledger_pass = media_ledger.get("verdict") == "media_purpose_ledger_pass"
    blockers = []
    if review_count and not ledger_pass:
        blockers.append("clean_media_purpose_schema_missing")
    if "generic_alt" in (media.get("reason_counts") or {}) and not ledger_pass:
        blockers.append("generic_alt_needs_role_or_purpose_closure")
    if missing:
        blockers.extend(f"required_evidence_missing:{name}" for name in missing)
    can_close_for_promotion = not blockers
    return {
        "gate": "media_review_threshold",
        "gate_status": gate.get("status"),
        "trigger": {
            "review_image_count": details.get("review_image_count"),
            "warn_threshold": details.get("warn_threshold"),
            "fail_threshold": details.get("fail_threshold"),
            "observed_review_count": review_count,
        },
        "closure_requirements": required,
        "media_purpose_ledger": {
            "provided": bool(media_ledger),
            "verdict": media_ledger.get("verdict"),
            "path": media_ledger.get("_path"),
            "review_item_count": ((media_ledger.get("summary") or {}).get("review_item_count")),
            "open_blocking_review_item_count": (
                (media_ledger.get("summary") or {}).get("open_blocking_review_item_count")
            ),
        },
        "policy_verdict": "can_close_clean_review_gate" if can_close_for_promotion else "not_ready_keep_review",
        "promotion_eligible": can_close_for_promotion,
        "blockers": blockers,
        "candidate_rule": (
            "A retained-media Clean review gate may close only when every review image has a reusable purpose/role "
            "classification or source-backed disposition, all image refs render, Standard has no open media blockers, "
            "and the closure does not rely on generic alt text alone."
        ),
    }


def llm_policy_verdict(
    clean_acceptance: dict[str, Any],
    structure: dict[str, Any],
    llm: dict[str, Any],
    standard: dict[str, Any],
    llm_ledger: dict[str, Any],
) -> dict[str, Any]:
    gate = gate_by_name(clean_acceptance, "llm_structure_revert_threshold")
    details = gate.get("details") if isinstance(gate.get("details"), dict) else {}
    status_counts = llm.get("status_counts") or {}
    failed_count = int(status_counts.get("failed") or 0)
    reverted_count = int(status_counts.get("reverted_structure_drift") or 0)
    required = {
        "clean_structure_pass": structure.get("structure_status") == "pass",
        "clean_structure_violations_zero": structure.get("structure_violations") == 0,
        "loss_audit_pass": structure.get("loss_audit_status") == "pass",
        "forbidden_losses_zero": structure.get("forbidden_losses") == 0,
        "standard_source_fidelity_pass": standard.get("source_fidelity_status") == "pass",
        "standard_text_hash_equals_clean_text_hash": standard.get("standard_text_hash_equals_clean_text_hash") is True,
        "standard_open_blocking_zero": standard.get("open_blocking_review_outcomes") == 0,
    }
    missing = [name for name, ok in required.items() if not ok]
    ledger_pass = llm_ledger.get("verdict") == "llm_fallback_ledger_pass"
    blockers = []
    if failed_count and not ledger_pass:
        blockers.append("failed_llm_chunks_need_raw_fallback_acceptance_ledger")
    if reverted_count and not ledger_pass:
        blockers.append("reverted_structure_chunks_need_fallback_integrity_ledger")
    if missing:
        blockers.extend(f"required_evidence_missing:{name}" for name in missing)
    can_close_for_promotion = not blockers
    return {
        "gate": "llm_structure_revert_threshold",
        "gate_status": gate.get("status"),
        "trigger": {
            "reverted_structure_count": details.get("reverted_structure_count", reverted_count),
            "failed_count": failed_count,
            "observed_reverted_count": reverted_count,
        },
        "closure_requirements": required,
        "llm_fallback_ledger": {
            "provided": bool(llm_ledger),
            "verdict": llm_ledger.get("verdict"),
            "path": llm_ledger.get("_path"),
            "fallback_record_count": ((llm_ledger.get("summary") or {}).get("fallback_record_count")),
            "global_revert_count": ((llm_ledger.get("summary") or {}).get("global_revert_count")),
            "open_blocking_item_count": ((llm_ledger.get("summary") or {}).get("open_blocking_item_count")),
        },
        "policy_verdict": "can_close_clean_review_gate" if can_close_for_promotion else "not_ready_keep_review",
        "promotion_eligible": can_close_for_promotion,
        "blockers": blockers,
        "candidate_rule": (
            "An LLM rollback Clean review gate may close only when each failed or reverted chunk has an explicit "
            "fallback ledger showing the retained Raw/Clean chunk is acceptable, plus global structure/loss/source "
            "fidelity gates pass."
        ),
    }


def render_html(report: dict[str, Any]) -> str:
    gate_rows = []
    for item in report["gate_policy_verdicts"]:
        gate_rows.append(
            "<tr>"
            f"<td>{html.escape(item['gate'])}</td>"
            f"<td>{html.escape(item['policy_verdict'])}</td>"
            f"<td>{html.escape(str(item['promotion_eligible']))}</td>"
            f"<td>{html.escape(', '.join(item['blockers']))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Clean Review Closure Policy Audit</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; line-height: 1.45; color: #202124; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 8px; text-align: left; vertical-align: top; }}
th {{ background: #f6f8fa; }}
pre {{ background: #f6f8fa; border: 1px solid #d0d7de; padding: 12px; overflow: auto; }}
.verdict {{ font-size: 20px; font-weight: 650; }}
</style>
</head>
<body>
<h1>Clean Review Closure Policy Audit</h1>
<p class="verdict">Overall verdict: {html.escape(report['overall_verdict'])}</p>
<p>{html.escape(report['decision'])}</p>
<table>
<thead><tr><th>Gate</th><th>Verdict</th><th>Promotion eligible</th><th>Blockers</th></tr></thead>
<tbody>
{''.join(gate_rows)}
</tbody>
</table>
<h2>Clean Summary</h2>
<pre>{html.escape(json.dumps(report['clean_summary'], ensure_ascii=False, indent=2))}</pre>
<h2>Standard Summary</h2>
<pre>{html.escape(json.dumps(report['standard_summary'], ensure_ascii=False, indent=2))}</pre>
<h2>Policy Verdicts</h2>
<pre>{html.escape(json.dumps(report['gate_policy_verdicts'], ensure_ascii=False, indent=2))}</pre>
</body>
</html>
"""


def build_report(
    clean_dir: Path,
    standard_dir: Path,
    media_ledger_path: Path | None = None,
    llm_ledger_path: Path | None = None,
) -> dict[str, Any]:
    clean_acceptance = read_json(clean_dir / "acceptance_report.json")
    structure = clean_structure_summary(clean_dir)
    media = media_summary(clean_dir)
    llm = llm_summary(clean_dir)
    standard = standard_summary(standard_dir)
    media_ledger = read_json(media_ledger_path) if media_ledger_path else {}
    if media_ledger and media_ledger_path:
        media_ledger["_path"] = str(media_ledger_path)
    llm_ledger = read_json(llm_ledger_path) if llm_ledger_path else {}
    if llm_ledger and llm_ledger_path:
        llm_ledger["_path"] = str(llm_ledger_path)
    verdicts = [
        media_policy_verdict(clean_acceptance, structure, media, standard, media_ledger),
        llm_policy_verdict(clean_acceptance, structure, llm, standard, llm_ledger),
    ]
    promotion_eligible = all(item.get("promotion_eligible") for item in verdicts)
    overall = "clean_review_closure_policy_pass" if promotion_eligible else "clean_review_closure_policy_not_ready"
    decision = (
        "Clean review gates remain open. Current Standard evidence contains this run's downstream risk, but "
        "does not provide all reusable Clean-level closure ledgers needed for promotion."
        if not promotion_eligible
        else "All observed Clean review gates have reusable closure evidence."
    )
    return {
        "schema": "luceon-clean-review-closure-policy-audit/v1",
        "clean_dir": str(clean_dir),
        "standard_dir": str(standard_dir),
        "policy": "audit_only_no_clean_status_mutation_no_standard_promotion",
        "overall_verdict": overall,
        "promotion_eligible": promotion_eligible,
        "decision": decision,
        "clean_summary": {
            "acceptance_status": clean_acceptance.get("status"),
            "hard_failure_count": clean_acceptance.get("hard_failure_count"),
            "review_gate_count": clean_acceptance.get("review_gate_count"),
            "review_gates": [
                gate.get("name") for gate in clean_acceptance.get("review_gates", []) if isinstance(gate, dict)
            ],
            "structure": structure,
            "media": media,
            "llm": llm,
        },
        "standard_summary": standard,
        "gate_policy_verdicts": verdicts,
        "next_required_artifacts": [
            item
            for item in [
                None if media_ledger.get("verdict") == "media_purpose_ledger_pass" else "clean_media_purpose_or_role_closure_ledger",
                None if llm_ledger.get("verdict") == "llm_fallback_ledger_pass" else "clean_llm_failed_and_reverted_chunk_fallback_ledger",
            ]
            if item
        ],
        "evidence_paths": {
            "clean_acceptance_report": str(clean_dir / "acceptance_report.json"),
            "clean_media_report": str(clean_dir / "media_report.json"),
            "clean_llm_progress": str(clean_dir / "llm_progress.jsonl"),
            "clean_llm_usage": str(clean_dir / "llm_usage.json"),
            "clean_review_items": str(clean_dir / "review_items.json"),
            "clean_structure_report": str(clean_dir / "structure_report.json"),
            "clean_loss_audit": str(clean_dir / "loss_audit.json"),
            "standard_acceptance_report": str(standard_dir / "standard_acceptance_report.json"),
            "standard_clean_review_scope_report": str(standard_dir / "clean_review_scope_report.json"),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-dir", required=True, type=Path)
    parser.add_argument("--standard-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--media-ledger", type=Path)
    parser.add_argument("--llm-ledger", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report(args.clean_dir, args.standard_dir, args.media_ledger, args.llm_ledger)
    write_json(args.out_dir / "clean_review_closure_policy_audit.json", report)
    (args.out_dir / "clean_review_closure_policy_audit.html").write_text(render_html(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(args.out_dir / "clean_review_closure_policy_audit.json"),
                "html": str(args.out_dir / "clean_review_closure_policy_audit.html"),
                "overall_verdict": report["overall_verdict"],
                "promotion_eligible": report["promotion_eligible"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
