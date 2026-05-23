# TASK-20260523-084713-P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite

## 1. Mainline Objective

Task 255 proved the mock-safe policy layer for explicit new-version intent:

```text
default completed v2 => CURRENT_CLEAN_MATERIAL_NOOP
explicit create-new-version + reason + aligned completed v2 history => allowed to plan v3
failed/mismatched/one-sided/missing-jobId history => blocked before submit
```

Task 256 must answer the next mainline question:

> Can Luceon's CleanService runner perform one controlled explicit
> new-version runtime dispatch for the existing single sample, verify the new
> `v3` output, and build a dry-run metadata persistence plan without writing
> Luceon DB metadata?

This task validates the real runtime path only up to dry-run DB apply.

It intentionally does not authorize a real Luceon DB metadata write.

## 2. Current Evidence

Accepted current main:

```text
main@b4b300e1a08a895896c2674a8cda3afff1160386
Task 255: ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION
```

Known single-sample identity:

```text
taskId=task-1779085089451
materialId=1842780526581841
serviceName=toc-rebuild
existing clean assetVersion=v2
expected new assetVersion=v3
```

Known canonical Raw Material:

```text
bucket=eduassets-raw
object=mineru/1842780526581841/v1/content_list_v2.json
size=31543
sha256=f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db
```

Known successful standalone Mineru2Table output from Task 245:

```text
bucket=eduassets-clean
prefix=toc-rebuild/1842780526581841/v2/
seven artifacts exist
metrics.tokens.total=6266
```

Known locked failed output from Task 242:

```text
bucket=eduassets-clean
prefix=toc-rebuild/1842780526581841/v1/
status=failed-run evidence, do not reuse or clean
```

Director authorization for Task 256:

```text
同意下达256
```

## 3. Critical Path Scope

Run one controlled single-sample CleanService explicit new-version runtime
dry-run:

1. Read the current task/material metadata and prove the existing `v2`
   completed/aligned state.
2. Prove the target `v3` MinIO output prefix is empty before dispatch.
3. Execute exactly one runtime `POST /api/v1/jobs` through the CleanService
   runner path with:

   ```js
   {
     intent: 'create-new-version',
     newVersionReason: 'director-authorized-single-sample-runtime-dry-run'
   }
   ```

4. Poll only the submitted job until terminal status or timeout.
5. Verify the new `v3` seven-artifact output through the accepted verifier.
6. Build the ingestion candidate and metadata persistence plan.
7. Call apply executor only in dry-run mode, with `allowRealApply=false`.
8. Confirm Luceon DB task/material metadata did not change.

Recommended success classification:

```text
RUNTIME_DRY_RUN_SUCCESS_NO_DB_APPLY
```

If the current runner returns `DRY_RUN_SUCCESS`, the report may use that code
as the actual runner result but must classify the task result as dry-run only,
not DB-applied.

## 4. True Preconditions

Lucode must verify these before any POST:

1. Current DB read-only state:

   ```text
   task.metadata.cleanServiceJobs['toc-rebuild'].assetVersion=v2
   task.metadata.cleanServiceJobs['toc-rebuild'].status or cleanState=completed
   task.metadata.cleanServiceJobs['toc-rebuild'].jobId exists
   material.metadata.cleanMaterials['toc-rebuild'].latestVersion=v2
   material.metadata.cleanMaterials['toc-rebuild'].status=completed
   ```

2. Canonical Raw Material exists and matches the known object/sha above.
3. Target output prefix is empty:

   ```text
   eduassets-clean/toc-rebuild/1842780526581841/v3/
   ```

4. Mineru2Table health is reachable and dependency checks are acceptable for a
   real single-sample job.
5. `CLEANSERVICE_ENABLED` must remain disabled unless already configured
   otherwise; this task must not enable scheduler/worker automation.

If any precondition fails, stop before POST and report a blocked
classification.

## 5. Deferrable Side Work

Do not include these in Task 256:

- real Luceon DB metadata apply;
- route/UI/operator button work;
- upload-server route wiring;
- scheduler/worker activation;
- callback/webhook receiver;
- batch strategy;
- cost desk UI;
- cleanup/reset/rollback/nullify of any existing task/material metadata;
- cleanup/delete/overwrite of Task 242 `v1` failed-run prefix;
- cleanup/delete/overwrite of Task 245 `v2` success prefix;
- RawMaterial2CleanMaterial.

Those remain separate tasks.

## 6. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed files:

```text
server/tests/cleanservice-task256-explicit-new-version-runtime-dryrun.mjs
TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

The runtime script may be omitted if Lucode can perform the run with an
existing accepted script or a temporary untracked script. If a temporary script
is used, the report must include the exact command, target task/material, and
bounded behavior proof.

Read-only source files:

```text
server/services/cleanservice/**
server/tests/cleanservice-*.mjs
```

Forbidden source/config files:

```text
server/upload-server.mjs
server/db-server.mjs
server/services/tasks/**
src/**
docs/**
docker-compose.yml
.env
.env.*
package.json
pnpm-lock.yaml
AGENTS.md
.agents/**
/Users/concm/prod_workspace/Mineru2Tables/**
```

Do not modify product source code in Task 256. If a product code defect blocks
the run, stop and report the defect instead of fixing it inside this task.

## 7. Authorized Runtime Boundary

This task authorizes a narrow runtime action set.

### 7.1 Authorized

Exactly one runtime dispatch:

```text
POST /api/v1/jobs
```

Only for:

```text
taskId=task-1779085089451
materialId=1842780526581841
serviceName=toc-rebuild
assetVersion=v3
```

Authorized side effects:

- Mineru2Table job store may gain exactly one new job record for Task 256.
- Mineru2Table may call LLM as needed for exactly this one job.
- Mineru2Table may write exactly the `v3` seven-artifact output under:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v3/
  ```

Authorized read-only operations:

- DB GET/read-only checks for the target task/material before and after run;
- MinIO stat/list/get only for the target raw object and `v3` output prefix;
- Mineru2Table `GET /health`, `GET /openapi.json`, and job polling for the
  submitted job only;
- local read-only hashing of `jobs.json`.

### 7.2 Forbidden

Strictly forbidden:

- more than one `POST /api/v1/jobs`;
- `POST /api/v1/jobs:from-storage`;
- manual MinIO put/copy/move/delete/cleanup/bucket mutation;
- any MinIO write outside `eduassets-clean/toc-rebuild/1842780526581841/v3/`;
- Luceon DB PATCH/POST/PUT/DELETE;
- direct DB file edit;
- direct `jobs.json` edit;
- Docker/Compose restart/recreate/build/down/up;
- `.env` or credential mutation;
- source code change except the optional runtime harness script;
- cleanup, reset, rollback, nullify, repair, reparse, or data rewrite;
- worker/scheduler activation;
- second retry POST if the job fails;
- UAT, L3, pressure PASS, production readiness, release readiness, or go-live
  declaration.

## 8. Required Runtime Behavior

The runtime path must use the accepted intent semantics:

```js
intent: 'create-new-version'
newVersionReason: 'director-authorized-single-sample-runtime-dry-run'
```

Expected behavior:

1. Existing v2 completed/aligned metadata passes the Task 255 precondition.
2. AssetVersion allocation produces `v3`.
3. Job request uses:

   ```text
   material_id=1842780526581841
   parse_task_id=task-1779085089451
   asset_version=v3
   input source=eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
   sink prefix=eduassets-clean/toc-rebuild/1842780526581841/v3/
   ```

4. Job completes or fails honestly.
5. If completed, verifier must require all seven artifacts:

   ```text
   flooded_content.json
   logic_tree.json
   readable_tree.md
   skeleton.json
   unresolved_anchors.json
   metrics.json
   provenance.json
   ```

6. `metrics.json` must report non-zero total tokens.
7. `provenance.json` must reference the canonical Raw Material ObjectRef and
   SHA.
8. Metadata candidate and persistence plan must be built.
9. Apply executor must stay dry-run:

   ```text
   allowRealApply=false
   ```

10. Post-run DB read-only check must prove no task/material metadata mutation.

## 9. Data Governance Red Lines

Because this is a Clean Material runtime validation:

1. ID-only/source-reference-only: do not persist or report full source text,
   full Markdown, full artifact JSON bodies, or model-generated source truth.
   The report may include bounded sizes, hashes, object refs, counts, states,
   token totals, and short status strings.
2. Asset hash locking: do not rename, rewrite, normalize, or overwrite any
   existing object path/hash. Task 242 `v1` and Task 245 `v2` are immutable.
3. Pure structural boundary: do not introduce LaTeX/TikZ/custom command logic.

## 10. Fast Validation Target

Minimum success evidence:

1. Exactly one POST was sent.
2. New jobId is recorded.
3. Job reaches `completed`.
4. `eduassets-clean/toc-rebuild/1842780526581841/v3/` contains exactly the
   required seven artifacts.
5. Each artifact has size and SHA256 recorded.
6. Verifier returns ok with non-zero token total.
7. Candidate and persistence plan are built.
8. Apply executor dry-run returns success without DB PATCH.
9. Post-run DB task/material metadata exactly matches the pre-run bounded
   metadata snapshot for `toc-rebuild`.
10. `v1` and `v2` prefixes remain untouched.

If the job fails honestly, the task can still be accepted as failed evidence if
it preserves all boundaries and reports the precise failure classification.

## 11. Required Checks

Run and record exact commands and exit codes:

```bash
node --check server/services/cleanservice/orchestration-runner.mjs
node --check server/tests/cleanservice-orchestration-runner-smoke.mjs
node server/tests/cleanservice-orchestration-runner-smoke.mjs
for f in server/tests/cleanservice-*.mjs; do node "$f" || exit 1; done
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

For runtime evidence, also record the exact command used to run the Task 256
harness, plus:

- pre/post job-store size, SHA256, and key count;
- pre/post DB bounded metadata snapshot hashes for target task/material;
- pre/post `v3` prefix object list;
- submitted jobId and final job status;
- seven artifact object refs, sizes, and SHA256 values;
- token totals and estimated cost if present.

Do not print secrets, key prefixes/suffixes, token values, balance values, or
raw LLM response bodies.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-23T08-47-13+0800_P0-CleanService-Explicit-New-Version-Single-Sample-Runtime-DryRun-NoDBWrite_REPORT.md
```

The report must include:

- final branch and exact GitHub-visible HEAD;
- changed file list;
- preflight evidence;
- exactly-one-POST proof;
- jobId and final status;
- v3 artifact list with bounded metadata only;
- verifier/candidate/plan/apply-dry-run result;
- DB no-write proof;
- `v1`/`v2` no-touch proof;
- required check outputs and exit codes;
- explicit statement that no real DB write, cleanup, Docker/env change, worker
  activation, or readiness/UAT claim occurred.

## 13. Stop Rules

Stop before POST if:

- current task/material metadata is not completed/aligned v2;
- target `v3` prefix already contains any object;
- Mineru2Table health is not acceptable for one controlled job;
- canonical raw object is missing or hash mismatched;
- endpoint/schema no longer matches Protocol v1 job submission;
- credentials are missing or obviously invalid;
- any step would require source code change outside the optional harness script;
- any step would require DB write before the dry-run plan.

Stop after one POST without retry if:

- job fails;
- verifier rejects output;
- token total is zero/missing;
- provenance source ObjectRef/SHA does not match canonical Raw Material;
- generated output lands outside the `v3` prefix;
- dry-run apply indicates it would write outside allowed metadata branches.

Recommended blocked/failure classifications:

```text
BLOCKED_CURRENT_METADATA_NOT_ALIGNED
BLOCKED_TARGET_V3_PREFIX_ALREADY_EXISTS
BLOCKED_RUNTIME_DEPENDENCY_UNHEALTHY
BLOCKED_RAW_MATERIAL_MISMATCH
RUNTIME_JOB_FAILED
BLOCKED_OUTPUT_VERIFICATION_FAILED
BLOCKED_DRY_RUN_PLAN_INVALID
RUNTIME_DRY_RUN_SUCCESS_NO_DB_APPLY
```

## 14. Acceptance Boundary

Acceptance of Task 256 may mean:

- one controlled new-version runtime dry-run was performed;
- `v3` output was generated and verified, or failed evidence was honestly
  captured;
- metadata candidate/plan/dry-run apply was proven without DB mutation.

Acceptance does not mean:

- DB metadata apply is accepted;
- worker/scheduler automation is activated;
- upload-server/operator route/UI is accepted;
- batch/callback/cost desk behavior is accepted;
- RawMaterial2CleanMaterial is started;
- Task 242 `v1` or Task 245 `v2` can be cleaned/reused;
- UAT, L3, pressure PASS, production readiness, release readiness, or go-live.
