# TASK-20260514-101343-P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening

Task:
P1 MinerU Stale Fallback Hygiene And Progress Semantics Hardening

Assignee:
DevelopmentEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_TASK.md`

Expected completion report:
`TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md` if present in the local workspace; if absent, do not block solely on that missing file, and follow `AGENTS.md`, `TEAM_CONTRACT`, and this task brief.
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- Task 115 report and Director review:
  - `TaskAndReport/2026-05-14T09-38-05+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_REPORT.md`
  - `TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Live-Progress-Observability-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`
- Task 116 report and Director review:
  - `TaskAndReport/2026-05-14T10-00-30+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_REPORT.md`
  - `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Log-Source-Ownership-Remediation-Route_DIRECTOR_REVIEW.md`

## Background

Task 115 proved the one-upload runtime path can complete after `luceon-sidecar` attach, but live MinerU business-progress observability still failed:

- configured log-channel ownership stayed `summaryState=empty`;
- configured stdout/stderr logs stayed empty/readable;
- `luceon-sidecar` stayed `observed-recent`;
- `/ops/mineru/global-observation` continued to use stale fallback content from `uat/scratch/mineru-api.log`;
- final material diagnostic was `fast-complete-no-business-signal`;
- browser list/detail semantics were understandable and did not show false failure, but still had no attributable business-progress log.

Task 116 identified the split:

- code semantics issue: stale workspace scratch fallback should not outrank configured production log channels or present stale `Predict 99%` as useful current progress;
- runtime ownership issue: true live progress likely requires later controlled MinerU ownership normalization, which is not authorized in this task.

## Objective

Implement code/test-only stale fallback hygiene so stale workspace fallback logs cannot pollute current MinerU progress semantics when configured production log paths are present but empty.

This task must preserve strict no-fabrication semantics: if there is no current attributable MinerU progress, the system should say that clearly instead of inventing page/batch/phase progress.

## Allowed Files

Preferred scope:

- `server/lib/ops-mineru-log-parser.mjs`
- focused tests under `server/tests/`, especially:
  - `server/tests/mineru-log-progress-smoke.mjs`
  - `server/tests/mineru-log-observation-transport-smoke.mjs`
  - `server/tests/mineru-log-channel-ownership-smoke.mjs`
  - `server/tests/mineru-log-source-live-smoke.mjs`

Optional only if required by failing focused tests:

- `src/app/utils/taskView.ts`

Task/report bookkeeping:

- `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`, only Task 117 row

Do not change unrelated files.

## Required Behavior

Implement and test these semantics:

1. If explicit configured log paths exist through `MINERU_LOG_PATH` and/or `MINERU_ERR_LOG_PATH`, stale workspace scratch fallback must not outrank configured production log channels as current business progress.
2. Stale fallback content such as old `uat/scratch/mineru-api.log` `Predict 99%` may be reported only as diagnostic/stale/non-authoritative, or ignored, but must not be selected as `latest-valid-business-signal` for current progress.
3. If configured logs are empty and fallback is stale, global observation should communicate configured channel empty / stale fallback ignored or diagnostic, not useful current phase progress.
4. If configured logs contain fresh business progress, current progress parsing must still work.
5. If no current attributable progress exists after fast MinerU completion, existing truthful diagnostics such as `fast-complete-no-business-signal` must remain valid.
6. Do not fabricate page counts, batch progress, phase progress, or current business signals.

## Forbidden Operations

- Do not upload PDFs.
- Do not run pressure, batch, soak, or long-run validation.
- Do not touch production runtime.
- Do not run Docker commands.
- Do not start, stop, restart, kill, relaunch, or normalize MinerU.
- Do not start, stop, restart, or mutate sidecar, supervisor, Ollama, DB, MinIO, upload-server, or frontend.
- Do not delete, truncate, rename, or edit log files.
- Do not repair, reparse, re-AI, retry, mutate, delete, or clean historical tasks/materials/artifacts.
- Do not modify samples, secrets, configs, model files, PRD truth, role contracts, release docs, or GitHub settings.
- Do not overwrite unrelated dirty worktree changes.
- Do not claim L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
- Do not push to GitHub unless this task's local role protocol explicitly requires it; Director will review and synchronize if needed.

## Required Checks

At minimum, run and record exit codes for:

- `git status --short --branch`
- `node --check server/lib/ops-mineru-log-parser.mjs`
- `node server/tests/mineru-log-progress-smoke.mjs`
- `node server/tests/mineru-log-observation-transport-smoke.mjs`
- `node server/tests/mineru-log-channel-ownership-smoke.mjs`
- `node server/tests/mineru-log-source-live-smoke.mjs`
- `git diff --check`

If `src/app/utils/taskView.ts` changes, also run:

- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`

If any required check is skipped, record the exact reason.

## Required Evidence

The completion report must include:

- changed files;
- exact behavior implemented;
- focused tests added or changed;
- command results and exit codes;
- proof that stale scratch fallback cannot outrank configured production logs as current progress;
- proof that fresh configured log business progress still parses;
- proof that empty configured logs remain diagnostic and do not fabricate progress;
- residual risk and whether production deployment/runtime validation is needed.

## Completion Report Requirements

Write the report to:

`TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`

Then update only Task 117 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- if completed: `Status=已回报待 Director 审查`, `Next Actor=Director`;
- if blocked: `Status=挂起`, `Next Actor=Director`;
- include changed files, checks summary, and whether production deployment validation is required.

Do not update project state docs, PRD, role contracts, release docs, or GitHub.

## Acceptance Criteria

Director can accept this task if:

- implementation is scoped to code/test fallback hygiene;
- stale fallback no longer pollutes current progress semantics when configured logs are present;
- fresh configured progress still works;
- no fabricated progress is introduced;
- required checks pass or skipped checks are justified;
- no forbidden runtime operation or readiness claim is performed.
