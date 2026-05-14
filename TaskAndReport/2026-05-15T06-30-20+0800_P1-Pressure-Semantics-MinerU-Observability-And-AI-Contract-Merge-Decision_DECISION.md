# P1 Pressure Semantics, MinerU Observability, And AI Contract Merge Decision

Time: 2026-05-15T06:30:20+0800

Role: Director

## User Instruction

The user clarified:

- Task 154 has not actually been executed.
- Director may merge Tasks 155 and 156 into a single dispatch.
- The 24-file pressure submission was manually performed by the user.
- Observed result should not be flattened into "overall failure": only a few tasks fell into AI recognition failure, most tasks including large files were successful, and retryable failures can match the expected project workflow.
- MinerU progress judgment must respect raw MinerU logs and direct MinerU API status, not only stale page-side summaries.

## Director Correction

Rows 154, 155, and 156 are now superseded before further execution:

- Task 154 report/review artifacts remain in the repository for traceability only. They must not be treated as accepted implementation, production evidence, or proof that the task was actually executed.
- Task 155 is withdrawn before execution and merged into the new dispatch.
- Task 156 is withdrawn before execution and merged into the new dispatch.

## New Dispatch

Create Task 157 as the merged DevelopmentEngineer task:

`TASK-20260515-063020-P1-Pressure-Semantics-MinerU-Observability-And-AI-Failure-Contract`

This merged task should address:

1. MinerU progress truth and UI/page semantics when raw MinerU logs show continued advancement while page summaries are stale.
2. Pressure result semantics that distinguish systemic failure from partial success with retryable AI residuals.
3. AI failure classification and manual retry eligibility metadata backfill to Material and ParseTask state.

## Boundaries

This decision does not authorize production deployment, new uploads, pressure/batch/soak tests, cleanup, repair, retry/reparse/re-AI for existing tasks, destructive DB/MinIO/Docker volume/data operations, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or any pressure PASS/L3/release-readiness/production-readiness/go-live claim.
