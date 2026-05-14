# Task Brief: P1 MinerU Log Channel Diagnostics Production Deployment And Runtime Validation

- Task ID: `TASK-20260514-080508-P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-And-Runtime-Validation`
- Issued at: 2026-05-14T08:05:08+0800
- Issued by: Director
- Assigned role: Director-executed per explicit User instruction in the Director thread
- Source decision: `TASK-20260514-065352-P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-Decision`
- Required report: `TaskAndReport/2026-05-14T08-05-08+0800_P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-And-Runtime-Validation_REPORT.md`

## Objective

Restore the normal GitHub-to-production path for the accepted Task 107 MinerU log-channel diagnostics, then perform only the minimum production deployment and read-only runtime validation authorized by the User.

## Context

Task 107 was accepted at code/test level, but production still lacked the new read-only diagnostic endpoint:

- `GET /ops/mineru/log-channel-ownership`
- `inspectMineruLogChannelOwnership()` helper
- ownership/status surfacing in `ops/runtime-ownership-status.sh`

Task 108 recorded the decision boundary. The User explicitly approved: "先恢复 GitHub 同步，然后继续 Option A 的最小生产部署 + 只读验证".

## Authorized Scope

1. Restore GitHub `main` synchronization so the accepted diagnostics are available through the normal repository path.
2. In production workspace `/Users/concm/prod_workspace/Luceon2026`, fast-forward to the synced `origin/main`.
3. Run the minimum necessary upload-server deployment command:
   - `docker compose up -d --build upload-server`
4. Run only read-only runtime checks:
   - production Git HEAD and dirty state;
   - upload health through CMS proxy;
   - `/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`;
   - `/__proxy/upload/ops/mineru/admission-circuit`;
   - `/__proxy/upload/ops/mineru/active-task`;
   - `/__proxy/upload/ops/mineru/log-channel-ownership`;
   - `ops/runtime-ownership-status.sh`;
   - source/container marker checks for the new endpoint/helper.

## Explicitly Not Authorized

- PDF upload;
- pressure, batch, soak, broad stress, or long-run testing;
- MinerU log observer sidecar start/restart;
- MinerU/Ollama/MinIO/DB restart beyond the minimum upload-server deployment;
- failed-task repair, reparse, re-AI, cleanup, or historical mutation;
- destructive DB/MinIO/Docker volume/data operation;
- model pull/delete/replace, secret/config/env mutation;
- sample-file mutation;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线 declaration.

## Acceptance Evidence Required

- GitHub `origin/main` includes the diagnostics commit.
- Production fast-forward and upload-server deployment command exit successfully.
- Runtime checks show the upload-server is reachable, dependency health is non-blocking, admission circuit is closed or clearly reported, active task state is clean or clearly reported, and the new log-channel ownership endpoint returns structured diagnostic data.
- Any skipped check or blocker must be reported exactly.
