# TASK-20260521-114801-P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening

Issued At: 2026-05-21T11:48:01+0800

Owner: lucode

Reviewer: luceon

Priority: P0

Status: 待执行

## 1. Mainline Objective

Before Luceon orchestrator wiring or any real CleanService job dispatch, close
the local Mineru2Table ingress exposure so the standalone service is reachable
only through loopback by default.

This is a true prerequisite for the mainline because the service now exposes
job-submission endpoints and is intended to sit beside Luceon as an independent
API service.

## 2. Current Evidence

Task 226 was accepted for local standalone deployment-prep only:

- Mineru2Table main:
  `b43852485d9f0e7d2918578df494afefe6b2f687`
- local deployment workspace:
  `/Users/concm/prod_workspace/Mineru2Tables`
- container:
  `mineru2table-api`

Luceon rechecked the running container and observed:

```text
docker compose ps mineru2table

NAME               IMAGE                        SERVICE        STATUS
mineru2table-api   mineru2tables-mineru2table   mineru2table   Up (healthy)

PORTS
0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

Luceon also observed external requests in the container log tail:

```text
138.68.11.125:<port> - "GET /health HTTP/1.1" 200 OK
138.68.11.125:<port> - "GET /openapi.json HTTP/1.1" 200 OK
```

The service payload honestly reports dependency configuration is not ready:

```json
{
  "status": "unhealthy",
  "checks": {
    "minio": "unconfigured",
    "llm": "not_configured",
    "dependencies": "ok"
  }
}
```

## 3. Critical Path Scope

Do only the minimum necessary to make the local standalone service loopback-only
by default and prove that the read-only endpoint checks still work.

Preferred implementation:

```text
Change Mineru2Table docker-compose.yml port mapping default from all interfaces
to loopback, with an explicit override variable only if needed.
```

Expected shape:

```yaml
ports:
  - "${API_BIND_HOST:-127.0.0.1}:${API_PORT:-8000}:8000"
```

If an existing project convention suggests a better name than `API_BIND_HOST`,
use the local convention, but keep the default loopback-only.

## 4. Environment And Write Boundary

### External Mineru2Table Repository

Repository:

```text
shcming2023/Mineru2Table2026
```

Local workspace:

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed files:

- `docker-compose.yml`
- `.env.example` only if needed to document the new optional bind variable
- `README.md` only if an existing deployment note must be corrected
- focused test or script only if the repository already has a clear compose
  config validation pattern

Forbidden files:

- `src/**`
- `api_server.py`
- business logic, storage logic, LLM logic, parsing logic, or protocol behavior
- real data, sample assets, generated outputs, secrets, and runtime volume data

Allowed operations:

- create a focused branch, for example
  `lucode/task-227-mineru2table-loopback-ingress`
- run `git diff --check`
- run `docker compose config` or equivalent static compose validation
- rebuild/recreate only `mineru2table-api` as needed:

  ```bash
  docker compose build --build-arg GIT_COMMIT="$(git rev-parse HEAD)" mineru2table
  docker compose up -d --no-deps mineru2table
  ```

- run read-only checks:

  ```bash
  docker compose ps mineru2table
  curl -fsS http://127.0.0.1:8000/health
  curl -fsS http://127.0.0.1:8000/openapi.json
  lsof -nP -iTCP:8000 -sTCP:LISTEN
  ```

Forbidden operations:

- no `docker compose down -v`
- no Docker volume deletion or prune
- no data directory deletion
- no MinIO object mutation
- no DB mutation
- no real LLM call
- no job-submission endpoint calls, including `POST /api/v1/jobs`,
  `POST /api/v1/jobs:from-storage`, or deprecated extract/task creation routes
- no secret creation, mutation, or printing
- no firewall, router, VPN, or host-level network reconfiguration
- no Luceon orchestrator wiring

### Luceon2026 Control Plane

Allowed files:

- `TaskAndReport/2026-05-21T11-48-01+0800_P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden files:

- `server/**`
- `src/**`
- `docs/**` unless Luceon explicitly requests a follow-up doc correction
- `AGENTS.md`
- `.agents/**`
- Docker, DB, MinIO, model, sample, or production data files inside Luceon2026

## 5. Fast Validation Target

The smallest acceptable proof is:

```text
mineru2table-api is still reachable from 127.0.0.1:8000, but Docker no longer
publishes 8000 on 0.0.0.0 or [::].
```

Required evidence:

- `docker compose ps mineru2table` shows `127.0.0.1:8000->8000/tcp` and does
  not show `0.0.0.0:8000` or `[::]:8000`;
- `lsof -nP -iTCP:8000 -sTCP:LISTEN` shows loopback binding only, or the report
  explains the Docker Desktop listener evidence precisely;
- `GET http://127.0.0.1:8000/health` still returns HTTP 200 with honest
  dependency state;
- `GET http://127.0.0.1:8000/openapi.json` still exposes the Protocol v1 paths;
- no `POST` route is invoked.

## 6. Stop Rule

Stop and report instead of widening scope if:

- loopback binding cannot be achieved with a small compose/env example change;
- the current worktree is dirty in tracked files before your edit;
- Docker recreate would require volume cleanup, secret edits, or port changes
  beyond binding host;
- a local 8000 conflict appears after changing to loopback;
- any validation would require a live job, MinIO write, or LLM call.

## 7. Deferrable Side Work

Do not implement in this task:

- Bearer-token or API-token enforcement unless already present and only needs
  documentation;
- Luceon CleanService HTTP transport wiring;
- webhook callback integration;
- real Raw Material ObjectRef dispatch;
- MinIO/LLM end-to-end behavior checks;
- RawMaterial2CleanMaterial.

Record these as residuals if relevant.

## 8. Positive Acceptance Criteria

Luceon can accept this task if:

- the external branch contains only the allowed minimal config/doc/test changes;
- compose validation passes;
- the local container is recreated without volume cleanup;
- 8000 is loopback-only;
- `/health` and `/openapi.json` read checks still work;
- report evidence includes exact commands, exit codes, and final SHAs;
- the Luceon ledger is updated to `Ready for luceon Review`.

## 9. Negative Acceptance Criteria

Return the task if:

- 8000 remains bound to `0.0.0.0` or `[::]`;
- the task changes business code or protocol behavior;
- it submits any job or touches real MinIO/LLM/DB data;
- it claims UAT, L3, production readiness, release readiness, pressure PASS, or
  go-live;
- it deletes or tracks private role files.

## 10. Report Requirements

Create the report at:

```text
TaskAndReport/2026-05-21T11-48-01+0800_P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening_REPORT.md
```

The report must include:

- source branch and final SHA;
- changed-file audit;
- compose config validation;
- local rebuild/recreate evidence;
- port/listener evidence before and after;
- read-only endpoint evidence;
- explicit no-job/no-MinIO/no-LLM/no-DB statement;
- residual risks and next-step recommendation.

## 11. Review Boundary

Passing this task means only:

```text
The local standalone Mineru2Table service no longer exposes port 8000 on all
interfaces and remains readable from loopback.
```

It does not authorize real CleanService dispatch, MinIO/LLM job execution,
UAT, L3, production readiness, release readiness, or go-live.
