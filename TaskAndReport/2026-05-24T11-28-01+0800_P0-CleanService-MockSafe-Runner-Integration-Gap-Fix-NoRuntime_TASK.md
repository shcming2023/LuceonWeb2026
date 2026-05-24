# TASK-20260524-112801-P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime

Issued at: 2026-05-24T11:28:01+0800

## 1. Mainline Objective

Task 256 found the next CleanService runner integration blockers during one
controlled runtime attempt, but that task was closed only as blocked diagnostic
evidence.

This task must fix those blockers in product code using mock-safe tests only:

```text
live provenance response shape
-> provenance job_id -probe policy
-> explicit new-version apply dry-run conflict semantics
```

The mainline question is:

> Can the accepted CleanService product chain handle the Task 256 live-response
> shape and explicit new-version dry-run semantics without harness mutation,
> runtime rerun, DB writes, or MinIO reads?

## 2. Current Evidence

Accepted control-plane baseline:

```text
main@c2fae93bb1a17624362804fbf3fbd7f9572eab09
Task 256 Review v3: ACCEPTED_BLOCKED_DIAGNOSTIC_EVIDENCE_WITH_LUCEON_EVIDENCE_CORRECTION
```

Task 256 blockers:

1. The harness reconstructed or promoted live provenance shape before product
   verifier consumption.
2. The harness normalized `provenance.json` `job_id` by stripping `-probe`.
3. The harness converted real apply dry-run blocker
   `BLOCKED_EXISTING_TOC_REBUILD_METADATA` into `DRY_RUN_SUCCESS`.

Task 256 remains not accepted as runtime dry-run success. It does not authorize
a new runtime validation, real DB apply, or another `POST /api/v1/jobs`.

User authorization for this task:

```text
Approve a separate mock-safe product fix task for the three integration gaps.
```

## 3. Critical Path Scope

Implement only mock-safe product fixes and focused tests for these behaviors.

### 3.1 Live Provenance Response Shape

The product chain must not require a harness to inject `job.provenance` into
the queried job response when the response already contains the seven artifact
ObjectRefs, including `artifacts.provenance`.

Required behavior:

- a completed queried job with artifact refs but no top-level `job.provenance`
  can reach `verifyCleanServiceOutputArtifacts`;
- the verifier reads `provenance.json` through the injected artifact reader;
- sourceInput is extracted from `provenance.inputs[0]` or `provenance.input`;
- missing/invalid provenance artifact still blocks honestly;
- no full artifact body is persisted in task/material metadata.

### 3.2 Provenance `job_id -probe` Policy

The product chain must make the `-probe` mismatch an explicit policy, not a
harness-side string mutation.

Required behavior:

- exact `provenance.job.job_id === expectedJobId` remains accepted;
- `provenance.job.job_id === expectedJobId + "-probe"` may be accepted only as
  a bounded, explicit compatibility policy;
- when the compatibility policy is used, the result must preserve both the
  canonical submitted jobId and the observed provenanceJobId in bounded
  verification/candidate/audit data, and must emit a warning such as
  `provenance-job-id-probe-suffix-accepted`;
- arbitrary suffixes, unrelated job IDs, missing job IDs, or mismatched
  material/version/raw input must still block before candidate persistence;
- the product code must not mutate the parsed provenance object to pretend the
  IDs were identical.

If Lucode believes accepting the `-probe` suffix is unsafe, stop and report a
blocked design finding instead of silently choosing another policy.

### 3.3 Explicit New-Version Apply Dry-Run Conflict Semantics

The dry-run apply path must distinguish:

- incompatible existing metadata that should block; from
- a valid explicit `create-new-version` plan whose current DB state still has
  completed aligned previous-version metadata.

Required behavior:

- with `allowRealApply=false`, explicit new-version intent, completed aligned
  existing `v2` task/material metadata, and target `v3` plan, dry-run apply may
  return `DRY_RUN_SUCCESS`;
- this must be implemented in product semantics, not by the runtime harness
  catching and converting `BLOCKED_EXISTING_TOC_REBUILD_METADATA`;
- unrelated existing metadata, failed/mismatched history, missing previous
  jobId, same-version overwrite, target mismatch, or missing explicit intent
  must still block;
- `allowRealApply=true` remains forbidden for this task unless existing code
  already blocks before DB calls. Do not implement or test real DB writes.

## 4. True Preconditions

Before editing, Lucode must confirm:

- current branch is based on current `origin/main`;
- Task 256 is closed on main as blocked diagnostic evidence;
- no runtime operation is needed to reproduce the three gaps;
- the fix can be expressed with injected mocks/fixtures.

If any gap requires a real Mineru2Table call, DB read/write, MinIO read/write,
Docker operation, env/credential mutation, or sample mutation, stop and write a
blocked report.

## 5. Deferrable Side Work

Do not include:

- new runtime validation;
- real DB metadata apply;
- upload-server route wiring;
- UI/operator button work;
- scheduler/worker activation;
- callback/webhook receiver;
- batch strategy;
- cost desk UI;
- cleanup/reset/rollback/nullify of existing metadata;
- cleanup/delete/overwrite of Task 242 `v1`, Task 245 `v2`, or Task 256 `v3`;
- RawMaterial2CleanMaterial.

## 6. Environment And Write Boundary

Work in the Lucode workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Allowed product files:

```text
server/services/cleanservice/protocol.mjs
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/metadata-persistence.mjs
server/services/cleanservice/metadata-apply-executor.mjs
server/services/cleanservice/orchestration-runner.mjs
server/services/cleanservice/states.mjs
```

Allowed test/report files:

```text
server/tests/cleanservice-orchestration-runner-smoke.mjs
server/tests/cleanservice-output-verifier-smoke.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
server/tests/cleanservice-metadata-persistence-smoke.mjs
TaskAndReport/2026-05-24T11-28-01+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Forbidden files and operations:

```text
server/upload-server.mjs
server/db-server.mjs
src/**
docs/**
docker-compose.yml
.env
.env.*
package.json
pnpm-lock.yaml
AGENTS.md
.agents/**
TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
TaskAndReport/2026-05-24T11-21-26+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_LUCEON_REVIEW-v3.md
/Users/concm/prod_workspace/Mineru2Tables/**
```

Do not modify the Task 256 runtime harness except to read it for diagnostic
context. It is evidence, not the product fix surface.

## 7. Safety Boundary

This task is strictly mock-safe / no-runtime.

Forbidden:

- `POST /api/v1/jobs`;
- `POST /api/v1/jobs:from-storage`;
- live `GET /api/v1/jobs/{job_id}` against Mineru2Table;
- DB GET/PATCH/POST/PUT/DELETE;
- MinIO stat/list/get/put/copy/move/delete;
- direct `jobs.json` read/write;
- Docker/Compose restart/recreate/build/down/up;
- `.env`, credential, model, sample-file, or secret mutation;
- cleanup/reset/rollback/repair/reparse/re-AI;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live declaration.

All tests must use in-memory records, injected clients, fake artifact readers,
and mock job responses.

## 8. Fast Validation Target

Minimum proof:

1. A mock completed job with seven artifact ObjectRefs and no top-level
   `job.provenance` reaches artifact verification and candidate/plan building.
2. Exact provenance jobId passes.
3. `expectedJobId + "-probe"` passes only under explicit bounded policy and
   records both IDs plus a warning.
4. unrelated provenance jobId fails.
5. Explicit new-version `v2 -> v3` dry-run apply returns `DRY_RUN_SUCCESS`
   without any DB client calls.
6. Non-explicit or incompatible metadata still returns
   `BLOCKED_EXISTING_TOC_REBUILD_METADATA` or a stricter blocker.
7. No source text/full artifacts appear in metadata summaries.

## 9. Required Checks

Run and record exact commands and exit codes:

```bash
node --check server/services/cleanservice/protocol.mjs
node --check server/services/cleanservice/output-verifier.mjs
node --check server/services/cleanservice/metadata-summary.mjs
node --check server/services/cleanservice/metadata-persistence.mjs
node --check server/services/cleanservice/metadata-apply-executor.mjs
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node --check server/tests/cleanservice-output-verifier-smoke.mjs
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --name-status origin/main...HEAD
git diff --check origin/main...HEAD
```

If `tsc` cannot run because dependencies are missing in the Lucode workspace,
report the exact reason and still run the focused Node checks.

## 10. Report Requirements

Create:

```text
TaskAndReport/2026-05-24T11-28-01+0800_P0-CleanService-MockSafe-Runner-Integration-Gap-Fix-NoRuntime_REPORT.md
```

The report must include:

- exact remote branch and full HEAD;
- changed-file list using three-dot diff;
- summary of each gap and its implemented product behavior;
- focused test cases added or changed;
- exact command outputs/exit codes;
- explicit no-runtime/no-DB/no-MinIO/no-Docker/no-env statement;
- residual risks and whether a later controlled runtime validation is
  recommended.

Update the branch-local Task 259 ledger row to:

```text
Status=Lucode 已回报待 Luceon 审查
Next Actor=Luceon
```

## 11. Stop Rules

Stop and report blocked if:

- the fix requires runtime evidence instead of mocks;
- accepting `-probe` cannot be made traceable without mutating provenance;
- dry-run apply semantics require real DB write policy decisions;
- changes would touch forbidden files;
- checks show unrelated CleanService behavior regression;
- the task expands into worker activation, runtime wiring, or real DB apply.

Recommended blocker classifications:

```text
BLOCKED_PROVENANCE_RESPONSE_SHAPE_UNRESOLVED
BLOCKED_PROVENANCE_JOB_ID_POLICY_UNSAFE
BLOCKED_DRY_RUN_CONFLICT_POLICY_REQUIRES_REAL_APPLY_DECISION
BLOCKED_SCOPE_WOULD_EXPAND
```

## 12. Review Boundary

Acceptance may mean:

- mock-safe code/test evidence shows the product chain can process the Task
  256-shaped live response without harness mutation;
- job ID policy is explicit and auditable;
- explicit new-version dry-run conflict semantics no longer require harness
  conversion.

Acceptance does not mean:

- a new runtime validation is accepted;
- the Task 256 `v3` output is newly verified;
- a second `POST /api/v1/jobs` is authorized;
- real DB apply is accepted;
- worker/scheduler/upload-server/operator integration is accepted;
- UAT, L3, pressure PASS, production readiness, release readiness, production
  online, or go-live.
