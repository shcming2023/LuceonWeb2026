# Lucia Review: P0 Parsed ZIP Manual Sample Layout Production Revalidation

- Review Time: `2026-05-09T18:59:37+0800`
- Reviewer: Lucia
- Reviewed Task: `TASK-20260509-164028-P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation`
- Reviewed Report: `TaskAndReport/2026-05-09T16-40-28+0800_P0-Parsed-Zip-Manual-Sample-Layout-Production-Revalidation_REPORT.md`
- Lucode Branch: `lucode/p0-parsed-zip-manual-sample-layout-production-revalidation`
- Report/Main HEAD: `0668b268cf6bb0718109e5c90f8c83aaadb204cb`
- Production Code HEAD Reported: `cd1812af0084c3b19b2a885102af2b7f56a45c86`
- Decision: `ACCEPTED_PRODUCTION_REVALIDATED_WITH_EXACT_SAMPLE_GAP`

## Review Summary

Lucode deployed the manual-sample parsed ZIP layout correction to production and rebuilt only `upload-server`. The production health endpoint returned OK.

Lucode could not validate against the exact Cambridge material because no matching production material/task was found and direct parsed ZIP probe for material `409615937854928` returned no parsed files. Lucode correctly did not create a new upload because Task 62 did not authorize one.

Lucia accepts the production revalidation because the default parsed ZIP layout was validated on an existing real production parsed material and matches the Director sample's normalized structural contract:

- exactly one user-facing top-level material folder;
- `<material-folder>/full.md`;
- OCR markdown, JSON, PDF, and images lifted directly under `<material-folder>/...`;
- no `<material-folder>/ocr/...`;
- no root `full.md`;
- no root `mineru-result.zip`;
- no root `artifact-manifest.json`;
- no app-generated `__MACOSX` or `.DS_Store`.

`mineru-raw` and `diagnostic` modes remain available for raw/debug access and intentionally retain raw/debug package entries.

## Independent Verification

Lucia independently rechecked:

- Director sample normalized ZIP manifest:
  - normalized file count `4468`;
  - one top-level folder;
  - no root files;
  - no intermediate `ocr` segment;
  - no root raw/debug package files after normalization.
- Production default ZIP `/tmp/luceon-parsed-user-417987242893597-layout.zip`:
  - normalized file count `195`;
  - one top-level folder `教科协和八下数学同步练习册A`;
  - no root files;
  - no intermediate `ocr` segment;
  - no root raw/debug package files.
- Production raw ZIP:
  - retains the raw `ocr/` tree as expected.
- Production diagnostic ZIP:
  - retains root `mineru-result.zip`, `artifact-manifest.json`, `full.md`, and raw `ocr/` tree as expected.
- `curl -fsS http://localhost:8081/__proxy/upload/health` -> PASS
- `git diff --check` -> PASS
- `node server/tests/parsed-zip-export-modes-smoke.mjs` -> PASS

## Residual Gap

The exact Cambridge sample was not revalidated as a production material because the corresponding parsed objects are unavailable in current production storage and Task 62 did not authorize a new upload. This is recorded as an exact-sample gap, not as a default parsed-ZIP layout blocker.

If Director requires byte/path-level revalidation against the Cambridge source material in production, Lucia must issue a separate scoped validation task authorizing a new controlled upload or restoration of the missing parsed object.

## Release Boundary

This review does not declare production release readiness. Task 60 remains Director-owned. Lucia may now treat the parsed-ZIP manual-sample layout blocker as resolved for the default export behavior, with the residual exact-sample gap explicitly recorded.

