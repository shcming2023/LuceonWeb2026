# P0 Canonical TOC And RawLaTeX Scaffold From Official Popo Tree Report

Completed at: 2026-06-04T13:10:00+0800

Branch: `codex/task-325-canonical-toc-rawlatex-scaffold`

## Summary

Implemented Luceon layer-3 deterministic compiler on top of the Task 324 official/review tree split.

New derived artifacts:

- `canonical_toc.json`
- `chapter_spans.json`
- `rawlatex_scaffold.json`

The implementation does not rerun MinerU-Popo inference and does not call an LLM. It compiles from the existing filtered review tree while preserving official Popo raw tree artifacts separately.

## Implementation

Changed:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`

Key behavior:

- Classifies TOC nodes into `unit`, `chapter`, `section`, `exercise`, `practice`, `past_paper`, `glossary`, `index`, and `unknown_heading`.
- Builds stable node ids and deterministic parent/child structure.
- Preserves source block ids and page ranges when present.
- Adds explicit warnings when source trace is missing, long headings need review, numbering regresses, or parent spans contain child spans.
- Produces RawLaTeX scaffold entries with source trace comments and TODO boundaries only; no cleaned prose is invented.
- Writes the new artifacts as extra CleanService artifact refs while keeping the existing seven-artifact roles intact.

## Validation

Passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
npx tsc --noEmit
npm run build
git diff --check
```

Real evidence replay:

- Input: Task 324 A800 Math 2022 `toc_view.json` evidence.
- Output summary:
  - `canonical_toc` nodes: 390
  - kind counts: `unit=8`, `chapter=33`, `section=100`, `exercise=216`, `practice=26`, `past_paper=5`, `glossary=1`, `index=1`
  - `chapter_spans`: 390
  - RawLaTeX scaffold files: 390

Evidence was generated locally under production control evidence:

```text
TaskAndReport/evidence/2026-06-04_Task324_TOC_View_Filter_UAT/task325_generated/
```

## Residual Risks

- The compiler is conservative: when official Popo/review tree lacks block ids or page ranges, it emits warnings instead of inventing source truth.
- OCR-damaged titles and inherited hierarchy drift are flagged/contained but not semantically repaired here.
- This produces RawLaTeX scaffold, not final CleanLaTeX.

## Negative Scope Confirmation

- No MinerU-Popo upstream/core/model change.
- No Popo inference rerun for validation.
- No LLM call.
- No invented textbook content.
- No asset hash rename.
- No DB/MinIO cleanup.
- No go-live/readiness/L3 claim.

