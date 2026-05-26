# P0 Release Gate Full Real UAT Stage0-6 - Report

Status: `COMPLETED_FULL_REAL_UAT_STAGE3_TO_STAGE6_WITH_FIXES`

## Authorization

The user explicitly authorized full real UAT testing on `2026-05-26`, including production rebuild/recreate/restart, submit-probe, fault injection, and bounded pressure uploads.

This report records UAT evidence only. It is not a readiness, release-readiness, go-live, pressure PASS, UAT signoff, or external production authorization statement.

## Summary

Full UAT found and fixed several real closeout gaps, then completed Stage 3 through Stage 6 evidence collection against `http://127.0.0.1:8081`.

Key results:

- Stage 3 smoke after no-cache deployment: `SMOKE_RESULT PASS=13 FAIL=0 SKIP=0 TOTAL=13`.
- Stage 4 real fault injection: worker crash recovery and MinerU-down admission isolation passed.
- Stage 5 bounded pressure: five PDF tasks submitted and all reached terminal `review-pending` with no scoped MinerU/AI concurrency violations.
- Stage 6 production rehearsal: locked-image deployment converged, services healthy, submit-probe passed, and MinerU settled to zero queued/processing tasks.
- Stage 7 remains unsigned / not created.

## Fixes Made During UAT

- `docker-compose.yml`, release checklist, and Stage evidence were corrected from the invalid/incompatible MinIO 2024 tag to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Production `.env` MinIO credentials were rotated locally away from forbidden defaults. Secret values were not printed or committed.
- `uat/release-gate.sh` now respects `TEST_PDF_DIR` and `TEST_MD_DIR` for controlled UAT fixtures.
- `server/upload-server.mjs` now allows Markdown upload while MinerU submit admission is open/down, while still blocking PDF parsing on MinerU and all uploads on MinIO blocking state.
- `uat/stress-test-concurrency.sh` now scopes active MinerU/AI concurrency counts to the current tracked batch and non-terminal tasks, avoiding false violations from unrelated historical tasks.

## Stage Evidence

### Stage 2 / Deployment Contract

- MinIO source contract: `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Local digest evidence: `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.
- `docker compose build --no-cache`: `PASS`.
- `docker compose up -d`: `PASS`.
- `docker compose ps`: frontend, upload-server, db-server, and MinIO healthy.

### Stage 3 / Smoke

Command:

```bash
BASE_URL=http://127.0.0.1:8081 bash uat/smoke-test.sh
```

Result:

```text
SMOKE_RESULT PASS=13 FAIL=0 SKIP=0 TOTAL=13
```

### Stage 4 / Fault Injection

Command:

```bash
TEST_PDF_DIR=/tmp/luceon-uat-fault/pdf \
TEST_MD_DIR=/tmp/luceon-uat-fault/md \
BASE_URL=http://127.0.0.1:8081 \
bash uat/release-gate.sh --with-fault
```

Evidence:

- Worker crash task: `task-1779782412432`.
- Recovery event: `parse-restart-mineru-resumed`.
- Worker crash task terminal state: `review-pending`.
- MinerU-down PDF response: `503` / `MINERU_ADMISSION_CIRCUIT_OPEN`.
- MinerU-down Markdown bypass task: `task-1779782921754`.
- Post-restart submit-probe recovery: three consecutive probe checks passed.

### Stage 5 / Bounded Pressure

Command:

```bash
TEST_PDF_DIR=/tmp/luceon-uat-stress2/pdf \
TEST_MD_DIR=/tmp/luceon-uat-stress2/md \
BASE_URL=http://127.0.0.1:8081 \
MAX_WAIT_MINUTES=10 \
POLL_INTERVAL=5 \
bash uat/stress-test-concurrency.sh
```

Result:

```text
STRESS_RESULT PASS=6 FAIL=0 PDF_TASKS=5 TOTAL_TASKS=5 MINERU_VIOLATION=0 AI_VIOLATION=0 TERMINAL=5
```

Task ids:

- `task-1779783332644`
- `task-1779783333310`
- `task-1779783333912`
- `task-1779783334501`
- `task-1779783335206`

All five reached terminal `review-pending`.

### Stage 6 / Production Rehearsal

Command:

```bash
RUN_MINERU_SUBMIT_PROBE=1 bash ops/runtime-ownership-status.sh
```

Evidence:

- Submit-probe status: `202`.
- Submit-probe task id after final no-cache deploy: `d0847bcd-bfaa-4452-bd5a-0bf0e5c3dc1f`.
- Admission circuit: closed.
- Docker services: healthy.
- Upload health: `ok=true`.
- DB health: `ok=true`.
- MinerU after settle:
  - `queued_tasks=0`
  - `processing_tasks=0`
  - `completed_tasks=25`
  - `failed_tasks=0`

## Checks

- `bash -n uat/smoke-test.sh uat/release-gate.sh uat/stress-test-concurrency.sh uat/fault-injection-admission.sh uat/fault-injection-worker-crash.sh ops/start-luceon-runtime.sh`: `PASS`
- `git diff --check`: `PASS`
- `npx tsc --noEmit`: `PASS`
- `npm run build`: `PASS`
- `docker compose build --no-cache`: `PASS`
- Post-deploy smoke: `PASS=13 FAIL=0 SKIP=0 TOTAL=13`

## Remaining Boundaries

- GitHub branch protection proof remains external evidence pending.
- Dependency vulnerability audit remains pending.
- Stage 7 remains unsigned / not created.
- This UAT does not authorize or claim readiness, release-readiness, go-live, external production launch, or unbounded pressure acceptance.
