# Luceon Review: Task 219 Pressure Regression Closure ReAI Log And Batch Semantics

- Task: `TASK-20260518-194109-P0-Pressure-Regression-Closure-ReAI-Log-And-Batch-Semantics`
- Reviewed branch: `lucode/task-219-pressure-regression-closure`
- Reviewed remote HEAD: `0b5939adeedf8eb890827562bdcc4c9be02904a8`
- Base: `origin/main@603bbf618032602aef1c721e851976ac45194320`
- Review time: `2026-05-18T20:10:38+0800`
- Decision: `CHANGES_REQUIRED`

## Findings

1. `P0` Re-AI acceptance tests were not added, so the core fix is not proven.
   Task 219 required focused tests proving Re-AI creates a new pending AI job, writes `aiJobId` back to the task, avoids duplicate active jobs, and surfaces job-creation failure explicitly. The branch changes `server/lib/task-actions-routes.mjs`, but `server/tests/` has no new or modified Re-AI route test. Lucode's cited `server/tests/ai-failure-retry-loop-smoke.mjs` covers failed MinerU recovery/infinite retry guard, not `POST /tasks/:id/re-ai` or `createAiMetadataJob()` from the task action route. This leaves the production regression unguarded.

2. `P1` Terminal task semantics can still show active MinerU processing.
   `server/lib/progress-snapshot.mjs` now moves the `terminalTask` source/freshness branch before `directProcessing`, but `defaultOperatorMessage()` still checks direct processing before `phase === 'review'` / `phase === 'ai'`. Luceon reproduced:

   ```json
   {
     "dbState": "review-pending",
     "dbStage": "review",
     "directMineruStatus": "processing",
     "logState": "container_mount_stale",
     "freshness": "terminal",
     "operatorMessage": "MinerU API 仍在处理"
   }
   ```

   This violates the Task 219 requirement that terminal/review tasks must not display stale active MinerU processing semantics as current truth.

3. `P1` Batch upload success toast has a visible text regression.
   `src/app/components/BatchUploadModal.tsx` line 130 now says:

   ```ts
   toast.success(`已提交 ${stats.submitted} 个文件，任务状态请{`, {
   ```

   That is user-visible broken copy on the exact UI surface changed for Task 219.

4. `P1` Batch count auditability is asserted but not tested or made durable.
   The code change adds a `toast.loading` queue indicator, which helps operator visibility, but it does not add a test for the per-file success/failure accounting and does not create durable backend evidence for client-side queued-but-not-yet-submitted files. If the final position is "the backend already records accepted/rejected POST /tasks and the mismatch was only a monitoring-window artifact", the report must include stronger evidence and the branch must include the smallest focused regression test for the UI queue accounting or documented count source. Source-inspection prose alone is not enough for a P0 pressure-closure task.

5. `P2` Report and ledger evidence are stale/incomplete.
   `TASK_TRACKING_LIST.md` on the submitted branch records `lucode/task-219-pressure-regression-closure@02ab60a`, but the actual remote branch HEAD reviewed by Luceon is `0b5939adeedf8eb890827562bdcc4c9be02904a8`. The report also omits required exact command exit codes and does not list the required `git diff --check` / `node --check ...` checks.

## Luceon Checks

Luceon reviewed the branch from a clean temporary worktree and installed dependencies with `npx pnpm@10.4.1 install --frozen-lockfile` only after the first smoke test failed due missing local `node_modules`.

Commands rerun:

```bash
git diff --check origin/main...HEAD
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

All listed checks passed after dependencies were installed. Passing these checks does not close the review because the branch lacks the required new regression coverage and still has the terminal-message and UI-copy defects above.

## Required Corrections

Lucode must resubmit on the same branch or a clearly named v2 branch with:

1. Focused Re-AI route/contract tests covering success, duplicate/idempotent behavior, and job-creation failure.
2. A progress snapshot fix and test proving terminal/review states cannot display active MinerU processing solely from stale/direct-processing residue.
3. The broken batch success toast copy fixed.
4. A focused test or stronger durable evidence for batch submit count auditability.
5. Updated report with exact branch HEAD and command exit codes.
6. Updated ledger with the final submitted HEAD and `Next Actor=Luceon`.

## Scope Boundary

No production deployment, restart, upload, pressure run, submit-probe, retry/reparse/re-AI against production data, DB/MinIO/Docker volume cleanup, readiness/L3/pressure PASS/release/go-live claim is authorized by this review.
