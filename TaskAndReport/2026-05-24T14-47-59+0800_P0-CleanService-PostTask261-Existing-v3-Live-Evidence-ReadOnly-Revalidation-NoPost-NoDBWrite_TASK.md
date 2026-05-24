# TASK-20260524-144759-P0-CleanService-PostTask261-Existing-v3-Live-Evidence-ReadOnly-Revalidation-NoPost-NoDBWrite

Issued at: 2026-05-24T14:47:59+0800

Actor: Luceon

## Mainline Objective

Determine whether the Task 261 mainline product code can consume the current
live-shaped task/material evidence and existing physical/job-store `v3`
CleanService evidence in a read-only, no-POST, no-DB-write rehearsal.

This task is a validation and evidence task for the `PDF -> Raw Material ->
Clean Material` chain. It is not a Lucode implementation task.

## Critical Path Scope

Luceon must perform a focused read-only revalidation from current `origin/main`
after Task 261 acceptance:

1. Sync the Luceon workspace with GitHub `main`.
2. Reconfirm current task ledger state and Task 261 closure.
3. Read only the directly relevant Task 259, Task 260, and Task 261 evidence.
4. Inspect the current CleanService product-code surface only as needed to run
   the rehearsal.
5. Perform read-only live-evidence collection:
   - DB GET for the target task/material;
   - MinIO list/get for accepted raw input and existing `v3` clean artifacts;
   - local Mineru2Table job-store file read for existing canonical and `-probe`
     `v3` job records.
6. Run a local product-code rehearsal with injected tripwire dependencies so
   `submitJob`, live runtime query, DB writes, and MinIO writes cannot occur.
7. Write a Luceon report and update the task ledger.

Target task/material baseline:

- Task: `task-1779085089451`
- Material: `1842780526581841`
- Accepted current DB state before this task: `toc-rebuild` `v2`
- Existing diagnostic physical/job-store target: `toc-rebuild/1842780526581841/v3/`
- Canonical `v3` job id: `luceon-task-1779085089451-toc-rebuild-v3`
- Observed provenance `v3` job id: `luceon-task-1779085089451-toc-rebuild-v3-probe`

## True Preconditions

- `origin/main` must include Task 261 acceptance.
- The workspace must be clean before report/ledger writing, except for this
  task's own allowed TaskAndReport edits.
- The target live services may be read only if they are already running.
  Luceon must not start, restart, rebuild, recreate, or reconfigure services to
  make this task pass.
- If read-only DB/MinIO/job-store evidence is unavailable, Luceon must report
  blocked instead of mutating runtime state.

## Allowed Reads

- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 259, Task 260, and Task 261 task/report/review files
- Directly relevant CleanService source and smoke-test files
- Read-only DB GET through the existing upload-server or DB endpoint
- Read-only MinIO list/get through existing configured credentials already
  available to the running service
- Read-only local file read of
  `/Users/concm/prod_workspace/Mineru2Tables/data/jobs.json`

## Allowed Writes

Only these repository writes are allowed:

- this task brief;
- the matching Luceon report;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

No business source-code edits are allowed.

## Forbidden Operations

This task forbids:

- runtime POST, including `POST /api/v1/jobs` and
  `POST /api/v1/jobs:from-storage`;
- submit-probe;
- live Mineru2Table job query through product runtime adapters;
- DB PATCH/POST/PUT/DELETE or any DB write;
- MinIO put/copy/move/delete/write/delete-marker or any object mutation;
- Docker/Compose restart/recreate/build/down/up/volume/prune;
- job-store edit;
- env, credential, model, secret, or sample mutation;
- cleanup, reset, rollback, retry, reparse, re-AI, or repair;
- worker, scheduler, or upload-server CleanService activation;
- Lucode implementation work;
- UAT, L3, pressure PASS, production readiness, release readiness,
  production online, or go-live claims.

## Current Evidence

Current control-plane anchor at dispatch:

```text
main = origin/main = 59d143c00b9dc6fdb905358984af0da94fa4190e
```

Task 261 accepted only mock-safe code/test evidence:

- source-input object paths are validated by literal path segments;
- material IDs with regex metacharacters are handled literally;
- versions are constrained to numeric `vN`;
- canonical rawMaterial remains first priority;
- completed-job `sourceInput` fallback is bounded and traceable;
- legacy parsed evidence is not promoted;
- existing `v3` no-POST reconciliation bypasses submit/query in mock-safe tests;
- explicit `allowProbeJobIdSuffix=true` is required for `-probe`;
- real apply and mismatch blockers remain.

Task 260 recorded the live evidence target:

- current DB remains accepted `v2`;
- physical/job-store `v3` exists but is diagnostic;
- canonical and `-probe` `v3` job-store keys point to the same prefix;
- provenance `input size_bytes=0` remains residual debt;
- before Task 261, full runner with live DB payload threw
  `legacy-parsed-evidence-skipped`.

## Fast Validation Target

The smallest useful proof is a read-only rehearsal showing whether current
main product code can reach an existing-`v3` no-POST dry-run result using:

- live-shaped DB task/material payload;
- accepted `sourceInput` fallback from the completed clean job;
- existing `v3` job-store/artifact refs;
- explicit `allowProbeJobIdSuffix=true`;
- tripwire dependencies proving no submit/query/write path was invoked.

## Positive Acceptance Criteria

Accept the task as successful only if the Luceon report proves:

1. DB GET and MinIO/job-store reads were read-only and bounded.
2. The target raw input and seven `v3` artifacts are present and hash-verified
   or otherwise explicitly reconciled to prior accepted evidence.
3. Current main product code handles the live-shaped payload without harness
   injection of `metadata.rawMaterial.mineru.contentListV2`.
4. Existing `v3` no-POST reconciliation reaches the expected dry-run outcome
   with `submitJob`, runtime job query, DB write, and MinIO write tripwires
   untouched.
5. `-probe` provenance is accepted only under explicit policy and the report
   records both canonical and observed job IDs.
6. The report preserves residual risks, especially diagnostic `v3`, dual
   job-store keys, and provenance `input size_bytes=0`.

## Negative Acceptance Criteria

Return blocked if success would require any of:

- runtime POST or submit-probe;
- live Mineru2Table job query through product adapters;
- DB write or DB metadata apply;
- MinIO write/delete/copy/move;
- job-store edit;
- Docker/Compose/service mutation;
- source-code changes;
- sample/env/credential/model mutation;
- treating Task 256 as retroactively successful;
- claiming readiness, UAT, L3, pressure PASS, or go-live.

## Required Checks

At minimum, record commands and exit codes for:

- `git status --short --branch`
- `git fetch origin --prune --tags`
- `git pull --ff-only origin main`
- `git rev-parse HEAD origin/main`
- `git diff --check`
- read-only DB GET evidence command
- read-only MinIO list/get evidence command
- read-only job-store evidence command
- local product-code rehearsal command

Run focused syntax or smoke checks only if needed to support the rehearsal.
Do not broaden into Lucode implementation checks.

## Report Requirements

Write:

```text
TaskAndReport/2026-05-24T14-47-59+0800_P0-CleanService-PostTask261-Existing-v3-Live-Evidence-ReadOnly-Revalidation-NoPost-NoDBWrite_REPORT.md
```

The report must include:

- final classification;
- exact Git baseline;
- command table with exit codes;
- read-only DB/MinIO/job-store evidence summary;
- tripwire call summary;
- product-chain result;
- accepted facts;
- blocked facts or residual risks;
- explicit non-claims and forbidden operations not performed;
- recommended next decision or task.

## Stop Rule

Stop and report blocked as soon as the read-only route requires mutation,
runtime POST, live runtime query, service restart, source-code change, or any
operation outside this brief.

## Review Boundary

Acceptance of this task can only mean:

```text
Post-Task261 read-only live-evidence rehearsal completed or blocked with
traceable evidence.
```

It must not be described as runtime success, DB apply success, CleanService
activation, UAT, L3, pressure PASS, production readiness, release readiness,
production online, or go-live.
