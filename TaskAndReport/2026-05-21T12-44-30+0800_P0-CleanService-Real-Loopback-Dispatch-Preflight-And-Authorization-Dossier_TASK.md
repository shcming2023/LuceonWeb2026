# TASK-20260521-124430-P0-CleanService-Real-Loopback-Dispatch-Preflight-And-Authorization-Dossier

Issued At: 2026-05-21T12:44:30+0800

Owner: lucode

Reviewer: luceon

Priority: P0

Status: 待执行

## 1. Mainline Objective

Prepare the exact read-only evidence and authorization dossier required before
Luceon attempts any real loopback dispatch to the local Mineru2Table service.

This task answers one mainline gate question:

```text
What exact prerequisites, credentials, sample ObjectRef, expected mutations, and
stop rules must be satisfied before Director can authorize one controlled real
POST /api/v1/jobs to Mineru2Table?
```

This task is read-only. It must not perform the real dispatch.

## 2. Current Evidence

Task 229 accepted code/test-level mock wiring:

- implementation branch:
  `lucode/task-229-worker-factory-retriable@5c759a1d5e270c6a63edbfd55daab88823b6c568`
- integrated merge commit:
  `4e953d0534868412044b57e85d26c3070242f78c`
- mock worker factory smoke:
  8/8 PASS
- default runtime:
  disabled-noop
- no real Mineru2Table POST accepted.

External Mineru2Table local service state rechecked by Luceon:

- Mineru2Table `main`:
  `af80ced635755384a2c878110013c3e2d8f9cb9a`
- host port publication:
  `127.0.0.1:8000` only
- `/health`:
  HTTP 200 with `status=unhealthy`, `minio=unconfigured`,
  `llm=not_configured`, `dependencies=ok`

## 3. Critical Path Scope

Produce a preflight and authorization dossier only.

Required outputs:

1. Current real Mineru2Table runtime readiness snapshot.
2. Current Luceon CleanService runtime configuration snapshot.
3. Exact mutation map for one real dispatch:
   - Mineru2Table job store;
   - MinIO reads;
   - MinIO writes;
   - LLM/API calls and cost exposure;
   - Luceon DB/metadata writes, if any future caller would persist result.
4. Required credentials and config presence matrix, with values masked.
5. Candidate input requirements for a single safe Raw Material ObjectRef.
6. Proposed single-dispatch authorization options for Director.
7. Stop rules for the future dispatch task.

Do not implement code in this task.

## 4. Environment And Write Boundary

Primary Luceon workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Mineru2Table deployment workspace:

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed read-only operations:

- `git status`, `git rev-parse`, `git log`, `git diff --name-status`;
- read task/report/review files;
- read source/config code needed to understand dispatch behavior;
- `docker compose ps mineru2table`;
- `docker inspect mineru2table-api`;
- `docker logs --tail` for read-only evidence;
- `GET http://127.0.0.1:8000/health`;
- `GET http://127.0.0.1:8000/openapi.json`;
- masked environment presence checks, for example boolean-only output such as
  `MINIO_ACCESS_KEY present: true/false`.

Forbidden operations:

- no `POST /api/v1/jobs`;
- no `POST /api/v1/jobs:from-storage`;
- no deprecated `/api/v1/extract` or `/api/v1/tasks` creation;
- no real CleanService worker tick against the local Mineru2Table endpoint;
- no Docker build/recreate/restart;
- no Docker volume deletion/prune;
- no MinIO object read/write/delete unless separately authorized;
- no DB mutation;
- no LLM/API call;
- no `.env` value printing;
- no secret creation, edit, or copy;
- no source code implementation;
- no frontend/UI, webhook, scheduler, upload-server, or output-ingestion work;
- no `AGENTS.md` or `.agents/**` tracking, deletion, or citation as project
  facts.

## 5. Read-Only Evidence Requirements

The report must include:

### A. Runtime Readiness Snapshot

- Mineru2Table Git HEAD and branch;
- Docker port binding;
- `/health` payload;
- `/openapi.json` Protocol v1 path/method audit;
- whether API key enforcement is configured or absent, without printing secret
  values.

### B. Dependency Configuration Matrix

Use masked/presence-only evidence:

```text
MINIO_ACCESS_KEY: present/absent
MINIO_SECRET_KEY: present/absent
DEEPSEEK_API_KEY or configured LLM key: present/absent
TOC_REBUILD_CALLBACK_SECRET: present/absent
ALLOWED_INPUT_BUCKETS: present/absent/value only if non-secret
ALLOWED_OUTPUT_BUCKETS: present/absent/value only if non-secret
```

Do not print actual secret values.

### C. Candidate ObjectRef Requirements

Define what a future single dispatch needs:

- `materialId`;
- `parseTaskId`;
- `assetVersion`;
- input bucket/object for `content_list_v2.json`;
- expected output bucket/prefix;
- source hash evidence if available;
- confirmation that the candidate is not legacy parsed-only.

If no candidate can be selected without DB/MinIO reads, record that Director
must authorize a separate read-only candidate-selection step.

### D. Mutation And Cost Map

State exactly what a future real dispatch is expected to mutate or consume:

- Mineru2Table job store file/path;
- MinIO read path;
- MinIO output prefix;
- LLM/API call and cost limits;
- Luceon metadata persistence if a future worker tick persists results.

### E. Director Authorization Options

Provide 2-3 concrete options:

- Option A: configure missing dependencies first, then authorize one controlled
  real dispatch;
- Option B: authorize a failure-mode dispatch with known missing dependencies to
  prove error path only;
- Option C: pause real dispatch and continue mock hardening.

Mark Lucode recommendation separately from Luceon/Director decision.

## 6. Stop Rule

Stop and report if:

- any evidence requires printing secrets;
- any proof would require a real POST;
- any proof would require MinIO/DB writes;
- current health remains dependency-unconfigured and no safe failure-mode
  authorization exists;
- a candidate ObjectRef cannot be identified without a separate authorized
  read-only DB/MinIO inspection.

## 7. Positive Acceptance Criteria

Luceon can accept this task if:

- report is read-only and evidence-backed;
- no secrets are printed;
- no job is submitted;
- current readiness and missing dependencies are clear;
- future mutation/cost map is explicit;
- Director options are concrete and bounded;
- ledger is updated to `Ready for luceon Review`;
- `git diff --check` passes for control-plane files.

## 8. Negative Acceptance Criteria

Return the task if:

- a real `POST` is made;
- MinIO/DB/LLM/Docker/env/secrets are mutated;
- secret values are printed;
- the report claims UAT, L3, production readiness, release readiness, pressure
  PASS, or go-live;
- it starts implementing code instead of producing the authorization dossier.

## 9. Report Requirements

Create the report at:

```text
TaskAndReport/2026-05-21T12-44-30+0800_P0-CleanService-Real-Loopback-Dispatch-Preflight-And-Authorization-Dossier_REPORT.md
```

The report must include command snippets and exit codes for all read-only checks.

## 10. Review Boundary

Passing this task means only:

```text
Director has enough current evidence to decide whether and how to authorize one
controlled real loopback dispatch in a later task.
```

It does not authorize the dispatch itself.
