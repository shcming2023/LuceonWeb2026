# User Decision Required: P1 Post Db-Sync Hardening One Upload Validation Authorization

- Decision ID: `TASK-20260514-140200-P1-Post-Db-Sync-Hardening-One-Upload-Validation-Authorization`
- Created: 2026-05-14T14:02:00+0800
- Created by: Director
- Next Actor: User
- Related review: `TaskAndReport/2026-05-14T14-02-00+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_DIRECTOR_REVIEW.md`

## Current Facts

Task 130 is accepted as scoped deployment/read-only validation:

- Production is on `4eb2e3b Accept db-sync warning hardening`.
- Services are healthy.
- Canonical dependency/admission/active-task checks are clean for the authorized scope.
- Read-only browser navigation did not emit the previous no-op `[db-sync] PUT /settings/*` plus `/secrets` warning pattern.

However, Task 130 did not upload a PDF. It therefore does not prove the warning remains absent during a fresh upload lifecycle.

## Decision Needed

Decide whether to authorize one controlled upload validation.

## Options

### Option A: Approve exactly one controlled upload validation

Assign TestAcceptanceEngineer to upload exactly one small/medium PDF from `/Users/concm/prod_workspace/Luceon2026/testpdf`, then stop and report:

- browser console counts for `[db-sync]`, `/settings/*`, `/secrets`, `Failed to fetch`, and HTTP 503
- task list/detail progress semantics
- final task/material/MinerU/AI state
- admission/active-task/runtime cleanliness after terminal state

Strictly forbidden: second upload, pressure, batch, soak, cleanup, repair, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, settings/secrets mutation, model/config/secret/sample mutation, readiness/L3/pressure PASS/release-readiness/go-live claim.

### Option B: Hold uploads and continue observation/code hardening only

Do not upload. Keep the deployed code in place and only monitor existing pages/endpoints or address unrelated technical debt.

Risk: this avoids new runtime mutation but leaves the fresh-upload console behavior unproven.

### Option C: Broaden directly to multi-PDF serial validation

Run more than one PDF after this fix.

Director does not recommend this now because the exact fresh-upload console behavior should be checked once before widening.

## Director Recommendation

Choose Option A.

Reason: the code is deployed and read-only validation passed. A single controlled upload is the smallest meaningful proof that the Task 128 warning pattern is gone during the real upload lifecycle. It keeps the next step useful without jumping to pressure or broader serial validation.

