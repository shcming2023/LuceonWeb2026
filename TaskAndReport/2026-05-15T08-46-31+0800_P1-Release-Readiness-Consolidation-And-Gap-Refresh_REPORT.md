# Architect Report: P1 Release Readiness Consolidation And Gap Refresh

- Task ID: `TASK-20260515-084631-P1-Release-Readiness-Consolidation-And-Gap-Refresh`
- Task brief: `TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_TASK.md`
- Role: `Architect`
- Report time: `2026-05-15T08:55+0800`
- Recommendation boundary: `CONDITIONAL_GO_AFTER_SPECIFIC_TASKS`

## Scope And Required Reading

This report is based on a Director task brief and the user-approved Option A decision after pressure-semantics acceptance.

Required reading was completed: `AGENTS.md`, `docs/codex/TEAM_CONTRACT.md`, `docs/codex/roles/architect.md`, `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, `docs/prd/Luceon2026-PRD-v0.4.md`, `docs/prd/Luceon2026-Stability-PRD-v0.1.md`, `docs/codex/TEST_POLICY.md`, `docs/codex/REPOSITORY_STRUCTURE.md`, `TaskAndReport/README.md`, `TaskAndReport/TASK_TRACKING_LIST.md`, Task 157 task/report/review, Task 159 task/report/review, Task 160 task/report/review, and this task brief.

No upload, pressure/batch/soak/fresh serial validation, cleanup, repair, retry, reparse, re-AI, destructive mutation, service/config/secret/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

## Read-Only Checks Performed

Development workspace:

- `git status --short --branch`: exit `0`; branch `development-engineer/p0-post-validation-ollama-mineru-blockers`, dirty shared role workspace.
- `rg`/`sed` reads of task ledger, project docs, reports, decisions, and reviews.

Production workspace:

- `git status --short --branch && git log -1 --oneline && docker compose ps`: exit `0`; HEAD `91c1352 Authorize pressure semantics production deployment`; core services healthy.
- `git diff --stat` / `git diff --name-only` for known local modified files: exit `0`.
- `GET /__proxy/upload/health`: HTTP `200`, `ok=true`.
- `GET /__proxy/upload/ops/dependency-health?ollamaChatProbe=true`: a 10s read-only client window timed out once; a 25s read-only window later returned HTTP `200`, `ok=true`, `blocking=false`, duration about `14157ms`, with Ollama chat OK after cold-before-chat.
- `GET /__proxy/upload/ops/mineru/admission-circuit`: HTTP `200`, circuit closed.
- `GET /__proxy/upload/ops/mineru/active-task`: HTTP `200`, no active/current/queued/takeover tasks; historical AI failures remain listed.
- Direct MinerU `/health`: HTTP `200`, healthy, `queued_tasks=0`, `processing_tasks=0`, `failed_tasks=0`.
- `/cms/` and `/cms/tasks`: HTTP `200`.

## Accepted Evidence Matrix

| Area | Accepted evidence | Current boundary |
| --- | --- | --- |
| Mainline flow | Current Phase 1 mainline remains upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review. | This report does not declare release readiness. |
| Code/test | Task 157 accepted at code/test level: AI failure classification, manual-only retry eligibility, MinerU progress truth semantics, pressure outcome semantics. Director reran focused smokes, TypeScript, build, and diff checks. | Broader dashboard/reporting adoption is not fully productized. |
| Production deployment | Task 159 accepted scoped production deployment/read-only validation. Production fast-forwarded to `91c1352`, target commit `2b59ef4` present, services healthy after `docker compose up -d --build upload-server cms-frontend`. | Compose also recreated DB/upload/frontend; acceptable evidence, but operational blast radius should stay visible. |
| Runtime health | Task 160 and current checks show upload health OK, MinerU idle/healthy, admission circuit closed, CMS routes 200, Docker services healthy. | dependency-health can exceed 10s because Ollama chat probe may cold-start; this is a readiness-observation gap. |
| Controlled uploads | Recent bounded one-upload validations reached `review-pending` with MinerU completed, parsed artifacts present, and AI analyzed. | No fresh upload was run in this task. |
| Pressure window | Latest accepted semantics classify the 24-task pressure window as mixed outcomes: `21 review-pending/review`, `3 failed/ai`, not systemic whole-run failure. | This is not pressure PASS or L3. It proves semantics and substantial throughput, with AI residuals visible. |
| AI/Ollama | Strict no-skeleton fallback remains preserved; Ollama `qwen3.5:9b` can be resident/chat OK; AI residual failures are classified as manual-only retry candidates. | Three AI residual failures remain unrepaired and unretried by design. Long metadata/repair generation under pressure remains a capacity risk. |
| MinerU | MinerU direct health currently healthy/idle; previously active pressure residue completed and is now visible as `review-pending/review`. Runtime progress semantics now distinguish remote processing from terminal failure. | Long-running MinerU progress observability is better, but no dedicated pressure dashboard exists. |
| MinIO/DB/frontend | Recent browser/read-only evidence shows task list/detail render correctly, no relevant db-sync warnings, no failed fetch, no HTTP 5xx, and task counts align. | Production has local source drift in DB/frontend-adjacent files that must be classified before a final release decision. |

## Current Release Blockers

1. Production source/runtime drift is not closed.
   - Production has six local modified files: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`.
   - Some diffs appear line-ending-only, but `docker-compose.override.yml` contains meaningful local runtime override changes.
   - Final release-readiness cannot rest on an unclassified dirty production tree.

2. dependency-health still has an operator-readiness timing gap.
   - A 10s read-only client check timed out.
   - A 25s check later passed after about `14157ms`, with `warmState=cold-before-chat` and Ollama chat OK.
   - This is not a service-down finding, but it means the readiness surface is not yet crisp enough for a final go/no-go screen without caveat.

3. AI residual disposition is unresolved.
   - The three pressure-window `failed/ai` tasks are now correctly classified as AI residuals/manual retry candidates.
   - They have not been repaired, retried, re-AIed, or owner-dispositioned.
   - A release decision can allow known AI residuals only if Director/User explicitly accepts that product boundary.

4. Release-level operating evidence remains incomplete.
   - Current evidence is strong for local production key path and mixed pressure semantics.
   - Release-grade rollback/recovery rehearsal, full error-path matrix, and clean production-source boundary review are still missing or stale.

## Non-Blocking Residual Debt / Polish

- Failed-AI detail copy remains understandable but generic: `需排查或重试`. This is polish unless Director/User want stricter operator copy before release.
- No dedicated pressure-batch summary dashboard exists. Current evidence comes from task counts, rows/details, DB summary, and runtime diagnostics.
- Stream/eventsource navigation teardown noise has appeared in browser checks but is already classified separately from non-stream failures.
- `classifyPressureRunOutcome()` and MinerU runtime truth helpers are accepted focused contracts; broader persistent reporting fields can be later hardening.

## Production Source / Runtime Drift Classification

| File | Observed diff type | Classification |
| --- | --- | --- |
| `.gitignore` | Appears line-ending-only in read-only diff. | Low functional risk, but should be normalized or consciously accepted before release packaging. |
| `docker-compose.override.yml` | Meaningful local override: strict AI env and MinIO console local-only binding. | Expected production-local override boundary, but it must be explicitly recorded as part of release environment truth. |
| `server/db-server.mjs` | Diff appears mostly line-ending-only around existing body/settings handling. | Needs follow-up confirmation; not a current runtime failure, but dirty backend source is a release-boundary risk. |
| `server/tests/worker-smoke.mjs` | Appears line-ending-only in test file. | Low runtime risk, but should not remain unexplained in release source tree. |
| `src/app/components/BatchUploadModal.tsx` | Appears line-ending-only around existing upload error handling. | Low functional risk from diff shown, but frontend source drift still needs classification. |
| `src/app/pages/SourceMaterialsPage.tsx` | One-line apparent line-ending diff around `/ai/analyze` fetch. | Low functional risk, but should be normalized/classified before readiness. |

Architect judgment: these files did not block Task 159/160 scoped acceptance, but they do block a clean `READY_FOR_USER_RELEASE_DECISION` recommendation because release readiness needs reproducible source/runtime truth.

## Go / No-Go Boundary

Recommendation: `CONDITIONAL_GO_AFTER_SPECIFIC_TASKS`

Reasoning:

- Not `NO_GO`: the deployed production runtime is reachable, services are healthy, mainline evidence is materially stronger, pressure semantics are corrected, and the pressure window is now understood as mixed task outcomes rather than systemic failure.
- Not `READY_FOR_USER_RELEASE_DECISION`: production source drift remains open; dependency-health has a 10s-vs-14s timing caveat; AI residual disposition and release-level rollback/error-path evidence remain unresolved.

Specific next tasks recommended:

1. `DevelopmentEngineer` or `Director`: production source-drift classification and release override boundary record.
   - Acceptance: each of the six dirty files is classified as expected override, line-ending-only normalize candidate, committed source change, or blocker; no unclassified production source drift remains.

2. `DevelopmentEngineer`: dependency-health readiness timing semantics hardening.
   - Acceptance: readiness endpoint distinguishes cold-before-chat but ultimately OK from hard failure; monitoring/client timeout expectations are documented or adjusted; existing dependency-health smokes pass.

3. `ProductManager` or `Director`: AI residual release policy decision.
   - Acceptance: user-facing boundary is explicit: known `failed/ai` residuals may remain as manual retry candidates, or must be handled before release.

4. `TestAcceptanceEngineer`: final read-only release-candidate preflight after tasks 1-3.
   - Acceptance: clean source/override state, core services healthy, canonical health within accepted timing, active-task idle, representative task list/detail still coherent, no readiness claim by the role.

Optional before go-live but recommended for a stronger release posture:

- rollback/recovery rehearsal;
- explicit error-path matrix for upload/MinerU/Ollama/MinIO/DB;
- pressure summary dashboard or durable batch-summary report surface.

## Forbidden Operations Confirmation

This Architect task did not perform upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, service start/stop/restart/rebuild/deploy/rollback, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, PRD truth/role contract/project-state/handoff edits, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness claim.

## Recommended Next Actor

`Director`

Director should review this consolidation and decide whether to dispatch the source-drift/override-boundary task first. That is the most concrete blocker between current evidence and a later user release decision.
