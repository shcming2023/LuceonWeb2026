# Lucia Task Brief: P0 Sample 3 Controlled Production Recovery

Task:
P0 Sample 3 Controlled Production Recovery

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-09T05-20-30+0800_P0-Sample3-Controlled-Production-Recovery_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-09T00-43-45+0800_P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix_TASK.md
- TaskAndReport/2026-05-09T02-42-47+0800_P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix_LUCIA_REVIEW.md
- TaskAndReport/2026-05-09T05-20-30+0800_P0-Sample3-Production-Recovery-Authorization_LUCIA_REVIEW.md

Background:
Task 45 diagnosed sample 3 as stuck after local timeout: MinerU API reported completion and result availability, but Luceon production still showed task/material processing and no AI metadata job. Task 46 was accepted at code level and merged to main; the accepted fix handles completed-after-local-timeout takeover without creating a second MinerU task and explicitly writes final task metadata `mineruStatus='completed'`.

Current known facts:
- Target parse task: `task-1778249434820`
- Target material: `mat-1778249419780`
- Existing MinerU task: `ec9452cc-94e4-4b36-bb64-efba86f38cf6`
- Prior observed state: task `running` / `mineru-processing`, material processing, no AI metadata job.
- MinerU API prior state: `completed`; result ZIP available.
- Accepted code-level fix is on GitHub main by Lucia review commits.
- Director authorized scoped production recovery for this target only.

PRD / contract reference:
- Phase 1 mainline remains upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Strict no-skeleton fallback and no silent degradation remain mandatory.
- Production release readiness remains unclaimed.

Objective:
Recover only the stuck production sample 3 task/material by applying the accepted Task 46 fix if necessary and using the safest existing application recovery path so the existing completed MinerU result is ingested and the task advances to `ai-pending`, `review-pending`, or another clearly evidenced valid terminal/blocked state.

Non-goals:
- Do not create a new sample upload.
- Do not recover unrelated tasks.
- Do not re-submit the target file to MinerU if the existing MinerU task/result can be used.
- Do not declare production release readiness, staging readiness, L3, or full-site acceptance.
- Do not tune model, timeout, prompt, or AI configuration.
- Do not perform cleanup or deletion.

Allowed files, modules, or operations:
- Inspect development and production git state.
- Fast-forward/sync the production workspace to the accepted GitHub main only if required for the Task 46 fix to be present.
- Preserve production-local `docker-compose.override.yml` and strict AI/model settings unchanged.
- Perform the minimum necessary Docker/Compose operation to apply the accepted server-side fix, limited to affected service restart/rebuild/recreate as needed.
- Run existing read-only health checks and existing application recovery/resume paths.
- Recover only `task-1778249434820` / `mat-1778249419780` using the existing `mineruTaskId` `ec9452cc-94e4-4b36-bb64-efba86f38cf6`.
- Create normal runtime state transitions and artifacts that the existing application recovery path produces for this target task.

Forbidden changes:
- Do not broaden scope beyond this task brief.
- Do not modify secrets, model names, timeout settings, provider config, or production override values.
- Do not delete or prune DB rows, MinIO objects, Docker volumes, Docker images, logs, tasks, materials, artifacts, or sample files.
- Do not manually edit production DB JSON/state unless Lucia and Director explicitly authorize a separate emergency repair task.
- Do not overwrite or replace existing MinIO source objects.
- Do not create a new upload for sample 3.
- Do not create a second MinerU task for the same target if the existing completed MinerU result is available.
- Do not run broad deploy/rebuild/restart/rollback unrelated to applying the accepted Task 46 fix.
- Do not restore heuristic chapter preprocessing, skeleton fallback, or silent degradation.
- Do not claim production release readiness.

Suggested direction:
1. Sync GitHub state in the development workspace and confirm `origin/main` contains the accepted Task 46 fix.
2. Inspect production workspace HEAD, override boundary, active parse tasks, active AI jobs, CMS health, DB health, MinIO health, MinerU readiness, and Ollama dependency health before mutation.
3. If production code lacks the accepted fix, fast-forward/apply GitHub main in production and perform the minimum service action needed for the upload/task worker code to run.
4. Trigger or wait for the existing application recovery path to process only the target task.
5. Confirm the target continues using MinerU task `ec9452cc-94e4-4b36-bb64-efba86f38cf6` and does not create a replacement MinerU task.
6. Verify target task/material state after recovery and capture AI job/result status.
7. If recovery cannot proceed safely through existing code paths, stop and report blocked with exact evidence.

Required checks:
- `git status --short --branch` in development workspace before and after.
- `git fetch origin`.
- Production workspace HEAD before and after.
- Production override boundary check: strict AI/model settings unchanged and MinIO console remains local-only.
- Read-only CMS/DB/MinIO/MinerU/Ollama health or dependency-health checks appropriate to current production scripts.
- Target task/material read before and after recovery.
- Active MinerU/Ollama heavy-stage counts before/during/after if available.
- `git diff --check` for any repository file changes.

Required evidence:
- Commands run with exit codes.
- Production HEAD before/after and whether a service restart/rebuild/recreate occurred.
- Exact before/after state for `task-1778249434820` and `mat-1778249419780`.
- Confirmation whether `mineruTaskId` stayed `ec9452cc-94e4-4b36-bb64-efba86f38cf6`.
- Confirmation whether any new MinerU task was created.
- Parsed artifact / MinIO result evidence if ingestion succeeds.
- AI metadata job state and material review state if AI is triggered.
- Explicit list of forbidden operations not performed.

GitHub sync requirements:
- Before starting: `cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026; git status --short --branch; git fetch origin; git pull --ff-only origin main`.
- Before reporting: `git status --short --branch; git log -1 --oneline`.
- Commit and push to GitHub if repository files are changed and this task requires remote synchronization.

Completion report storage requirements:
- Write the completion report into `TaskAndReport/` using this naming rule: `YYYY-MM-DDTHH-MM-SS+0800_P0-Sample3-Controlled-Production-Recovery_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, current status, next actor, next action, and required output.
- Do not rely on Director chat relay for completion reporting.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- branch and HEAD
- files changed
- production operations performed
- commands run with exit codes
- checks skipped and reasons
- before/after runtime evidence
- risks, blockers, or residual technical debt
- GitHub sync status
- whether Lucia review, Director decision, or additional validation is required

Acceptance criteria:
- Target task/material is recovered to a valid next state using the existing completed MinerU result, or a clear safe-blocked report explains why recovery cannot proceed.
- No second MinerU submission is created for the target.
- Production override, strict AI/model config, secrets, Docker volumes, DB/MinIO data outside normal target recovery flow, and samples remain unchanged.
- No production release-readiness claim is made.

