# Director Review: P1 Post Terminal Diagnostic Cleanup Exactly One Controlled Upload Validation

## Review Result

`ACCEPTED_BOUNDED_ONE_UPLOAD_VALIDATION_PASS_WITH_DB_SYNC_CONSOLE_NOISE_FOLLOW_UP`

## Reviewed Materials

- Task brief: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_TASK.md`
- TestAcceptanceEngineer report: `TaskAndReport/2026-05-14T19-25-26+0800_P1-Post-Terminal-Diagnostic-Cleanup-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- User decision: `TaskAndReport/2026-05-14T19-21-07+0800_P1-Next-Validation-Scope-After-Terminal-Diagnostic-Cleanup_DECISION.md`
- Prior deployment review: `TaskAndReport/2026-05-14T19-21-07+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`

## Director Findings

Task 145 is accepted for the exact bounded validation scope.

The report shows exactly one UI upload from `/Users/concm/prod_workspace/Luceon2026/testpdf/2025_2026学年春季课程中数G8_提取.pdf`:

- task: `task-1778758370859`
- material: `3380327087858932`
- MinerU task: `204b8692-8e2f-4aa8-9fe6-f9de62e1fd35`
- AI job: `ai-job-1778758387317-1ccb`

The uploaded task reached a coherent terminal state:

- task `review-pending` / stage `review`;
- material `reviewing`;
- MinerU `completed`;
- parsed files `21`;
- AI metadata `analyzed`;
- AI job `review-pending`.

The terminal task detail and task list primary progress line showed:

`MinerU 已完成，解析产物 21 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 3/3`

The old no-attributed-log diagnostic was not appended as terminal `最后可见进度` for this fresh successful task. This closes the evidence gap that remained after Task 143's read-only validation.

Director spot-checks after the report confirmed:

- production is still at `58f1437`;
- production Docker services are healthy;
- upload health is OK;
- dependency-health is OK and non-blocking;
- MinerU admission is closed;
- active-task has no active/current/queued/takeover-required work;
- direct MinerU `/health` is idle with `queued_tasks=0`, `processing_tasks=0`, and `failed_tasks=0`;
- DB API state for `task-1778758370859`, material `3380327087858932`, and AI job `ai-job-1778758387317-1ccb` matches the report;
- post-terminal browser refresh on detail and list showed the expected progress text and had no relevant console warnings, non-stream request failures, or HTTP 5xx.

## Residual Issue

The upload lifecycle produced two real browser console warnings during the upload/polling window:

- `[db-sync] POST /materials failed (count=1): Failed to fetch`
- `[db-sync] PUT /asset-details/3380327087858932 failed (silent): Failed to fetch`

These warnings did not block task completion and were absent after terminal refresh, but they are still relevant operator-facing console noise under the task brief. They should not be ignored because this project has already spent effort reducing db-sync/settings/secrets noise. The correct next step is a narrow development diagnosis/hardening task, not broader runtime validation.

## Boundaries

This review accepts only the bounded one-upload validation. It does not declare production readiness, release-readiness, L3, pressure PASS, go-live readiness, or large-scale stability.

No second upload, batch/intake, pressure, soak, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, MinerU/Ollama/supervisor mutation, or readiness claim was authorized or accepted.

## Next Step

Issue a scoped DevelopmentEngineer code/test-level task to diagnose and harden the upload-time db-sync console warnings. That follow-up must not deploy to production or run additional uploads unless separately authorized.
