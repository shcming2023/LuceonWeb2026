# Director Review: P0 Post Fix Production Deployment And Non Destructive Runtime Validation

Review time:
2026-05-13T14:46:20+0800

Reviewed task:
`TASK-20260513-142231-P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation`

Reviewed report:
`TaskAndReport/2026-05-13T14-22-31+0800_P0-Post-Fix-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md`

Decision:
`ACCEPTED_NON_DESTRUCTIVE_RUNTIME_VALIDATION_WITH_ROUTE_NOTE`

## Summary

Director accepts the DevelopmentEngineer report at deployment/runtime-validation level.

Production was fast-forwarded from `301e4da` to `51f21d0`, and the upload server was rebuilt/recreated with the minimum necessary service scope. Runtime validation surfaces are healthy enough to dispatch the follow-up exactly-one-upload TestAcceptanceEngineer validation.

This review does not declare production release readiness, L3, pressure PASS, or full acceptance.

## Evidence Reviewed

DevelopmentEngineer reported:

- production `main` fast-forwarded from `301e4da` to `51f21d0`;
- `docker compose up -d --build upload-server` completed with exit 0;
- upload server health returned ok;
- dependency health with MinerU submit probe and Ollama chat probe returned `ok=true`, `blocking=false`;
- admission circuit was closed;
- active/current/queued/takeover-required task lists were empty;
- Ollama `qwen3.5:9b` was resident and chat probe succeeded;
- Task 87 code-path markers were present in production source and upload-server container;
- no validation upload, pressure test, failed-task repair, cleanup, destructive data/model/volume operation, sample mutation, L3 claim, pressure PASS claim, or release-readiness claim occurred.

Director independently rechecked production read-only:

- `/Users/concm/prod_workspace/Luceon2026` is on `main` at `51f21d0`;
- production retains only the expected local `docker-compose.override.yml` diff for strict AI/model env and local-only MinIO console binding;
- `docker compose ps` shows `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy;
- `http://localhost:8081/__proxy/upload/health` returns upload-server ok;
- dependency health with `mineruSubmitProbe=1&ollamaChatProbe=1` returns `ok=true`, `blocking=false`;
- canonical `http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` returns 200 with circuit `closed`;
- canonical `http://localhost:8081/__proxy/upload/ops/mineru/active-task` returns 200 with no active/current/queued/takeover-required tasks and unchanged historical AI failure `task-1778651226016`;
- `http://127.0.0.1:11434/api/ps` lists resident `qwen3.5:9b`;
- production source contains `headersTimeout: requestTimeoutMs`, `bodyTimeout: requestTimeoutMs`, `headersTimeoutMs: requestTimeoutMs`, `bodyTimeoutMs: requestTimeoutMs`, `fast-complete-no-business-signal`, and `../../lib/ops-mineru-log-parser.mjs`.

## Route Note

The DevelopmentEngineer report records short route examples:

- `/__proxy/upload/ops/admission-circuit`
- `/__proxy/upload/ops/active-task`

Director recheck shows those short routes return 404 HTML. The correct production routes are:

- `/__proxy/upload/ops/mineru/admission-circuit`
- `/__proxy/upload/ops/mineru/active-task`

The report's conclusion remains accepted because the required canonical routes pass and dependency-health also embeds the same non-blocking circuit state. Follow-up tasks must use the canonical `/ops/mineru/...` routes.

## Boundary

Accepted:

- scoped production deployment of accepted Task 87 code path;
- non-destructive runtime-surface validation;
- evidence is sufficient to authorize one controlled TestAcceptanceEngineer upload validation.

Not accepted or not claimed:

- production release readiness;
- L3;
- pressure PASS;
- 24-PDF pressure retry/test;
- multiple uploads;
- failed-task repair, reparse, re-AI, deletion, or cleanup;
- DB/MinIO/Docker volume/data mutation;
- model pull/delete/replace/reload;
- broad restart/rollback;
- sample-file mutation.

## Follow-Up

Director issued:

`TASK-20260513-144620-P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment`

Assigned to:

`TestAcceptanceEngineer`

The follow-up task is limited to exactly one controlled upload from the production test sample directory, with task-page progress semantics and terminal-state evidence. It must not perform pressure testing, second upload, historical task repair, cleanup, destructive operations, or release-readiness claims.
