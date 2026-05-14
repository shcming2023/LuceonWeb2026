# Director Review: P1 MinerU Terminal Progress Attribution Hardening

- Task ID: `TASK-20260514-162311-P1-MinerU-Terminal-Progress-Attribution-Hardening`
- Reviewed report: `TaskAndReport/2026-05-14T16-23-11+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_REPORT.md`
- Review time: 2026-05-14T16:56:48+0800
- Reviewer: Director
- Result: `ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

## Scope Reviewed

Reviewed the DevelopmentEngineer code/test report and the scoped patch for MinerU terminal progress-attribution semantics.

The task boundary was respected:

- no production deployment
- no upload or validation run
- no batch/intake, pressure, soak, L3, pressure PASS, release-readiness, or go-live claim
- no cleanup, repair, reparse, re-AI, destructive mutation, service ownership mutation, settings/secrets/config/model/sample mutation, PRD truth change, role-contract change, or release-state change

## Evidence Reviewed

Changed implementation files:

- `src/app/utils/taskView.ts`
- `server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs`

Report files:

- `TaskAndReport/2026-05-14T16-23-11+0800_P1-MinerU-Terminal-Progress-Attribution-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Director re-ran the reported checks in both the DevelopmentEngineer workspace context and the clean GitHub sync clone after integrating the scoped patch:

- `node server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` - pass
- `node --check server/tests/mineru-terminal-diagnostic-precedence-smoke.mjs` - pass
- `node server/tests/task-detail-progress-and-supervisor-status-smoke.mjs` - pass
- `git diff --check` - pass
- `npx pnpm@10.4.1 exec tsc --noEmit` - pass

## Judgment

Accepted at code/test level.

The patch makes successful terminal MinerU tasks with completed MinerU state and parsed artifact evidence prefer a completion-oriented primary line:

- `MinerU 已完成，解析产物 N 个`
- or `MinerU 已完成，解析产物 N 个；最后可见进度：...`

The previous attribution residual remains inspectable as diagnostic metadata when present. Failed/no-artifact/in-flight semantics are still covered by focused tests and are not silently converted to success.

## Integration Note

DevelopmentEngineer intentionally did not push from the role thread. Director integrated the scoped patch and report into GitHub `main` from the clean sync clone because this is an important code/test change and Director owns routine GitHub synchronization.

## Residual Risks

- This is not yet production-deployed.
- No runtime/browser validation has confirmed the production UI now shows the hardened terminal semantics.
- The patch improves UI-derived display semantics; it does not repair lower-level log attribution or fabricate missing MinerU business progress.
- Broader batch/intake or pressure-style validation remains intentionally unauthorized.

## Decision

Task 138 is closed as accepted at code/test level:

`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

Director records Task 139 as a User decision for scoped production deployment and read-only browser/runtime validation.
