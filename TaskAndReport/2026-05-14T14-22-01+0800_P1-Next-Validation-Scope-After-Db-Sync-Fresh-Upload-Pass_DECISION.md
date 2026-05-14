# User Decision Required: P1 Next Validation Scope After Db-Sync Fresh Upload Pass

- Decision ID: `TASK-20260514-142201-P1-Next-Validation-Scope-After-Db-Sync-Fresh-Upload-Pass`
- Created: 2026-05-14T14:22:01+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T14-22-01+0800_P1-Post-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

## Current Facts

Task 132 passed the exactly-one fresh-upload validation after the db-sync hardening deployment:

- one PDF upload reached `review-pending`
- material is `reviewing`
- MinerU completed
- AI analyzed with `qwen3.5:9b`
- db-sync/settings/secrets warnings did not recur
- runtime returned idle and nonblocking

The remaining evidence gap is scale and durability. This is still not pressure, batch, soak, L3, release-readiness, or go-live evidence.

## Decision Needed

Choose the next validation scope.

## Options

### Option A: Small serial validation, up to 3 PDFs

Authorize TestAcceptanceEngineer to run up to 3 additional PDFs from `/Users/concm/prod_workspace/Luceon2026/testpdf`, strictly one at a time. Each upload must reach a terminal state before the next begins. Stop on the first systemic failure.

Measure:

- db-sync/settings/secrets console and network counts
- task list/detail progress semantics
- terminal task/material/MinerU/AI states
- post-terminal dependency/admission/active-task/MinerU cleanliness

This is the Director recommendation.

Reason: it is the smallest useful next step after one fresh-upload pass. It checks whether the db-sync fix remains clean across a few documents without jumping to pressure or batch behavior.

### Option B: Hold further uploads and address MinerU progress attribution residual first

Do not upload. Instead, assign analysis or code work on the residual "no attributable MinerU business-progress log" terminal message seen in Task 132.

Reason to choose: if the immediate priority is observability polish rather than broader functional validation.

Risk: the db-sync fix remains validated on only one fresh upload.

### Option C: Move directly to pressure/batch validation

Director does not recommend this now.

Reason: the project has only just cleared one fresh-upload validation after a console-noise fix, and prior batch/pressure history is failure-prone. Jumping straight to pressure would mix db-sync evidence, MinerU progress attribution, and batch stability into one noisy test.

## Director Recommendation

Choose Option A.

Do not declare readiness after Option A alone. If Option A passes, the next discussion should be whether to run a carefully bounded serial-longer validation or a small pressure preflight, not broad pressure or go-live.

## Decision Recorded

User approved Option A at 2026-05-14T14:24:48+0800.

Director will issue a scoped TestAcceptanceEngineer task for up to 3 additional PDFs from `/Users/concm/prod_workspace/Luceon2026/testpdf`, strictly serial, one terminal state before the next, and stop on systemic failure.
