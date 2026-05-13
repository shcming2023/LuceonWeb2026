# Director Review: P0 Batched AI And MinerU Fixes Production Deployment And Runtime Validation

Review time:
2026-05-13T18:31:48+0800

Reviewed task:
`TASK-20260513-163104-P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation`

Reviewed report:
`TaskAndReport/2026-05-13T16-31-04+0800_P0-Batched-AI-And-MinerU-Fixes-Production-Deployment-And-Runtime-Validation_REPORT.md`

## Decision

`ACCEPTED_NON_DESTRUCTIVE_RUNTIME_VALIDATION_WITH_COMPOSE_DEPENDENCY_NOTE`

The DevelopmentEngineer report is accepted at deployment/runtime-validation level.

Production is now on `50e5621 Review MinerU diagnostics and dispatch deployment`, which includes the accepted Task 91 AI metadata single-pass finalization guard and Task 93 terminal MinerU diagnostic precedence code paths.

This is not production readiness, L3, pressure PASS, release-readiness, or a validation upload pass.

## Evidence Accepted

DevelopmentEngineer evidence shows:

- production fast-forwarded from `51f21d0` to `50e5621`;
- exact expected deployment command exited 0:
  `docker compose up -d --build upload-server cms-frontend`;
- upload-server and frontend were healthy after deployment;
- dependency-health returned `ok=true`, `blocking=false`;
- MinerU submit probe succeeded;
- admission circuit was closed;
- active/current/queued/takeover work was empty;
- Ollama `qwen3.5:9b` was resident and chat-ready;
- frontend `/cms/` returned HTTP 200;
- accepted Task 91 and Task 93 deployed markers were present in production containers;
- no upload, pressure test, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad rollback, sample mutation, L3, pressure PASS, or release-readiness claim was performed.

## Director Spot Check

Director independently performed a non-destructive runtime spot check after the report:

- production workspace: `main...origin/main`, local `docker-compose.override.yml` retained as expected;
- production HEAD: `50e5621 Review MinerU diagnostics and dispatch deployment`;
- `docker compose ps`: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy;
- upload health: `{"ok":true,"service":"upload-server"}`;
- admission circuit: closed;
- active-task endpoint: no active task, no current processing task, no queued tasks, no completed-but-not-ingested tasks, no drift tasks, no submit-retryable tasks, no takeover-required tasks;
- historical AI failures remained visible and were not repaired: `task-1778655375028`, `task-1778651226016`;
- frontend `/cms/`: HTTP 200;
- Ollama `/api/ps`: `qwen3.5:9b` resident;
- dependency-health with Ollama chat probe: `ok=true`, `blocking=false`, MinerU health OK, submit probe disabled for the Director spot check, last DevelopmentEngineer submit probe still recorded OK, Ollama `chatOk=true`, `keepAlive=24h`.

## Compose Dependency Note

The report correctly surfaces one operational caveat: although the authorized command targeted `upload-server` and `cms-frontend`, Docker Compose also rebuilt/recreated `cms-db-server` as a dependency side effect.

This is accepted for this task because:

- the exact Director-authorized command was used;
- no `docker compose down`, `down -v`, volume removal, prune, cleanup, rollback, or data mutation command was run;
- post-deployment DB/runtime health was green;
- no evidence indicates DB or MinIO data loss.

Future production deployment task briefs should keep this Compose dependency behavior explicit when frontend rebuilds may traverse `cms-db-server`.

## Remaining Boundary

This task only proves the accepted code paths are deployed and non-destructive runtime surfaces are currently healthy.

It does not prove:

- a new upload reaches a correct terminal state;
- the AI metadata job avoids the previous duplicate second-pass failure in production;
- the task page shows the improved terminal MinerU diagnostic on a live task;
- long-run or pressure behavior.

## Next Action

Director is issuing a separate scoped validation task:

`TASK-20260513-183148-P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes`

Assignee:
`TestAcceptanceEngineer`

Scope:
exactly one controlled upload from the known production test PDF source, with task-page/API observation of MinerU progress semantics and AI finalization behavior.

Still forbidden:
pressure test, second upload, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad restart/rollback, sample mutation, L3, pressure PASS, production-readiness, or release-readiness declaration.
