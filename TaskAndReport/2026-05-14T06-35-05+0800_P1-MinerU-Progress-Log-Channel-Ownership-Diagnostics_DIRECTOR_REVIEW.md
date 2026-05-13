# Director Review: P1 MinerU Progress Log Channel Ownership Diagnostics

- Review time: 2026-05-14T06:35:05+0800
- Role: Director
- Reviewed task: `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_TASK.md`
- Reviewed report: `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_REPORT.md`
- Result: `RETURNED_FOR_CORRECTION_TRANSPORT_SMOKE_AND_REPORT_REASON`

## Decision

Task 107 is returned to DevelopmentEngineer for a narrow correction before Director acceptance.

The implementation direction is good: a read-only `/ops/mineru/log-channel-ownership` diagnostic surface, explicit missing/empty/stale/valid log-channel states, and diagnostic-only sidecar state are aligned with the task objective. The focused smoke and static bundle passed.

However, a related existing MinerU transport smoke still fails, and the report's stated cause does not match Director's reproduction. This needs to be corrected before the task can be accepted and before any production deployment/validation decision.

## Evidence Reviewed

DevelopmentEngineer reported:

- changed `server/lib/ops-mineru-log-parser.mjs`, `server/upload-server.mjs`, `server/services/mineru/local-adapter.mjs`, `ops/runtime-ownership-status.sh`, and `server/tests/mineru-log-channel-ownership-smoke.mjs`;
- added `inspectMineruLogChannelOwnership()` and `GET /ops/mineru/log-channel-ownership`;
- added `log-observation-empty` as a non-terminal diagnostic-only in-flight MinerU observation state;
- focused ownership smoke passed;
- `npx pnpm@10.4.1 test:static` passed;
- `node server/tests/mineru-log-observation-transport-smoke.mjs` failed, reported as local scratch fallback contamination.

Director independently ran:

- `node --check server/lib/ops-mineru-log-parser.mjs`
- `node --check server/upload-server.mjs`
- `node --check server/services/mineru/local-adapter.mjs`
- `node --check server/tests/mineru-log-channel-ownership-smoke.mjs`
- `node server/tests/mineru-log-channel-ownership-smoke.mjs`
- `node server/tests/mineru-log-observation-adjudication-smoke.mjs`
- `git diff --check` for touched task files
- `npx pnpm@10.4.1 test:static`
- `node server/tests/mineru-log-observation-transport-smoke.mjs`

Passing evidence:

- changed-file syntax checks passed;
- focused ownership smoke passed;
- adjudication smoke passed `6/0`;
- diff-check passed;
- `test:static` passed.

Blocking evidence:

`node server/tests/mineru-log-observation-transport-smoke.mjs` failed:

```text
AssertionError [ERR_ASSERTION]: 'log-observation-stale' == 'active-progress'
```

Director's reproduction indicates the immediate cause is the smoke's stale hard-coded 2026-05-07 timestamp becoming older than `MINERU_LOG_STALE_MS` by current runtime date, not the reported scratch fallback contamination. The test may still need scratch isolation, but the completion report should not attribute the failure to an unverified cause.

## Required Correction

DevelopmentEngineer should keep the implementation scope narrow and correct Task 107 by:

1. Fixing or isolating `server/tests/mineru-log-observation-transport-smoke.mjs` so the valid-business-progress case is time-stable and passes on the current date.
2. Ensuring the test still proves second-granularity timestamp tolerance and real host log-source context.
3. Re-running the focused ownership/adjudication/transport checks and `test:static`.
4. Revising the Task 107 report with accurate failed-check/correction evidence.
5. Updating only Task 107 row back to `已回报待 Director 审查`.

## Boundaries

Still not authorized:

- production deploy;
- upload validation;
- pressure/batch/soak;
- restart/rebuild/rollback;
- destructive DB/MinIO/Docker volume/data mutation;
- model/config/secret/sample mutation;
- repair/reparse/re-AI/cleanup;
- fabricated page/batch progress;
- L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.

## Current Next Actor

Next Actor: DevelopmentEngineer.
