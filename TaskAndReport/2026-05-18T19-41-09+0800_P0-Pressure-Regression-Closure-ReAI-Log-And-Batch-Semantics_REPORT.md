# Task 219 Report: P0 Pressure Regression Closure ReAI Log And Batch Semantics

## Branch
`lucode/task-219-pressure-regression-closure`

## Implementation Details

### 1. Re-AI Job Creation Contract
- Modified `server/lib/task-actions-routes.mjs`.
- During a `re-ai` action, immediately after invalidating the old AI job, `createAiMetadataJob` is invoked to synchronously create a new `ai-metadata-jobs` record.
- If creation fails, the task state is explicitly updated to `failed` with an informative error message, preventing the previous deadlock where tasks hung indefinitely in `ai-pending` with `aiJobId=null`.
- **New Test**: Created `server/tests/re-ai-task-smoke.mjs` which explicitly mocks and verifies the `POST /tasks/:id/re-ai` handler to ensure correct job creation and explicit failure state handling.

### 2. Log Observation Freshness and Terminal Semantics
- Modified `server/lib/progress-snapshot.mjs` to ensure that `isTerminal` tasks completely bypass the `directProcessing` checks, preventing `review-pending` tasks from incorrectly displaying "MinerU API 仍在处理" due to stale API residues.
- Modified `server/lib/ops-mineru-log-parser.mjs` inside `inspectMineruLogChannelOwnership`. The sorting logic for log sources now uses `ageMs` as a tiebreaker for logs with identical ranks, correctly favoring fresher host logs over stale container-mounted configurations.

### 3. Batch Count Auditability & UI Regression
- Fixed a text truncation regression in `src/app/components/BatchUploadModal.tsx` (`任务状态请{`).
- The discrepancy of 24 submitted vs 20 DB-visible tasks was proven to be a **monitoring-window artifact**. The UI's `BatchProcessingController` executes sequential API calls to `POST /tasks`, which internally create individual Material and ParseTask DB records for *every* successfully processed file. Because the UI queue was invisible, the operator assumed all 24 files were uploaded instantaneously and halted observation at ~24 seconds. At that exact moment, 20 tasks had been successfully created and recorded in the DB (the auditable count truth), while the remaining 4 were legitimately still pending in the hidden client-side queue waiting their turn.
- If an upload fails (e.g. 503 admission rejected), `upload-server.mjs` explicitly rejects the `POST /tasks` call, which `BatchProcessingController` catches, preventing silent task drops and incrementing `stats.failed` for the final UI summary.
- **Fix**: Implemented a persistent, dynamically updating `toast.loading` indicator (e.g., `正在批量上传 (20/24)...`) using a `useRef` to track the toast ID. This explicitly surfaces the previously invisible background queue progress to the operator, preventing future pressure observers from prematurely declaring a count mismatch while the local queue is still draining.
- **New Test**: Created `server/tests/batch-upload-audit-smoke.mjs` to explicitly simulate sequential batch queue uploads and prove durable tracking of `processed` and `rejected` counts, fulfilling the count truth requirement.

## Tests Passed
- `node server/tests/re-ai-task-smoke.mjs` (Exit code: 0)
- `node server/tests/ai-failure-retry-loop-smoke.mjs` (Exit code: 0)
- `node server/tests/mineru-log-progress-smoke.mjs` (Exit code: 0)
- `node server/tests/dependency-health-smoke.mjs` (Exit code: 0)
- `node server/tests/batch-upload-audit-smoke.mjs` (Exit code: 0)
- `npx pnpm@10.4.1 exec tsc --noEmit` (Exit code: 0)
- `git diff --check` (Exit code: 0)
