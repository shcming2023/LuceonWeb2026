# TASK-20260521-112955-P0-Mineru2Table-Mainline-Integration-And-Local-Deployment-Readiness

Issued At: 2026-05-21T11:29:55+0800

Owner: lucode

Reviewer: luceon

Priority: P0

Status: 待执行

## 1. Mainline Objective

Move the accepted Mineru2Table Protocol v1 gap-fix branch into the external
service mainline, then prove the local standalone Mineru2Table container can be
rebuilt and inspected through read-only endpoints.

This task answers one mainline question only:

```text
Can the independently developed Mineru2Table service be promoted to its own main
branch and run locally as the next deployable CleanService candidate, before
Luceon orchestrator wiring begins?
```

## 2. Current Evidence

Luceon accepted Task 225 at external service code/test level only:

- Accepted external branch:
  `origin/lucode/task-225-mineru2table-protocol-gap-fixes@b43852485d9f0e7d2918578df494afefe6b2f687`
- Luceon acceptance review:
  `TaskAndReport/2026-05-21T11-24-49+0800_P0-Mineru2Table-External-Service-Protocol-Gap-Fixes_LUCEON_REVIEW.md`
- Acceptance boundary:
  not merged to Mineru2Table main, not deployed, not wired into Luceon orchestration.

Fresh pre-dispatch checks from Luceon:

```bash
git -C /Users/concm/prod_workspace/Mineru2Tables merge-base --is-ancestor \
  origin/main origin/lucode/task-225-mineru2table-protocol-gap-fixes
# exit 0
```

```text
Mineru2Table local worktree:
  HEAD        43754fa0f3d1
  origin/main 7e9e592cac7d
  accepted branch b43852485d9f
  status: main...origin/main [behind 5]
```

The accepted branch Docker surface currently declares:

- compose service: `mineru2table`
- container name: `mineru2table-api`
- default host port: `${API_PORT:-8000}:8000`
- process command:
  `uvicorn api_server:app --workers 1 --host 0.0.0.0 --port 8000`
- Dockerfile supports build arg `GIT_COMMIT` and exports
  `IMPLEMENTATION_COMMIT`.

## 3. Critical Path Scope

Do only these steps, in order.

### Phase A - External Mainline Integration Decision

1. In the external Mineru2Table repository, fetch current remote refs.
2. Confirm whether `origin/main` is still an ancestor of
   `origin/lucode/task-225-mineru2table-protocol-gap-fixes`.
3. If the branch remains a clean fast-forward successor and repo policy allows
   it, advance Mineru2Table `main` to
   `b43852485d9f0e7d2918578df494afefe6b2f687` and push `main`.
4. If direct main update is blocked by branch protection, permission, conflict,
   or unexpected divergence, stop and report the exact blocker. Do not invent a
   workaround in this task.

Recommended source-control route when allowed:

```text
fast-forward merge into Mineru2Table main, preserving the accepted commit SHA
for traceability.
```

### Phase B - Local Deployment Workspace Sync

Only after Phase A succeeds and remote `origin/main` points to the accepted
Task 225 implementation:

1. Use `/Users/concm/prod_workspace/Mineru2Tables` as the local deployment
   workspace.
2. Confirm the worktree is clean enough for a fast-forward pull.
3. Run a fast-forward-only sync to the new Mineru2Table `origin/main`.
4. Record pre-sync and post-sync SHAs.

If the worktree is dirty, diverged, or cannot fast-forward, stop and report.

### Phase C - Local Container Rebuild And Read-Only Validation

Only after Phase B succeeds:

1. Rebuild only the Mineru2Table service image from the synced external main:

   ```bash
   docker compose build --build-arg GIT_COMMIT="$(git rev-parse HEAD)" mineru2table
   ```

2. Recreate only the Mineru2Table service container, without dependency or
   volume cleanup:

   ```bash
   docker compose up -d --no-deps mineru2table
   ```

3. Run read-only checks only:

   ```bash
   docker compose ps mineru2table
   curl -fsS http://127.0.0.1:8000/health
   curl -fsS http://127.0.0.1:8000/openapi.json
   ```

4. Confirm OpenAPI exposes the Protocol v1 read/write surface without invoking
   any write endpoint:

   - `/api/v1/jobs`
   - `/api/v1/jobs/{job_id}`
   - `/api/v1/jobs:from-storage`

5. Record whether `/health` returns HTTP 200 and the structured health payload.
   If dependency checks are degraded because secrets or external services are
   not configured, report that as dependency/config evidence. Do not edit
   secrets or create fake health.

## 4. True Preconditions

- Task 225 accepted external branch must remain the source being promoted.
- External `main` integration must be clean and auditable before any local
  container rebuild.
- Local deployment workspace must fast-forward to the integrated external main.
- Read-only validation must not submit jobs or mutate MinIO, DB, LLM state, or
  service data beyond the container rebuild/recreate required for this task.

## 5. Environment And Write Boundary

### External Mineru2Table Repository

Repository:

```text
shcming2023/Mineru2Table2026
```

Local deployment workspace:

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed operations:

- `git fetch`, `git status`, `git log`, `git diff`, `git merge-base`
- clean fast-forward integration of the accepted Task 225 branch into
  Mineru2Table `main`
- push of Mineru2Table `main` only if it is the clean fast-forward result
- fast-forward sync of `/Users/concm/prod_workspace/Mineru2Tables`
- `docker compose build --build-arg GIT_COMMIT=... mineru2table`
- `docker compose up -d --no-deps mineru2table`
- read-only `docker compose ps`, limited `docker logs --tail`, and read-only
  HTTP `GET /health` / `GET /openapi.json`

Forbidden operations:

- no new Mineru2Table feature work or opportunistic refactor
- no conflict-resolution rewrite unless Luceon explicitly approves after a
  blocker report
- no Docker volume deletion, prune, `down -v`, data directory deletion, or
  output cleanup
- no MinIO object create/update/delete
- no DB mutation
- no real LLM call
- no `POST /api/v1/jobs`, `POST /api/v1/jobs:from-storage`, legacy
  `/api/v1/extract`, legacy task creation, or any job-submission endpoint
- no secret printing, `.env` mutation, or synthetic secret creation
- no port mapping change unless explicitly authorized after reporting a blocker

### Luceon2026 Control Plane

Allowed files:

- `TaskAndReport/2026-05-21T11-29-55+0800_P0-Mineru2Table-Mainline-Integration-And-Local-Deployment-Readiness_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden files:

- `server/**`
- `src/**`
- `docs/**` unless Luceon explicitly requests a follow-up documentation update
- `AGENTS.md`
- `.agents/**`
- Docker, Compose, env, DB, MinIO, model, sample, or production data files in
  the Luceon project

## 6. Deferrable Side Work

Record but do not implement in this task:

- Luceon CleanService worker HTTP transport wiring.
- Feature flag enablement from Luceon to Mineru2Table.
- Real Raw Material ObjectRef dispatch.
- Webhook callback loop validation with Luceon.
- MinIO end-to-end output inspection from real materials.
- RawMaterial2CleanMaterial service planning or implementation.
- Broad hardening beyond evidence needed for local deployment readiness.

## 7. Fast Validation Target

The smallest useful proof is:

```text
Mineru2Table main contains the accepted Task 225 protocol fixes, the local
mineru2table-api container is rebuilt from that commit, and read-only endpoints
prove the Protocol v1 API surface is present.
```

This is not a production validation and not a Luceon orchestration validation.

## 8. Stop Rule

Stop and report instead of widening scope if any of these occur:

- the accepted branch is no longer a clean fast-forward successor of
  Mineru2Table `main`;
- direct main update is blocked by repository policy or permissions;
- local `/Users/concm/prod_workspace/Mineru2Tables` has dirty or divergent
  tracked changes;
- Docker build or service recreate would require volume deletion, broad cleanup,
  port changes, or secret edits;
- `GET /health` or `GET /openapi.json` fails in a way that cannot be explained
  without code/config mutation;
- any validation would require a live job submission, MinIO write, or LLM call.

## 9. Positive Acceptance Criteria

Luceon can accept this task only if the report includes:

- exact external Mineru2Table integration method;
- exact final Mineru2Table `main` SHA;
- exact local `/Users/concm/prod_workspace/Mineru2Tables` pre-sync and post-sync
  SHAs;
- exact Docker build and recreate commands with exit codes;
- `docker compose ps mineru2table` evidence;
- `GET /health` HTTP status and structured response summary;
- `GET /openapi.json` endpoint audit proving the three Protocol v1 paths are
  present;
- explicit evidence that no job submission endpoint was invoked;
- explicit evidence that no DB, MinIO object, Docker volume, model, sample, or
  secret mutation was performed;
- Luceon control-plane report and ledger update.

## 10. Negative Acceptance Criteria

Return or block the task if any of these happen:

- Mineru2Table main is not the accepted Task 225 implementation or its clean
  descendant;
- container rebuild depends on unreported local changes;
- validation uses `POST` job endpoints or real MinIO/LLM processing;
- a degraded health result is presented as deployment-ready;
- Luceon orchestrator wiring is included;
- docs/report language claims UAT, L3, production readiness, release readiness,
  pressure PASS, or go-live;
- private role files are tracked, copied, cited as project facts, or deleted.

## 11. Report Requirements

Create the report at:

```text
TaskAndReport/2026-05-21T11-29-55+0800_P0-Mineru2Table-Mainline-Integration-And-Local-Deployment-Readiness_REPORT.md
```

The report must include:

- summary;
- source-control decision and command transcript;
- local deployment sync evidence;
- Docker build/recreate evidence;
- read-only endpoint evidence;
- changed-files audit for both repositories;
- safety boundary statement;
- residual risks and deferred side work;
- final status recommendation.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only
after all completed evidence is committed and pushed.

## 12. Review Boundary

Passing this task means only:

```text
Mineru2Table external mainline integration and local standalone read-only
deployment validation are acceptable for the next planning step.
```

It does not mean:

- Luceon can dispatch real CleanService jobs;
- Mineru2Table is production-ready;
- Raw Material to Clean Material flow is validated;
- MinIO outputs are business-accepted;
- UAT, L3, pressure PASS, release readiness, or go-live is achieved.
