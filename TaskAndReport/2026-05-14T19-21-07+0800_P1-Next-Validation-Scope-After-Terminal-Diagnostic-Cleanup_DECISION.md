# User Decision Required: P1 Next Validation Scope After Terminal Diagnostic Cleanup

## Current Facts

- Task 143 deployed the accepted Task 141 terminal diagnostic cleanup to production.
- Production is at `58f1437`.
- Production services and dependency health are currently healthy and non-blocking.
- Read-only browser validation confirms existing successful terminal task details no longer append the old no-attributed-log diagnostic as `最后可见进度`.
- Real backend/pipeline/page progress remains visible where it exists.
- The old diagnostic remains visible only in historical failed AI rows, outside the Task 143 success-terminal acceptance boundary.
- No fresh upload was performed in Task 143, because the task explicitly forbade uploads.

## Blocker / Decision Point

The cleanup is accepted for deployed read-only behavior, but the project still lacks one fresh post-cleanup upload lifecycle proving that a newly submitted PDF now presents clean MinerU progress semantics from upload through terminal review-pending state.

This is a validation-scope decision, not a code decision.

## Options

### Option A: Recommended

Authorize TestAcceptanceEngineer to run exactly one controlled fresh upload from `/Users/concm/prod_workspace/Luceon2026/testpdf`.

Rules:

- choose one small or medium PDF;
- upload exactly one PDF;
- observe until terminal state or clear systemic failure;
- verify task page progress semantics, task/material/MinerU/AI state coherence, admission/active-task state, and browser console/network noise;
- stop immediately after the one upload;
- write a report and return to Director review.

Not authorized under Option A:

- second upload;
- batch/intake/pressure/soak validation;
- cleanup/repair/reparse/re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- settings/secrets/config/model/sample mutation;
- service ownership mutation;
- readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim.

### Option B

Hold validation here and do no further runtime action.

Risk: the deployed cleanup remains verified only against existing task data, not a new post-cleanup upload lifecycle.

### Option C

Proceed directly to broader serial validation or pressure-style validation.

Director does not recommend this yet. The project should first obtain one clean fresh-upload lifecycle after the terminal diagnostic cleanup, because that is the narrowest missing evidence.

## Director Recommendation

Choose Option A.

It is the smallest useful next step, is reversible in process terms, avoids pressure or concurrency, and directly answers the remaining evidence gap created by Task 143's read-only boundary.

## User Decision

- Decision time: `2026-05-14T19:25:26+0800`
- Decision: `USER_APPROVED_OPTION_A`
- User instruction: `同意 option A`

Director will issue a scoped TestAcceptanceEngineer task for exactly one controlled fresh upload. No second upload, batch/intake/pressure/soak validation, cleanup/repair/reparse/re-AI, destructive mutation, settings/secrets/config/model/sample mutation, service ownership mutation, readiness/L3/pressure PASS/release-readiness/production-readiness/go-live claim is authorized.
