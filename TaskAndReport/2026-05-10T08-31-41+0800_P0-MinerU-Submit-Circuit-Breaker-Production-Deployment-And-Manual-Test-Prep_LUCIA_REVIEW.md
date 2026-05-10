# Lucia Review: P0 MinerU Submit Circuit Breaker Production Deployment And Manual Test Prep

- Review Time: `2026-05-10T08:31:41+0800`
- Reviewer: Lucia
- Task ID: `TASK-20260510-081906-P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep`
- Task Brief: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_TASK.md`
- Lucode Report: `TaskAndReport/2026-05-10T08-19-06+0800_P0-MinerU-Submit-Circuit-Breaker-Production-Deployment-And-Manual-Test-Prep_REPORT.md`
- Review Decision: `ACCEPTED_DEPLOYED_BUT_RUNTIME_BLOCKED`

## Judgment

Lucode completed the authorized upload-server deployment and preserved the production-local override boundary, but production manual PDF testing must not restart as a normal validation pass yet.

The remaining blocker is not unmerged Task 64 code. The accepted circuit-breaker code is deployed to production upload-server, and the upload-server is healthy. The blocking condition is the real production MinerU submit path: MinerU `/health` is OK, but `POST /tasks` still returns HTTP 500 through the dependency-health submit probe.

This is release-blocking runtime evidence. It is not production release readiness.

## Evidence Reviewed

Lucode reported:

- production path: `/Users/concm/prod_workspace/Luceon2026`;
- production deployed HEAD after sync/deploy: `e015cc8ed8de60eae27d0883ed6e3fa22d5d59fd`;
- production-local dirty file preserved: `docker-compose.override.yml`;
- deploy command: `docker compose up -d --build upload-server`;
- `cms-upload-server` rebuilt and healthy;
- upload health: `{"ok":true,"service":"upload-server"}`;
- dependency-health with `mineruSubmitProbe=true`: `ok=false`, `blocking=true`, MinIO OK, Ollama OK, MinerU `/health` OK, MinerU submit probe HTTP 500;
- active-task diagnostics empty;
- no manual PDF upload, no failed pressure-task repair, no broad service restart, no DB/MinIO/Docker volume/task/material/artifact/log/sample mutation, no secret/model/timeout/override change, and no release-readiness claim.

Lucia independently rechecked:

- development main HEAD: `e10a2141a5589fbaa34e67eb46fd48208a612f0c`;
- `origin/main`: `e10a2141a5589fbaa34e67eb46fd48208a612f0c`;
- production HEAD/origin-main at deployed code: `e015cc8ed8de60eae27d0883ed6e3fa22d5d59fd`;
- production local dirty file remains limited to `docker-compose.override.yml`;
- `curl -fsS http://localhost:8081/__proxy/upload/health` returned OK;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` returned `ok=false`, `blocking=true`, MinerU `healthOk=true`, submit probe `status=500`, and Ollama `chatOk=true`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'` returned no active, queued, takeover-required, or historical AI failure tasks;
- `docker compose ps upload-server` in production showed `cms-upload-server` healthy;
- `git diff --check` passed in development.

## Scope Compliance

Accepted:

- production upload-server was updated to the accepted code boundary;
- strict AI/model and MinIO console local-only override settings were preserved;
- deployment action stayed scoped to `upload-server`;
- checks were read-only after deployment.

Not accepted as ready:

- normal manual PDF validation cannot restart while MinerU submit probe is blocking;
- production release readiness remains blocked;
- the failed 24 pressure-test tasks remain unrepaired and were not authorized for repair.

## Remaining Decision

Director decision is required before any MinerU runtime remediation or manual-test restart. Lucia is recording Task 67 for that decision.

Lucia must not autonomously authorize MinerU runtime recovery after heartbeat waits because the action may involve production service/runtime mutation and can affect parsing behavior. Production release readiness also remains Director-owned in Task 60.

