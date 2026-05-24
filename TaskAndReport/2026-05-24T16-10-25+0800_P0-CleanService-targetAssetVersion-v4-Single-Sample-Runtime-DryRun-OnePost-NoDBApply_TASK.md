# TASK-20260524-161025-P0-CleanService-targetAssetVersion-v4-Single-Sample-Runtime-DryRun-OnePost-NoDBApply

Issued at: 2026-05-24T16:10:25+0800

Actor: Luceon

## Mainline Objective

Generate the first clean `v4` runtime evidence for the CleanService
`toc-rebuild` path, using the Task 265 accepted `targetAssetVersion: "v4"`
product path.

This task is intended to move the mainline from mock-safe readiness into
controlled real runtime evidence:

```text
accepted DB v2 history + explicit targetAssetVersion v4
=> exactly one runtime CleanService POST
=> v4 job/artifacts evidence
=> dry-run metadata plan only
=> no DB apply
```

## Critical Path Scope

Execute a single-sample runtime dry-run against the existing canonical sample:

```text
parseTaskId/task id = task-1779085089451
materialId = 1842780526581841
serviceName = toc-rebuild
previous accepted assetVersion = v2
previous accepted jobId = luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
targetAssetVersion = v4
expected request jobId = luceon-task-1779085089451-toc-rebuild-v4
expected output prefix = eduassets-clean/toc-rebuild/1842780526581841/v4/
raw input = eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
raw input sha256 = f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
raw input size = 31543
```

This is not a broad runtime rollout. It is one controlled evidence-producing
operation.

## True Preconditions

Before the POST, Luceon must verify all gates below. If any gate fails, stop and
write the report as blocked without making the POST.

Required preflight gates:

1. GitHub `main` is synchronized and clean.
2. Task 265 code is present on `main`.
3. Target task/material are readable.
4. Existing task clean job and material clean material are completed, aligned,
   and still represent accepted `toc-rebuild v2`.
5. Previous task job id is present and matches:
   `luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230`.
6. Raw input object exists and matches the expected SHA256 and size above.
7. Target `v4` job id is not already present in the runtime job store.
8. Target `v4` prefix is absent or empty before the POST.
9. Current product planner can generate the expected `v4` request without
   modifying DB state.
10. The runtime endpoint and health/status checks are reachable without Docker
    or Compose mutation.

## Authorized Operations

The Director explicitly approved this task direction in-thread on 2026-05-24.

Only the following live/runtime operations are authorized:

1. Read-only DB/API reads for the exact target task/material and post-run
   verification.
2. Read-only MinIO list/get/head operations for:
   - the exact raw input object;
   - target material `toc-rebuild` prefixes `v2`, `v3`, and `v4`.
3. Read-only Mineru2Table job-store/status inspection before and after the run.
4. Runtime health/status GET requests needed to confirm endpoint reachability.
5. Exactly one CleanService protocol runtime POST for the target sample and
   target `v4` request.
6. Runtime query/status polling for that one posted job until terminal state or
   a bounded timeout.
7. Service-side writes that are a direct consequence of the exactly-one POST:
   - one job-store record for the target job id or the service's exact returned
     job id if it differs;
   - `v4` artifacts under the exact target prefix.
8. Local focused tests and syntax/type checks if needed to confirm the current
   product path before or after the run.
9. TaskAndReport report/ledger writes for this task.

No other live operation is authorized.

## Forbidden Operations

This task forbids:

- a second runtime POST, retry POST, submit-probe, or alternate endpoint POST;
- fresh sample selection;
- DB PATCH/POST/PUT/DELETE or metadata apply;
- manual MinIO put/copy/move/delete/write/delete-marker/cleanup;
- manual job-store edit/delete/cleanup/reset;
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation;
- env, credential, model, secret, source sample, or local override mutation;
- worker, scheduler, or upload-server CleanService activation;
- retry/reparse/re-AI/repair/rollback after a failed or partial run;
- source-code changes;
- UAT, L3, pressure PASS, production readiness, release readiness,
  production online, or go-live claims.

## Execution Rules

Use current `main`; no implementation branch is expected for this Luceon
runtime-validation task.

The run must use current product semantics:

```js
{
  intent: "create-new-version",
  newVersionReason: "director-authorized-v4-runtime-dryrun-no-db-apply",
  targetAssetVersion: "v4",
  reconcileExistingJob: false,
  allowProbeJobIdSuffix: false
}
```

`allowProbeJobIdSuffix` must remain false for the new `v4` path. A `-probe`
provenance job id in new `v4` evidence is a product/runtime blocker, not an
accepted success.

Exactly one POST means:

- count the submission call, not only successful jobs;
- if the POST times out, returns an error, or returns a failed job, do not retry;
- if the job remains in progress after bounded observation, stop and report the
  in-progress evidence without a second POST;
- if a partial artifact set is created, do not clean it up.

## Fast Validation Target

The smallest useful positive result is:

```text
preflight gates pass
exactly one runtime POST sent for target v4
runtime job reaches completed
seven v4 artifacts exist under the target prefix
verifier accepts canonical provenance without -probe
metadata persistence apply remains dry-run only
DB accepted state remains unchanged after the run
```

## Positive Acceptance Criteria

This task can be accepted as successful runtime dry-run evidence if:

- all preflight gates pass;
- exactly one runtime POST is made;
- the request records `asset_version=v4`;
- the request job id and sink prefix match the expected v4 target;
- runtime status reaches a terminal successful/completed state;
- the target v4 prefix contains the required seven artifacts;
- artifact hashes, sizes, and parseability are recorded;
- provenance records the canonical job id, asset version `v4`, target material,
  parse task id, source input object, and source input hash;
- the verifier accepts the v4 artifact set with `allowProbeJobIdSuffix=false`;
- persistence planning and apply executor run in dry-run mode only;
- DB operation count is zero;
- post-run DB read confirms no accepted metadata was applied;
- the report records exact commands, exit codes, endpoint, job id, POST count,
  artifact evidence, and residual risks.

## Blocked / Failed Evidence Criteria

If the runtime POST is made but the job fails, times out, stays in progress, or
produces invalid artifacts, do not retry. Record the exact state as blocked or
failed evidence.

Examples:

- protocol/client transport failure after the one POST;
- Mineru2Table terminal failed state;
- LLM/provider/auth/cost failure;
- non-canonical `-probe` provenance in new v4 artifacts;
- missing artifact, invalid JSON/Markdown, zero-token false-success shape, or
  sourceInput/provenance mismatch;
- dry-run apply conflict;
- post-run DB drift.

## Required Checks

Minimum expected commands/evidence:

```text
git status --short --branch
git fetch origin --prune --tags
git pull --ff-only origin main
git rev-parse HEAD origin/main
git diff --check
node --check server/services/cleanservice/asset-version.mjs
node --check server/services/cleanservice/cleanservice-worker.mjs
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/services/cleanservice/metadata-apply-executor.mjs
node server/tests/cleanservice-asset-version-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Runtime evidence must include:

- preflight task/material facts;
- preflight raw object facts;
- preflight target v4 prefix/job-store absence;
- exact POST count;
- request shape or bounded redacted request summary;
- status observation timeline;
- post-run job-store facts;
- post-run v4 artifact inventory and hashes;
- dry-run apply result;
- post-run DB unchanged evidence.

If any check is skipped, the report must explain why.

## Report Requirements

Write:

```text
TaskAndReport/2026-05-24T16-10-25+0800_P0-CleanService-targetAssetVersion-v4-Single-Sample-Runtime-DryRun-OnePost-NoDBApply_REPORT.md
```

The report must include:

- task id and task brief path;
- execution main SHA;
- exact runtime endpoint and target ids;
- preflight gate table;
- one-POST evidence and POST count;
- status timeline;
- artifact inventory and hashes;
- verifier result;
- dry-run persistence/apply result;
- post-run DB unchanged evidence;
- skipped checks and reasons;
- classification: success, blocked, failed, or in-progress;
- risks and next recommendation.

## Stop Rule

Stop immediately and write the report if:

- a preflight gate fails;
- executing the task would require a second POST;
- executing the task would require DB apply, manual MinIO write/delete,
  job-store edit, Docker/Compose mutation, secret/env/model/source mutation, or
  cleanup;
- the task would need to widen beyond the exact target sample.

## Review Boundary

Acceptance can only mean:

```text
Single-sample targetAssetVersion v4 runtime dry-run evidence was produced and
reviewed under the one-POST, no-DB-apply boundary.
```

It must not mean DB metadata apply is authorized, worker/scheduler activation is
authorized, broad CleanService rollout is authorized, product structural quality
is final, or the system is ready for UAT/L3/pressure/readiness/go-live.
