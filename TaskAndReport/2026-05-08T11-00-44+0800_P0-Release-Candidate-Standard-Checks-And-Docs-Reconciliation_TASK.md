# P0 Release Candidate Standard Checks And Docs Reconciliation

Task:
P0 Release Candidate Standard Checks And Docs Reconciliation

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T11-00-44+0800_P0-Release-Candidate-Standard-Checks-And-Docs-Reconciliation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/2026-05-08T10-52-19+0800_P0-Release-Candidate-Non-Destructive-Preflight-And-Evidence-Pack_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Lucode's non-destructive preflight evidence pack was accepted. Production release readiness remains unclaimed and Director release-scope decisions remain pending. Lucia may continue only with non-destructive validation and documentation tasks.

## Objective

Run the next layer of non-destructive standard checks and reconcile release-readiness documentation evidence.

The output must clarify whether current `main` has enough non-destructive evidence for Lucia to prepare a release-readiness review checklist, without claiming release readiness.

## Non-goals

- Do not approve production release readiness.
- Do not deploy, rebuild, restart, rollback, or mutate production runtime state.
- Do not run Docker pull/build/compose operations.
- Do not mutate DB, MinIO, Docker volumes, tasks, production artifacts, secrets, or local overrides.
- Do not perform controlled uploads or create new production tasks unless explicitly approved by Director.
- Do not implement fixes or refactors.
- Do not change PRD truth or role contracts.

## Allowed Operations

- Read repository documents, source, tests, scripts, and configuration.
- Run non-mutating checks in the development workspace.
- Run read-only runtime health checks against the already-running `http://localhost:8081` service.
- Propose documentation reconciliation items in the report.
- Write one completion report under `TaskAndReport/`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md`.

## Required Checks

In the development workspace:

- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `git log -1 --oneline`
- `git diff --check`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `node server/tests/dependency-health-smoke.mjs`
- `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check`
- `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh`

Read-only runtime checks:

- `curl -fsS 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`
- `curl -fsS http://localhost:8081/__proxy/upload/ops/dependency-repair/status`
- `curl -fsS http://localhost:8081/__proxy/db/health`

Documentation inspection:

- Compare `docs/codex/PROJECT_STATE.md` and `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md` for release-readiness-relevant drift.
- Identify exact documentation updates Lucia should make after review.

If any check is skipped, report the exact reason.

## Required Evidence

The report must include:

- Command results with exit codes.
- Whether Tier 2 Standard and UAT smoke passed, failed, or were skipped.
- Runtime health summaries.
- Documentation drift list with exact files and sections.
- Remaining blockers before production release-readiness review.
- Pending Director decisions.

## Forbidden Changes

- Do not restart, rebuild, or deploy any service.
- Do not run Docker pull/build/compose commands.
- Do not mutate production data or local override files.
- Do not create production upload tasks.
- Do not claim production release readiness.
- Do not directly edit `PROJECT_STATE.md`, `HANDOFF.md`, PRD, or review docs in this task; list recommended doc updates in the report for Lucia review.

## Completion Report Requirements

- Write report to `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Release-Candidate-Standard-Checks-And-Docs-Reconciliation_REPORT.md`.
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status `已回报待审`, `Next Actor=Lucia`, next action, and required output.
- Commit and push only the report and task tracking update if repository files are changed.

## Acceptance Criteria

- Standard non-destructive checks are run or explicitly skipped with reasons.
- Documentation drift is specific and actionable.
- No production mutation is performed.
- Production release readiness is not claimed.
