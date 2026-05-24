# TASK-20260524-173140-P0-CleanMaterial-Operator-Decision-Minimal-UI-And-Metadata-Patch-MockSafe-NoRuntime-NoLiveDBWrite

Issued at: 2026-05-24T17:31:40+0800

Actor: Lucode

## Mainline Objective

Turn the current Clean Material surface from "inspectable evidence" into a
minimal operator-gated product object.

The current mainline has already reached:

```text
toc-rebuild v4 durable metadata
=> product-visible Clean Material summary
=> read-only artifact inspection
=> narrow operator decision semantics plan
```

This task should implement the smallest product surface and metadata patch
construction needed for an operator to mark the current Clean Material version
as accepted, needing repair, or rejected. It must not grow into an approval
system, workflow engine, permission system, batch review feature, or downstream
RawMaterial2CleanMaterial launch.

## Critical Path Scope

Implement only the current-version operator decision path for the existing Clean
Material card.

Required scope:

1. Extend the Clean Material view model to expose `operatorDecision` from:

   ```text
   material.metadata.cleanMaterials[serviceName].operatorDecision
   ```

2. Default an existing inspectable Clean Material with no recorded decision to:

   ```text
   pending-review
   ```

3. Add minimal UI in the existing Clean Material card for the current version:

   ```text
   Accept
   Needs repair
   Reject
   ```

4. Require a reason for negative decisions:

   ```text
   needs-repair
   rejected
   ```

5. Construct a bounded material metadata PATCH payload that records:

   - `state`;
   - `decidedAt`;
   - `decidedBy`;
   - optional `note`;
   - required `reason` for negative decisions;
   - `artifactSnapshot.assetVersion`;
   - `artifactSnapshot.jobId`;
   - `artifactSnapshot.provenanceObjectName`;
   - `artifactSnapshot.sourceInput`;
   - `artifactSnapshot.artifactRefs`.

6. Preserve existing material metadata and existing Clean Material summary
   fields. Because the current DB PATCH route shallow-merges `metadata`, the
   implementation must not send a partial `metadata.cleanMaterials` object that
   drops sibling services or existing fields such as `latestVersion`, `status`,
   `provenanceObjectName`, `prefix`, `sourceInput`, `stats`, or `warnings`.

7. Keep decision writes material-scoped only for this task. Do not mirror the
   decision into task metadata unless a future task explicitly authorizes that.

8. Validate with mock-safe tests or smokes only. Lucode must not execute a live
   DB PATCH, browser-click a real decision save, run CleanService runtime, or
   touch production.

## True Preconditions

Use current `main` as the baseline.

Accepted anchors:

- Task 267: durable `toc-rebuild v4` metadata exists for the canonical sample.
- Task 268: Clean Material summary card is product-visible.
- Task 269: Clean Material artifacts are read-only inspectable.
- Task 270: narrow operator decision semantics accepted at planning level.

Canonical sample for mocks and examples:

```text
materialId = 1842780526581841
taskId = task-1779085089451
serviceName = toc-rebuild
assetVersion = v4
jobId = luceon-task-1779085089451-toc-rebuild-v4
```

Lucode may use this sample shape in mock fixtures, but the implementation must
not hard-code this material ID, task ID, job ID, or version as the only usable
path.

## Allowed Files

Allowed implementation files:

- `src/app/utils/cleanMaterialView.ts`
- optional new focused helper under `src/app/utils/`, for example
  `src/app/utils/cleanMaterialDecision.ts`
- `src/app/components/CleanMaterialSummaryCard.tsx`
- optional new focused component under `src/app/components/`, for example
  `src/app/components/CleanMaterialOperatorDecisionControl.tsx`
- `src/app/pages/AssetDetailPage.tsx`
- `src/app/pages/TaskDetailPage.tsx`
- `src/store/types.ts` only if a narrow type addition is needed

Allowed test/check files:

- a focused no-dependency mock-safe check if needed, preferably colocated with
  the helper pattern already used by the repo or under `server/tests/` with no
  live runtime dependency.

Allowed control-plane files:

- this task's Lucode report under `TaskAndReport/`;
- branch-local update to `TaskAndReport/TASK_TRACKING_LIST.md`.

## Forbidden Operations And Files

Forbidden files unless Luceon explicitly issues a broader task:

- `server/upload-server.mjs`
- `server/db-server.mjs`
- CleanService runtime/orchestration files
- Mineru2Table integration files
- `scripts/`
- `uat/`
- package files
- Docker/Compose files
- PRD/architecture docs
- local private role files: `AGENTS.md`, `.agents/**`

Forbidden operations:

- live DB `POST` / `PATCH` / `PUT` / `DELETE`;
- manual browser save against a live runtime;
- CleanService runtime run;
- Mineru2Table POST, submit-probe, live job query, or alternate endpoint probe;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- production deployment or production runtime validation;
- model, env, secret, sample, source asset, or local override mutation;
- DB schema migration;
- broad approval workflow, assignment, escalation, role/permission redesign, or
  audit-export system;
- RawMaterial2CleanMaterial execution, button, scheduling, or launch;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claims.

## Product Requirements

The Clean Material card should show:

- current operator decision state;
- `pending-review` when the Clean Material is present and no decision exists;
- read-only existing decision details when a decision exists;
- available actions only for the current non-superseded Clean Material version;
- disabled action state when artifact refs are missing;
- negative-decision reason input;
- optional note input if it can be kept compact.

Use a bounded local operator label such as `local-operator` if the app has no
current authenticated operator identity. Do not implement authentication or
multi-user governance in this task.

## Metadata Patch Requirements

The future user-triggered save path may use the existing DB proxy route:

```text
PATCH /__proxy/db/materials/:materialId
```

However, Lucode must validate this only with a mocked/stubbed fetch or helper
unit check, not against the live DB.

The patch must target material metadata only:

```text
material.metadata.cleanMaterials[serviceName].operatorDecision
```

The patch must preserve:

- existing material top-level fields;
- existing `metadata` sibling branches;
- existing `metadata.cleanMaterials` sibling services;
- existing current service summary fields.

The patch must not modify:

- task metadata;
- artifact object names;
- sourceInput object names or hashes;
- CleanService execution status;
- downstream RawMaterial2CleanMaterial status.

## Fast Validation Target

Use mock data shaped like the current canonical `toc-rebuild v4` metadata and
prove:

1. no stored decision renders as `pending-review`;
2. `accepted` can produce a bounded patch with operator identity, timestamp,
   and artifact snapshot;
3. `needs-repair` and `rejected` require non-empty reason;
4. missing artifact refs disable decision submission;
5. a superseded or non-current version is read-only;
6. the generated metadata patch preserves existing clean-material fields and
   sibling metadata branches;
7. the validation uses stubbed/mocked fetch or pure helper checks and performs
   zero live DB writes.

## Deferrable Side Work

Defer:

- task-level decision mirroring;
- durable historical decision registry;
- version comparison UI;
- batch decision UI;
- multi-user identity, permissions, assignments, and governance;
- audit export/reporting;
- artifact annotation or editing;
- automatic repair/rebuild;
- RawMaterial2CleanMaterial;
- production validation and readiness.

## Stop Rule

Stop and report blocked instead of widening scope if implementation appears to
require:

- live DB mutation for validation;
- a new server route or DB schema migration;
- auth/permission redesign;
- broad workflow, dashboard, assignment, or batch-review design;
- CleanService runtime or Mineru2Table interaction;
- task metadata mirroring;
- RawMaterial2CleanMaterial behavior.

## Acceptance Criteria

Luceon can accept this task at code/test level if:

- the UI exposes the current operator decision state in the Clean Material card;
- current v4 with no decision defaults to `pending-review`;
- `accepted`, `needs-repair`, and `rejected` are supported for the current
  non-superseded version;
- negative decisions require a reason;
- the metadata patch contains a bounded artifact snapshot;
- the patch preserves existing material metadata and service summary fields;
- validation is mock-safe and records no live DB write/runtime operation;
- changed files remain inside the allowed boundary;
- report evidence includes exact branch and full remote HEAD.

Acceptance does not mean production validation, readiness, DB mutation, workflow
approval, or downstream cleaning acceptance.

## Required Checks

At minimum run:

```bash
git diff --check origin/main...HEAD
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Also run a focused mock-safe helper check for decision metadata construction if
one is added. If Lucode does not add a focused check, the report must explain
why `tsc`/build plus code-level helper review is sufficient for this bounded
UI/patch task.

Do not run live runtime validation.

## Required Report

Write:

```text
TaskAndReport/2026-05-24T17-31-40+0800_P0-CleanMaterial-Operator-Decision-Minimal-UI-And-Metadata-Patch-MockSafe-NoRuntime-NoLiveDBWrite_REPORT.md
```

The report must include:

- task id and task brief path;
- exact remote branch and full HEAD;
- files changed;
- implementation summary;
- metadata patch shape summary;
- mock-safe validation evidence;
- commands run with exit codes;
- skipped checks and exact reasons;
- risks, blockers, and residual debt;
- explicit boundary statement confirming no live DB write, no runtime, no
  MinIO write/delete, no Docker/production operation, no RawMaterial2CleanMaterial,
  and no readiness/go-live claim;
- whether Luceon review is required.

## Handoff

After completion, update the branch-local ledger row to:

```text
Status = Lucode 已回报待 Luceon 审查
Next Actor = Luceon
```

Push a remote branch named like:

```text
lucode/TASK-20260524-173140-P0-CleanMaterial-Operator-Decision-Minimal-UI-And-Metadata-Patch-MockSafe-NoRuntime-NoLiveDBWrite
```

Do not merge to `main`.
