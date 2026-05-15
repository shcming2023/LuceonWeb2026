# DevelopmentEngineer Report: P1 Dependency Health Timing Semantics Production Deployment And Read-Only Validation

- Task ID: `TASK-20260515-093631-P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation`
- Task brief: `TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_TASK.md`
- Role: `DevelopmentEngineer`
- Report time: `2026-05-15T10:02+0800`

## Scope

This work was based on the Director task brief above, the Task 164 Director review, and the Task 165 user Option A decision.

Objective completed: production was fast-forwarded to a GitHub main descendant containing accepted commit `d3c9952`, `upload-server` was rebuilt/restarted with the minimum allowed Compose command, and read-only runtime validation confirmed `/ops/dependency-health` exposes the new Ollama timing/readiness fields.

No upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim was performed or made.

## Required Reading

Completed:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- this task brief
- Task 164 report and Director review
- Task 165 decision file

Note: the shared development workspace is dirty, so the report and task-row update were written in a clean temporary GitHub sync clone at `/tmp/luceon-task166-check`. The active DevelopmentEngineer role file was read from the shared development workspace because the temporary clone's GitHub snapshot still contains older historical role files.

## Branch / HEAD

Development workspace:

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD: `005ca96 Hold Task 108 auto progress on GitHub sync`
- Status: dirty shared role workspace; not used for report/ledger writeback.

Report workspace:

- Path: `/tmp/luceon-task166-check`
- Branch: `main`
- HEAD before report edits: `1716add Dispatch dependency health production validation`

Production:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Branch before deploy: `main`
- HEAD before deploy: `91c1352 Authorize pressure semantics production deployment`
- HEAD after deploy: `1716add Dispatch dependency health production validation`
- `d3c9952` containment: `git merge-base --is-ancestor d3c9952 HEAD` exited `0`.

## Production Preflight Evidence

Preflight before deployment:

- Production `git status --short --branch`: `## main...origin/main` plus the known Task 163 local-boundary files:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`
- Production `git log -1 --oneline`: `91c1352 Authorize pressure semantics production deployment`
- `docker compose ps`: `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` were all `healthy`.
- Frontend `/cms/` HTTP status: `200`
- Upload health: `{"ok":true,"service":"upload-server"}`
- Dependency health before deploy: `ok=true`, `blocking=false`; Ollama was healthy but did not yet expose the new readiness/timing fields.
- MinerU admission circuit: `open=false`, `state=closed`, active-task clean.
- Active task diagnostics: no active task, no queued tasks, no completed-but-not-ingested tasks, no drift tasks, no submit-retryable tasks, no takeover-required tasks; only historical AI failures were listed.
- Direct MinerU `/health`: `status=healthy`, `queued_tasks=0`, `processing_tasks=0`.

Preflight did not find active parse/AI/MinerU work, open MinerU admission, parse/upload dependency blocking, unhealthy core Docker services, unhealthy direct MinerU, or unrelated production changes that blocked fast-forward.

## Deployment Commands

| Command | Exit | Evidence |
| --- | ---: | --- |
| `git fetch origin` in development workspace | interrupted after hanging | The shared dirty workspace fetch did not complete; no local worktree files were changed. Remote was then confirmed with a clean clone. |
| `git ls-remote origin refs/heads/main` in development workspace | 0 | Remote main: `1716add7649fb08c44a50b34b824da1a006f3208`. |
| `git clone --depth=1 https://github.com/shcming2023/Luceon2026.git /tmp/luceon-task166-check` | 0 | Clean report workspace created at `1716add`. |
| `git fetch origin` in production | 0 | Updated production `origin/main` from `91c1352` to `1716add`. |
| `git pull --ff-only origin main` in production | 0 | Fast-forwarded `91c1352..1716add`; no merge commit. |
| `docker compose up -d --build upload-server` in production | 0 | Built `luceon2026-upload-server`; recreated only `cms-upload-server`; `cms-minio` was waited healthy as dependency. |

No `docker compose down`, volume cleanup, prune, Docker data cleanup, broad restart, rollback, upload, repair, retry, reparse, or re-AI command was run.

## Post-Deploy Read-Only Validation

Production after deployment:

- `git log -1 --oneline`: `1716add Dispatch dependency health production validation`
- `git status --short --branch`: `## main...origin/main` plus the same known local-boundary dirty files.
- Code markers present in `server/upload-server.mjs`:
  - `recommendedDependencyHealthClientTimeoutMs`
  - `annotateOllamaReadiness`
  - `readinessState`
  - `recommendedClientTimeoutMs`
  - `coldStartChatSucceeded`

Runtime checks:

- `docker compose ps`: all core services healthy; `cms-upload-server` recreated and healthy.
- Upload health: `{"ok":true,"service":"upload-server"}`
- `/cms/` HTTP status: `200`
- `/cms/tasks` HTTP status: `200`
- Dependency health: `ok=true`, `blocking=false`
- MinerU admission circuit: `open=false`, `state=closed`
- Active-task diagnostics: no active task, no queued tasks, no completed-but-not-ingested tasks, no drift tasks, no submit-retryable tasks, no takeover-required tasks.
- Direct MinerU `/health`: `status=healthy`, `queued_tasks=0`, `processing_tasks=0`

MinerU submit-probe was not used after deployment because active-task/admission/direct-health evidence was already safe and the task did not require a submit-probe.

## Dependency Health Ollama Fields Observed

Production `/ops/dependency-health` returned the following `dependencies.ollama` timing/readiness fields after deployment:

```json
{
  "ok": true,
  "blockingParse": false,
  "blockingAi": false,
  "readinessBlocking": false,
  "readinessState": "resident-chat-succeeded",
  "readinessSeverity": "info",
  "timingNote": "Ollama model was resident before chat and responded in 504ms.",
  "probeTimeoutMs": 15000,
  "recommendedClientTimeoutMs": 20000,
  "warmState": "resident-before-chat",
  "failureKind": null,
  "modelResident": true,
  "chatOk": true,
  "coldStartChatTimeout": false,
  "warmChatTimeout": false,
  "durationMs": 504
}
```

`coldStartChatSucceeded` was not present in this observed response because the model was already resident before chat (`warmState=resident-before-chat`). The absence is expected for this specific resident success case.

## Skipped Checks

- No PDF upload or fresh validation was run because the task explicitly forbids uploads and pressure/batch/soak/fresh serial validation.
- No cleanup, cancel, repair, retry, reparse, or re-AI was run because all are explicitly forbidden.
- No MinerU submit-probe was run post-deploy because read-only active-task/admission/direct-health evidence was clean and the task says not to use it unless active-task/admission evidence says it is safe.
- No frontend rebuild was run because the accepted change is in `server/upload-server.mjs`, and the task preferred the minimum `docker compose up -d --build upload-server`.
- No GitHub push was performed because the DevelopmentEngineer task authorizes local report and row update, not remote push.

## Risks / Blockers / Residual Debt

- The production worktree remains dirty with the known Task 163 local-boundary files. This did not block fast-forward. No cleanup or normalization was performed.
- The report/ledger update is in the clean temporary clone rather than the shared dirty development workspace. Director may need to integrate or synchronize these artifacts.
- Runtime validation observed the resident-model success path. The cold-before-chat slow-success branch remains code/test-covered but was not naturally observed in this production read-only check because `qwen3.5:9b` was resident.
- This is scoped runtime evidence for dependency-health timing semantics only. It is not a production-readiness, release-readiness, L3, pressure PASS, or go-live claim.

## Director Review Needed

Yes. Director should review this production deployment/read-only validation report, decide acceptance or correction, and decide whether the next release-readiness blocker should be AI residual disposition policy or rollback/error-path evidence.
