# TASK-20260515-202908-P1 Manual Clean 24-PDF Pressure Monitoring Report

- Role: TestAcceptanceEngineer
- Task brief: `TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_TASK.md`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`
- Development HEAD before report: `e858b68`
- Production HEAD during final snapshot: `1716add`
- Final snapshot time: 2026-05-16 05:53 +0800
- Scope: read-only monitoring of the User-started manual clean 24-PDF pressure run.
- Forbidden actions confirmation: no upload, reset/cleanup, manual MinerU submit-probe, retry/reparse/re-AI, cancel/repair, restart/rebuild/redeploy, DB/MinIO/Docker/config/secrets/models/sample mutation, pressure PASS, L3, release, production-readiness, or go-live claim.

## Summary

The pressure run reached a terminal observed state by the final read-only snapshot.

- Observed pressure tasks: 24
- Task final states: 23 `review-pending`, 1 `failed`
- Task final stages: 23 `review`, 1 `ai`
- Material MinerU status: 24 `completed`
- Material AI status: 23 `analyzed`, 1 `failed`
- Active/running/queued/AI-pending tasks at final snapshot: 0
- Direct MinerU final health: healthy, queued 0, processing 0, completed 48, failed 0
- Final admission circuit: closed, no active parse/AI backlog
- Final dependency health with `mineruSubmitProbe=false`: ok, non-blocking; Ollama readiness `resident-chat-succeeded` with `qwen3.5:9b`

Recommendation for Director: accept this monitoring evidence as terminal with residual issues. This is not a pressure PASS/L3/release-readiness/production-readiness/go-live claim.

## Snapshot Timeline

| Time (+0800) | Observed task state | Key evidence |
| --- | --- | --- |
| 2026-05-15 20:33 | 1 running, 23 pending | First 52.96 MB PDF active; direct MinerU processing and logs progressing. |
| 2026-05-15 21:36 | 1 review-pending, 1 running, 22 pending | First large PDF completed to review-pending; second 45.25 MB PDF running. Dependency-health no-submit timed out, but direct MinerU/API/logs showed progress. |
| 2026-05-16 00:36 | 4 review-pending, 1 failed, 1 running, 18 pending | One AI-stage failure appeared; active 96.5 MB PDF still progressing in MinerU logs/API. |
| 2026-05-16 03:36 | 12 review-pending, 1 failed, 1 AI-running, 2 AI-pending, 1 running, 7 pending | Direct MinerU showed no processing tasks for the DB-active item, while DB/active-task still lagged; logs showed smaller-file progress. |
| 2026-05-16 05:53 | 23 review-pending, 1 failed, 0 active | All observed pressure-run tasks terminal; MinerU queued/processing 0; admission closed; dependency-health ok with no submit-probe. |

## Final Counts

### Upload Tasks

| Metric | Count |
| --- | ---: |
| Total pressure-window tasks | 24 |
| `review-pending` | 23 |
| `failed` | 1 |
| `running` | 0 |
| `pending` | 0 |
| `ai-running` | 0 |
| `ai-pending` | 0 |
| Active/queued by active-task API | 0 |

### Materials

| Metric | Count |
| --- | ---: |
| Total pressure-window materials | 24 |
| Material status `reviewing` | 23 |
| Material status `failed` | 1 |
| MinerU status `completed` | 24 |
| AI status `analyzed` | 23 |
| AI status `failed` | 1 |

### AI Metadata Jobs

| Metric | Count |
| --- | ---: |
| Total pressure-window AI jobs | 24 |
| `review-pending` | 23 |
| `failed` | 1 |
| `qwen3.5:9b` review-pending jobs | 23 |

## Residual Failed Item

| Field | Value |
| --- | --- |
| Task ID | `task-1778848110965` |
| Material ID | `1161333216880605` |
| File | `Cambridge IGCSE(0607) International Mathematics Coursebook Extended_2018(Haese Mathematics).pdf` |
| Size | 45,247,007 bytes |
| Final task state/stage | `failed` / `ai` |
| MinerU task ID | `3e6a4a27-1066-4ddf-bc7f-2e71cd9b1df1` |
| Material MinerU status | `completed` |
| Failure message | `AI 识别失败：已归类为可人工评估手动重试的残留失败` |
| AI job ID | `ai-job-1778854627880-0a6f` |
| Classification | Isolated AI-stage residual failure; retry/manual-review candidate by product policy. Not evidence of whole-run system failure. |

## Successful Examples

Large PDF examples that reached review-pending:

| Task ID | File | Size |
| --- | --- | ---: |
| `task-1778848122289` | `Cambridge IGCSE(0580) Core and Extended Mathematics_2022(Cambridge University Press).pdf` | 102,034,314 |
| `task-1778848118902` | `Cambridge IGCSE(0580) Extended Mathematics Practice Book__2023(Cambridge University Press).pdf` | 103,549,160 |
| `task-1778848116953` | `Cambridge IGCSE(0580) Extended Mathematics Student Book_2018(Oxford University Press).pdf` | 96,516,982 |
| `task-1778848115048` | `Cambridge IGCSE(0606) and O Level(4037) Additional Mathematics _2018(Haese Mathematics).pdf` | 91,501,329 |

Small PDF examples that reached review-pending:

| Task ID | File | Size |
| --- | --- | ---: |
| `task-1778848133447` | `出国.pdf` | 33,814 |
| `task-1778848133541` | `蓝月、血月、橙月？月亮为啥还会变色？.pdf` | 76,797 |
| `task-1778848133768` | `财务回执(￥50,000.00).pdf.pdf` | 96,870 |

## Runtime Evidence

Commands were run read-only unless noted as local report writeback in the development workspace.

| Workspace | Command / endpoint | Exit code / result | Key output |
| --- | --- | --- | --- |
| Dev | `git status --short --branch` | 0 | `## main...origin/main` |
| Dev | `TaskAndReport/TASK_TRACKING_LIST.md` and task brief read | 0 | Task 190 assigned to TestAcceptanceEngineer before report. |
| Prod | `git status --short --branch` | 0 | `## main...origin/main` with local modified production files present. |
| Prod | `git rev-parse --short HEAD` | 0 | `1716add` |
| Prod | `curl -fsS http://localhost:8081/__proxy/upload/health` | 0 | `{"ok":true,"service":"upload-server"}` |
| Prod | `curl .../ops/dependency-health?mineruSubmitProbe=false` | 0 final snapshot | `ok=true`, `blocking=false`, MinerU ok, Ollama ok, readiness `resident-chat-succeeded`, counts parse/AI pending/running all 0. |
| Prod | `curl .../ops/admission-circuit` | 0 | Circuit `closed`; active task clean; parse/AI pending/running all 0. |
| Prod | `curl .../ops/mineru/active-task` | 0 | `activeTask=null`, queued empty, one historical AI failure task retained. |
| Prod | `curl http://127.0.0.1:8083/health` | 0 | healthy, queued 0, processing 0, completed 48, failed 0. |
| Prod | `/cms/tasks` HTTP check | 0 | HTTP 200, reachable. |
| Prod | DB task/material/AI job queries for pressure window | 0 | 24 tasks/materials/AI jobs; 23 review/analyzed, 1 AI failure. |
| Prod | MinerU log stat/tail | 0 | Business progress visible through final OCR/page processing; final stdout mostly API-noise after terminal state. |

## Production Dirty Summary

Production workspace had local modified files during final read-only monitoring:

- `.gitignore`
- `docker-compose.override.yml`
- `docs/codex/TEST_MATRIX.md`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `ops/runtime-ownership-status.sh`
- `server/db-server.mjs`
- `server/tests/worker-smoke.mjs`
- `src/app/components/BatchUploadModal.tsx`
- `src/app/pages/SourceMaterialsPage.tsx`

This report did not modify production files.

## Observability And Operator Semantics

Human operator semantics did not always match backend/log evidence during the run:

- At earlier snapshots, UI/active-task semantics could imply stale log observation while direct MinerU stdout/stderr logs and direct MinerU task API still showed real progress.
- Around the 03:36 snapshot, DB/active-task evidence lagged direct MinerU evidence: direct MinerU had completed the active MinerU task while DB still represented it as active/running.
- The final state is coherent across DB/material/AI-job/admission/direct MinerU evidence, but the intermediate mismatch makes manual judgment harder during long-running tasks.

Recommended follow-up: improve progress semantics by correlating DB state, active-task API, direct MinerU task status, and MinerU log business-progress timestamps instead of relying on a single source.

## Dependency And AI Findings

- Final dependency-health with `mineruSubmitProbe=false` was healthy and non-blocking.
- Earlier no-submit dependency-health calls timed out at 15 seconds while direct MinerU/API/log evidence still showed progress. This should be treated as observability/readiness-latency risk, not pressure-run failure by itself.
- Ollama final readiness succeeded with `qwen3.5:9b`.
- The only residual failure was an AI-stage failure after MinerU completion, so the failure should be handled as retry/manual-review residual work rather than whole-run parse failure.

## Acceptance Boundary

What this report supports:

- The User-started 24-PDF pressure run reached terminal observed state.
- Large PDFs and small PDFs both produced review-pending materials.
- MinerU completed all 24 pressure-window materials.
- One isolated AI recognition residual failure remains.
- No active/running/queued pressure task remained at final snapshot.

What this report does not support:

- No pressure PASS claim.
- No L3 claim.
- No release-readiness or production-readiness claim.
- No go-live claim.
- No claim that UI/operator semantics are sufficient without follow-up.

## Risks And Recommended Next Actions

1. Director should decide whether 23 review-pending plus 1 isolated AI-stage retry/manual-review candidate satisfies the pressure-run acceptance boundary.
2. Create a follow-up observability task for page/backend/log semantic alignment, especially active-task progress and log-staleness wording.
3. Create a follow-up resilience task for AI-stage retry/manual-review handling if the Director wants residual failures to be automatically routable.
4. Keep production dirty-state ownership separate from this monitoring task; this report only records it.

## Final Recommendation

Suggested Director decision: accept the monitoring evidence as complete with residuals, then route the isolated AI failure and observability mismatches as follow-up work. Final task acceptance and any release decision remain Director/User owned.
