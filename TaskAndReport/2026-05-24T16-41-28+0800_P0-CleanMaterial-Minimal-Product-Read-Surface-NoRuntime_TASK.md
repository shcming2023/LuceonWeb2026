# TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime

Issued at: 2026-05-24T16:41:28+0800

Actor: Lucode

## Mainline Objective

Make the already promoted single-sample `toc-rebuild v4` Clean Material visible
and reviewable in the product surface.

The current stage breakthrough is:

```text
PDF -> Raw Material -> CleanService toc-rebuild v4 metadata
=> operator can see and verify the current Clean Material from existing product pages
```

Task 267 already made `v4` durable DB product truth for the canonical sample.
This task turns that durable backend fact into a minimal read-only product
surface. It must not reopen runtime execution, planner normalization, broad
metadata governance, or CleanService automation.

## Critical Path Scope

Implement the shortest product path that lets an operator inspect the current
Clean Material summary for:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
current clean assetVersion = v4
current clean jobId = luceon-task-1779085089451-toc-rebuild-v4
provenanceObjectName = toc-rebuild/1842780526581841/v4/provenance.json
raw input object = mineru/1842780526581841/v1/content_list_v2.json
raw input sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
raw input size = 31543
tokensTotal = 6266
unresolvedAnchorCount = 0
artifact count = 7
```

Minimum expected implementation:

1. Add a thin read model/helper for the existing metadata shape:
   - `material.metadata.cleanMaterials["toc-rebuild"]`
   - `task.metadata.cleanServiceJobs["toc-rebuild"]`
2. Add a minimal UI card or section in existing detail surfaces, preferably:
   - `src/app/pages/AssetDetailPage.tsx`
   - `src/app/pages/TaskDetailPage.tsx`
3. Show the current clean material state without fetching artifact content:
   - service name;
   - status / cleanState;
   - `latestVersion` / `assetVersion`;
   - job id when available from task metadata;
   - provenance object ref;
   - source input object / sha256 / size;
   - token count and unresolved anchor count;
   - artifact role/object refs or at least a role count plus expandable refs.
4. Handle the known Task 267 shape where
   `material.metadata.cleanMaterials["toc-rebuild"].prefix` is `null`.
   Do not treat this as absence of Clean Material when task artifact refs and
   material provenance ref are present.
5. Show a quiet empty state when no Clean Material metadata exists.

## True Preconditions

- Start from current GitHub `main`.
- Treat Task 267 report and ledger row as the current evidence anchor.
- Keep all data access read-only.
- Keep the implementation compatible with existing `MaterialMetadata` extension
  fields and current task/material objects.

## Allowed Files And Modules

Allowed implementation files:

- `src/store/types.ts`
- `src/app/utils/cleanMaterialView.ts` or another focused utility under
  `src/app/utils/`
- `src/app/pages/AssetDetailPage.tsx`
- `src/app/pages/TaskDetailPage.tsx`
- `src/app/components/ProcessPipelineCard.tsx`
- `src/app/components/MetadataTab.tsx`
- one small focused component under `src/app/components/` if it keeps the UI
  simpler than embedding the view twice

Allowed test/report files:

- focused tests or smoke helpers under existing test locations if useful;
- the required Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

If another file is truly necessary, record why in the report and keep the
change directly tied to this read surface.

## Forbidden Operations

Forbidden:

- runtime CleanService run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- DB `POST` / `PATCH` / `PUT` / `DELETE`;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, or pressure test;
- production deployment or production runtime validation;
- model, env, secret, sample, source asset, or local override mutation;
- broad product redesign, navigation rewrite, scheduler/worker activation,
  RawMaterial2CleanMaterial implementation, or generalized CleanService
  registry/lifecycle abstraction;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live claims.

`NoRuntime` here means no CleanService/runtime/data mutation and no production
operation. Developer `tsc`, build, and local read-only UI checks are allowed.

## Deferrable Side Work

Do not solve these in this task:

- material-side `prefix=null` database normalization;
- planner/candidate summary normalization for future jobs;
- artifact content previews/download authorization;
- multi-service Clean Material registry;
- batch CleanService listing;
- worker/scheduler activation;
- RawMaterial2CleanMaterial cleaning stage;
- broad AI metadata governance cleanup.

Record any useful observations as residual debt in the report.

## Fast Validation Target

The fastest useful proof is:

```text
given current Task 267 v4 metadata shape
=> product read model returns current toc-rebuild v4 summary
=> existing detail surface displays v4 as current Clean Material
=> prefix=null does not hide the clean material
=> no write/runtime path is introduced
```

Use a small fixture/unit check if practical. If browser verification is run, it
must be read-only and the report must state the URL and exact observed fields.

## Positive Acceptance Criteria

Luceon can accept the task if all are true:

- a user can find the `toc-rebuild v4` Clean Material summary from an obvious
  existing detail view for the canonical sample;
- the surface shows `v4` as current and does not present `v2` as the current
  Clean Material;
- the surface exposes enough refs for manual traceability:
  job id, provenance object, source input object/sha/size, artifact count or
  refs, token count, and unresolved anchor count;
- `prefix=null` on material summary is handled gracefully;
- absence of Clean Material metadata renders a clear empty state;
- no runtime, DB write, MinIO write, Docker, upload, retry, reparse, Re-AI, or
  production operation is added or executed;
- TypeScript/build checks pass or any skipped check is justified with exact
  reason.

## Negative Acceptance Criteria

Return or block the task if:

- the UI hides v4 because `material.cleanMaterials.toc-rebuild.prefix` is null;
- the implementation requires live artifact content fetches to show the summary;
- the implementation mutates task/material metadata;
- a POST/PATCH/PUT/DELETE path is added or executed for this feature;
- the branch performs broad UI redesign, generalized registry work, or unrelated
  cleanup;
- the report claims UAT/L3/readiness/go-live or broad production validation.

## Required Checks

Run at minimum:

```bash
git diff --check origin/main...HEAD
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If a focused utility/test is added, run the corresponding focused check. If any
check is skipped, record the exact reason.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T16-41-28+0800_P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- implementation summary;
- product surface summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- evidence for the v4 read surface, including how `prefix=null` is handled;
- explicit boundary statement confirming no runtime, no DB write, no MinIO
  write, no Docker/production operation, and no readiness/go-live claim;
- risks, blockers, and residual debt;
- whether Luceon review is required.

## Handoff

After completion, update the branch-local ledger row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Push a remote branch named like:

```text
lucode/TASK-20260524-164128-P0-CleanMaterial-Minimal-Product-Read-Surface-NoRuntime
```

Do not merge to `main`.
