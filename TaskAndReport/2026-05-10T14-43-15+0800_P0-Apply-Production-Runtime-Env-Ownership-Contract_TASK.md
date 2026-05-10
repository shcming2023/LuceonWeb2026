# Lucode Task: P0 Apply Production Runtime Env Ownership Contract

- Task ID: `TASK-20260510-144315-P0-Apply-Production-Runtime-Env-Ownership-Contract`
- Created At: `2026-05-10T14:43:15+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Lucia Review: `TaskAndReport/2026-05-10T14-43-15+0800_P0-Local-Production-Service-Ownership-Unification_LUCIA_REVIEW.md`
- Related P0 Task: `TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_TASK.md`

## Objective

Apply the accepted production runtime ownership env contract to the running production `upload-server` container, then prove endpoint truth is now explicit runtime env/compose truth rather than DB/settings-derived truth.

This is a narrow config-application step between P0 ownership unification and P1 entry-circuit work.

## Authorized Scope

Allowed:

- sync production workspace to current `origin/main` if clean except known local `docker-compose.override.yml`;
- preserve production-local `docker-compose.override.yml`;
- rebuild/recreate only `upload-server` if needed to apply compose env values;
- inspect running `cms-upload-server` env after redeploy;
- run read-only health/dependency/active-task checks;
- run `ops/runtime-ownership-status.sh`;
- report whether Task 70 can be activated.

Required runtime env values in the running `cms-upload-server` container:

- `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`
- `OLLAMA_API_URL=http://host.docker.internal:11434`
- `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- `DISABLE_AI_SKELETON_FALLBACK=true`
- `ALLOW_AI_SKELETON_FALLBACK=false`

## Required Checks

Before applying:

- development `git status --short --branch`;
- production `git status --short --branch`;
- production HEAD and `origin/main`;
- production `git diff -- docker-compose.override.yml`;
- inspect current `cms-upload-server` env for the five required variables;
- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`.

Apply:

- use the minimum necessary command, expected to be `docker compose up -d --build upload-server` after production sync, unless a narrower equivalent is available;
- do not restart MinerU, Ollama, MinIO, DB, frontend, or the broad Docker stack.

After applying:

- inspect running `cms-upload-server` env and confirm all five required values;
- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`;
- `bash ops/runtime-ownership-status.sh /Users/concm/prod_workspace/Luceon2026`;
- development `git diff --check`.

## Result Classification

Report one of:

- `RUNTIME_ENV_CONTRACT_APPLIED_READY_FOR_P1`: all required env values are present in running upload-server, health/dependency checks are non-blocking, and no forbidden mutation occurred.
- `RUNTIME_ENV_CONTRACT_APPLIED_BUT_BLOCKED`: env values are present, but health/dependency checks still block.
- `RUNTIME_ENV_CONTRACT_APPLICATION_BLOCKED`: scoped application could not be completed safely.

## Forbidden Scope

- Do not create validation uploads.
- Do not run pressure tests.
- Do not repair or reprocess failed tasks.
- Do not mutate DB rows, MinIO objects, Docker volumes, tasks, materials, artifacts, logs, samples, secrets, model/provider selection, timeout policy, or production override settings.
- Do not restart MinerU, Ollama, MinIO, DB, frontend, or broad Docker stack.
- Do not claim L3, production release readiness, or full-site acceptance.

## Required Report

Create:

`TaskAndReport/2026-05-10T14-43-15+0800_P0-Apply-Production-Runtime-Env-Ownership-Contract_REPORT.md`

Report must include:

- production path and HEAD before/after;
- local override summary;
- exact apply command;
- running upload-server env before/after;
- health/dependency/active-task evidence before/after;
- runtime ownership helper output summary;
- result classification;
- whether Lucia may activate Task 70;
- explicit no-release-readiness statement.

