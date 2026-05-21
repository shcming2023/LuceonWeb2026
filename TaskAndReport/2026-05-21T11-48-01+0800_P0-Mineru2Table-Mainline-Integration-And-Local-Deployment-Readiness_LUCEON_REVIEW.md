# Luceon Review - TASK-20260521-112955-P0-Mineru2Table-Mainline-Integration-And-Local-Deployment-Readiness

Review Time: 2026-05-21T11:48:01+0800

Reviewer: Luceon

Decision: ACCEPTED_LOCAL_STANDALONE_DEPLOYMENT_PREP_WITH_REQUIRED_INGRESS_FOLLOWUP

## 1. Scope Reviewed

This review covers Task 226 only:

- external Mineru2Table mainline fast-forward integration;
- local `/Users/concm/prod_workspace/Mineru2Tables` deployment workspace sync;
- local `mineru2table-api` container rebuild/recreate;
- read-only `/health` and `/openapi.json` validation.

This review does not accept Luceon orchestrator wiring, real CleanService
dispatch, live MinIO/LLM processing, RawMaterial2CleanMaterial, UAT, L3,
production readiness, release readiness, pressure PASS, or go-live.

## 2. Evidence Rechecked By Luceon

Luceon pulled the Luceon2026 control-plane update:

```text
Luceon2026 HEAD: 807f86357523512bb078b46f135204de65f0aeed
Changed files from previous Luceon dispatch:
A TaskAndReport/2026-05-21T11-29-55+0800_P0-Mineru2Table-Mainline-Integration-And-Local-Deployment-Readiness_REPORT.md
M TaskAndReport/TASK_TRACKING_LIST.md
```

Luceon fetched the external Mineru2Table repository and confirmed:

```text
Mineru2Table local HEAD:  b43852485d9f0e7d2918578df494afefe6b2f687
Mineru2Table origin/main: b43852485d9f0e7d2918578df494afefe6b2f687
Latest commit: TASK-225: Fix all protocol gaps and clean up temp dirs safely
```

The local Mineru2Table worktree has no tracked source diff. It contains an
untracked `data/` directory, treated as local deployment runtime state and not
deleted or modified by Luceon.

Container evidence rechecked by Luceon:

```text
mineru2table-api image: mineru2tables-mineru2table
container state: Up (healthy)
published ports: 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
IMPLEMENTATION_COMMIT: b43852485d9f0e7d2918578df494afefe6b2f687
```

Read-only endpoint evidence rechecked by Luceon:

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

OpenAPI path/method audit rechecked by Luceon:

```text
/api/v1/jobs: POST deprecated=False
/api/v1/jobs/{job_id}: GET deprecated=False
/api/v1/jobs:from-storage: POST deprecated=False
/api/v1/extract: POST deprecated=True
/api/v1/tasks: POST deprecated=True
/api/v1/tasks/{task_id}: GET deprecated=True
```

Container log tail showed `GET /health` and `GET /openapi.json` only in the
observed tail; no job-submission `POST` was observed by Luceon in that tail.

## 3. Luceon Evidence Corrections

Luceon made a narrow control-plane evidence correction to the submitted report:

- `/api/v1/jobs` is currently observed as `POST`, not `GET/POST`.
- The OpenAPI check proves core path visibility only; it does not prove full
  Protocol v1 behavioral compliance.
- Docker `healthy` means the Docker HTTP healthcheck returned success. The
  application payload itself correctly reports `status=unhealthy` because MinIO
  and LLM credentials are unconfigured.

These corrections do not invalidate Task 226 because the task required read-only
path-surface verification, not real job behavior validation.

## 4. Acceptance

Task 226 is accepted for the narrow mainline objective:

```text
Mineru2Table main now contains the accepted Task 225 implementation, the local
standalone container has been rebuilt from that commit, and read-only endpoint
checks prove the expected Protocol v1 paths are present.
```

Accepted facts:

- external Mineru2Table `origin/main` is now
  `b43852485d9f0e7d2918578df494afefe6b2f687`;
- local deployment workspace is synced to the same SHA;
- container `IMPLEMENTATION_COMMIT` reports the same SHA;
- `/health` returns HTTP 200 with honest unconfigured dependency status;
- `/openapi.json` exposes the expected Protocol v1 paths;
- no Luceon wiring or live job run was accepted.

## 5. Required Follow-Up Before Wiring

Luceon discovered a safety blocker for the next mainline step:

```text
docker compose ps shows 0.0.0.0:8000 and [::]:8000 published bindings.
docker logs show external IP requests to /health and /openapi.json.
```

Because Task 226 did not authorize port-binding changes, Luceon did not mutate
the running service. However, Luceon will not authorize real Luceon orchestrator
wiring or job submission while the standalone service remains exposed on all
interfaces.

Task 227 is therefore dispatched as a true prerequisite: narrow loopback ingress
boundary hardening for Mineru2Table local deployment.

## 6. Final Boundary

Task 226 is closed as local standalone deployment-prep acceptance only.

It is not:

- UAT;
- L3;
- production-ready;
- release-ready;
- pressure PASS;
- go-live;
- evidence that MinIO or LLM job behavior works;
- evidence that Luceon can dispatch real CleanService jobs.
