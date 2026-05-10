# Lucode Task: P0 Entry Circuit Production Deployment And Non-Destructive Runtime Validation

- Task ID: `TASK-20260510-154254-P0-Entry-Circuit-Production-Deployment-And-Non-Destructive-Runtime-Validation`
- Created At: `2026-05-10T15:42:54+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 下达待执行
- Director Authorization: `TASK-20260510-153154-P0-Entry-Circuit-Production-Deployment-Validation-Authorization`
- Related Accepted Code Task: `TASK-20260510-142045-P1-Entry-Circuit-And-Durable-Admission-State`

## Objective

Deploy the accepted P1 durable MinerU admission-circuit code to production, then perform only non-destructive runtime validation proving that the deployed runtime exposes and honors the new intake-safety surfaces.

This task is strictly narrow Option A. It does not authorize validation upload, pressure test, failed-task repair, release-readiness declaration, or any destructive production operation.

## Required Scope

1. Sync production deployment path `/Users/concm/prod_workspace/Luceon2026` to the accepted GitHub `main` HEAD that includes:
   - implementation commit `98339b6`;
   - Lucia review / decision ledger through current `origin/main`.
2. Preserve production-local `docker-compose.override.yml` semantics:
   - `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`;
   - `OLLAMA_API_URL=http://host.docker.internal:11434`;
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`;
   - `DISABLE_AI_SKELETON_FALLBACK=true`;
   - `ALLOW_AI_SKELETON_FALLBACK=false`;
   - MinIO console remains local-only bound, e.g. `127.0.0.1:19001:9001`.
3. Use only the minimum necessary Docker/Compose or service operation to apply the accepted upload-server code.
4. Run non-destructive runtime validation evidence:
   - deployed GitHub HEAD in production;
   - production override boundary summary without printing secrets;
   - `GET http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`;
   - `GET http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`;
   - active-task / queue state sufficient to state whether intake is safe;
   - Ollama `/api/ps` or equivalent read-only residency evidence;
   - CMS and upload-server reachability if needed to confirm the deployment.

## Required Checks

- `git status --short --branch` in development workspace before and after;
- `git fetch origin`;
- production workspace `git status --short --branch`;
- production workspace HEAD after apply;
- `git diff --check` for any repository changes made by this task;
- read-only curl or equivalent checks for the required runtime endpoints above.

## Forbidden Scope

- Do not create a validation upload.
- Do not run pressure tests.
- Do not repair, retry, mutate, or delete failed production tasks.
- Do not delete DB rows, MinIO objects, Docker volumes, logs, samples, or artifacts.
- Do not mutate secrets, models, timeouts, strict AI flags, MinIO console binding, or production override values.
- Do not perform broad stack restart, rollback, or unrelated service recovery.
- Do not claim production release readiness, L3, full-site acceptance, or manual pressure-test readiness.
- Do not treat ordinary `/health` green as sufficient; the report must include submit-probe and admission-circuit evidence.

## Required Report

Create:

`TaskAndReport/2026-05-10T15-42-54+0800_P0-Entry-Circuit-Production-Deployment-And-Non-Destructive-Runtime-Validation_REPORT.md`

The report must include:

- exact development `main` HEAD and production deployed HEAD;
- production override summary and preserved boundaries;
- exact command/check evidence, including exit codes or HTTP status;
- dependency-health submit-probe result;
- admission-circuit result;
- active-task/queue state;
- Ollama `/api/ps` or equivalent evidence;
- whether production runtime is ready for the next Director decision;
- explicit skipped/forbidden items.
