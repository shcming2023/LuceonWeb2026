# Luceon Review - TASK-20260521-114801-P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening

Review Time: 2026-05-21T12:12:19+0800

Reviewer: Luceon

Decision: ACCEPTED_CONFIG_RUNTIME_LEVEL_WITH_EXTERNAL_MAIN_INTEGRATION

## 1. Scope Reviewed

This review covers Task 227 only:

- Mineru2Table compose ingress binding change;
- local `mineru2table-api` recreate/read-only validation;
- no Luceon CleanService wiring;
- no job submission;
- no MinIO, LLM, DB, secret, sample, or Docker volume mutation.

This review does not accept UAT, L3, production readiness, release readiness,
pressure PASS, go-live, or real Raw Material to Clean Material behavior.

## 2. Evidence Rechecked By Luceon

Luceon pulled the Luceon2026 control-plane report:

```text
Luceon2026 HEAD: dc0804f6f82c4d382a8214d09f355b5638147ca7
Report: TaskAndReport/2026-05-21T11-48-01+0800_P0-Mineru2Table-Loopback-Ingress-Boundary-Hardening_REPORT.md
```

The external branch exists on GitHub:

```text
refs/heads/lucode/task-227-mineru2table-loopback-ingress
af80ced635755384a2c878110013c3e2d8f9cb9a
```

The local checkout's default fetch refspec tracks only `main`, so Luceon
explicitly fetched the review branch ref before comparing it.

External diff against Mineru2Table `origin/main` before acceptance:

```text
M .env.example
M docker-compose.yml
git diff --check: exit 0
```

No `src/**`, `api_server.py`, parsing logic, storage logic, LLM logic, protocol
behavior, data, sample, secret, or volume file was changed.

The actual diff is limited to:

```text
docker-compose.yml:
- "${API_PORT:-8000}:8000"
+ "${API_BIND_HOST:-127.0.0.1}:${API_PORT:-8000}:8000"

.env.example:
+ API_BIND_HOST=127.0.0.1
```

## 3. External Main Integration

Because the branch is a clean fast-forward successor and passed review, Luceon
integrated it into the external Mineru2Table mainline:

```text
git merge-base --is-ancestor origin/main origin/lucode/task-227-mineru2table-loopback-ingress
ancestor_exit=0

git checkout main
git merge --ff-only origin/lucode/task-227-mineru2table-loopback-ingress
git push origin main

origin/main: b438524 -> af80ced
```

Post-integration state:

```text
Mineru2Table main HEAD:   af80ced635755384a2c878110013c3e2d8f9cb9a
Mineru2Table origin/main: af80ced635755384a2c878110013c3e2d8f9cb9a
```

The local Mineru2Table workspace still contains untracked `data/` runtime state.
Luceon did not delete or modify it.

## 4. Runtime Evidence Rechecked

Container status:

```text
NAME               IMAGE                        SERVICE        STATUS        PORTS
mineru2table-api   mineru2tables-mineru2table   mineru2table   Up (healthy)  127.0.0.1:8000->8000/tcp
```

Docker inspect port mapping:

```json
{"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"8000"}]}
```

Host listener:

```text
TCP 127.0.0.1:8000 (LISTEN)
```

Compose config expands to:

```text
host_ip: 127.0.0.1
target: 8000
published: "8000"
protocol: tcp
```

Container build commit:

```text
IMPLEMENTATION_COMMIT=af80ced635755384a2c878110013c3e2d8f9cb9a
```

Read-only health:

```json
{
  "status": "unhealthy",
  "service_name": "toc-rebuild",
  "service_version": "1.0.0",
  "protocol_version": "v1",
  "checks": {
    "minio": "unconfigured",
    "llm": "not_configured",
    "dependencies": "ok"
  }
}
```

OpenAPI path/method audit:

```text
/api/v1/jobs: POST deprecated=False
/api/v1/jobs/{job_id}: GET deprecated=False
/api/v1/jobs:from-storage: POST deprecated=False
/api/v1/extract: POST deprecated=True
/api/v1/tasks: POST deprecated=True
/api/v1/tasks/{task_id}: GET deprecated=True
```

Observed log tail contains `GET /health` and `GET /openapi.json` only. Luceon
did not observe job-submission `POST` calls in the reviewed tail.

Note: Uvicorn still listens on `0.0.0.0` inside the container. That is acceptable
for this task because the Docker host publication is now loopback-only.

## 5. Acceptance

Task 227 is accepted for the narrow prerequisite:

```text
Mineru2Table local deployment now defaults to loopback-only host publication,
and the rebuilt local standalone container remains readable on 127.0.0.1:8000.
```

Accepted facts:

- `0.0.0.0:8000` and `[::]:8000` are no longer published on the host;
- `127.0.0.1:8000` remains available;
- the service still reports honest dependency-unconfigured status;
- Protocol v1 paths remain visible in OpenAPI;
- no job, MinIO, LLM, DB, secret, volume, or Luceon wiring mutation was accepted.

## 6. Next Step

With the external service mainline and loopback ingress ready, the next mainline
task can move to Luceon-side orchestration foundation.

Task 228 is dispatched as a narrow, disabled-by-default HTTP transport wiring
task. It must use mock HTTP validation first and must not submit real jobs to
the local Mineru2Table service.

## 7. Final Boundary

This is config/runtime-level acceptance only.

It is not:

- real CleanService dispatch;
- MinIO/LLM end-to-end validation;
- UAT;
- L3;
- production readiness;
- release readiness;
- pressure PASS;
- go-live.
