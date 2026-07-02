#!/usr/bin/env python3
"""Refresh Standard issue candidate dispositions and related acceptance gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from standard_from_clean import apply_issue_candidate_gates_to_acceptance, refresh_issue_candidate_disposition_audit_artifacts


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Standard issue candidate disposition audit.")
    parser.add_argument("--standard-dir", required=True, type=Path, help="Existing standard-final directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    standard_dir = args.standard_dir
    audit = refresh_issue_candidate_disposition_audit_artifacts(standard_dir)
    acceptance = apply_issue_candidate_gates_to_acceptance(standard_dir, audit)
    print(
        json.dumps(
            {
                "standard_dir": str(standard_dir),
                "issue_candidate_count": audit.get("count"),
                "unresolved_blocking_count": audit.get("unresolved_blocking_count"),
                "disposition_counts": audit.get("disposition_counts"),
                "acceptance_status": acceptance.get("status"),
                "quality_score": acceptance.get("quality_score"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
