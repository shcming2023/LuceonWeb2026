# Lucode Task Brief: P0 Release Candidate Two-Pass Validation Pass 2

- Task ID: `TASK-20260509-090138-P0-Release-Candidate-Two-Pass-Validation-Pass-2`
- Issued at: 2026-05-09T09:01:38+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `9063a14`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Read-only sample inventory: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

## Objective

Run production-candidate validation pass 2 after the accepted dependency-health Ollama smoke alignment revision.

This is validation pass 2 of 2 under the Director timebox. Revision cycle 1 of 2 has been used by Task 53. If pass 2 still exposes a blocker, report the exact blocker and a go/no-go recommendation; do not begin another repair without a new Lucia or Director decision.

This task may establish `PRODUCTION_RELEASE_CANDIDATE_READY_FOR_LUCIA_REVIEW`; it must not declare production release readiness.

## Authorized Scope

You may:

1. Fast-forward/sync the production workspace to the accepted `main` commit as needed.
2. Preserve production-local override boundaries:
   - strict AI/model settings unchanged
   - MinIO console remains local-only: `127.0.0.1:19001:9001`
3. Use minimum necessary non-destructive Docker/Compose action to apply the accepted upload-server code if required.
4. Run read-only runtime checks and controlled production validation uploads only if preflight gates pass.
5. Use the external sample directory only as read-only input inventory; do not copy samples into the repository.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness
- delete DB rows, MinIO objects, Docker volumes, logs, tasks, artifacts, or samples
- mutate secrets, model selection, timeout config, production override settings, or local sample files
- run broad deploy/rebuild/restart/rollback outside the minimum needed to apply current main
- create more than two controlled validation uploads in this pass
- run simultaneous heavy MinerU parse jobs or simultaneous heavy Ollama metadata jobs
- use skeleton fallback or silent degradation
- treat a warm-only recovery as launch-ready if the cold readiness gate fails without clearly classifying that residual for Lucia review

Stop and report immediately if any hard-stop boundary would be required.

## Required Pass 2 Gates

### 1. Production Sync And Boundary Gate

Record:

- development `main` HEAD
- production HEAD before and after sync
- production `git status --short --branch`
- changed files or local overrides in production
- exact override evidence for strict AI/model and MinIO local-only binding

If production contains unexpected dirty code changes beyond allowed local override, stop and report.

### 2. Revised Dependency Gate

Run and record:

- CMS reachability
- DB health
- MinIO reachability
- MinerU health plus submit probe
- Ollama `qwen3.5:9b` readiness
- `/ops/dependency-health?mineruSubmitProbe=true`

Run one cold dependency-health check first after the revised code is active. If the only failure is Ollama cold-load timeout, you may run exactly one bounded non-mutating Ollama warm-up and rerun warm dependency-health. Record both results. A warm-only pass remains a launch-readiness residual unless the report explicitly classifies it for Lucia review.

### 3. Diagnostic Classification Gate

Validate in production:

- `/ops/mineru/active-task`
- `/ops/mineru/diagnostics`

Expected result:

- known historical terminal AI failures remain in `historicalAiFailureTasks`, not `takeoverRequiredTasks`
- actionable completed-but-not-ingested or running-completed MinerU cases remain visible in `takeoverRequiredTasks`

Record exact IDs observed.

### 4. Stage-Queued Validation Gate

If gates 1-3 pass and active heavy-stage work is idle, run up to two controlled validation uploads under the accepted stage-queued rule:

- next upload may start only after prior upload/storage intake is durable
- active MinerU parse-running count must stay `<=1`
- active Ollama metadata-running count must stay `<=1`
- record task ID, material ID, objectName, sample path, size, hash, stage transitions, MinerU result, AI job result, and final operator-facing state

Use true samples from the external sample inventory when practical. Do not modify, move, rename, normalize, or sync sample files.

### 5. Release Candidate Evidence Matrix

Return a matrix with these rows:

- production code/version sync
- override/security boundary
- CMS/API reachability
- DB health
- MinIO health
- MinerU health and submit path
- Ollama cold readiness
- Ollama warm readiness, if used
- upload and MinIO intake
- MinerU parse
- AI metadata
- manual review state
- stage-queued heavy-stage behavior
- diagnostics classification
- rollback/recovery readiness
- remaining release blockers

Each row must be one of `PASS`, `BLOCKER`, `RESIDUAL_ACCEPTABLE_WITH_BOUNDARY`, or `NOT_TESTED`, with exact evidence.

## Required Checks

At minimum:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Production/runtime checks must include the endpoint evidence described above.

## Required Report

Create:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Release-Candidate-Two-Pass-Validation-Pass-2_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 54 with:

- status
- report path
- branch / HEAD
- validation pass count used
- revision cycle count used
- next actor
- exact next action

If pass 2 is clean, set Next Actor to Lucia with `PRODUCTION_RELEASE_CANDIDATE_READY_FOR_LUCIA_REVIEW`.

If blockers remain, set Next Actor to Lucia with `BLOCKED_AFTER_PASS_2` and include a go/no-go recommendation. Do not start another repair without a new Lucia or Director decision.
