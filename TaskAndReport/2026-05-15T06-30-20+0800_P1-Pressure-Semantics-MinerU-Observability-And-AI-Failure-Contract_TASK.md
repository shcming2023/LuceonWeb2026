# Task 157: P1 Pressure Semantics, MinerU Observability, And AI Failure Contract

Task ID: `TASK-20260515-063020-P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract`

Created: 2026-05-15T06:30:20+0800

Assigned Role: `DevelopmentEngineer`

Status: `下达待执行`

Expected Report: `TaskAndReport/2026-05-15T06-30-20+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract_REPORT.md`

## Context

This task supersedes and merges the prior pending/corrected work around Tasks 154, 155, and 156.

Director correction: the user clarified that Task 154 has not actually been executed. Existing Task 154 report/review artifacts must remain traceable, but must not be treated as accepted implementation evidence. Tasks 155 and 156 are withdrawn before execution and merged here.

The immediate trigger is the user-observed 24-file manual pressure submission. The user observed that:

- Page semantics and real logs are inconsistent, making manual judgment difficult.
- Current project judgment of whether MinerU is active/successful appears not to fully use raw MinerU output logs.
- A concrete observation showed raw logs first appearing stuck at `Table-ocr det 65/66`, then later advancing to `Table-ocr det 66/66`, `Table-ocr rec`, `Table-wireless`, `Table-wired`, and finally `OCR-det ch 7/45` at sample time.
- Direct MinerU API still returned `status=processing`, `error=null`, `completed_at=null`.
- Only a few of the 24 tasks fell into AI recognition failure; this should not be flattened into "overall failure" when most tasks, including large files, succeeded and the failed AI recognition cases are retryable.

## Objective

Make the code-level semantics match the real runtime facts:

1. A MinerU task whose direct MinerU API status is still `processing` and whose raw MinerU logs show fresh advancement must not be presented or classified as terminal failure/stall merely because a page-side summary or sidecar observation is stale.
2. Pressure/manual batch outcomes must distinguish systemic failure from partial success with retryable AI residuals.
3. AI recognition timeout/transport failures must be classified and recorded as manual-retry-eligible failed AI residuals in both Material and ParseTask state, without introducing automatic retry or skeleton fallback.

## Required Reading

Before implementation, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- This task brief
- The following traceability artifacts as context only:
  - `TaskAndReport/2026-05-15T06-30-20+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Contract-Merge-Decision_DECISION.md`
  - Task 153 report/review
  - Task 154 task/report/review, with the correction that it is superseded and not accepted as executed implementation evidence
  - Task 155 and Task 156 task briefs, with the correction that they are withdrawn and merged here

## Implementation Scope

### 1. MinerU Progress Truth And Observability

Inspect existing task-page, ops endpoint, sidecar, and upload/task state code. Then improve the existing implementation so that operator-facing semantics can distinguish:

- Direct MinerU API says the task is still processing.
- Direct MinerU API reports terminal success.
- Direct MinerU API reports terminal error.
- Luceon local timeout has occurred, but remote MinerU still reports processing.
- Page/sidecar observation is stale or weaker than raw MinerU log evidence.
- Raw MinerU logs show fresh stage advancement even if a compact summary line looks stuck.

Use existing project patterns and keep the change scoped. Do not create a new broad observability subsystem unless the current code has no smaller integration point.

### 2. UI / Page Semantics

Update the relevant task page and/or task list semantics so the operator can tell the difference between:

- "MinerU is still processing and raw logs are advancing."
- "Observation is stale; direct MinerU still processing."
- "Local Luceon timeout happened, but remote MinerU is still processing."
- "Terminal MinerU failure."
- "Parse succeeded, but AI metadata failed and is manually retry eligible."

Avoid wording that makes a still-processing MinerU task look like a final failed state.

### 3. Pressure Result Semantics

Where pressure/manual batch result classification is represented in code, task state, report helpers, or UI labels, make the semantics explicit:

- A run with most parse tasks successful, large files successful, and a small number of AI timeout/transport failures should be represented as partial success with retryable AI residuals, not as full pressure failure.
- A systemic failure requires evidence such as broad parse failures, DB/MinIO systemic failure, terminal MinerU error affecting the batch, all tasks stuck without fresh advancement, or another explicit infrastructure-wide failure signal.

If this project does not yet have a single pressure-summary module, implement the smallest practical code/test hook or documented helper that prevents future reports/UI from flattening these outcomes incorrectly.

### 4. AI Failure Classification And Backfill

Implement the missing code-level contract from the superseded 154/156 work:

- Transport-style AI failures such as timeout, connection failure, 5xx, stream interruption, or Ollama unavailable should be classified as AI recognition residuals eligible for manual retry.
- This classification must be visible in AI job/task events and also backfilled into Material and ParseTask metadata/state where the UI and future operators can find it.
- Do not mark schema validation, JSON repair failure, or untrusted AI output as equivalent transport retryability unless existing project policy already does so.
- Do not introduce automatic retry, automatic requeue, or any skeleton fallback.

## Non-Goals

This task does not authorize:

- Production deployment.
- Upload, pressure/batch/soak test, or new sample submission.
- Cleanup, cancel, repair, retry, reparse, or re-AI for existing tasks.
- Destructive DB, MinIO, Docker volume, Docker data, or local filesystem operations.
- Docker down/restart/rebuild or service ownership changes.
- Settings, secrets, config, model, or sample-library mutation.
- Automatic retry/requeue.
- Skeleton fallback weakening.
- Any pressure PASS, L3, release-readiness, production-readiness, or go-live claim.

## Acceptance Criteria

1. Still-processing MinerU tasks with direct API `processing` and raw log advancement are not classified or displayed as terminal failures solely because a page summary is stale.
2. The UI or exposed task semantics clearly show stale observation versus fresh raw-log advancement.
3. AI timeout/transport failures are recorded as manual-retry-eligible AI residuals in Material and ParseTask state.
4. Partial success with retryable AI residuals is represented separately from systemic pressure failure.
5. Focused tests cover:
   - Raw MinerU log advancement beyond a stale summary.
   - Direct MinerU `processing` overriding terminal-looking local timeout language.
   - AI transport failure classification and Material/ParseTask backfill.
   - Partial success with retryable AI residuals not being classified as whole-run/systemic failure.
6. Existing required checks continue to pass.

## Required Checks

Run and report exit codes for:

- `git diff --check`
- Syntax checks for changed server `.mjs` files, for example `node --check <file>`
- Any newly added or directly relevant smoke/unit tests
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build` if frontend code changes

If any check is skipped, explain the exact reason.

## Reporting Requirements

Write the completion report at:

`TaskAndReport/2026-05-15T06-30-20+0800_P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract_REPORT.md`

The report must include:

- Branch and HEAD.
- Files changed.
- Implementation summary.
- Exact commands and exit codes.
- Test evidence.
- Any skipped checks and exact reasons.
- Residual risks and technical debt.
- Whether Director review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md` so this row becomes `已回报待 Director 审查`, `Next Actor=Director`, with the report path filled in.
