# P0 Adaptive Evidence-Pack Production Validation Runbook And Preflight

Task:
P0 Adaptive Evidence-Pack Production Validation Runbook And Preflight

Task ID:
`TASK-20260508-154115-P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T15:41:15+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T15-41-15+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T15-11-45+0800_P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T15-11-45+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Authorization_DECISION.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Director has not yet authorized scoped production/runtime validation for the accepted adaptive evidence-pack code. Two Lucia heartbeat checks have occurred without a Director decision. Lucia is not authorized to approve production runtime mutation autonomously.

To avoid a blocked task flow, Lucode must prepare a non-destructive production validation runbook and read-only preflight evidence. This task must not apply the validation or mutate runtime state.

## Objective

Prepare the exact runbook, evidence plan, and read-only preflight needed to execute production validation quickly once Director authorizes it.

## Scope

Lucode must:

1. Identify the current dev `main` HEAD and production workspace HEAD.
2. Read, but do not modify, production `docker-compose.override.yml` and confirm the strict AI/model settings and MinIO console local-only binding expectations.
3. Identify the precise deployment/apply steps that would be required after Director authorization.
4. Identify the precise large-PDF validation sample path and any expected hashes/sizes already recorded.
5. Define how to verify that adaptive evidence-pack selection is active during production validation, including which structured fields/logs must be inspected:
   - `aiClassificationSamplingMode`
   - `aiClassificationInputOriginalLength`
   - `aiClassificationInputSampledLength`
   - `aiClassificationInputHash`
   - `aiClassificationInputSelectionReasons`
   - `aiClassificationInputSelectionThresholds`
   - `aiClassificationRawTrace.input.observed`
6. Define pass, fail, and inconclusive criteria for the later production validation.
7. List rollback boundaries and forbidden operations.

## Allowed Checks

Only non-destructive checks are allowed:

- Git status/log/fetch reads.
- File reads in dev and production workspaces.
- Read-only `docker compose config` or equivalent config rendering, if it does not recreate or restart services.
- Read-only local health checks such as dependency-health and DB health, if services are already running.
- Read-only inspection of existing task/report artifacts.

## Forbidden

- Do not deploy, restart, rebuild, recreate, or rollback production services.
- Do not run `docker compose up`, `down`, `restart`, `rm`, `pull`, `build`, `prune`, or volume-affecting commands.
- Do not create a new upload or validation task.
- Do not mutate DB rows, MinIO objects, Docker volumes, task records, artifacts, logs, secrets, or local override files.
- Do not change model, timeout, fallback, or strict AI settings.
- Do not claim production release readiness.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight_REPORT.md`

The report must include:

- Current dev and production HEADs.
- Production override boundary confirmation from read-only inspection.
- Proposed production validation runbook after Director authorization.
- Exact evidence fields/logs to collect.
- Pass/fail/inconclusive criteria.
- Rollback and forbidden-operation boundaries.
- All commands run with exit codes.
- Confirmation that no production mutation, controlled validation artifact creation, data cleanup, secret change, Docker mutation, or release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.

## Acceptance Criteria

- The later production validation can be executed from the runbook without rediscovery once Director authorizes it.
- No production mutation occurs in this task.
- Director task 32 remains the authority for whether actual production validation may proceed.
