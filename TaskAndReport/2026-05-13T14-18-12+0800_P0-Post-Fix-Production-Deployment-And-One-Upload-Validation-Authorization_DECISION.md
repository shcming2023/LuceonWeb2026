# Decision: P0 Post Fix Production Deployment And One Upload Validation Authorization

Task:
`TASK-20260513-141812-P0-Post-Fix-Production-Deployment-And-One-Upload-Validation-Authorization`

Decision required from:
User

Recorded by:
Director

Decision file:
`TaskAndReport/2026-05-13T14-18-12+0800_P0-Post-Fix-Production-Deployment-And-One-Upload-Validation-Authorization_DECISION.md`

Decision status:
`PENDING_USER_DECISION`

## Decision Boundary

Task 87 has been accepted at code/test level, but no production deployment or production validation has been performed.

The next useful step would require two actions that need explicit owner boundary:

1. scoped production deployment of the accepted Task 87 code path;
2. exactly one additional controlled production upload to verify:
   - real Ollama metadata inference is no longer cut off at the unintended 30-second header timeout;
   - task-page/API MinerU progress semantics now show either real structured progress or the truthful fast-complete diagnostic.

The previous user authorization allowed exactly one upload. Task 86 consumed that authorization and produced failed validation evidence. This decision asks whether to authorize the next scoped attempt after code-level fixes.

## Current Facts

- Task 86 production validation failed but produced useful evidence.
- MinerU parse/storage passed for sample `2025_2026学年春季课程中数G8_提取.pdf`.
- The Task 86 AI stage failed because two Ollama provider requests hit `UND_ERR_HEADERS_TIMEOUT` at about 30 seconds despite provider timeout `180000ms`.
- Task 86 did not expose `mineruObservedProgress.progressSemantics`.
- Task 87 code/test fixes are accepted by Director at code/test level.
- Production is not yet updated to the Task 87 code path.
- No release-readiness, L3, or pressure PASS claim is valid.

## Options Considered

### Option A: Approve Scoped Deploy + One Upload Validation

Authorize the next two-step validation track:

1. DevelopmentEngineer performs minimum necessary production deployment and non-destructive runtime validation for the accepted Task 87 code path.
2. If deployment/runtime checks pass, TestAcceptanceEngineer performs exactly one controlled small/medium upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

Boundaries:

- no pressure test;
- no 24-PDF retry;
- no failed-task repair, cleanup, reparse, or re-AI of historical tasks;
- no destructive DB/MinIO/Docker volume/data mutation;
- no model pull/delete/replace/reload;
- no secret, override, PRD, role-contract, or release-truth mutation;
- no production release-readiness, L3, or pressure PASS declaration.

Director recommendation: `Option A`.

Reason: Task 87 has passed code/test review and directly addresses the two observed blockers. Without one scoped production deployment plus one real upload, the project remains stuck at code-level confidence and cannot know whether the operator-facing production path is fixed.

### Option B: Deploy Only, No Upload

Authorize production deployment and non-destructive runtime checks only, but do not create another validation upload.

Risk: safer operationally, but it will not prove the actual fixed path, because both blockers only manifested during a real upload/AI metadata run.

### Option C: Hold

Do not deploy or validate yet.

Risk: avoids immediate production movement, but leaves the project blocked at exactly the current failure boundary.

## User Decision

Pending.

## Director Interpretation

Until the user decides, Director must not authorize the next production deployment or new upload.

If the same user decision remains unanswered for two consecutive heartbeat wakeups, Director may auto-progress only the conservative recommended path under the existing heartbeat rule, provided the row records the wait evidence and the resulting task remains scoped, non-destructive, reversible, and explicitly excludes release-readiness/L3/pressure claims.

## Authorized Next Action

Pending user decision.

## Explicitly Not Authorized

- production release readiness;
- L3;
- pressure PASS;
- 24-PDF pressure retry/test;
- multiple uploads;
- failed-task repair, cleanup, reparse, or re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- model pull/delete/replace/reload;
- secret/config/override mutation beyond the minimum deployment mechanics explicitly assigned later;
- broad restart/rollback;
- sample-file mutation.

## Next Actor

`User`

## Required Output

User decision on Option A, B, or C. Director should record the decision before issuing any follow-up task.
