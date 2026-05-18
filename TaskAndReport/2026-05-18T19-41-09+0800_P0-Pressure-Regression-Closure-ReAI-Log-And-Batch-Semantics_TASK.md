# TASK-20260518-194109-P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics

## 1. Task Summary

- Task ID: `TASK-20260518-194109-P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics`
- Task row: `219`
- Issued at: `2026-05-18T19:41:09+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Priority: `P0`
- Suggested branch: `lucode/task-219-pressure-regression-closure`
- Expected report path: `TaskAndReport/2026-05-18T19-41-09+0800_P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics_REPORT.md`

## 2. Context

This task closes the code/test follow-up from the 2026-05-18 production 24-PDF pressure regression and the user's manual Re-AI attempt on the single AI-failed task.

Observed production evidence from read-only monitoring:

- User-submitted expected batch count: `24`.
- DB-visible tasks in the submission window `2026-05-18T06:17:48Z` to `2026-05-18T06:18:12Z`: `20`.
- Final visible batch state before Re-AI: `0 queued / 0 processing / 19 review-pending / 1 failed`.
- The failed task was `task-1779085079151`, file `Cambridge IGCSE(0580)  Core and Extended Mathematics_2023(Hodder Education).pdf`, stage `ai`, strict AI failure from repair timeout/no-skeleton guard.
- User then triggered Re-AI. The task changed to `state=ai-pending`, `stage=ai`, `progress=80`, `message=用户发起 Re-AI，等待 AI Worker 拾取`, `aiJobId=null`.
- `/__proxy/db/ai-metadata-jobs?parseTaskId=task-1779085079151` still had only the old job `ai-job-1779096373808-f209`, marked `failed` by Re-AI. No new `pending` AI job was created.
- `/__proxy/upload/ops/dependency-health` showed `aiPending=0` and `aiRunning=0`; upload-server logs after Re-AI did not show `Created AI Metadata Job` or `ai-worker Picking up job`.
- Code inspection matched the runtime symptom: `reAiTask()` only marks the parse task `ai-pending` and clears `aiJobId`; `TaskWorker` does not pick up `ai-pending`; `AiMetadataWorker` scans only `ai-metadata-jobs` with `state=pending`.
- MinerU log observation still showed a channel freshness gap after the run:
  - host log `/Users/concm/ops/logs/mineru-api.err.log`: size `15702570`, mtime `2026-05-18T18:58:25+0800`, latest meaningful signals included `OCR-rec 113/113`, `Layout Predict 1/1`, `OCR-det 7/7`, `Processing pages 100% 1/1`;
  - upload-server container-mounted log `/host/mineru-logs/mineru-api.err.log`: size `15294736`, mtime `2026-05-18T18:22:18+0800`, latest visible signal still `MFR Predict 96% 576/599`;
  - all 20 visible batch tasks still carried stale log observation or stale diagnostic metadata after terminal task states.

This is not a release readiness, pressure PASS, L3, or go-live record. It is a focused repair task for the runtime/worker semantics exposed by the test.

## 3. Objective

Implement a code/test-level closure so the next pressure run is not blocked by the same three classes of ambiguity:

1. Re-AI must actually create or recover a runnable AI Metadata Job.
2. MinerU log/task semantics must not leave stale container observations as the apparent truth after host logs have moved on or tasks have reached terminal/review states.
3. Batch upload/task creation counts must be auditable so a user-submitted `N` files vs DB-visible `M` tasks mismatch is surfaced, not silently lost.

## 4. Required Fix Areas

### A. Re-AI Job Creation Contract

Fix the Re-AI path so `POST /tasks/:id/re-ai` cannot leave a task indefinitely in `ai-pending` with no active AI job.

Required behavior:

- invalidate or retire the previous AI job as today;
- create a new `ai-metadata-jobs` row in `state=pending` for the same parse task and parsed markdown object, or add a clearly tested worker self-heal path that creates it immediately from `ai-pending + aiJobId=null + markdownObjectName exists`;
- write the new `aiJobId` back to the parse task and metadata;
- preserve strict no-skeleton/no silent fallback semantics;
- handle double-click/idempotent Re-AI without duplicate active AI jobs;
- if job creation fails, surface an explicit failed/create-failed state and event instead of a quiet `ai-pending` stall;
- preserve existing resource checks: Material must exist and Markdown parsed artifact must exist.

### B. Log Observation Freshness And Terminal Semantics

Harden the log observation contract exposed through active-task/task-list semantics.

Required behavior:

- host-side sidecar or host log evidence must outrank stale container-mounted log observations when it is fresher and attributable;
- container-mounted log staleness must remain visible as an observability warning, not as the current MinerU phase for already terminal/review tasks;
- terminal states (`review-pending`, `completed`, `failed` after known AI failure) should not keep saying "MinerU API still processing" solely because stale historical metadata remains;
- active-task/dependency diagnostics should make these dimensions explicit:
  - direct MinerU lifecycle state;
  - host/sidecar log freshness;
  - container-mounted log freshness;
  - DB task state/stage;
  - whether the displayed progress is current, historical completion evidence, or diagnostic-only stale residue.
- do not weaken direct MinerU API lifecycle authority.

### C. Batch Count Auditability

Make the upload/task creation path auditable enough to explain or prevent `24 submitted` vs `20 DB-visible task records`.

Required behavior:

- identify where multi-file upload acceptance, task creation, and UI submission count can diverge;
- add or harden code/tests so per-file success/failure/task-id creation is visible to the UI/operator or at least recorded in a queryable event/response;
- do not silently report a batch as accepted when some files did not produce tasks;
- keep this scoped to evidence and safety. Do not add a new product workflow beyond what is necessary to expose the count truth.

If the count mismatch is proven to be a monitoring-window artifact rather than an upload/task bug, report the exact evidence and add the smallest guard/test that prevents future pressure reports from using an ambiguous time window.

## 5. Allowed Files

Lucode may modify focused backend/frontend/test files such as:

- `server/lib/task-actions-routes.mjs`
- `server/services/ai/metadata-job-client.mjs`
- `server/services/ai/metadata-worker.mjs`
- `server/services/queue/task-worker.mjs`
- `server/lib/progress-snapshot.mjs`
- `server/lib/ops-mineru-diagnostics.mjs`
- `server/lib/pressure-result-semantics.mjs`
- `server/upload-server.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `src/app/components/BatchUploadModal.tsx`
- `src/app/pages/TaskManagementPage.tsx`
- focused tests under `server/tests/`
- concise TaskAndReport docs needed for this task

Keep edits narrow. Do not touch unrelated UI redesign, CleanService/Mineru2Table, settings, taxonomy, or asset-library scope unless directly required by the three fix areas above.

## 6. Required Tests And Checks

Add or update focused tests that prove:

1. Re-AI from a failed/review-pending task creates a new pending AI job and writes the new `aiJobId` back to the task.
2. Re-AI cannot create duplicate active jobs for the same parse task.
3. Re-AI job creation failure leaves an explicit actionable state/event and does not silently stall.
4. AI strict no-skeleton fallback remains enforced.
5. Fresh host/sidecar log evidence outranks stale container log evidence.
6. Terminal/review tasks do not display stale active MinerU processing semantics as current truth.
7. Batch upload/task creation exposes per-file task creation success/failure or provides an exact auditable count source.

Run and report exact commands plus exit codes:

```bash
git diff --check
node --check server/lib/task-actions-routes.mjs
node --check server/services/ai/metadata-job-client.mjs
node --check server/services/ai/metadata-worker.mjs
node --check server/services/queue/task-worker.mjs
node --check server/upload-server.mjs
node server/tests/ai-failure-retry-loop-smoke.mjs
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

If a listed file is untouched or a check is not applicable, state that precisely. If Lucode adds new smoke tests, include them in the report with exit codes.

## 7. Forbidden Scope

- No production restart/rebuild/deploy.
- No upload, pressure run, submit-probe, retry/reparse/re-AI/approve/cancel/delete/reset against production data.
- No DB/MinIO/Docker volume cleanup or mutation.
- No model/secret/sample mutation.
- No broad architecture rewrite.
- No readiness, L3, pressure PASS, release-readiness, or go-live claim.

## 8. Required Report

Write:

`TaskAndReport/2026-05-18T19-41-09+0800_P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics_REPORT.md`

The report must include:

- task brief path;
- branch and HEAD;
- files changed;
- implementation summary by fix area A/B/C;
- exact commands and exit codes;
- evidence for every required test;
- explicit statement of any skipped test and reason;
- residual risks and production validation needs;
- whether Luceon review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Task 219 status: `Lucode 已回报待 Luceon 审查`
- Task 219 Next Actor: `Luceon`
- Include report path and branch/HEAD.

## 9. Acceptance Criteria

- A user-triggered Re-AI produces a runnable AI job or an explicit actionable failure; it no longer parks a task in `ai-pending` with no pending job.
- Operator/task-list semantics distinguish current MinerU progress from stale historical log residue after terminal states.
- Host/sidecar vs container log freshness conflict is explicit and cannot silently mislead the task list.
- Batch submit count and task creation count are auditable.
- Existing parsing and AI strict-failure policies are preserved.
- Code/test evidence is sufficient for Luceon review before any production deployment decision.
