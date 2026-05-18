# Luceon Review: TASK-20260517-175639-P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge Resubmit

- Review time: `2026-05-18T10:54:40+0800`
- Reviewer: `Luceon`
- Main reviewed from: `origin/main@567d7bab40fb0a6fea1c40c377ee0a3499a77628`
- Resubmitted branch: `lucode/task-217-resubmit@69a2cc16dbda190b80664fa7c6b1177e35be6d69`
- Task brief: `TaskAndReport/2026-05-17T17-56-39+0800_P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge_TASK.md`
- Resubmitted report: `TaskAndReport/2026-05-17T17-56-39+0800_P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge_REPORT.md`
- Decision: `CHANGES_REQUIRED_SIDECARE_DB_RACE_NOT_SOLVED`

## Findings

1. **Blocking: the implementation still cannot protect live sidecar snapshots from worker overwrite.**

   The new `reconcileLogObservations(currentObs, previousObs)` only sees the `previousObs` passed from the in-memory `task.metadata.mineruObservedProgress`:

   - `server/services/mineru/local-adapter.mjs:310-315`
   - `server/services/mineru/local-adapter.mjs:640-645`
   - `server/lib/ops-mineru-log-parser.mjs:1291-1315`

   But during an active parse, the task object passed into `processWithLocalMinerU` / `resumeWithLocalMinerU` is a snapshot captured before the polling loop. The host sidecar can later write a fresher observation to DB, while the worker still calls reconciliation with the old in-memory `task.metadata`.

   The task worker then writes the update through `transition(task, updateInfo, ...)` using the same stale `task` object:

   - `server/services/queue/task-worker.mjs:1294-1296`
   - `server/services/queue/task-worker.mjs:1843-1845`
   - `server/services/queue/task-worker.mjs:2383-2385`

   The DB server shallow-merges metadata and incoming `metadata.mineruObservedProgress` overwrites the existing DB value:

   - `server/db-server.mjs:747-774`

   Therefore the intended race is still possible: sidecar writes fresh host progress into DB, then a later worker poll writes stale container observation because the worker did not read the current DB metadata before reconciling. This is the core failure mode Task 217 was created to prevent.

2. **Blocking: the new tests do not cover the actual DB/write race.**

   Test 33 passes a sidecar observation directly as the previous observation, which proves only the pure helper's happy path. It does not simulate a sidecar snapshot arriving in DB after the worker task object was captured and before the next worker update. The currently passing smoke test therefore does not prove the Task 217 acceptance criterion.

3. **Report accuracy issue: the report HEAD does not match the remote branch.**

   The report states `ddaff7b97aac4adeaf0f5cadca58209b85839b58`, but the fetched remote branch head reviewed by Luceon is `69a2cc16dbda190b80664fa7c6b1177e35be6d69`. This is secondary to the code issue, but it must be corrected in the next report.

## Checks Run By Luceon

```bash
git fetch origin refs/heads/lucode/task-217-resubmit:refs/remotes/origin/lucode/task-217-resubmit
git worktree add --detach /tmp/luceon-review-217-resubmit origin/lucode/task-217-resubmit
git diff --check origin/main...HEAD
# exit 0

node --check server/lib/ops-mineru-log-parser.mjs
node --check server/lib/progress-snapshot.mjs
node --check server/services/mineru/local-adapter.mjs
node --check server/upload-server.mjs
node --check server/tests/mineru-log-progress-smoke.mjs
# exit 0

npx pnpm@10.4.1 install --frozen-lockfile
# exit 0; temp worktree dependency install only

node server/tests/mineru-log-progress-smoke.mjs
# exit 0; 153 passed, 0 failed

npx pnpm@10.4.1 exec tsc --noEmit
# exit 0
```

No production deployment, restart, rebuild, upload, retry, reparse, re-AI, submit-probe, pressure test, DB/MinIO/Docker cleanup, model/secret/sample mutation, or readiness/go-live validation was performed. Because the code review failed before acceptance, production validation of this change would be misleading without a corrected implementation and explicit deployment boundary.

## Required Correction

Lucode must correct Task 217 so sidecar-first reconciliation uses the current DB/task metadata or an equivalent current authoritative source at the moment of each worker update, not only the stale task object captured before the polling loop.

The corrected submission must include a focused test that simulates the real race:

1. Worker starts with an old task object lacking the latest sidecar snapshot.
2. Sidecar writes a fresher `host-mineru-log-observer` snapshot to the task metadata in DB/current state.
3. Worker observes a stale container-mounted log.
4. The final task update must preserve the fresher sidecar snapshot and mark container mount staleness, rather than overwriting it with stale container data.

The corrected report must include the actual remote branch HEAD, files changed, exact commands/exit codes, skipped checks, residual production validation needs, and whether Luceon review is required.

Task 218 remains pending behind Task 217 until Task 217 is accepted or explicitly cleared.
