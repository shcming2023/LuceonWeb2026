#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.codex_workbook_repair import (
    WorkbookRepairError,
    repair_staging_candidate,
    repair_workbook_project,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply conservative deterministic print repairs to a refined ElegantBook project."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--staging-dir", type=Path)
    source.add_argument("--project-dir", type=Path)
    parser.add_argument("--report", type=Path, help="Optional report path for --project-dir mode.")
    args = parser.parse_args()

    try:
        if args.staging_dir:
            report = repair_staging_candidate(args.staging_dir)
        else:
            report = repair_workbook_project(args.project_dir)
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                report["report_path"] = str(args.report.resolve())
    except WorkbookRepairError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
