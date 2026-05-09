# Lucode Task Brief: P0 Release Candidate Two-Pass Validation Pass 1

- Task ID: `TASK-20260509-082854-P0-Release-Candidate-Two-Pass-Validation-Pass-1`
- Issued at: 2026-05-09T08:28:54+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `f0b9381`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Read-only sample inventory: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

## Objective

Run production-candidate validation pass 1 under Director's accelerated timebox:

- Maximum total validation passes for this push: 2.
- Maximum total revision cycles after this point: 2.
- If pass 1 finds blockers, report exact blocker evidence and propose the smallest revision candidate.
- If pass 1 is clean, report whether a final pass 2 is sufficient for Lucia to consider production release readiness.

This task may establish `PRODUCTION_RELEASE_CANDIDATE_READY_FOR_LUCIA_REVIEW`; it must not itself declare production release readiness.

## Authorized Scope

You may:

1. Fast-forward/sync the production workspace to the accepted `main` commit as needed.
2. Preserve production-local override boundaries:
   - strict AI/model settings unchanged
   - MinIO console remains local-only: `127.0.0.1:19001:9001`
3. Use minimum necessary non-destructive Docker/Compose action to apply the latest upload-server code if required.
4. Run read-only runtime checks and at most two controlled production validation uploads only if preflight gates pass.
5. Use the external sample directory only as read-only input inventory; do not copy samples into the repository.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness
- delete DB rows, MinIO objects, Docker volumes, logs, tasks, artifacts, or samples
- mutate secrets, model selection, timeout config, production override settings, or local sample files
- run broad deploy/rebuild/restart/rollback outside the minimum needed to apply current main
- create more than two controlled validation uploads
- run simultaneous heavy MinerU parse jobs or simultaneous heavy Ollama metadata jobs
- use skeleton fallback or silent degradation
- treat warm-up-gated health as release-ready if cold dependency health remains a blocking risk without a documented Lucia/Director acceptance boundary

Stop and report immediately if any hard-stop boundary would be required.

## Required Pass 1 Gates

### 1. Production Sync And Boundary Gate

Record:

- dev `main` HEAD
- production HEAD before and after sync
- production `git status --short --branch`
- changed files or local overrides in production
- exact override evidence for strict AI/model and MinIO local-only binding

If production contains unexpected dirty code changes beyond allowed local override, stop and report.

### 2. Dependency Gate

Run and record:

- CMS reachability
- DB health
- MinIO reachability
- MinerU health plus submit probe
- Ollama `qwen3.5:9b` readiness
- `/ops/dependency-health?mineruSubmitProbe=true`

Run one cold dependency-health check first. If the only failure is Ollama cold-load timeout, you may run exactly one bounded non-mutating Ollama warm-up and rerun warm dependency-health. Record both results. A cold failure remains a launch-readiness risk unless the report explicitly proposes a release runbook boundary for Lucia review.

### 3. Task 50 Diagnostic Classification Gate

Validate in production:

- `/ops/mineru/active-task`
- `/ops/mineru/diagnostics`

Expected result:

- known historical terminal AI failures are surfaced in `historicalAiFailureTasks`, not `takeoverRequiredTasks`, when still present in production data
- actionable completed-but-not-ingested or running-completed MinerU cases remain visible in `takeoverRequiredTasks`

Record the exact IDs observed, including whether `task-1778222027064`, `task-1778120784621`, and `task-1778118934116` still exist and how they are classified.

### 4. Stage-Queued Validation Gate

If gates 1-3 pass and active heavy-stage work is idle, run at most two controlled validation uploads under the accepted stage-queued rule:

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
- Ollama warm readiness
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

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Release-Candidate-Two-Pass-Validation-Pass-1_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 52 with:

- status
- report path
- branch / HEAD
- validation pass count used
- revision cycle count used
- next actor
- exact next action

If pass 1 is clean, set Next Actor to Lucia with `PRODUCTION_RELEASE_CANDIDATE_READY_FOR_LUCIA_REVIEW`.

If blockers remain, set Next Actor to Lucia with `BLOCKED_WITH_REVISION_CANDIDATE`, and include the smallest proposed revision scope. Do not start a repair without a new Lucia task.
