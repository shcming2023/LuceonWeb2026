# TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime Luceon Review

Review time: 2026-05-24T17:10:28+0800

Reviewer: Luceon

## Decision

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_INTEGRATION_AND_HEAD_CORRECTION
```

Task 269 is accepted at code/test/product-surface level and integrated into
`main`.

This acceptance means the accepted single-sample `toc-rebuild v4` Clean
Material artifacts now have a minimal read-only product inspection surface. It
does not mean CleanService automation, approval workflow, batch validation, UAT,
L3, pressure PASS, production readiness, release readiness, production online,
or go-live.

## Review Anchors

| Item | Value |
| --- | --- |
| Task brief | `TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_TASK.md` |
| Lucode report | `TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_REPORT.md` |
| Reviewed branch | `origin/lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime` |
| Reviewed branch HEAD | `e224cdf12ebd67806bf2aedb8cf50f972146657a` |
| Review baseline | `origin/main@8bd4cd3a7e087e6b2bb4355ba8698341b1641426` |
| Integration method | `git merge --ff-only origin/lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime` |

## Luceon Evidence Correction

Lucode's report and branch-local ledger again did not embed the final full
remote HEAD and instead referred to the final handoff. Luceon independently
resolved the reviewed remote branch HEAD as:

```text
e224cdf12ebd67806bf2aedb8cf50f972146657a
```

The implementation is accepted; the final HEAD evidence is corrected in this
review and in the closed ledger row.

## Diff Scope

Three-dot changed files:

```text
A TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_REPORT.md
M TaskAndReport/TASK_TRACKING_LIST.md
M server/upload-server.mjs
A src/app/components/CleanMaterialArtifactInspector.tsx
M src/app/components/CleanMaterialSummaryCard.tsx
```

The implementation stayed inside the allowed task surface.

## Code Review Findings

Accepted:

- `CleanMaterialArtifactInspector` is embedded in the existing Clean Material
  card rather than introducing a new workflow surface.
- The inspector selects `readable_tree.md` first when available, then JSON, then
  the first artifact.
- Markdown artifacts use the existing escaped `renderMarkdown()` path.
- JSON artifacts are fetched read-only and pretty-printed when parseable, with
  text fallback when not parseable.
- Artifact open links use the existing `/__proxy/upload/proxy-file` route with
  explicit bucket information.
- The existing `resolveBucketForObject()` path now narrowly accepts
  `bucket=clean` and `bucket=eduassets-clean`, resolving to `eduassets-clean`.
  No write, delete, list-clean, cleanup, runtime, or broad storage-config path
  was added.
- `prefix=null` remains tolerated because the UI operates from task artifact
  refs already surfaced by Task 268.
- Empty, loading, fetch-error, and unsupported-preview states are present.

Residual but accepted:

- Browser runtime verification was not run by Lucode or Luceon. This review is
  code/test-level product-surface acceptance based on static build and code
  inspection.
- The clean bucket name is currently a narrow resolver default/env read
  (`MINIO_CLEAN_BUCKET || eduassets-clean`), not a full storage settings model.
  That is acceptable for this mainline step and should not be generalized until
  needed.

## Checks

Luceon ran:

| Command | Result | Notes |
| --- | --- | --- |
| `git diff --name-status origin/main...origin/lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime` | PASS | scoped files only |
| `git diff --check origin/main...origin/lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime` | PASS | no whitespace errors |
| `git diff --check origin/main...HEAD` | PASS | repeated on detached reviewed HEAD |
| `node --check server/upload-server.mjs` | PASS | exit 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS | exit 0 |
| `npx pnpm@10.4.1 run build` | PASS | exit 0; Vite built 1649 modules; existing large chunk warning only |

## Boundary

Not performed by Luceon review:

- CleanService runtime run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- DB `POST` / `PATCH` / `PUT` / `DELETE`;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume mutation;
- job-store edit;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- production deployment or production runtime validation;
- approval/rejection workflow;
- RawMaterial2CleanMaterial implementation;
- model/env/secret/sample/source mutation;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live claim.

## Next Recommendation

The mainline has now moved from durable v4 metadata to product-visible summary
and artifact inspection.

The next useful mainline step should be a Director-level product decision:
define the minimal operator outcome after artifact inspection. Recommended
options are:

1. `CleanMaterial Inspect ReadOnly Browser Verification` if the Director wants
   browser evidence before further work.
2. `CleanMaterial Operator Decision Surface Planning` to decide whether the next
   user action is approve, reject, request repair, or proceed to the next clean
   stage.

Do not start broad automation, batch processing, or RawMaterial2CleanMaterial
from this acceptance alone.
