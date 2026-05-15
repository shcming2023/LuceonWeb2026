# Task Brief: P1 Dependency Health Timing Semantics Production Deployment And Read-Only Validation

- Task ID: `TASK-20260515-093631-P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation`
- Created: 2026-05-15T09:36:31+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T09-29-17+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-Decision_DECISION.md`
- Based on Director review: `TaskAndReport/2026-05-15T09-29-17+0800_P1-Dependency-Health-Timing-Semantics-Hardening_DIRECTOR_REVIEW.md`
- Accepted GitHub main commit to deploy: `d3c9952 Accept dependency health timing semantics`

## Context

Task 164 was accepted at code/test level and integrated to GitHub main at `d3c9952`.

The accepted change hardens `/ops/dependency-health` Ollama semantics so the operator and validation scripts can distinguish:

- resident model chat success;
- cold-before-chat slow but successful probe;
- cold-start chat timeout;
- warm/resident chat timeout;
- chat HTTP failure;
- missing required model;
- tags/service reachability failures.

The accepted fields include:

- `readinessState`;
- `readinessSeverity`;
- `timingNote`;
- `probeTimeoutMs`;
- `recommendedClientTimeoutMs`;
- `blockingAi`;
- `readinessBlocking`;
- `coldStartChatSucceeded`.

The important contract is that Ollama/AI failures may block AI readiness, but must not be flattened into parse/upload blocking. `blockingParse` must remain false for Ollama-only issues.

Production still needs a scoped deployment and read-only validation before this fix can count as runtime evidence.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. This task brief
12. Task 164 report and Director review
13. Task 165 decision file

If the role file, this task row, Task 164 report/review, or Task 165 decision file is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial context.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- MinerU endpoint: `http://127.0.0.1:8083`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`

## Objective

Deploy the accepted Task 164 code to production with the minimum necessary production operation, then perform non-destructive read-only validation that production is healthy and `/ops/dependency-health` exposes the new Ollama readiness/timing semantics.

This task does not upload PDFs, run pressure tests, clean/repair/retry existing tasks, mutate MinerU/Ollama/MinIO data, or declare production readiness.

## Mandatory Preflight

Before any production deployment, run and record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- production `docker compose ps`;
- frontend `/cms/` HTTP status;
- upload health: `http://localhost:8081/__proxy/upload/health`;
- dependency-health without submit probe;
- MinerU admission circuit: `http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit`;
- active task diagnostics: `http://localhost:8081/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health`: `http://127.0.0.1:8083/health`.

Stop and write a blocked report if:

- active parse/AI/MinerU work exists and deployment would interrupt it;
- MinerU admission circuit is open;
- dependency-health is blocking for parse/upload dependencies;
- Docker core services are unhealthy;
- direct MinerU is unhealthy;
- production workspace has unrelated local changes that prevent a clean fast-forward;
- deployment would require broad restart/rollback, destructive mutation, cleanup/repair/reparse/re-AI, or any operation outside this brief.

Known production-local boundary from Task 163:

- `.gitignore`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, and `src/app/pages/SourceMaterialsPage.tsx` may appear dirty from EOL-only/no-semantic drift;
- `docker-compose.override.yml` may appear dirty as expected production-local override for strict AI env and MinIO console local-only binding.

Do not clean, normalize, delete, overwrite, or commit these production-local files. If they block fast-forward, stop and report the exact blocker.

## Allowed Operations

Allowed:

- in the production deployment path, run the GitHub sync commands necessary to fast-forward production to current `origin/main` containing commit `d3c9952` or a descendant containing it;
- rebuild/restart only the minimum service surface needed for `server/upload-server.mjs` dependency-health changes:
  - preferred command: `docker compose up -d --build upload-server`
- run non-destructive health/read-only checks after deployment;
- verify accepted code markers are present in production source:
  - `recommendedDependencyHealthClientTimeoutMs`
  - `annotateOllamaReadiness`
  - `readinessState`
  - `recommendedClientTimeoutMs`
  - `coldStartChatSucceeded`
- write the report and update the task row locally.

If `docker compose up -d --build upload-server` causes Compose to recreate dependent services automatically, record exactly what changed and verify service health afterward.

If production deployment requires also rebuilding another service for routing/static assets, stop and explain why. Do not broaden the deployment without Director review unless the required extra service is mechanically recreated by Compose as a dependency of the allowed command.

## Forbidden Operations

Forbidden:

- PDF upload or any fresh upload validation;
- pressure/batch/soak test or broader serial validation;
- cleanup, cancel, repair, retry, reparse, or re-AI for existing tasks;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem operations;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, prune;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring production readiness, release readiness, L3, pressure PASS, production上线, or go-live readiness.

## Post-Deploy Read-Only Validation

After deployment, record:

- production branch and HEAD before/after;
- whether commit `d3c9952` or a descendant containing it is present;
- `docker compose ps`;
- upload health OK;
- dependency-health non-blocking for parse/upload dependencies;
- full `dependencies.ollama` readiness/timing fields from dependency-health, including:
  - `readinessState`;
  - `readinessSeverity`;
  - `timingNote`;
  - `probeTimeoutMs`;
  - `recommendedClientTimeoutMs`;
  - `blockingAi`;
  - `readinessBlocking`;
  - `blockingParse`;
  - `warmState`;
  - `failureKind`;
  - `coldStartChatSucceeded` if present;
- MinerU admission circuit closed;
- active-task state and whether active parse/AI/MinerU work exists;
- direct MinerU `/health`;
- frontend `/cms/` and `/cms/tasks` HTTP 200.

Do not use MinerU submit-probe unless active-task/admission evidence says it is safe. If submit-probe is used, state why it was safe and record the result.

Do not upload or mutate runtime data during validation.

## Required Report

Write:

`TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`

The report must include:

- confirmation this work was based on this Director task brief;
- required reading completed;
- development branch/HEAD and production before/after HEAD;
- production preflight evidence;
- deployment commands and exit codes;
- post-deploy read-only validation evidence;
- exact dependency-health Ollama readiness/timing field values observed in production;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that no upload, pressure/batch/soak, cleanup/repair/reparse/re-AI, destructive mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

Update row 166 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
