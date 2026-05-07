# Task: P1 MinerU Sidecar Task-Level Log Attribution

```text
Task:
P1 MinerU Sidecar Task-Level Log Attribution

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
TaskAndReport/2026-05-07T10-41-51+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-07T10-34-23+0800_P0-Production-Ops-Sidecar-Supervisor-Recovery_SUPPLEMENTAL_REPORT.md

Background:
After `luceon-sidecar` was restored, host MinerU logs contained valid business progress for a fast-completing task, but task-level `mineruObservedProgress` stayed low-signal and the UI still appeared to lack useful parse logs.

Known evidence:
- Task `task-1778120784621` / file `走向成功_英语_二模卷16篇.pdf`.
- MinerU completed and parsed files count was reported as `25`.
- Host logs contained progress lines for a 24-page task, including Layout Predict, Table OCR, OCR det/rec, and Processing pages.
- Global observation was non-null but stale/unattributed.
- Task-level `mineruObservedProgress` remained `log-observation-no-business-signal`.
- Current server attribution code requires exactly one eligible active MinerU task before attaching sidecar observation to a task.

Objective:
Analyze the MinerU sidecar task-level attribution gap for fast-completing tasks and propose the smallest safe fix. This is an investigation and task-design pass unless Lucia separately authorizes implementation.

Non-goals:
- Do not implement code changes in this task.
- Do not mutate production tasks or logs.
- Do not restart MinerU, Ollama, Docker, supervisor, or sidecar.
- Do not change parse state semantics.
- Do not claim production release readiness.

Required investigation:
1. Inspect current sidecar and upload-server attribution flow:
   - `ops/mineru-log-observer.mjs`
   - `server/upload-server.mjs` routes `/ops/mineru/active-task`, `/ops/mineru-log-observation`, `/ops/mineru/global-observation`
   - `server/lib/ops-mineru-log-parser.mjs`
   - UI consumers of `mineruObservedProgress`
2. Use existing reports and code to explain why fast-completing tasks can lose useful task-level attribution.
3. Determine whether the likely fix belongs in:
   - sidecar polling cadence/context capture
   - upload-server attribution logic
   - parser history/backfill support
   - task-worker parse progress persistence
   - UI fallback to global observation or raw log evidence
4. Identify test coverage needed before implementation.
5. Recommend one scoped implementation task with allowed files and acceptance criteria.

Allowed commands:
- read-only `rg`, `sed`, `git show`, `git diff`
- read-only HTTP checks if needed
- read-only log inspection if needed

Forbidden operations:
- Do not edit code.
- Do not restart services.
- Do not mutate production task state.
- Do not delete logs or data.

Required report evidence:
- File paths and line-level references for the attribution bottleneck.
- Exact explanation of why `not exactly 1 active task` causes loss of task-level logs.
- Whether current behavior is a data-loss problem, UI fallback problem, or timing/attribution problem.
- Recommended implementation task with priority, allowed files, test plan, and risks.

Completion report storage requirements:
- Write the report into TaskAndReport/:
  `YYYY-MM-DDTHH-MM-SS+0800_P1-MinerU-Sidecar-Task-Level-Log-Attribution_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, status, next actor, and evidence summary.
- Commit and push only task/report tracking changes to GitHub `main`.

Acceptance criteria:
- Lucia can decide whether to assign implementation.
- No production state is changed.
- The proposed fix preserves existing MinerU parse semantics and does not create silent degradation.
```
