# Director Decision Required: P0 MinerU Runtime Submit-500 Recovery Authorization

- Decision ID: `TASK-20260510-083141-P0-MinerU-Runtime-Submit-500-Recovery-Authorization`
- Created At: `2026-05-10T08:31:41+0800`
- Created By: Lucia
- Status: `挂起`
- Next Actor: Director
- Related Review: `TaskAndReport/2026-05-10T08-31-41+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_LUCIA_REVIEW.md`
- Related Deployment Report: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_REPORT.md`

## Decision Needed

The accepted upload-server circuit-breaker code has been deployed, but production MinerU submit-path recovery is still required before normal manual PDF testing can restart.

Director must choose one:

1. Authorize a scoped MinerU runtime recovery task.
2. Hold manual testing and request more read-only MinerU evidence first.
3. Hold the release-readiness track until the MinerU runtime is repaired outside this task flow.

## Current Confirmed Facts

- Production upload-server is healthy after scoped rebuild.
- Production upload-server code is deployed at `e015cc8ed8de60eae27d0883ed6e3fa22d5d59fd`.
- Production-local `docker-compose.override.yml` is intentionally dirty and preserved.
- MinIO is OK.
- Ollama `qwen3.5:9b` is OK from the upload-server dependency-health path.
- MinerU `/health` is OK.
- MinerU submit probe still fails with HTTP 500 and `blocking=true`.
- Active task diagnostics show no active/queued/takeover-required tasks.
- Manual PDF testing should not restart as a normal validation pass while submit probe remains blocking.
- Production release readiness remains unclaimed and blocked.

## If Option 1 Is Approved

Lucia should issue a scoped Lucode task with these boundaries:

- allow only the minimum necessary MinerU runtime recovery action needed to clear submit-path HTTP 500;
- prefer read-only diagnosis first, then the smallest service-level action if needed;
- verify `dependency-health?mineruSubmitProbe=true` after recovery;
- verify upload health and active-task diagnostics after recovery;
- do not create a new validation upload unless Director separately authorizes it after the submit probe passes;
- do not repair or reprocess the failed 24 pressure-test tasks unless separately authorized;
- do not mutate DB rows, MinIO objects, Docker volumes, secrets, model/provider/timeout/override settings, samples, or historical artifacts;
- do not declare production release readiness.

## Autonomy Boundary

Lucia may record heartbeat wait evidence but must not autonomously authorize MinerU runtime recovery after two unanswered heartbeats. This decision can involve production runtime/service mutation and therefore remains Director-owned.

