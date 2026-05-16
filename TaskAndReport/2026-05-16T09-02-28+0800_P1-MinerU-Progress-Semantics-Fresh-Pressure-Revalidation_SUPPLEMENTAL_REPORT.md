# P1 MinerU Progress Semantics Fresh Pressure Revalidation Supplemental Snapshot 09:02

- Task ID: `TASK-20260516-084828-P1-MinerU-Progress-Semantics-Fresh-Pressure-Revalidation`
- Role: TestAcceptanceEngineer
- Supplemental snapshot time: 2026-05-16 09:02 +0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD observed: `0598ca5`

## Current Classification

`IN_PROGRESS_ACTIVE_PRESSURE_RUN`

No terminal or no-progress condition is met. Continue read-only monitoring.

## Fresh Run Counts

Read-only DB summary for records created after Task 205 issue time:

| Dataset | Fresh records | State / stage summary |
| --- | ---: | --- |
| tasks | 24 | 1 `running` / `mineru-processing`, 23 `pending` / `upload` |
| materials | 24 | 24 `processing` |
| AI metadata jobs | 0 | AI stage has not started |

Active task remained:

- task: `task-1778892864544`
- material: `2276905321424867`
- MinerU task: `cd19b2fd-8a68-4627-8966-cbe1f90e4e5e`
- file: `Cambridge IGCSE(0607) International Mathematics  Coursebook_2023(Hodder Express).pdf`
- size: 52,964,792 bytes
- DB state/stage: `running` / `mineru-processing`

## Progress Semantics Evidence

`/ops/mineru/active-task`:

- `progressSnapshot.version=progress-snapshot-v0.1`
- `phase=parse`
- `source=direct-mineru`
- `sourcePriority=direct-mineru`
- `directMineruStatus=processing`
- `dbState=running`
- `dbStage=mineru-processing`
- `logState=stale`
- `operatorMessage=MinerU API 仍在处理`

Direct MinerU task API:

- endpoint: `http://127.0.0.1:8083/tasks/cd19b2fd-8a68-4627-8966-cbe1f90e4e5e`
- status: `processing`
- completed_at: `null`
- error: `null`
- queued_ahead: 0

Direct MinerU health:

- `queued_tasks=19`
- `processing_tasks=1`
- `completed_tasks=53`
- `failed_tasks=0`

## Log Evidence And Semantics Note

Host log files were fresh at this snapshot:

- `/Users/concm/ops/logs/mineru-api.log`: mtime `2026-05-16 09:02:43 +0800`
- `/Users/concm/ops/logs/mineru-api.err.log`: mtime `2026-05-16 09:02:44 +0800`

Tail evidence showed forward movement since the 08:55 snapshot:

- MFR progressed through `1201/1201`.
- Table OCR detection progressed through `24/24`.
- Table OCR recognition progressed through `248/248`.
- Table wireless prediction progressed through `24/24`.
- Table wired prediction started.

Important semantic finding:

- Active-task correctly prioritized direct MinerU API as progress truth and did not treat stale logs as failure.
- The log-channel ownership endpoint still reported configured container-mounted log sources as stale/idle, while direct host log tail showed fresh business progress. This is an observability mismatch worth preserving for Director review: log-channel diagnostics can still look stale even when direct host logs are moving.

## Commands Run

| Workspace | Command / endpoint | Exit code | Key output |
| --- | --- | ---: | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Prod | `date`, `git status --short --branch`, `git rev-parse --short HEAD` | 0 | `2026-05-16 09:02:28 +0800`; production HEAD `0598ca5` |
| Prod | `curl .../ops/mineru/active-task` | 0 | active task still direct-MinerU `processing`; progressSnapshot operator message says MinerU API is still processing |
| Prod | `curl http://127.0.0.1:8083/tasks/cd19b2fd-8a68-4627-8966-cbe1f90e4e5e` | 0 | direct MinerU `processing`, no error |
| Prod | DB summaries through `/__proxy/db/*` | 0 | 24 fresh records; 1 running, 23 pending; AI jobs 0 |
| Prod | `stat` and `tail` host MinerU logs | 0 | fresh log mtime and forward progress |
| Prod | `curl .../ops/mineru/log-channel-ownership` | 0 | endpoint-reported configured log sources stale/idle despite host log progress |

## Forbidden Actions Confirmation

No upload, cleanup/reset, submit-probe, retry, reparse, re-AI, repair, cancel, restart, rebuild, redeploy, DB/MinIO/Docker/config/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Next Monitoring Need

Continue monitoring. Next useful snapshot should check whether the first large PDF reaches result-store / ai-pending / review-pending, and whether the queued count advances from 19 with the next MinerU task started.
