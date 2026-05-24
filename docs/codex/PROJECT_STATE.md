# Luceon2026 Project State

Last updated: 2026-05-24

## 1. Current Milestone

Milestone: `6.9.1`

Purpose: preserve the current working mainline after the fresh 24-PDF validation sequence, then continue the two-role Luceon/Lucode development stage with local dual-thread worktree isolation.

Rollback anchor: Git tag `v6.9.1`.

## 2. Current Mainline

The current Phase 1 mainline is:

`upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`

Current dependency shape:

| Dependency | Current role |
| --- | --- |
| Frontend | React/Vite SPA under `/cms`; `/cms/tasks` is the main workbench |
| Upload/API | Express upload server behind `/__proxy/upload` |
| Data API | Express JSON DB server behind `/__proxy/db` |
| Storage | Docker MinIO |
| Parser | Local conda MinerU FastAPI, normally reached by containers through `http://host.docker.internal:8083` |
| AI | Host Ollama, required model `qwen3.5:9b` |
| Strict AI mode | Skeleton fallback must not be represented as real AI recognition |

Online MinerU remains compatibility-only unless explicitly reactivated by future project direction.

## 3. 6.9.1 Evidence Boundary

The user has classified the main process as basically running through.

Most recent accepted evidence before this cleanup:

- Task 205 fresh 24-PDF run reached terminal backend state.
- 24/24 MinerU parses completed.
- 23/24 tasks/materials/AI jobs reached `review-pending` / `reviewing`.
- 1/24 item failed in AI stage after successful MinerU completion.
- Direct MinerU final state was healthy with no queued or processing tasks and no MinerU failures.
- Admission circuit was closed.
- Active-task diagnostics were clean.
- The new progress semantics avoided falsely declaring failure while direct MinerU API/log evidence still showed progress.

Boundary: this is a 6.9.1 milestone and rollback anchor. It is not a blanket production-readiness, L3, release-readiness, production上线, or go-live declaration.

## 4. Non-Blocking Residuals

These are known residuals but do not block the 6.9.1 milestone:

- One AI-stage failure from the 24-PDF run is manually retry eligible, but retry/re-AI is not performed by this cleanup.
- MinerU log-channel ownership/freshness diagnostics still have an observability gap: host logs can be fresh while the configured/container log channel appears stale.
- CleanService / Mineru2Table work remains future direction only and is not part of the active milestone. The PRD v0.4 architecture contract establishes the next direction as the `PDF -> Raw Material -> Clean Material` durable asset chain (Raw Material as prerequisite, Mineru2Table as prep, RawMaterial2CleanMaterial as final cleaning).
- Broader release hardening, rollback rehearsal, security review, and multi-user boundaries remain future work.

## 5. Collaboration State

As of 2026-05-16, the previous Director/ProductManager/Architect/DevelopmentEngineer/TestAcceptanceEngineer workflow is dissolved by user decision.

As of 2026-05-24, Lucode is no longer treated as an external IDE workspace. The active collaboration model is two local threads/worktrees with separate ignored private role prompts.

The active next-stage model is:

| Role | Environment | Responsibility |
| --- | --- | --- |
| `Luceon` | `/Users/concm/prod_workspace/Luceon2026` | Director + Architect + TestAcceptanceEngineer responsibilities: planning, task briefs, architecture review, task-ledger ownership, report review, validation, production deployment coordination, milestone records |
| `Lucode` | `/Users/concm/Dev_workspace/Luceon2026` | DevelopmentEngineer + ProductManager responsibilities: product refinement, implementation, local developer checks, branch/report creation |

The shared control plane is GitHub `main` plus task/report branches in `https://github.com/shcming2023/Luceon2026`.

Initial Lucode triggering is manual: after Luceon issues or returns a task, the user sends `Lucode, check task` in the Lucode thread. A heartbeat automation may be added later only after the manual flow is stable.

Lucode handoff is branch-local until Luceon review: Lucode pushes a `lucode/<task-id-or-short-slug>` branch whose ledger row may say `Next Actor=Luceon` while `origin/main` still says `Next Actor=Lucode`. Luceon `check task` must inspect that matching remote branch before concluding there is no Luceon task.

Luceon may explicitly use Codex subagents for bounded exploration, tests, log analysis, evidence extraction, or review assistance when the user authorizes subagent or parallel-agent work for the current task. Subagents are internal Luceon helpers, not project roles or task-ledger actors.

Archived workflow material:

- `archive/team-model-retired-2026-05-16/`
- `archive/legacy-roles-2026-05-15/`
- `archive/phase1-governance-2026-05-11/agents-workflows/`

`TaskAndReport/` is active for the Luceon/Lucode workflow and remains the historical evidence registry.

## 6. Current Repository Hygiene Boundary

The 6.9.1 cleanup:

- retires active role/collaboration docs from the active docs tree,
- preserves historical tasks, reports, reviews, decisions, and technical documents,
- refreshes current entrypoint docs for the post-6.9.1 state,
- does not mutate production runtime, production data, MinIO objects, Docker volumes, DB rows, models, secrets, or local sample files.

## 7. Current Next Step

No feature task is active at the time this role model is recorded.

Future work should begin from a user goal or `check task` against GitHub-synchronized `TaskAndReport/TASK_TRACKING_LIST.md`. Do not infer that archived role files or pre-6.9.1 historical rows are active instructions.
