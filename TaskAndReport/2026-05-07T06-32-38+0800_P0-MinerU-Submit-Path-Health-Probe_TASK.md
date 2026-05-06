# Task: P0 MinerU Submit-Path Health Probe

```text
Task:
P0 MinerU Submit-Path Health Probe

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T06-32-38+0800_P0-MinerU-Submit-Path-Health-Probe_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- TaskAndReport/TASK_TRACKING_LIST.md

Background:
Phase 1 governance identified TD-001: MinerU /health can report healthy while the actual /tasks submit path is unavailable in a half-failed MinerU runtime. Current backend dependency health primarily checks /health. This is insufficient for Tier 2 Standard and future production-readiness gates because the real pipeline depends on submitting parsing tasks to MinerU /tasks.

Current known facts:
- Current HEAD before assignment: c2df91665fe5a2bd7f32f51d9ff8fc26a66aaf90.
- Current Phase 1 mainline: /cms/tasks upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review.
- Existing dependency health endpoint: server/upload-server.mjs /ops/dependency-health.
- Existing Tier 2 Standard pre-check: scripts/tier2-standard-check.mjs.
- Existing focused smoke: server/tests/dependency-health-smoke.mjs.
- Existing deep real-runtime script: server/tests/mineru-deep-check.mjs.
- TD-001 remains open in docs/codex/PROJECT_STATE.md.

PRD / contract reference:
- docs/codex/PROJECT_STATE.md TD-001.
- docs/codex/TEST_POLICY.md L2 / Tier 2 Standard dependency-health requirements.
- docs/prd/Luceon2026-PRD-v0.4.md section 12.4 Tier 2 Standard验收.

Objective:
Add an explicit MinerU submit-path dependency probe so Standard readiness can detect the case where MinerU /health is OK but POST /tasks is unavailable, failing, timing out, or returning no task id.

Non-goals:
- Do not implement Retry/Reparse/Re-AI APIs.
- Do not implement SSE.
- Do not refactor upload-server.mjs broadly.
- Do not change MinerU online compatibility behavior.
- Do not change AI skeleton fallback semantics.
- Do not update PRD truth, PROJECT_STATE, HANDOFF, or role contracts. Lucia will update project ledger after review and acceptance.

Allowed files, modules, or operations:
- server/upload-server.mjs
- scripts/tier2-standard-check.mjs
- server/tests/dependency-health-smoke.mjs
- .env.example, only if a new environment variable is introduced
- docs/codex/TEST_POLICY.md, only if command semantics or validation policy text must be clarified
- TaskAndReport/TASK_TRACKING_LIST.md, only to add report path, branch, and HEAD after execution
- TaskAndReport/*_REPORT.md, only for the completion report

Forbidden changes:
- Do not broaden scope beyond this task brief.
- Do not perform broad rewrites or framework-level refactors.
- Do not change unrelated files.
- Do not change PRD truth, project ledger facts, role contracts, or release judgments.
- Do not commit secrets, tokens, local private credentials, generated outputs, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands.
- Do not run docker compose down -v.
- Do not restore deprecated heuristic chapter-preprocessing logic.
- Do not configure silent degradation for required parsing, preprocessing, or AI recognition paths.
- Do not turn expensive MinerU synthetic submit probing on for every default dependency-health call unless explicitly requested by query or environment flag.

Suggested direction:
1. Extend MinerU dependency-health result shape with explicit fields such as:
   - healthOk
   - submitProbe.enabled
   - submitProbe.ok
   - submitProbe.status
   - submitProbe.durationMs
   - submitProbe.taskId when available
   - submitProbe.error when failed
2. Keep the existing cheap /health behavior as the default for ordinary /ops/dependency-health calls.
3. Add an opt-in submit probe trigger, for example:
   - query flag: /ops/dependency-health?mineruSubmitProbe=true
   - and/or env flag: DEPENDENCY_HEALTH_MINERU_SUBMIT_PROBE=true
4. When submit probing is enabled, dependencies.mineru.ok must require both /health success and POST /tasks submit success.
5. The submit probe should call the active local MinerU endpoint directly and submit a minimal synthetic PDF payload to /tasks.
6. The probe should be non-destructive to Luceon data: do not create Material, ParseTask, MinIO objects, or DB rows. It may create a synthetic task inside MinerU only.
7. The probe must use short bounded timeouts and return explicit failure reasons for HTTP non-2xx, timeout, invalid JSON, or missing task_id/taskId.
8. Update scripts/tier2-standard-check.mjs so Tier 2 Standard fails when the backend dependency-health submit probe fails.
9. Add or extend tests in server/tests/dependency-health-smoke.mjs to cover:
   - /health down -> blocking true.
   - /health OK and submit probe disabled -> current default behavior remains cheap.
   - /health OK but /tasks submit fails, with submit probe enabled -> mineru.ok false and blocking true.
   - /health OK and /tasks submit returns task_id/taskId -> mineru.ok true when MinIO is OK.
   - Ollama down still does not block parse unless strict no-skeleton semantics already require it.

Required checks:
- git status --short --branch
- node server/tests/dependency-health-smoke.mjs
- npx pnpm@10.4.1 exec tsc --noEmit
- npx pnpm@10.4.1 run build
- npx pnpm@10.4.1 run tier2:standard:check, if local MinerU, MinIO, CMS, and Ollama qwen3.5:9b are available
- BASE_URL=http://localhost:8081 bash uat/smoke-test.sh, if the local runtime is already running and reachable

Required evidence:
- Before/after summary of /ops/dependency-health JSON fields for MinerU.
- A failing mock or local evidence case where /health is OK but submit probe fails and blocking becomes true.
- A passing mock or local evidence case where /health and submit probe both succeed.
- Exact command outputs or summarized pass/fail lines with exit codes.
- Any skipped runtime checks must include the exact blocker, not a generic statement.

GitHub sync requirements:
- Before starting:
  cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026
  git status --short --branch
  git fetch origin
  git pull --ff-only origin main
- Create a scoped branch from origin/main, suggested:
  lucode/p0-mineru-submit-path-health-probe
- Commit and push the branch to GitHub.
- Do not merge to main before Lucia review.

Completion report storage requirements:
- Write the completion report into TaskAndReport/ using this naming rule:
  YYYY-MM-DDTHH-MM-SS+0800_P0-MinerU-Submit-Path-Health-Probe_REPORT.md
- Update TaskAndReport/TASK_TRACKING_LIST.md with report path, branch, HEAD, and current status.
- Do not rely on Director chat relay for completion reporting.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- branch and HEAD
- files changed
- implementation summary
- commands run and exit codes
- checks skipped and reasons
- evidence for submit-probe failure and success behavior
- GitHub remote sync status
- risks, blockers, or residual technical debt
- whether Lucia review or Director decision is required

Acceptance criteria:
- Tier 2 Standard can no longer pass solely because MinerU /health returns 200 when POST /tasks is failing.
- Default dependency-health remains lightweight unless submit probe is explicitly requested or enabled.
- Submit-probe failure is represented as a clear MinerU dependency failure with blocking=true.
- POST /tasks upload behavior is not regressed.
- Existing strict no-skeleton and local MinerU mainline semantics remain unchanged.
- dependency-health smoke, TypeScript check, and build pass.
- No unrelated refactor, no secret exposure, no destructive operation, no PRD/project-ledger promotion by Lucode.
```
