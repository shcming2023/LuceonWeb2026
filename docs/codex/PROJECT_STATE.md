# Luceon2026 Project State

Last updated: 2026-05-25

## 1. Current Milestone

Milestone: `6.9.1`

Purpose: preserve the current working mainline after the fresh 24-PDF
validation sequence, then continue closeout through the unified Luceon owner
workflow with strict development/production workspace separation.

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

As of 2026-05-25, the separate Lucode implementation role is retired for new
work. Luceon is the unified accountable owner for planning, requirements,
architecture, product, implementation, testing, acceptance, and scoped
production validation/deployment coordination.

The active next-stage model is:

| Workspace | Path | Responsibility |
| --- | --- | --- |
| Development | `/Users/concm/Dev_workspace/Luceon2026` | Business code, product implementation, developer checks, scoped implementation branches |
| Production/control | `/Users/concm/prod_workspace/Luceon2026` | Current truth, `TaskAndReport/`, acceptance evidence, mainline closure, deployment/runtime operations only when explicitly authorized |

The shared control plane is GitHub `main` plus `TaskAndReport/` in
`https://github.com/shcming2023/Luceon2026`.

New active task rows use `Next Actor=Luceon`, `User`, or `None`. Historical
Lucode rows, reports, reviews, and branches remain evidence records but are not
used for new dispatch or check-task branch handoff.

Luceon may explicitly use Codex subagents for bounded exploration, tests, log analysis, evidence extraction, or review assistance when the user authorizes subagent or parallel-agent work for the current task. Subagents are internal Luceon helpers, not project roles or task-ledger actors.

Archived workflow material:

- `archive/team-model-retired-2026-05-16/`
- `archive/legacy-roles-2026-05-15/`
- `archive/phase1-governance-2026-05-11/agents-workflows/`

`TaskAndReport/` is active for the unified Luceon workflow and remains the
historical evidence registry.

## 6. Current Repository Hygiene Boundary

The 6.9.1 cleanup:

- retires active role/collaboration docs from the active docs tree,
- preserves historical tasks, reports, reviews, decisions, and technical documents,
- refreshes current entrypoint docs for the post-6.9.1 state,
- does not mutate production runtime, production data, MinIO objects, Docker volumes, DB rows, models, secrets, or local sample files.

## 7. Current Next Step

Current active row:

- Task 280:
  `TASK-20260525-123633-P0-RawMaterial2CleanMaterial-Real-Artifact-Shape-Compatibility-MockSafe-ReadOnly-NoDBWrite-NoMinIOWrite-NoRuntimePost`
- `Next Actor=Luceon`
- Goal: make the artifact-backed RawMaterial2CleanMaterial draft consume real
  canonical v4 artifact body shapes after Task 279 fixed clean-bucket proxy
  reads.

Future work should begin from a user goal or `check task` against
GitHub-synchronized `TaskAndReport/TASK_TRACKING_LIST.md`. Do not infer that
archived role files, retired Lucode workflow docs, or pre-6.9.1 historical rows
are active instructions.
