# User Decision: P1 MinerU Log Channel Diagnostics Production Deployment

- Recorded at: 2026-05-14T06:53:52+0800
- Role: Director
- Decision ID: `TASK-20260514-065352-P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-Decision`
- Trigger: Task 107 accepted at code/test level; production deployment has not been performed.
- Current production HEAD observed during review: `159d80e Accept MinerU log observation hardening`
- Next Actor: User

## Current Facts

Task 107 added a read-only MinerU log-channel ownership diagnostic surface:

- `GET /ops/mineru/log-channel-ownership`;
- missing/empty/stale/valid log-channel classification;
- diagnostic-only sidecar observed/not-observed state;
- no host path exposure in the new public diagnostic payload;
- no-false-failure behavior preserved for in-flight MinerU API states;
- focused ownership, adjudication, transport, diff-check, and `test:static` passed.

The code is accepted at code/test level only. Production still needs a separate deployment before the endpoint can be inspected in the real runtime.

## Decision Needed

Decide whether to authorize a scoped production deployment and non-destructive runtime validation of the accepted Task 107 diagnostics.

This matters because the project is now trying to govern MinerU progress observability. Without deploying the diagnostic endpoint, we cannot see whether production reports the expected current issue clearly: empty/stale/missing log channel, sidecar not observed, and no attributable business progress.

## Options

### Option A: Scoped Production Deployment And Non-Destructive Runtime Validation (Director Recommended)

Authorize DevelopmentEngineer to:

- preflight production active-task/admission/dependency/Docker health;
- fast-forward production to the accepted diagnostics commit when available on `origin/main`;
- run the minimum necessary upload-server deployment command, expected `docker compose up -d --build upload-server`;
- run only read-only runtime checks:
  - upload health;
  - dependency-health;
  - admission circuit;
  - active-task;
  - new `/ops/mineru/log-channel-ownership`;
  - `ops/runtime-ownership-status.sh`;
  - source/container marker checks for the new endpoint/helper.

Explicitly not authorized:

- PDF upload;
- pressure, batch, soak, broad stress, or long-run testing;
- sidecar start/restart;
- MinerU/Ollama/MinIO/DB restart beyond the minimum upload-server deployment;
- cleanup, repair, reparse, re-AI, historical mutation;
- destructive DB/MinIO/Docker volume/data operation;
- model pull/delete/replace, secret/config/env mutation;
- sample-file mutation;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 declaration.

Why recommended:

This is the smallest step that makes the new diagnostics visible in production and tells us whether the current log-channel ownership problem is now directly observable.

### Option B: Hold At Code/Test Level

Do not deploy yet. Keep Task 107 accepted as code/test-level only.

Risk:

MinerU progress observability remains ungoverned in production. Future uploads or pressure attempts would still lack the new diagnostic surface.

### Option C: Skip Deployment And Start Sidecar/Ops Recovery

Not recommended.

Risk:

Starting sidecar or changing runtime ownership before deploying the diagnostic endpoint would reduce evidence quality. We would be changing the system before installing the tool that tells us what state it is actually in.

## Director Recommendation

Choose Option A.

If this decision item remains unanswered for two consecutive Director heartbeat/check-task cycles, Director may follow the standing no-long-term-blocker rule and issue the conservative Option A deployment/runtime-validation task only if production preflight is clean. The automatic path must not authorize upload, pressure testing, sidecar start/restart, destructive operations, L3, production readiness, release readiness, go-live readiness, or production上线.

## Heartbeat Wait Evidence

- `2026-05-14T07:12:19+0800`: first Director heartbeat/check-task after Task 108 was recorded. No user decision was present. Director recommendation remains Option A. No auto-progress was triggered because this is wait count 1 of 2.
- `2026-05-14T07:32:19+0800`: second Director heartbeat/check-task after Task 108 was recorded. No user decision was present. Production read-only preflight through the CMS proxy was clean: upload health OK, admission circuit closed, active-task clean, dependency-health `ok=true`/`blocking=false` with MinerU submit probe. However GitHub publication remained blocked: local HEAD was `047b154`, `origin/main` was still `392416c`, and `git push origin HEAD:main` timed out again. Auto-progress was not triggered because Option A requires the accepted diagnostics commit to be available from `origin/main` before production fast-forward/deploy.

## Current Hold After Second Heartbeat

The conservative automatic path is intentionally held until GitHub synchronization is restored or the User explicitly authorizes a different source-of-truth route. Director still recommends Option A after GitHub sync is restored.

Not recommended: deploying production directly from the unsynced local branch, starting/restarting the MinerU log observer sidecar first, or changing runtime ownership before the diagnostics endpoint is visible from the normal repository-to-production path.
