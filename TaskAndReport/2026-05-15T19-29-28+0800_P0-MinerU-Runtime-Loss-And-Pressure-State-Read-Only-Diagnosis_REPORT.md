# DevelopmentEngineer Report: P0 MinerU Runtime Loss And Pressure State Read-Only Diagnosis

- Report time: 2026-05-15T19:37:01+0800
- Based on Director task brief: `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_TASK.md`
- Execution role: DevelopmentEngineer
- Scope: read-only production diagnosis only
- Forbidden operations respected: no restart/relaunch/kill, no submit-probe, no upload, no retry/reparse/re-AI, no cancel/repair/reset, no cleanup, no Docker up/down/down-v/prune, no DB/MinIO/data/config/secret/model/sample mutation, no readiness/L3/pressure PASS/go-live claim.

## Branch / HEAD

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
  - `git status --short --branch`: `## main...origin/main`
  - HEAD: `0801999 docs: add CleanService PRD addendum`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
  - `git status --short --branch`: `## main...origin/main`
  - HEAD: `1716add Dispatch dependency health production validation`
  - Dirty files observed in production workspace: `.gitignore`, `docker-compose.override.yml`, `docs/codex/TEST_MATRIX.md`, `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`, `ops/runtime-ownership-status.sh`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`

## Files Changed

- `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Diagnosis Summary

1. MinerU API is currently not reachable on the expected runtime port.
   - `lsof -nP -iTCP:8083 -sTCP:LISTEN` found no listener.
   - direct `curl http://127.0.0.1:8083/health` returned connection refused.
   - upload-server dependency health reports `mineru.ok=false`, `healthOk=false`, `error=connect ECONNREFUSED`, `blocking=true`.

2. There is no visible active tmux-owned MinerU API session.
   - `tmux list-sessions` returned no tmux server.
   - process inventory did not show a live `mineru-api` / `uvicorn` owner, apart from the diagnostic shell commands themselves.
   - `launchctl list` shows `com.office.mineru`, but `launchctl print gui/501/com.office.mineru` reports `state = not running`, `runs = 1`, `last exit code = 0`, program `/Users/concm/ops/bin/start-mineru-all.sh`.

3. Runtime ownership is inconsistent across current docs and host launcher.
   - Production repo ownership doc expects host tmux session `luceon-mineru` and command `bash ops/start-mineru-api.sh`.
   - Host LaunchAgent `/Users/concm/Library/LaunchAgents/com.office.mineru.plist` points to `/Users/concm/ops/bin/start-mineru-all.sh`, which starts tmux sessions `mineru_api` and `mineru_gradio`.
   - `ops/runtime-ownership-status.sh` checks both `mineru_api` and `luceon-mineru`, implying the repo already knows both names may appear.
   - No owner is currently active, so the evidence supports "MinerU runtime lost", not "running elsewhere behind a different visible owner".

4. Log evidence shows MinerU was alive and processing the large pressure task, then became stale/lost.
   - `/Users/concm/ops/logs/mineru-api.err.log` shows active pipeline processing for the large `f8e44788-db97-4273-89da-dc5bbfa29d71` task through 2026-05-15 18:19:27 local time, including `Pipeline processing window batch 8/10: 512/578 pages`.
   - log-channel ownership endpoint at 2026-05-15T11:36:45Z reports both configured MinerU logs as `stale`; selected stderr log mtime `2026-05-15T10:26:09.721Z`, stdout log mtime `2026-05-15T10:34:59.467Z`.
   - This matches the user-visible concern that the task page/log channel no longer provides fresh MinerU progress semantics.

5. The 24 pressure tasks drifted after the TestAcceptanceEngineer final snapshot.
   - Task 181 final snapshot: 5 `review-pending`, 1 `running/mineru-processing`, 18 `pending/upload`.
   - Director spot-check when issuing Task 183: 5 `review-pending`, 6 `failed`, 13 `pending`.
   - Current read-only DB snapshot: 5 `review-pending`, 1 `failed/mineru-processing`, 12 `failed/submit-failed-retryable`, 6 `pending/upload`.
   - The drift was caused by the worker continuing to process/retry after MinerU was already unreachable, converting later pending tasks into retryable submit failures one by one.

## Current 24-Task Status

| State | Stage | Count |
| --- | --- | ---: |
| `review-pending` | `review` | 5 |
| `failed` | `mineru-processing` | 1 |
| `failed` | `submit-failed-retryable` | 12 |
| `pending` | `upload` | 6 |

AI jobs:

- 5 AI metadata jobs exist.
- All 5 are `review-pending`, provider `ollama`, model `qwen3.5:9b`, confidence `30`, `needsReview=true`.
- No AI jobs exist for the 19 non-review-pending tasks.

## Non-Terminal / Failed Task Table

| Task ID | State | Stage | Retries | Material ID | File | Latest evidence |
| --- | --- | --- | ---: | --- | --- | --- |
| `task-1778821689802` | `pending` | `upload` | 0 | `3715380338163834` | `06第六章 长期股权投资与合营安排.pdf` | Created, not yet submitted |
| `task-1778821688815` | `pending` | `upload` | 0 | `3921565860585718` | `2025_2026学年春季课程中数G8_提取.pdf` | Created, not yet submitted |
| `task-1778821687711` | `pending` | `upload` | 0 | `3962856870004329` | `2025.pdf` | Created, not yet submitted |
| `task-1778821687039` | `pending` | `upload` | 0 | `4461123631340409` | `财务回执(￥50,000.00).pdf.pdf` | Created, not yet submitted |
| `task-1778821686368` | `pending` | `upload` | 0 | `1318391841654809` | `出国.pdf` | Created, not yet submitted |
| `task-1778821685243` | `pending` | `upload` | 1 to 4 observed | `4258505476429320` | `附件三：考务流程培训-纸笔标准考试.pdf` | `lastSubmitError=本地 MinerU 不可达: http://host.docker.internal:8083` |
| `task-1778821684605` | `failed` | `submit-failed-retryable` | 6 | `1145216985632070` | `蓝月、血月、橙月？月亮为啥还会变色？.pdf` | MinerU submit unreachable |
| `task-1778821684061` | `failed` | `submit-failed-retryable` | 6 | `2254986632440968` | `期末质量分析及建议（曹云童 ）.pdf` | MinerU submit unreachable |
| `task-1778821683516` | `failed` | `submit-failed-retryable` | 6 | `607955458758655` | `向树叶学习：人工光合作用.pdf` | MinerU submit unreachable |
| `task-1778821682921` | `failed` | `submit-failed-retryable` | 6 | `2812666502572371` | `走向成功_英语_二模卷16篇.pdf` | MinerU submit unreachable |
| `task-1778821682184` | `failed` | `submit-failed-retryable` | 6 | `2774317387071012` | `G7_Workbook_ready_to_print.pdf` | MinerU submit unreachable |
| `task-1778821681423` | `failed` | `submit-failed-retryable` | 6 | `1300888795027708` | `PDF document-4F18-A8A3-62-0.pdf` | MinerU submit unreachable |
| `task-1778821679707` | `failed` | `submit-failed-retryable` | 6 | `128454372286093` | `Cambridge IGCSE(0580) Core Mathematics_2023(Hodder Education).pdf` | MinerU submit unreachable |
| `task-1778821678265` | `failed` | `submit-failed-retryable` | 6 | `291281034391813` | `Cambridge IGCSE(0580) Core and Extended Mathematics_2018(Cambridge University Press).pdf` | MinerU submit unreachable |
| `task-1778821677014` | `failed` | `submit-failed-retryable` | 6 | `4078241404222032` | `Cambridge IGCSE(0580) Core and Extended Mathematics_2018(Hodder Education).pdf` | MinerU submit unreachable |
| `task-1778821675075` | `failed` | `submit-failed-retryable` | 6 | `4056381605810704` | `Cambridge IGCSE(0580) Core and Extended Mathematics_2022(Cambridge University Press).pdf` | MinerU submit unreachable |
| `task-1778821672612` | `failed` | `submit-failed-retryable` | 6 | `1287819703568079` | `Cambridge IGCSE(0580) Core and Extended Mathematics_2023(Hodder Education).pdf` | MinerU submit unreachable |
| `task-1778821669268` | `failed` | `submit-failed-retryable` | 6 | `366187464744193` | `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge University Press).pdf` | MinerU submit unreachable |
| `task-1778821666605` | `failed` | `mineru-processing` | 0 | `2299860817314472` | `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf` | `[resume] 本地等待 MinerU 超时 (3600s)，但 MinerU task f8e44788-db97-4273-89da-dc5bbfa29d71 最后状态为 processing，不代表业务失败` |

## Recovery Assessment

Current evidence supports a staged recovery, but no recovery was performed in this task.

Recommended approval sequence:

1. Director/User approval for a MinerU-only runtime relaunch, with no DB/MinIO/task mutation.
   - Scope should be limited to restoring the host MinerU API owner and verifying `127.0.0.1:8083/health`.
   - Director should decide the canonical owner name before action: repo doc says `luceon-mineru`, while current LaunchAgent script starts `mineru_api`.

2. After MinerU is reachable, run read-only checks first.
   - dependency-health without submit probe.
   - active-task diagnostics.
   - log-channel ownership diagnostics.
   - direct health check.

3. Only if explicitly authorized, run one side-effecting MinerU submit probe.
   - This is not read-only and was not run during Task 183.

4. Separately approve task-state reconciliation.
   - `task-1778821666605` needs special adjudication because Luceon marked it `failed/mineru-processing`, while the last known MinerU-side status was `processing`; if the restored MinerU runtime no longer has the task/result, this may require a Director decision between reparse/retry versus marking the pressure evidence as unrecoverable.
   - The 12 `submit-failed-retryable` tasks and 6 `pending/upload` tasks should not be retried automatically until MinerU ownership is stable and Director approves mutation.

## Risks / Blockers / Residual Debt

- Blocker: MinerU runtime is not currently present on 8083.
- Blocker: Runtime ownership is split between documented `luceon-mineru` and LaunchAgent/script `mineru_api`; this should be unified before the next pressure run.
- Risk: The admission circuit is `closed` despite current MinerU `connect ECONNREFUSED`; this may allow stale acceptance/worker drift unless intake blocking is revalidated after runtime recovery.
- Risk: Log-channel freshness is stale; task-page progress semantics may again become unreadable during long MinerU jobs unless sidecar/log ownership is made explicit and monitored.
- Risk: Production workspace has existing dirty files; I did not alter production files.
- Residual debt: Need a recovery runbook that separates MinerU-only relaunch, submit-probe, task retry/reparse, and failed-state reconciliation into separately approved steps.

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch && git rev-parse --short HEAD && git log -1 --oneline` — exit 0
- `sed -n ...` on required role/project/PRD/test/repository/task docs — exit 0
- `rg -n '^\\| 183 \\|' TaskAndReport/TASK_TRACKING_LIST.md` — exit 0

Production workspace / runtime read-only diagnostics:

- `git status --short --branch && git rev-parse --short HEAD && git log -1 --oneline` — exit 0
- `docker compose ps` — exit 0
- `lsof -nP -iTCP:8083 -sTCP:LISTEN || true` — command exit 0; no listener returned
- `pgrep -af 'mineru-api|mineru|uvicorn' || true` — command exit 0; only diagnostic command matches observed
- `ps -ef | rg -i 'mineru|uvicorn|fastapi|python' || true` — command exit 0; only diagnostic command matches observed
- `tmux list-sessions || true` — command exit 0; stderr reported no tmux server
- `launchctl list | grep -i mineru || true` — command exit 0; `com.office.mineru` present
- `launchctl print gui/$(id -u)/com.office.mineru` — exit 0; state `not running`
- `curl -sS --max-time 5 http://localhost:8081/__proxy/upload/health || true` — command exit 0; service OK
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=false' || true` — command exit 0; MinerU blocking, submit probe disabled
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit || true` — command exit 0
- `curl -sS --max-time 20 http://localhost:8081/__proxy/upload/ops/mineru/active-task || true` — command exit 0
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership || true` — command exit 0
- `curl -sS --max-time 10 http://127.0.0.1:8083/health || true` — command exit 0 wrapper; curl reported connection refused
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/tasks > /tmp/luceon-task183-tasks.json` — exit 0
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/materials > /tmp/luceon-task183-materials.json` — exit 0
- `curl -sS --max-time 20 http://localhost:8081/__proxy/db/ai-metadata-jobs > /tmp/luceon-task183-ai-jobs.json` — exit 0
- `jq ... /tmp/luceon-task183-*.json` — exit 0
- `stat`, `tail`, `rg` over `/Users/concm/ops/logs/mineru-api*.log` and LaunchAgent logs — exit 0
- `docker compose logs --since ... upload-server | rg ... || true` — command exit 0
- `sed -n ... ops/start-mineru-api.sh docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md ops/runtime-ownership-status.sh` — exit 0
- `sed -n ... /Users/concm/ops/bin/start-mineru-all.sh` — exit 0
- `docker inspect cms-upload-server --format ... | rg ... || true` — command exit 0

## Skipped Checks And Reasons

- MinerU submit probe: skipped because Task 183 explicitly forbids submit-probe.
- Service restart/relaunch/kill: skipped because Task 183 explicitly forbids runtime mutation.
- Upload/retry/reparse/re-AI/cancel/repair/reset: skipped because Task 183 explicitly forbids task/data mutation.
- Docker up/down/down-v/prune: skipped because Task 183 explicitly forbids Docker mutation.
- DB/MinIO direct write or cleanup: skipped because Task 183 explicitly forbids production data mutation.

## Evidence

- Direct dependency-health: `mineru.ok=false`, `mineru.healthOk=false`, `error=connect ECONNREFUSED`, `blocking=true`, `submitProbe.enabled=false`.
- Direct port evidence: no 8083 listener and `curl http://127.0.0.1:8083/health` failed to connect.
- Ownership evidence: `com.office.mineru` LaunchAgent exists but is `not running`; no tmux server; no active `mineru-api` process found.
- Log evidence: last business-progress evidence is from `mineru-api.err.log`, but log-channel endpoint now reports configured logs as stale.
- Task evidence: `/__proxy/db/tasks` returned exactly 24 pressure tasks; state counts are 5 review-pending / 1 failed mineru-processing / 12 failed submit-failed-retryable / 6 pending upload.
- AI evidence: `/__proxy/db/ai-metadata-jobs` returned exactly 5 jobs, all `review-pending`.

## Review Need

Director review is required.

Follow-up production mutation requires explicit Director/User approval, ideally split into:

1. MinerU owner-name decision and MinerU-only relaunch authorization.
2. Post-relaunch read-only verification.
3. Optional submit-probe authorization.
4. Optional task-state reconciliation/retry/reparse authorization for the 19 unresolved pressure tasks.

