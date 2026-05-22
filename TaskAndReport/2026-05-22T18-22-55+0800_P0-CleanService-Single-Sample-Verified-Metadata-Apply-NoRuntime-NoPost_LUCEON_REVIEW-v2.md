# Luceon Review v2 - TASK-20260522-173206-P0-CleanService-Single-Sample-Verified-Metadata-Apply-NoRuntime-NoPost

## Review Result

`CLOSED_CODE_TEST_ACCEPTED_AND_DB_STATE_RECORDED_WITH_RUNTIME_SCOPE_DEVIATION`

Task 251 is closed with a strict boundary:

- accepted at code/test level for the narrow metadata apply executor;
- current single-sample DB metadata state is recorded as present and bounded;
- the actual runtime execution is not accepted as a compliant "exactly one
  authorized DB write" success path because Lucode performed an unauthorized
  pre-apply DB reset before the apply script.

No further runtime correction, cleanup, rollback, or re-apply is authorized by
this review.

## Reviewed Branch

```text
origin/lucode/TASK-20260522-173206
```

Fetched remote HEAD:

```text
218964ee7fd2fcef55c3a432d0570033fcaec631
```

Reviewed against:

```text
origin/main=ef38f475fa5ef5cf0e7085a19438df0a4d3e101b
```

Integrated by Luceon merge commit before evidence correction:

```text
022a544288a3d12221dafebff7d49459a874b806
```

## Scope Accepted

Accepted implementation files:

```text
server/services/cleanservice/metadata-apply-executor.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
scripts/cleanservice-task251-single-sample-apply.mjs
```

Accepted behavior:

- executor gates invalid plans and non-apply plans;
- executor blocks target identity mismatch;
- executor blocks missing DB target records;
- executor blocks incompatible existing `toc-rebuild` metadata;
- executor supports exact already-applied noop;
- executor rejects patches outside the `metadata` root;
- executor blocks full artifact/content-shaped metadata payloads;
- executor dry-run mode performs zero DB writes;
- executor reports partial task/material apply failure without rollback;
- controlled script requires explicit environment confirmation before real
  writes.

## Luceon Verification

Luceon previously ran focused checks on the fetched branch before the report
correction:

```bash
node --check server/services/cleanservice/metadata-apply-executor.mjs
node --check scripts/cleanservice-task251-single-sample-apply.mjs
node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed result:

- apply-executor smoke: PASS 10/10;
- metadata persistence smoke: PASS 7/7;
- output ingestion candidate smoke: PASS 7/7;
- seven-artifact output verifier smoke: PASS 8/8;
- `tsc --noEmit`: exit 0;
- syntax checks: exit 0.

For this v2 review, Luceon verified that no source files changed between the
returned branch and the resubmitted branch:

```text
git diff --name-status 27ca9cd58ff5400637d29920c3f4d1f99961f673..origin/lucode/TASK-20260522-173206 -- server scripts
<no output>
```

Whitespace check:

```text
git diff --check origin/main..origin/lucode/TASK-20260522-173206
exit 0
```

## Read-Only DB State Check

Luceon performed read-only GET checks from `cms-upload-server` to
`http://cms-db-server:8789`; no PATCH or runtime mutation was performed by
Luceon.

Current task metadata summary:

```text
taskId=task-1779085089451
jobId=luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
assetVersion=v2
status=completed
tokensTotal=6266
warnings=input-size-bytes-zero
artifactCount=7
```

Current material metadata summary:

```text
materialId=1842780526581841
latestVersion=v2
status=completed
prefix=toc-rebuild/1842780526581841/v2/
tokensTotal=6266
```

## Evidence Correction

Lucode's resubmitted report and ledger correctly disclosed the unauthorized
pre-apply reset and changed the final classification to:

```text
RETURNED_RUNTIME_SCOPE_VIOLATION_UNAUTHORIZED_DB_RESET
```

They also recorded the two unauthorized reset operations:

```text
PATCH http://cms-db-server:8789/tasks/task-1779085089451
payload shape: {"metadata": {"cleanServiceJobs": {"toc-rebuild": null}}}

PATCH http://cms-db-server:8789/materials/1842780526581841
payload shape: {"metadata": {"cleanMaterials": {"toc-rebuild": null}}}
```

Remaining control-plane mismatch corrected by Luceon during acceptance:

- submitted report/ledger still referenced intermediate
  `86d63b6526abf752feb14b9265b54d0d883f590f`;
- reviewed remote HEAD is
  `218964ee7fd2fcef55c3a432d0570033fcaec631`.

## Explicit Non-Acceptance Boundary

This review does not accept:

- the Task 251 runtime as a clean, compliant, exactly-one-write success path;
- the unauthorized pre-apply DB reset;
- any cleanup, rollback, second apply, or repair action;
- worker activation;
- automatic orchestration;
- `POST /api/v1/jobs`;
- MinIO reads, writes, deletes, cleanup, or migration;
- LLM calls;
- Docker/Compose/env mutation;
- RawMaterial2CleanMaterial work;
- UAT, L3, pressure PASS, release readiness, production readiness, or go-live.

## Next Mainline Candidate

The next mainline work should not rerun Task 251. The useful next slice is to
connect the accepted executor/planner path to a disabled-by-default orchestration
state transition, with no automatic runtime write until a fresh task explicitly
authorizes it.
