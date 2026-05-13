# TASK-20260513-193320-P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair Director Review

- Role: Director
- Review time: 2026-05-13T19:45:57+0800
- Reviewed report: `TaskAndReport/2026-05-13T19-33-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-AI-JSON-Repair_REPORT.md`
- Production HEAD under validation: `de2d23f`
- Validation task: `task-1778672291622`
- Material: `validation-json-repair-1778672290`
- MinerU task: `4affdec7-13aa-4a28-806d-07e71aad536d`
- AI job: `ai-job-1778672312564-0b2f`

## Decision

`ACCEPTED_CONTROLLED_UPLOAD_VALIDATION_BOUNDARY_PASS`

I accept Task 98 at the assigned validation boundary: exactly one authorized production upload after the AI JSON repair deployment reached the safe human-review terminal state.

This is not production readiness, release readiness, L3, pressure PASS, batch PASS, or soak PASS.

## Evidence Reviewed

The TestAcceptanceEngineer report states that the authorized sample:

- matched expected SHA-256 `71b95d983cdf73507c7334d3682f117f1dfce454286a6bb9f60d437a070b3cfb`;
- created exactly one upload task `task-1778672291622`;
- completed MinerU parsing with `21` parsed artifacts;
- created AI job `ai-job-1778672312564-0b2f`;
- reached final task state `review-pending`, material status `reviewing`, and AI job state `review-pending`;
- produced non-skeleton metadata with title `多边形错题集`, subject `数学`, grade `八年级`, material type `试卷`;
- preserved human review with confidence `30` and `needsReview=true`;
- ended with active parse/AI queues clean and MinerU admission circuit closed.

Director spot-checks confirmed the same production state through:

- `GET /__proxy/db/tasks/task-1778672291622`
- `GET /__proxy/db/materials/validation-json-repair-1778672290`
- `GET /__proxy/db/ai-metadata-jobs/ai-job-1778672312564-0b2f`
- `GET /__proxy/upload/ops/mineru/admission-circuit`
- `GET /__proxy/upload/ops/mineru/active-task`

The original Task 95 failure mode did not recur. The first AI pass was schema-invalid, but deterministic repair mode `deterministic-draft-normalization` succeeded and the final state remained strict no-skeleton.

## Residual Issues

MinerU progress semantics remain a P1 operator-observability issue:

- this fast-complete sample still surfaced diagnostic-only progress wording;
- transient false `worker-failed` events occurred because of `log-observation-unreadable`;
- the runtime self-corrected and reached `review-pending`, but the task history remains confusing for operators.

This residual did not block the Task 98 validation boundary, but it should stay visible before any production-readiness decision.

## Not Claimed

No second upload, pressure/batch/soak run, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, sample mutation, L3 validation, production-readiness, or release-readiness is accepted or declared by this review.

## Next Step

Task 99 records the next user decision: whether to proceed from single-sample success to a small stage-queued validation scope, fix the remaining MinerU progress-observability debt first, or hold.
