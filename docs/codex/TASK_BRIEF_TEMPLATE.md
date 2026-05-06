# Luceon2026 Lucia -> Lucode Task Brief Template

Last updated: 2026-05-07

Use this template when Lucia assigns development or testing work to Lucode. The task brief is the execution contract. Lucode must not broaden work beyond the signed scope.

Every task brief and completion report must be stored under `TaskAndReport/` and recorded in `TaskAndReport/TASK_TRACKING_LIST.md`.

## Lucia Task Brief

```text
Task:

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
TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md

Background:

Current known facts:

PRD / contract reference:

Objective:

Non-goals:

Allowed files, modules, or operations:

Forbidden changes:
- Do not start from vague oral instructions or self-created tasks.
- Do not broaden scope beyond this task brief.
- Do not perform broad rewrites or framework-level refactors unless explicitly assigned.
- Do not change unrelated files.
- Do not change PRD truth, project ledger facts, role contracts, or release judgments unless explicitly assigned.
- Do not commit secrets, tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands without explicit Director approval.
- Do not restore deprecated heuristic chapter-preprocessing logic as a main path.
- Do not configure silent degradation for required parsing, preprocessing, or AI recognition paths.
- Do not claim UAT, L2, L3, production readiness, or release readiness without the evidence required below.

Suggested direction:

Required checks:

Required evidence:

GitHub sync requirements:
- Before starting: cd /Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026; git status --short --branch; git fetch origin; git pull --ff-only origin main.
- Before reporting: git status --short --branch; git log -1 --oneline.
- Commit and push to GitHub if repository files are changed and this task requires remote synchronization.

Completion report storage requirements:
- Write the completion report into TaskAndReport/ using this naming rule: YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md.
- Update TaskAndReport/TASK_TRACKING_LIST.md with report path, branch, HEAD, and current status.
- Do not rely on Director chat relay for completion reporting.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- branch and HEAD
- files changed
- implementation or testing summary
- commands run with exit codes
- checks skipped and reasons
- runtime or test evidence when applicable
- risks, blockers, or residual technical debt
- GitHub sync status
- whether Lucia review, Director decision, or additional validation is required

Acceptance criteria:
```

## Lucode Completion Report

```text
Task:

Assignee:
Lucode

Report to:
Lucia

Report file:
TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md

Confirmation:
This work was executed based on Lucia's task brief dated [date].

Branch and HEAD:

Files changed:

Implementation or testing summary:

Commands run and exit codes:

Checks skipped and reasons:

Evidence:

Risks, blockers, or residual technical debt:

GitHub sync status:

Required Lucia review:

Required Director decision:

Additional validation required:
```
