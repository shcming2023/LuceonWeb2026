# Director Review: P1 Pressure Progress Semantics Root-Cause Diagnosis

- Review time: 2026-05-16T06:20:58+0800
- Reviewed task: `TASK-20260516-060744-P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis`
- Reviewed report: `TaskAndReport/2026-05-16T06-07-44+0800_P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis_REPORT.md`
- Reviewer: Director
- Result: `ACCEPTED_ROOT_CAUSE_DIAGNOSIS_BACKEND_CONTRACT_IMPLEMENTATION_REQUIRED`

## Evidence Reviewed

The DevelopmentEngineer report confirms this was executed as a read-only diagnosis task:

- no code/source/UI/test implementation;
- no production mutation;
- no upload or pressure rerun;
- no retry/reparse/re-AI/repair/reset;
- no MinerU submit-probe;
- no readiness, L3, pressure PASS, or go-live claim.

The report inspected the expected source-of-truth surfaces:

- DB `ParseTask`;
- material metadata;
- MinIO parsed artifacts;
- AI job / AI events;
- `/ops/mineru/active-task`;
- `/ops/dependency-health?mineruSubmitProbe=false`;
- direct MinerU `/health` and `/tasks/{id}`;
- MinerU log parser and log-channel ownership;
- `/cms/tasks` list/detail semantics.

Director spot-check accepts the reported code-path map as credible. Key references include:

- `server/upload-server.mjs` active-task and dependency-health routes;
- `server/lib/ops-mineru-diagnostics.mjs` historical AI-failure classification;
- `server/lib/ops-mineru-log-parser.mjs` runtime/log progress semantics;
- `server/services/mineru/local-adapter.mjs` MinerU polling and progress message updates;
- `server/services/queue/task-worker.mjs` progress-event logging;
- `src/app/utils/taskView.ts` and `/cms/tasks` page rendering.

## Accepted Root Cause

The long-running progress-semantics problem is not a single MinerU runtime failure.

Accepted diagnosis:

1. Primary defect: progress semantics do not expose source, timestamp, freshness, and confidence as a first-class model. UI/backend surfaces flatten DB state, direct MinerU truth, log observation, dependency-health readiness, and AI phase into similar-looking status text.
2. Expected async lag: DB task state can lag direct MinerU completion until worker polling, result fetch, artifact storage, and AI handoff complete.
3. Diagnostic gap: log-channel `stale` after terminal or idle state is too easy to read as active parsing trouble.
4. Diagnostic gap: dependency-health is readiness, not per-task progress; timeout during heavy processing should not be treated as parse failure by itself.
5. Secondary defect: event logs can contain ambiguous rows such as `Status changed to undefined` when metadata-only updates omit state/message.

## Judgment

Accepted.

The diagnosis answers the user's correction: implementation should not begin from UI wording alone. The first implementation step must create a clearer backend progress contract and direct/DB reconciliation semantics, then UI wording can consume that contract in a later task.

This review does not approve production deployment, pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

## Next Action

Director issued:

- `TASK-20260516-062058-P1-MinerU-Progress-Snapshot-Contract-And-Active-Task-Reconciliation`

The task is code/test level only. It should implement the backend progress snapshot contract, active-task direct/DB reconciliation semantics, terminal/idle log-state distinction, and event-log cleanup. Broad UI redesign and production deployment remain out of scope.

