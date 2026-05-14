# DevelopmentEngineer Report: P1 MinerU Progress Log Channel Ownership Diagnostics

## Based On

- Director task brief: `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_TASK.md`
- Upstream analysis: `TaskAndReport/2026-05-14T05-42-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_REPORT.md`
- Director review: `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Observability-Ownership-Review_DIRECTOR_REVIEW.md`

## Branch / HEAD / Worktree

- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD: `7268666`
- Initial check command run: `git status --short --branch`
- GitHub sync: not run, per DevelopmentEngineer current instruction. No fetch, pull, push, commit, or branch operation was performed.
- Worktree note: the workspace already contained many unrelated modified/untracked files before this task. This task only intentionally changed the files listed below plus this report and the Task 107 ledger row.

## Files Changed

- `server/lib/ops-mineru-log-parser.mjs`
- `server/upload-server.mjs`
- `server/services/mineru/local-adapter.mjs`
- `ops/runtime-ownership-status.sh`
- `server/tests/mineru-log-channel-ownership-smoke.mjs`
- `server/tests/mineru-log-observation-transport-smoke.mjs`
- `TaskAndReport/2026-05-14T06-07-35+0800_P1-MinerU-Progress-Log-Channel-Ownership-Diagnostics_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

- Added `inspectMineruLogChannelOwnership()` as a read-only diagnostic surface for MinerU log-channel ownership.
- The diagnostic now distinguishes `missing`, `empty`, `unreadable`, `stale`, `api-noise-only`, `available-no-business-signal`, `valid-business-progress`, and `confirmed-error-log-signal`.
- Added sanitized log-source descriptors with `sourceId`, `configuredBy`, `logRole`, `logSourceContext`, and `logSourceBaseName`; absolute host paths are not exposed in the new ownership endpoint payload.
- Added sidecar state reporting as diagnostic-only: `expected`, `runningState`, `runningObserved`, `lastObserverCheckedAt`, `observerAgeMs`, and explicit `managementScope`. The endpoint does not start, stop, restart, or manage the sidecar process.
- Added `GET /ops/mineru/log-channel-ownership` to upload-server. It reads current global observation memory and log-channel state only.
- Updated `ops/runtime-ownership-status.sh` to include the new read-only ownership endpoint.
- Split empty log files from unreadable files in `parseLatestMineruProgress()` by returning `log-observation-empty`.
- Added `log-observation-empty` to non-terminal diagnostic-only MinerU observation handling, preserving the no-false-failure rule for in-flight MinerU API states.
- Added focused smoke test coverage for missing, empty, stale, valid business progress, fast-complete no-business-signal, in-flight no false failure, and sidecar observed/not-observed states.
- Correction after Director return: made `server/tests/mineru-log-observation-transport-smoke.mjs` time-stable by using a current timestamp and isolating `process.cwd()` to the temp scratch directory so workspace fallback logs cannot participate in the transport smoke candidate set.

## Required Questions Answered

1. Chosen log-channel ownership diagnostic surface:
   - `inspectMineruLogChannelOwnership()` and `GET /ops/mineru/log-channel-ownership`.

2. Missing / empty / stale / valid states:
   - Missing: file does not exist.
   - Empty: file exists and size is `0`.
   - Stale: file exists but mtime age is greater than `MINERU_LOG_STALE_MS`.
   - Valid business progress: log content contains attributable progress/window/document-shape/engine-config signals.

3. Sidecar expected/running/unknown:
   - The sidecar is reported as expected.
   - Recent `globalLogObservation` produces `observed-recent`.
   - Older observation produces `observed-stale`.
   - No observation produces `not-observed`.
   - Process management remains outside this endpoint.

4. MinerU API lifecycle authority:
   - The new diagnostics explicitly state that MinerU API status and Luceon task lifecycle remain terminal failure authority.
   - Log-channel diagnostics describe observability ownership only.

5. Private host paths:
   - The new endpoint does not expose absolute log paths; it exposes basename and source/configuration role only.

6. Remaining production-ops-only work:
   - Deploying this diagnostic endpoint/script update to production, restarting/rebuilding services, observing the real host sidecar process, and validating against live production logs require a separate Director/user-authorized production task.

## Commands Run And Exit Codes

- `git status --short --branch` — exit 0.
- `rg -n "\| (下达待执行|执行中|退回待修正|修正中) \| DevelopmentEngineer \|" TaskAndReport/TASK_TRACKING_LIST.md` — exit 1; canonical status scan did not match because Task 107 used `已下达待执行`.
- `tail -n 30 TaskAndReport/TASK_TRACKING_LIST.md` — exit 0.
- `sed -n ...` and `rg ...` read-only inspection commands over task brief, prior report/review, and allowed source files — exit 0.
- `node --check server/lib/ops-mineru-log-parser.mjs` — exit 0.
- `node --check server/upload-server.mjs` — exit 0.
- `node --check server/services/mineru/local-adapter.mjs` — exit 0.
- `node --check ops/mineru-log-observer.mjs` — exit 0.
- `node --check server/tests/mineru-log-channel-ownership-smoke.mjs` — exit 0.
- `node server/tests/mineru-log-channel-ownership-smoke.mjs` — exit 0.
- `node server/tests/mineru-log-observation-adjudication-smoke.mjs` — exit 0.
- `node --check server/tests/mineru-log-observation-transport-smoke.mjs` — exit 0.
- `node server/tests/mineru-log-observation-transport-smoke.mjs` — exit 0 after correction.
- `git diff --check -- server/lib/ops-mineru-log-parser.mjs server/upload-server.mjs server/services/mineru/local-adapter.mjs ops/runtime-ownership-status.sh server/tests/mineru-log-channel-ownership-smoke.mjs` — exit 0.
- `npx pnpm@10.4.1 test:static` — exit 0.

## Skipped / Failed Checks And Reasons

- The earlier `node server/tests/mineru-log-observation-transport-smoke.mjs` failure was corrected. Director reproduced the immediate cause as the test's stale hard-coded `2026-05-07` timestamp becoming older than the current runtime date. I revised the smoke to generate a current timestamp while preserving the second-granularity tolerance assertions and host log-source context evidence.
- No production endpoint validation was run because the task only allowed production read-only inspection and this implementation has not been deployed by a Director-authorized production task.
- No upload, pressure test, batch/soak test, repair, reparse, re-AI, restart, rebuild, rollback, or production deployment was run.

## Evidence

- Focused smoke output included:
  - `Case 1 Pass: missing log file is distinct and host paths are not exposed`
  - `Case 2 Pass: empty log file is distinct from missing/unreadable`
  - `Case 3 Pass: stale log file is distinct`
  - `Case 4 Pass: valid business progress lines are detected`
  - `Case 5 Pass: fast-complete without business signal is not fabricated into progress`
  - `Case 6 Pass: in-flight MinerU API state is not terminally failed solely by an empty log channel`
  - `Case 7 Pass: sidecar expected/running state is reported without process management`
- `test:static` completed with Vite build success. Vite emitted only the existing large chunk warning.
- `git diff --check` passed for the task-touched files.
- Transport smoke output after correction included:
  - `Case 1 Pass: host log source is explicit and second-granularity timestamp tolerance keeps valid business logs`
  - `Case 2 Pass: observations outside timestamp tolerance remain excluded`
  - `Case 3 Pass: missing log-source diagnostics keep the real observer source context`

## Risks / Blockers / Residual Debt

- Existing local `uat/scratch` fallback logs remain a general hygiene risk for tests that do not isolate `process.cwd()` or env log paths; the corrected transport smoke now isolates `cwd` for its own assertions.
- The new endpoint is implemented in the development workspace only. Production visibility requires a separate authorized deploy/restart/rebuild task.
- The endpoint can infer sidecar liveness only from recent global observations. It intentionally does not inspect or manage OS processes.
- Some `server/upload-server.mjs` diff context includes pre-existing dirty workspace changes unrelated to this task; this report does not claim ownership of those unrelated modifications.

## Review / Next Step

- Director review required: yes.
- Current Next Actor after ledger update: `Director`.
- Need follow-up production validation or user decision: yes, if Director wants the new endpoint deployed and verified against live MinerU logs/sidecar state.
