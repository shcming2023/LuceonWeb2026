# Test Acceptance Report: P1 Post Db-Sync Hardening Small Serial Validation

- Task ID: `TASK-20260514-142448-P1-Post-Db-Sync-Hardening-Small-Serial-Validation`
- Task brief: `TaskAndReport/2026-05-14T14-24-48+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T14:35:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes
- Validation level: production small strict-serial UI upload validation

## Required Reading

Completed required reading from the task brief:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- current task brief
- `TaskAndReport/2026-05-14T14-05-03+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T14-22-01+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-14T14-22-01+0800_P1-Next-Validation-Scope-After-Db-Sync-Fresh-Upload-Pass_DECISION.md`

## Scope

Executed the user-approved Option A boundary:

- maximum allowed uploads: `3`
- actual uploads: `3`
- mode: strictly serial; each upload reached terminal state and post-terminal runtime checks were safe before the next upload
- sample source: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- upload path: UI file input on `http://localhost:8081/cms/tasks`

Not performed: concurrent upload, pressure, batch, soak, L3, release-readiness, go-live claim, cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets/config/model/sample mutation, Docker down/volume cleanup, service ownership mutation, broad deployment/rebuild/rollback, or source-code change.

## Workspace And HEAD Evidence

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch during check: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Worktree: dirty shared role workspace with many pre-existing modified/untracked files and TaskAndReport records.

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD requirement: on/includes `4eb2e3b Accept db-sync warning hardening`
- Each upload preflight confirmed production HEAD contained `4eb2e3b`.
- Production worktree had pre-existing dirty files; no unrelated files were reverted.

## Commands And Exit Codes

Development workspace:

- `git status --short --branch` - exit 0
- task ledger, task brief, role, policy, PRD, report, review, and decision reads - exit 0

Production workspace:

- Per-upload preflight used:
  - development `git status --short --branch` - exit 0
  - production `git status --short --branch` - exit 0
  - production `git log -1 --oneline` - exit 0
  - `docker compose ps` - exit 0
  - `/__proxy/upload/health` - HTTP OK
  - `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true` - HTTP OK
  - `/__proxy/upload/ops/mineru/admission-circuit` - HTTP OK
  - `/__proxy/upload/ops/mineru/active-task` - HTTP OK
  - direct MinerU `/health` - HTTP OK
- Serial Playwright UI upload/observation script - exit 0

Observation artifact: `/tmp/luceon-task134-observations.json`.

## Preflight And Postflight Summary

Before every upload and after every terminal state:

- Docker services were healthy.
- Production HEAD included `4eb2e3b`.
- Upload health was OK.
- Dependency-health was `ok=true`, `blocking=false`.
- Admission circuit was closed.
- Parse/AI pending/running counts were `0/0` before each upload and after each terminal state.
- Active-task had no active/current/queued/drift/submit-retryable/takeover-required work.
- Direct MinerU was healthy with queued `0`, processing `0`, failed `0`.

No unsafe preflight or post-terminal runtime condition occurred.

## Sample And Result Matrix

| Label | Sample | Size | SHA-256 | Task / Material | MinerU / AI job | Final state | Parsed files |
| --- | --- | ---: | --- | --- | --- | --- | ---: |
| s1 | `/Users/concm/prod_workspace/Luceon2026/testpdf/财务回执(￥50,000.00).pdf.pdf` | `96870` | `40f67c5e5ba41bd4b0c322d128b3274fff4527f93cf75b774f7a67b863038e31` | `task-1778740127704` / `1457753975095108` | `92134a1f-2a35-49e6-afe5-a48d00352855` / `ai-job-1778740137981-b608` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `9` |
| s2 | `/Users/concm/prod_workspace/Luceon2026/testpdf/向树叶学习：人工光合作用.pdf` | `86884` | `2230acbb40524e1de80f1ebe57a13c5f41db353e15c6727f5ebb97383154e16c` | `task-1778740183408` / `4266893951443412` | `b6025132-0167-4f83-b056-b32447c97028` / `ai-job-1778740199344-2920` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `8` |
| s3 | `/Users/concm/prod_workspace/Luceon2026/testpdf/蓝月、血月、橙月？月亮为啥还会变色？.pdf` | `76797` | `80ece67614c1808a4247496402ceb71b4dd0fdd09ecae9023723c4a530fcb244` | `task-1778740275811` / `3508165266955156` | `a21e0022-d64a-466a-93ba-9e36839959da` / `ai-job-1778740283440-0a5f` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `8` |

All three AI jobs ended `review-pending` with model `qwen3.5:9b`.

All three state sequences were:

`pending -> running -> ai-pending -> ai-running -> review-pending`

All three stage sequences were:

`upload -> mineru-processing -> complete -> ai -> review`

Sample handling: read-only. No sample was copied, moved, renamed, edited, deleted, truncated, or committed.

## Db-Sync / Console / Network Evidence

Per-upload counts:

| Label | `[db-sync]` console | `/settings/` console | `/secrets` console | `Failed to fetch` console | HTTP 503 console | HTTP 503 network | PUT `/settings/*` | PUT `/secrets` | Request failures | Settings/secrets request failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| s1 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |
| s2 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |
| s3 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |

The two request failures per upload were expected Playwright/navigation-close SSE aborts:

- `GET /__proxy/upload/tasks/stream` -> `net::ERR_ABORTED`
- `GET /__proxy/upload/tasks/stream?taskId=<taskId>` -> `net::ERR_ABORTED`

No request failure involved `/settings/*` or `/secrets`.

Result: Task 128's no-op db-sync settings/secrets warning pattern did not recur across this three-PDF strict serial validation.

## Progress Semantics Evidence

Task detail:

- s1: `当前进展` present in `32/33` observations.
- s2: `当前进展` present in `57/58` observations.
- s3: `当前进展` present in `44/45` observations.

Task list:

- The list page row for each sample showed the uploaded filename, truncated task id, stage, engine `LOCAL-MINERU`, state `待复核`, and `状态一致` at final refresh.
- During processing, list rows showed progress/status text. Examples:
  - s1: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
  - s2: `MinerU 正在解析：backend=pipeline，相位 版面识别，批次 1/1，页 4/4`
  - s3: `MinerU 正在解析：backend=pipeline`
- s2 and s3 retained the Task 132-style residual in terminal/final row text: `MinerU 已完成，但本次未捕获可归因业务进度日志`.

## Final Runtime Evidence

After s3 terminal state:

- Production HEAD still included `4eb2e3b`.
- Docker services healthy.
- Dependency-health `ok=true`, `blocking=false`.
- Admission circuit closed.
- Parse/AI pending/running counts `0/0`.
- Active-task clean.
- Direct MinerU healthy with no queued/processing/failed task.

Historical AI failure rows remained listed separately in active-task diagnostics and were not part of this task.

## Artifacts

- Observation artifact: `/tmp/luceon-task134-observations.json`
- Screenshots:
  - `/tmp/luceon-task134-s1-before-upload.png`
  - `/tmp/luceon-task134-s1-list-1.png`
  - `/tmp/luceon-task134-s1-list-5.png`
  - `/tmp/luceon-task134-s1-list-32.png`
  - `/tmp/luceon-task134-s1-detail-1.png`
  - `/tmp/luceon-task134-s1-detail-5.png`
  - `/tmp/luceon-task134-s1-detail-32.png`
  - `/tmp/luceon-task134-s1-post-final-list.png`
  - `/tmp/luceon-task134-s1-post-final-detail.png`
  - `/tmp/luceon-task134-s2-before-upload.png`
  - `/tmp/luceon-task134-s2-list-1.png`
  - `/tmp/luceon-task134-s2-list-5.png`
  - `/tmp/luceon-task134-s2-list-57.png`
  - `/tmp/luceon-task134-s2-detail-1.png`
  - `/tmp/luceon-task134-s2-detail-5.png`
  - `/tmp/luceon-task134-s2-detail-57.png`
  - `/tmp/luceon-task134-s2-post-final-list.png`
  - `/tmp/luceon-task134-s2-post-final-detail.png`
  - `/tmp/luceon-task134-s3-before-upload.png`
  - `/tmp/luceon-task134-s3-list-1.png`
  - `/tmp/luceon-task134-s3-list-5.png`
  - `/tmp/luceon-task134-s3-list-44.png`
  - `/tmp/luceon-task134-s3-detail-1.png`
  - `/tmp/luceon-task134-s3-detail-5.png`
  - `/tmp/luceon-task134-s3-detail-44.png`
  - `/tmp/luceon-task134-s3-post-final-list.png`
  - `/tmp/luceon-task134-s3-post-final-detail.png`

## Skipped Checks And Reasons

- No fourth upload was run because the task authorized at most three uploads.
- No concurrent, pressure, batch, soak, L3, release-readiness, or go-live validation was run because forbidden by the task.
- No cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets mutation, source-code change, or runtime/service mutation was run because forbidden by the task.

## Risks And Residual Issues

- This is still small strict-serial evidence only; it does not prove pressure, batch, soak, L3, release-readiness, or go-live.
- The terminal progress-attribution residual persists for at least s2/s3: final UI text can say `MinerU 已完成，但本次未捕获可归因业务进度日志` even when task/material/AI states are coherent.
- Request failures caused by SSE aborts on page close/navigation remain observable but are unrelated to settings/secrets/db-sync and did not affect terminal outcomes.
- Historical AI failures remain listed by active-task diagnostics; they were not mutated.
- Production and development worktrees remain dirty with pre-existing unrelated changes.

## Acceptance Judgment

Recommendation: `pass with residual risks`.

Rationale:

- All three authorized uploads completed under strict serial control.
- Every upload reached coherent terminal state: task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed`, AI job `review-pending`.
- Preflight and post-terminal checks were safe for every upload.
- Db-sync/settings/secrets warning recurrence did not occur across all three uploads.
- No forbidden operation was performed and no readiness/L3/go-live claim is made.

Director review is required for final task acceptance and next-step decision.
