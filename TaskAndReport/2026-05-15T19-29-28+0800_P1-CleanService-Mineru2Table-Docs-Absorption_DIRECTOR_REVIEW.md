# Director Review: P1 CleanService Mineru2Table Docs Absorption

- Task ID: `TASK-20260515-192113-P1-CleanService-Mineru2Table-Docs-Absorption`
- Review time: 2026-05-15T19:29:28+0800
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-15T19-21-13+0800_P1-CleanService-Mineru2Table-Docs-Absorption_REPORT.md`
- Result: `ACCEPTED_PRD_ADDENDUM_REQUIRED_BEFORE_CANONICAL_ARCHITECTURE_DOCS`

## Judgment

I accept the Architect absorption report.

The report correctly distinguishes the user-provided CleanService/Mineru2Table materials as valuable draft source material, not current project truth. It also correctly identifies the stale draft issues that must be reconciled before canonical promotion:

- ADR still contains open questions;
- Vision still has fixed `N=3` retention;
- Protocol lacks `options.max_cost_cny` / `options.max_tokens_total`;
- adaptation plan must align with `¥5` Luceon soft limit, `¥8` service hard limit, and deprecated multipart route retention;
- new `eduassets-raw` / `eduassets-clean` layout should apply to new assets while legacy data remains legacy unless separately migrated.

## Accepted Findings

Accepted:

- Mineru2Table is directionally appropriate as a future `toc-rebuild` CleanService;
- MinIO object references are the right integration primitive;
- Luceon should remain orchestrator and own material/version/task/review/circuit semantics;
- direct copy of the draft docs would be unsafe;
- ProductManager PRD addendum is required before canonical architecture/contract docs are promoted as implementation direction.

Not accepted or not claimed:

- CleanService architecture is not yet project truth;
- no canonical docs have been approved;
- no code implementation is authorized;
- no production or runtime change is authorized;
- this review does not affect the separate Task 181 pressure-test blocker.

## Next Action

I am issuing Task 184 to ProductManager to draft a CleanService/Mineru2Table PRD addendum. After that addendum is reviewed, Director can dispatch a reconciled Architect task for canonical architecture/contract docs.
