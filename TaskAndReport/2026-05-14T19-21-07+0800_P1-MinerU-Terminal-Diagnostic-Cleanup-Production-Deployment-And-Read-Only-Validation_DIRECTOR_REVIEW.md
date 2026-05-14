# Director Review: P1 MinerU Terminal Diagnostic Cleanup Production Deployment And Read-Only Validation

## Review Result

`ACCEPTED_SCOPED_DEPLOYMENT_AND_READ_ONLY_VALIDATION_PASS_FRESH_UPLOAD_DECISION_REQUIRED`

## Reviewed Materials

- Task brief: `TaskAndReport/2026-05-14T19-08-58+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_TASK.md`
- DevelopmentEngineer report: `TaskAndReport/2026-05-14T19-08-58+0800_P1-MinerU-Terminal-Diagnostic-Cleanup-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Accepted code/test-level source task: Task 141
- Authorization decision: Task 142 Option A

## Director Findings

Task 143 is accepted at the scoped production deployment and read-only validation level.

The report shows production was fast-forwarded from `15105c2` to `58f1437`, the accepted Task 141 code markers are present in production, and `cms-frontend` was rebuilt/restarted. The report also records that no upload, batch/intake, pressure, soak, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, settings/secrets/config/model/sample mutation, or readiness claim was performed.

Director spot-checks confirmed:

- production HEAD is `58f1437`;
- production Docker services are healthy;
- upload health is OK;
- dependency health is OK and non-blocking;
- admission circuit is closed;
- no active, queued, completed-but-not-ingested, drift, submit-retryable, or takeover-required MinerU work is present;
- direct MinerU health settled back to idle after submit probe activity.

Browser read-only validation also supports the acceptance result. The relevant successful terminal detail pages display clean success progress:

- `task-1778741537754`: `MinerU 已完成，解析产物 9 个`
- `task-1778741838537`: `MinerU 已完成，解析产物 25 个`
- `task-1778741990445`: `MinerU 已完成，解析产物 82 个；最后可见进度：backend=pipeline，相位 页面处理，批次 1/1，页 27/27`

The old no-attributed-log diagnostic no longer appears as the appended `最后可见进度` on the checked successful terminal task details. The same read-only browser check observed the old diagnostic still present only in historical failed AI rows on the task list, which is outside the Task 143 success-terminal acceptance boundary.

Console/network evidence is also acceptable for this scope: no relevant `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, or non-stream request-failed signal was observed. SSE teardown aborts were excluded as expected navigation artifacts.

## Boundaries

This review does not declare production readiness, L3, pressure PASS, release-readiness, go-live, or general large-scale stability.

This review also does not prove a fresh post-cleanup upload lifecycle, because Task 143 intentionally performed read-only validation against existing production tasks. Fresh upload validation remains a separate user decision.

## Next Step

Record a user decision for the next validation scope. Director recommendation is Option A: authorize exactly one controlled fresh upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`, observe the full new task lifecycle and MinerU progress semantics after this cleanup, then stop for review. Do not proceed to pressure, batch, or broader serial validation until that fresh lifecycle evidence is available.
