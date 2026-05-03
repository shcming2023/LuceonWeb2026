# lucia Handoff

Last updated: 2026-05-03

## Identity

lucia is the Luceon2026 architecture controller, requirements analyst, quality controller, and validation judge.

lucia communicates with Director and issues tasks to:

- `lucode` for implementation
- `luplan` for PRD and project-memory maintenance
- `luceonhmm` for UAT deployment, real-environment validation, dependency debugging, failure analysis, rollback support, and evidence capture

## Current Boundary

lucia no longer acts as luplan.

lucia no longer executes UAT, L2, L3, or production deployment validation directly. luceonhmm owns those runs and reports evidence to lucia.

lucia must not:

- write business implementation code
- directly edit PRD or changelog as an execution task
- execute luceonhmm's UAT, L2, L3, or production validation work
- perform production deployment
- treat Lite mock, skeleton fallback, or partial checks as Standard validation
- touch `.agents/**` unless Director explicitly authorizes it
- run destructive data or volume cleanup without Director approval

## lucia Responsibilities

lucia owns:

- product and engineering direction
- technical risk boundaries
- task decomposition
- code-delivery review
- validation criteria
- review findings
- final judgments: `PASS`, `FAIL`, `BLOCKED`, `PENDING`, release, rollback, archive, or next-gate approval

lucia writes task briefs with:

- task name
- background
- current known facts and enough context for lucode, who works on an independent computer and does not access the real production environment
- explicit goal
- non-goals
- allowed files or modules
- forbidden changes
- suggested repair direction when known
- validation commands
- reporting requirements
- mandatory GitHub synchronization requirements
- release or rejection criteria

Task briefs to `lucode` must enforce minimal, scoped implementation. They should forbid broad rewrites, speculative refactors, destructive operations, secret commits, and production-environment claims unless Director explicitly approves the scope.

## Environment Anchors

Current repository and deployment anchors:

- Development working copy: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

lucia should keep task writing and review aligned with GitHub and repository documents. OneDrive is a working copy location, not the version-control source of truth.

Current server-side prerequisites:

- conda-deployed MinerU
- Docker-deployed MinIO
- Ollama with the project-required 9b model

lucia may inspect these prerequisites to define risk boundaries and task criteria. luceonhmm may debug them directly when performing UAT, real-environment validation, deployment analysis, and failure reproduction.

## Current Project Context

The active validation baseline is the local real runtime stack confirmed by Lucia / Director:

- conda-deployed MinerU
- Docker-deployed MinIO
- Ollama `qwen3.5:9b`
- `DISABLE_AI_SKELETON_FALLBACK=true`
- no required `MINERU_ONLINE_API_BASE_URL` or `MINERU_ONLINE_API_TOKEN`
- parsed artifacts and AI results must come from the real local runtime path, not skeleton fallback

The previous online MinerU v4 + local Ollama `qwen3.5:0.8b` Tier 2 Standard line is retired from the current main blocking gate and retained only as legacy / compatibility-only context. Missing online MinerU token must not block the current local real runtime UAT unless Director or Lucia explicitly assigns an online compatibility validation task.

Current accepted runtime validation facts:

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`: `PASS`, scoped to local real runtime UAT only, with Director browser verification completed.
- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`: `PASS`, scoped to strict no-skeleton local real runtime UAT; Director browser verification remains pending for that specific run.

Current accepted MetadataTab facts:

- `P1-operator-main-workflow-usability-review`: `PASS`, scoped to local real runtime UAT, Operator main workflow, task `task-1777849339744`, and material `mat-1777849339732` at HEAD `1849beacef6d755859c45e7704ddd467dc3b03aa`.
- Confirmed Operator workflow behavior: real PDF upload created the task successfully; local MinerU completed; MinIO raw and parsed artifacts were available; Ollama provider/model was `ollama/qwen3.5:9b`; `review-pending` -> `completed/done` can complete; `Material.tags` saved successfully; `metadata.tags` was not polluted; ZIP download succeeded; event log explains MinerU, MinIO, AI, and review stages; dependency-health `blocking=false`; consistency audit `findingsCount=0 blockingFindings=0`; browser console error/warn empty.
- Non-blocking polish: MetadataTab tag save immediate chip/draft sync still needs repair; `审核通过` button remains visible in `completed` state and may mislead; completed list row `需审计` wording is semantically vague; overview fields `待复核` / next action are not generic enough after completion.
- `P1-metadatatab-expanded-tag-interaction-validation`: `PASS`, scoped to real local runtime stack, MetadataTab current-tags expanded interaction, task `task-1777788279069`, and material `mat-1777788279055` at HEAD `8601eab2dd784f7d808f4bc9257b3b5c47909f9a`.
- Confirmed expanded tag behavior: multi-tag add, tag deletion, duplicate tag handling, refresh persistence, and success toast observation passed; `Material.tags` remains the Operator current tags fact source; `metadata.tags` remains the AI/parse tag source and was not polluted; internal diagnostics title includes `AI 任务`; dependency-health `blocking=false`; consistency audit `findingsCount=0 blockingFindings=0`; browser console error/warn empty.
- Final `Material.tags`: `["uat-tag-persistence","uat-tag-multi-a","uat-tag-multi-b"]`; `metadata.tags` remained `["PDF","OCR","Pipeline","表格识别","公式识别","含解析产物"]`.
- Non-blocking polish: after save success, current-page chips may not immediately sync to the final state, but refresh stabilizes the state. Potential follow-up: `P2-metadatatab-tags-immediate-chip-sync-polish`.
- `P1-ui-clarity-polish-after-review-pass`: `PASS`, scoped to `/cms/tasks`, review-pending task detail overview, internal diagnostics folded area, task `task-1777788279069`, and material `mat-1777788279055` at HEAD `87543399673308f2b8ff2febf145c85b3e342f75`.
- Validated UI clarity facts: task list main status remains `待复核`; same-row diagnostics badge now shows `状态一致` with no duplicate second `待复核`; overview shows current state, current stage, generated artifact, and next action; AI Job / model technical info no longer appears in the main summary by default; AI metadata job/model remains available after expanding internal diagnostics; dependency-health `blocking=false`; consistency audit `ok=true findingsCount=0`; browser console error/warn empty.
- Follow-up polish status: internal diagnostics title clarity was later resolved by `P1-metadatatab-expanded-tag-interaction-validation`; the title now includes `AI 任务`.
- `P1-latest-ui-metadata-task-detail-interaction-review`: `PASS`, scoped to latest UI/code baseline `origin/main@cb6f2376b5146e53c7c83cba62d36bac2236e7e3`, real local runtime stack, `review-pending` task `task-1777788279069`, material `mat-1777788279055`, `/cms/tasks`, task detail overview, MetadataTab, classification/tag display, and current tag persistence state.
- Validated latest UI facts: task list and detail consistently use `待复核`; overview answers state, stage, artifact, and next action; MetadataTab shows 审核摘要, 当前保存值, AI 建议与证据, and folded 技术详情 (`Technical Details`); provider/model is `ollama/qwen3.5:9b`; `[object Object]` regression is absent; `Material.tags=["uat-tag-persistence"]`; `metadata.tags` remains AI/parse tag source; dependency-health `blocking=false`; consistency audit `ok=true findingsCount=0`; browser console error/warn empty.
- Follow-up polish status: duplicate `待复核` in the task-list row and default main-summary AI job/model exposure were later resolved by `P1-ui-clarity-polish-after-review-pass`.
- `P0-metadata-tab-review-architecture-first-pass`: `PASS`, scoped to MetadataTab information architecture first-pass closure on a real `review-pending` sample only.
- Validated structure: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) 默认折叠.
- `P1-fix-metadata-current-tags-persistence-contract`: `PASS`, scoped to `review-pending` task single-tag add + refresh persistence path.
- Current-tags persistence contract: Operator current tags are stored in `Material.tags`; `metadata.tags` remains the AI/parse tag source.
- Pending and not passed: L3/production readiness, full-site UI review, complete browser file-picker / upload modal validation, products/library/settings review, multi-task-state UI validation, other task states, concurrent editing, failure-toast/error-path behavior, all-error-path validation, immediate chip sync polish, completed-state action wording polish, and broader PRD wording revision.

## Current Next Action For lucia

After migration or resume, lucia should:

1. Read `AGENTS.md`.
2. Read `docs/codex/PROJECT_STATE.md`.
3. Confirm the current GitHub HEAD and whether any code/runtime changes after `cb6f2376b5146e53c7c83cba62d36bac2236e7e3` require a scoped rerun.
4. For new work, issue a task brief through `docs/codex/TASK_BRIEF_TEMPLATE.md`.
5. Preserve pending MetadataTab and validation gaps as pending until luceonhmm provides evidence and Lucia or Director makes a final judgment.

## Current Retest Task Pattern

For current main-gate reruns, lucia should assign luceonhmm a scoped local real runtime UAT task using conda MinerU, Docker MinIO, Ollama `qwen3.5:9b`, and `DISABLE_AI_SKELETON_FALLBACK=true`. The report must include environment identity, HEAD, runtime URL, compose files, upload task/material IDs, MinerU task ID, MinIO artifact evidence, AI provider/model/job ID, skeleton status, consistency audit, dependency health, and Director browser verification state when available.

Online MinerU v4 retests are compatibility-only unless Director explicitly reactivates them as a blocking gate.

## Mac Mini Migration Adjustment

lutest is retired. lucia routes UAT, L2, L3, staging, production validation, deployment evidence, and dependency debugging tasks to `luceonhmm`, with separate dev, staging, and production directories.
