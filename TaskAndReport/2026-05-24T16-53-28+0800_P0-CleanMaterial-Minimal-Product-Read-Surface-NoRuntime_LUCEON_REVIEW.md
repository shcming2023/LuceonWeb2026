# TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime Luceon Review

Review time: 2026-05-24T16:53:28+0800

Reviewer: Luceon

## Decision

```text
ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_INTEGRATION_AND_HEAD_CORRECTION
```

Task 268 is accepted at code/test/product-surface level and integrated into
`main`.

This acceptance means the current single-sample `toc-rebuild v4` Clean Material
metadata can be read through existing product detail surfaces. It does not mean
CleanService automation, scheduler/worker activation, batch validation, UAT,
L3, pressure PASS, production readiness, release readiness, production online,
or go-live.

## Review Anchors

| Item | Value |
| --- | --- |
| Task brief | `TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_TASK.md` |
| Lucode report | `TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_REPORT.md` |
| Reviewed branch | `origin/lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime` |
| Reviewed branch HEAD | `9d59be26ce880f57f6c153791a3035797daa094f` |
| Review baseline | `origin/main@80d1af06a4850dddbf48d1182e000daab1a94d5e` |
| Integration method | `git merge --ff-only origin/lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime` |

## Luceon Evidence Correction

Lucode's report and branch-local ledger did not embed the final full remote HEAD
and instead referred to the final handoff. Luceon independently resolved the
remote branch HEAD as:

```text
9d59be26ce880f57f6c153791a3035797daa094f
```

This was a control-plane evidence gap, not an implementation blocker. The
accepted HEAD is recorded in this review and in the closed ledger row.

## Diff Scope

Three-dot changed files:

```text
A TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_REPORT.md
M TaskAndReport/TASK_TRACKING_LIST.md
A src/app/components/CleanMaterialSummaryCard.tsx
M src/app/pages/AssetDetailPage.tsx
M src/app/pages/TaskDetailPage.tsx
A src/app/utils/cleanMaterialView.ts
M src/store/types.ts
```

The implementation stayed inside the allowed task surface.

## Code Review Findings

Accepted:

- `buildCleanMaterialView()` is a thin read-only helper over the existing
  `material.metadata.cleanMaterials["toc-rebuild"]` and
  `task.metadata.cleanServiceJobs["toc-rebuild"]` shapes.
- The helper derives current version, status, job id, provenance, source input,
  token count, unresolved anchor count, artifact refs, and a `hasPrefixGap`
  signal without fetching artifact content.
- `prefix=null` does not hide the accepted v4 summary; provenance and task
  artifact refs remain usable for read-surface traceability.
- `CleanMaterialSummaryCard` renders a quiet empty state when no Clean Material
  metadata exists.
- The card is mounted on both `AssetDetailPage` and `TaskDetailPage` overview,
  making the accepted Clean Material visible from existing product detail flows.
- No write path, runtime trigger, artifact-content fetch, broad registry, or
  unrelated redesign was introduced.

Residual but accepted:

- Browser runtime verification was not run by Lucode or Luceon. This review is
  code/test-level product-surface acceptance based on static build and code
  inspection.
- Material-side `prefix=null` remains a data normalization debt. The UI now
  tolerates it; no DB correction was made or authorized.

## Checks

Luceon ran:

| Command | Result | Notes |
| --- | --- | --- |
| `git diff --name-status origin/main...origin/lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime` | PASS | scoped files only |
| `git diff --check origin/main...origin/lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime` | PASS | no whitespace errors |
| `git diff --check origin/main...HEAD` | PASS | repeated on detached reviewed HEAD |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS | exit 0 |
| `npx pnpm@10.4.1 run build` | PASS | exit 0; Vite built 1648 modules; existing large chunk warning only |

## Boundary

Not performed by Luceon review:

- CleanService runtime run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- DB `POST` / `PATCH` / `PUT` / `DELETE`;
- MinIO write/copy/move/delete/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume mutation;
- job-store edit;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- production deployment or production runtime validation;
- model/env/secret/sample/source mutation;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live claim.

## Next Recommendation

The mainline has now moved from durable v4 metadata to product-visible v4 Clean
Material summary.

The next useful mainline task should be one of:

1. A narrow read-only product verification on the local app surface for the
   canonical sample, if the Director wants browser evidence before the next
   stage.
2. A bounded planner/data-shape follow-up to normalize future `prefix` handling
   without ad hoc DB repair.
3. A first operator workflow decision for what action should follow a visible
   Clean Material: inspect artifacts, approve clean material, or start the next
   cleaning stage.

Do not start broad cleanup or automation activation from this acceptance alone.
