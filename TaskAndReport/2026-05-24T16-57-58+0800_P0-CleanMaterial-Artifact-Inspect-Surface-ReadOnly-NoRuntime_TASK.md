# TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime

Issued at: 2026-05-24T16:57:58+0800

Actor: Lucode

## Mainline Objective

Move the Clean Material mainline from "v4 is visible as metadata" to "v4
artifacts are inspectable by an operator".

The stage breakthrough is:

```text
durable toc-rebuild v4 metadata
=> product-visible Clean Material summary
=> operator can open/read the v4 Clean Material artifacts
```

Task 268 made the accepted `toc-rebuild v4` summary visible on existing asset
and task detail pages. This task should add the minimal read-only artifact
inspection surface needed for human review. Do not widen into workflow
automation, approval, generalized registry, or the next cleaning stage.

## Critical Path Scope

Target canonical sample:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
clean bucket = eduassets-clean
clean prefix = toc-rebuild/1842780526581841/v4/
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Known artifact roles:

```text
flooded_content.json
logic_tree.json
metrics.json
provenance.json
readable_tree.md
skeleton.json
unresolved_anchors.json
```

Minimum expected implementation:

1. Extend the Task 268 Clean Material summary/card path so artifact refs are
   actionable, not only visible.
2. Provide a read-only inspect panel/modal/inline area from existing detail
   surfaces.
3. Preview `readable_tree.md` as text/Markdown using the existing rendering
   style where practical.
4. Preview JSON artifacts as formatted JSON or readable text when selected.
5. Provide a direct open/download link for each artifact through an existing or
   narrowly extended read-only object proxy.
6. Preserve the Task 268 behavior where `material.cleanMaterials.toc-rebuild`
   may have `prefix=null`; artifact inspect must still work from task artifact
   refs and material provenance ref.
7. Render clear loading, error, unsupported, and empty states.

## True Preconditions

Artifact inspection is allowed only as read-only object access.

The current upload proxy resolver supports raw/parsed buckets but does not
clearly expose `eduassets-clean`. If required for this task, Lucode may add the
minimum read-only support needed for:

```text
bucket=clean
bucket=eduassets-clean
```

in the existing `/__proxy/upload/presign` and `/__proxy/upload/proxy-file`
path. This must be a bucket-resolution/read-only-streaming change only. Do not
add write, delete, list-clean, cleanup, runtime execution, or broad storage
configuration behavior.

## Allowed Files And Modules

Allowed frontend files:

- `src/app/utils/cleanMaterialView.ts`
- `src/app/components/CleanMaterialSummaryCard.tsx`
- one focused artifact inspect component under `src/app/components/`
- `src/app/pages/AssetDetailPage.tsx`
- `src/app/pages/TaskDetailPage.tsx`
- existing preview utilities/components if reused narrowly
- `src/store/types.ts` only if the view type needs a small extension

Allowed backend file, only if needed for read-only clean artifact access:

- `server/upload-server.mjs`

Allowed test/report files:

- focused smoke/unit tests for the view helper or upload proxy resolver if
  useful;
- the required Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

If any other file is necessary, record why in the report and keep it directly
attached to artifact inspection.

## Forbidden Operations

Forbidden:

- CleanService runtime run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- DB `POST` / `PATCH` / `PUT` / `DELETE`;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, or pressure test;
- production deployment or production runtime validation;
- model, env, secret, sample, source asset, or local override mutation;
- approval/rejection workflow for Clean Material;
- RawMaterial2CleanMaterial implementation;
- generalized CleanService registry/lifecycle/workflow abstraction;
- broad UI redesign or unrelated cleanup;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live claims.

## Deferrable Side Work

Do not solve these now:

- material-side `prefix=null` DB normalization;
- batch artifact browser;
- artifact annotation, approval, reject, or operator decision workflow;
- Clean Material version comparison;
- artifact content editing;
- RawMaterial2CleanMaterial;
- scheduler/worker activation;
- authorization model redesign for object access.

Record any useful residual debt in the report.

## Fast Validation Target

The fastest useful proof is:

```text
given Task 267/268 v4 metadata
=> click/select readable_tree.md from the Clean Material card
=> product fetches it read-only from eduassets-clean
=> readable content is displayed
=> JSON artifacts can be selected and viewed as formatted JSON/text
=> no write/runtime path is introduced
```

If local browser verification is practical, use a read-only local app check and
record the URL plus observed fields. If browser verification is not run, state
the exact reason and provide static/build evidence.

## Positive Acceptance Criteria

Luceon can accept if all are true:

- the canonical sample exposes actionable v4 artifact refs from the existing
  Clean Material surface;
- `readable_tree.md` can be opened/previewed read-only;
- at least one JSON artifact can be opened/previewed read-only as formatted JSON
  or readable text;
- direct open/download URLs use a read-only proxy/presign route and do not
  require DB or MinIO writes;
- missing artifact refs, fetch failures, and unsupported content types have
  clear UI states;
- `prefix=null` does not block artifact inspection;
- no runtime, POST, DB write, MinIO write/delete, Docker, production operation,
  or workflow automation is added or executed;
- required checks pass or skipped checks are justified exactly.

## Negative Acceptance Criteria

Return or block if:

- artifact inspection depends on a new CleanService run or live Mineru2Table
  query;
- the implementation writes task/material metadata or MinIO content;
- clean artifact object access is routed through raw/parsed bucket by mistake;
- the UI hides v4 artifacts because material `prefix` is null;
- the branch introduces approval/workflow state, generalized registry work, or
  broad redesign;
- the report claims UAT/L3/readiness/go-live or broad production validation.

## Required Checks

Run at minimum:

```bash
git diff --check origin/main...HEAD
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If `server/upload-server.mjs` is changed, also run:

```bash
node --check server/upload-server.mjs
```

If focused tests are added, run them. If any check is skipped, record the exact
reason.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- implementation summary;
- product artifact-inspection summary;
- commands run with exit codes;
- skipped checks and exact reasons;
- evidence that `readable_tree.md` and at least one JSON artifact are inspectable
  or, if browser verification was not run, static evidence of the exact route
  and object URLs that would be used;
- explicit statement for how `eduassets-clean` bucket access is handled;
- explicit boundary statement confirming no runtime, no DB write, no MinIO
  write/delete, no Docker/production operation, and no readiness/go-live claim;
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
lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime
```

Do not merge to `main`.
