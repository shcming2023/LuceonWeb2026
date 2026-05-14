# Test Acceptance Report: P1 Extended Strict Serial Validation After Small Serial Pass

- Task ID: `TASK-20260514-144550-P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass`
- Task brief: `TaskAndReport/2026-05-14T14-45-50+0800_P1-Extended-Strict-Serial-Validation-After-Small-Serial-Pass_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: 2026-05-14T15:08:00+0800
- Workspaces used: development and production
- Entered production deployment path: yes
- Validation level: production extended strict-serial UI upload validation

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
- `TaskAndReport/2026-05-14T14-24-48+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T14-42-24+0800_P1-Post-Db-Sync-Hardening-Small-Serial-Validation_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-14T14-42-24+0800_P1-Next-Validation-Scope-After-Small-Serial-Pass_DECISION.md`

## Scope

Executed the user-approved Option A boundary:

- maximum allowed uploads: `6`
- actual uploads: `6`
- mode: strictly serial; each upload reached terminal state and post-terminal runtime checks were safe before the next upload
- sample source: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- upload path: UI file input on `http://localhost:8081/cms/tasks`
- sample selection: all six selected files were not used in Tasks 132 or 134

Not performed: concurrent upload, pressure, batch, soak, L3, pressure PASS, release-readiness, go-live claim, cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets/config/model/sample mutation, Docker down/volume cleanup, service ownership mutation, broad deployment/rebuild/rollback, or source-code change.

## Workspace And HEAD Evidence

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch during check: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Worktree: dirty shared role workspace with many pre-existing modified/untracked files and TaskAndReport records.

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD requirement: includes `4eb2e3b Accept db-sync warning hardening`
- Every upload preflight confirmed production HEAD contained `4eb2e3b`.
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
- One mid-run read-only status probe during s6 MinerU processing - exit 0; confirmed active task was the current authorized s6 parse.

Observation artifact: `/tmp/luceon-task136-observations.json`.

## Preflight And Postflight Summary

Before every upload and after every terminal state:

- Docker services were healthy.
- Production HEAD included `4eb2e3b`.
- Upload health was OK.
- Dependency-health was `ok=true`, `blocking=false`.
- Admission circuit was closed.
- Parse/AI pending/running counts were `0/0` before each upload and after each terminal state.
- Active-task had no active/current/queued/drift/submit-retryable/takeover-required work outside the current authorized in-flight upload.
- Direct MinerU was healthy with queued `0`, processing `0`, failed `0`.

No unsafe preflight or post-terminal runtime condition occurred.

## Sample And Result Matrix

| Label | Sample | Previously used in Tasks 132/134 | Size | SHA-256 | Task / Material | MinerU / AI job | Final state | Parsed files |
| --- | --- | --- | ---: | --- | --- | --- | --- | ---: |
| s1 | `/Users/concm/prod_workspace/Luceon2026/testpdf/出国.pdf` | no | `33814` | `444b2acfa19f23758059cb799848a05e09821b2c6f5a53e64ff39cfbd935444f` | `task-1778741470357` / `2940075716431972` | `55b90501-30c2-4718-98f0-301e44fbed93` / `ai-job-1778741486517-e7a6` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `8` |
| s2 | `/Users/concm/prod_workspace/Luceon2026/testpdf/PDF document-4F18-A8A3-62-0.pdf` | no | `711046` | `bb491c5782c001a60e9af1c8d531cbf3ce9807f0db341af765c31cc2d75e56f4` | `task-1778741537754` / `4196147960597252` | `1806c4f5-f44c-4f4f-9e45-e4bf3ce416b8` / `ai-job-1778741543707-4b6a` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `9` |
| s3 | `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf` | no | `530205` | `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb` | `task-1778741619870` / `3439586851712516` | `fede7707-fbb3-42f9-805f-a8b872befb2c` / `ai-job-1778741629933-4128` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `21` |
| s4 | `/Users/concm/prod_workspace/Luceon2026/testpdf/期末质量分析及建议（曹云童 ）.pdf` | no | `1041695` | `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8` | `task-1778741710716` / `4260342169678244` | `80a95595-5a71-476c-9faf-32e3ed4984f6` / `ai-job-1778741736316-0e8e` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `21` |
| s5 | `/Users/concm/prod_workspace/Luceon2026/testpdf/走向成功_英语_二模卷16篇.pdf` | no | `3457503` | `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac` | `task-1778741838537` / `1476308125891172` | `a92d309b-5893-487f-9d32-9134f2f3a972` / `ai-job-1778741872147-411f` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `25` |
| s6 | `/Users/concm/prod_workspace/Luceon2026/testpdf/附件三：考务流程培训-纸笔标准考试.pdf` | no | `5349060` | `d2e8e9bcd5b59e88a516d2143ece6a03060bf01276481e09d7577a5f82c5ae5a` | `task-1778741990445` / `181918346486532` | `2ab31f05-da0c-44bb-a242-64cf1e2095a8` / `ai-job-1778742087445-19ea` | task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed` | `82` |

All six AI jobs ended `review-pending` with model `qwen3.5:9b`.

All six state sequences were:

`pending -> running -> ai-pending -> ai-running -> review-pending`

All six stage sequences were:

`upload -> mineru-processing -> complete -> ai -> review`

Sample handling: read-only. No sample was copied, moved, renamed, edited, deleted, truncated, or committed.

## Db-Sync / Console / Network Evidence

Per-upload counts:

| Label | `[db-sync]` console | `/settings/` console | `/secrets` console | `Failed to fetch` console | HTTP 503 console | HTTP 503 network | PUT `/settings/*` | PUT `/secrets` | Request failures | Settings/secrets request failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| s1 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `3` | `0` |
| s2 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `3` | `0` |
| s3 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |
| s4 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `3` | `0` |
| s5 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |
| s6 | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `2` | `0` |

Request failures were limited to browser navigation/close aborts:

- `GET /__proxy/upload/tasks/stream` -> `net::ERR_ABORTED`
- `GET /__proxy/upload/tasks/stream?taskId=<taskId>` -> `net::ERR_ABORTED`
- in s1/s2/s4, one additional `GET /__proxy/upload/ops/dependency-health` abort occurred during page close/navigation

No request failure involved `/settings/*` or `/secrets`.

Result: Task 128's db-sync/settings/secrets warning pattern did not recur across this six-PDF extended strict-serial validation.

## Progress Semantics Evidence

Task detail `当前进展` visibility:

- s1: `40/41` observations
- s2: `50/51` observations
- s3: `55/56` observations
- s4: `80/81` observations
- s5: `96/97` observations
- s6: `129/130` observations

Task list examples during MinerU processing:

- s1: `MinerU 正在解析：backend=pipeline，相位 版面识别，批次 1/1，页 1/1`
- s1: `MinerU 正在解析：backend=pipeline，相位 OCR 检测，批次 1/1，页 1/1`
- s2: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
- s3: `MinerU 正在解析：backend=pipeline，相位 公式/版面模型识别，批次 1/1，页 3/3`
- s4: progress mostly surfaced as terminal/previous-row snippets and terminal attribution residual
- s5: `MinerU 正在处理，但日志观测滞后：backend=pipeline`
- s6: `MinerU 正在解析：backend=pipeline` and `MinerU 正在处理，但日志观测滞后：backend=pipeline`

Terminal/final list rows:

- All six final list rows showed uploaded filename, truncated task id, stage `review`, engine `LOCAL-MINERU`, state `待复核`, and `状态一致`.
- s2/s3/s4/s5 terminal rows included `MinerU 已完成，但本次未捕获可归因业务进度日志`.
- s1/s6 terminal rows showed AI completion without that terminal MinerU residual in the captured final list snippet.

Interpretation:

- Operator-visible progress was present throughout detail pages and often visible in list rows.
- The known progress-attribution residual still appears for several samples, especially terminal/final row text after successful completion.
- This residual did not prevent coherent terminal task/material/MinerU/AI state.

## Final Runtime Evidence

After s6 terminal state:

- Production HEAD still included `4eb2e3b`.
- Docker services healthy.
- Dependency-health `ok=true`, `blocking=false`.
- Admission circuit closed.
- Parse/AI pending/running counts `0/0`.
- Active-task clean.
- Direct MinerU healthy with no queued/processing/failed task.

Historical AI failure rows remained listed separately in active-task diagnostics and were not part of this task.

## Artifacts

- Observation artifact: `/tmp/luceon-task136-observations.json`
- Screenshots: `/tmp/luceon-task136-s{1..6}-*.png`, including pre-upload, selected list/detail observations, and post-final list/detail screenshots for each sample.

## Skipped Checks And Reasons

- No seventh upload was run because the task authorized at most six uploads.
- No concurrent, pressure, batch, soak, L3, pressure PASS, release-readiness, or go-live validation was run because forbidden by the task.
- No cleanup, repair, reparse, re-AI, failed-task mutation, settings/secrets mutation, source-code change, or runtime/service mutation was run because forbidden by the task.

## Risks And Residual Issues

- This is extended strict-serial evidence only; it does not prove pressure, batch concurrency, soak, L3, release-readiness, or go-live.
- Terminal MinerU progress attribution remains imperfect: several successful tasks still show `MinerU 已完成，但本次未捕获可归因业务进度日志`.
- Some in-flight progress was `日志观测滞后` rather than fresh attributable business progress. This supports treating the progress-attribution item as an observability residual, not a terminal pipeline failure.
- Request failures caused by SSE/dependency-health aborts on page close/navigation remain observable but are unrelated to settings/secrets/db-sync and did not affect terminal outcomes.
- Historical AI failures remain listed by active-task diagnostics; they were not mutated.
- Production and development worktrees remain dirty with pre-existing unrelated changes.

## Acceptance Judgment

Recommendation: `pass with residual risks`.

Rationale:

- All six authorized uploads completed under strict serial control.
- Every upload reached coherent terminal state: task `review-pending`, material `reviewing`, MinerU `completed`, AI `analyzed`, AI job `review-pending`.
- Preflight and post-terminal checks were safe for every upload.
- Db-sync/settings/secrets warning recurrence did not occur across all six uploads.
- No forbidden operation was performed and no readiness/L3/pressure/go-live claim is made.

Director review is required for final task acceptance and next-step decision.
