# P0 Contents First Canonical TOC Spine And Span Binding Report

Completed at: 2026-06-04T13:20:00+0800

Branch: `codex/task-326-contents-first-canonical-toc`

## Summary

Implemented Contents-first canonical TOC generation for layer-3 RawLaTeX scaffold.

When MinerU markdown is available in `mineru-result.zip`, the adapter now extracts the book Contents section and uses it as the global canonical TOC spine. Official Popo/review tree remains the source evidence for block/page binding and exercise supplementation, but its hierarchy is no longer trusted as the book-level directory authority.

## Changes

- `luceon_service/service.py`
  - Extracts optional Markdown from MinerU result zip.
  - Parses Contents entries for units, chapters, sections, past paper questions, glossary, and index.
  - Builds canonical TOC from Contents first when available.
  - Binds Popo/review tree source block/page evidence by numbering/title signals.
  - Keeps fallback Task 325 behavior when no Contents markdown exists.
  - Fixes OCR-glued numbered section classification such as `12.1Different...`.
- `luceon_service/tests/test_popo_invocation_boundary.py`
  - Adds Contents-first regression coverage for missing sections and Unit Project handling.

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

## A800 Math 2022 Evidence Replay

Input:

- Task 324 `toc_view.json`
- A800 Math 2022 MinerU markdown Contents excerpt
- No Popo inference rerun
- No LLM call

Before Task 326:

- Unit-like nodes: 8
- sections: 100 / expected 103
- missing: `1.5`, `12.1`, `15.4`
- many sections inherited wrong unit/project parent chains

After Task 326:

- compiler: `luceon-layer3-deterministic-rules/contents-first`
- units: 6
- sections: 103 / expected 103
- missing sections: none
- extra sections: none
- misplaced sections by Unit 1-6 rule: 0
- RawLaTeX scaffold entries: 358

## Residual Risks

- Contents OCR can still contain title spacing issues, but it is a better global spine than Popo body hierarchy for this textbook.
- Source block/page binding may be missing where official body tree cannot match a Contents entry; such cases are explicitly warned instead of invented.
- This remains RawLaTeX scaffold, not final CleanLaTeX.

## Negative Scope Confirmation

- No MinerU-Popo core/model change.
- No Popo inference rerun.
- No LLM call.
- No invented textbook content.
- No asset hash rename.
- No DB/MinIO cleanup.
- No production deployment/readiness/L3/go-live claim.
