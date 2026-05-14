# Director Review: P1 Upload-Time Db-Sync Hardening Production Deployment And Read-Only Validation

## Review Result

`ACCEPTED_SCOPED_DEPLOYMENT_AND_READ_ONLY_VALIDATION_PASS_FRESH_UPLOAD_VALIDATION_AUTHORIZED`

## Reviewed Materials

- Task brief: `TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_TASK.md`
- DevelopmentEngineer report: `TaskAndReport/2026-05-14T20-38-00+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- User decision: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Hardening-Production-Deployment-Decision_DECISION.md`
- Code/test-level Director review: `TaskAndReport/2026-05-14T19-54-24+0800_P1-Upload-Time-Db-Sync-Console-Noise-Diagnosis-And-Hardening_DIRECTOR_REVIEW.md`

## Director Findings

Task 148 is accepted at scoped deployment and read-only validation level.

The report shows production was fast-forwarded from `58f1437` to `89271a1`, which contains the accepted Task 146 frontend db-sync lifecycle hardening. The required markers are present in production source:

- `dbSyncPageLifecycleEnding`
- `cancelled during page lifecycle change`
- `db-sync-page-lifecycle-noise`

The report also shows `docker compose up -d --build cms-frontend` completed successfully. Compose also recreated `cms-db-server` and `cms-upload-server`; this is consistent with previous Compose dependency/build behavior and all core services returned healthy.

Director spot-checks confirmed:

- production HEAD is `89271a1`;
- production branch is `main...origin/main`;
- production still has the pre-existing unrelated local modifications reported by DevelopmentEngineer;
- all core Docker services are healthy;
- upload health is OK;
- dependency-health is OK and non-blocking;
- MinerU admission circuit is closed;
- active-task has no active/current/queued/takeover-required work;
- direct MinerU health is idle with `queued_tasks=0`, `processing_tasks=0`, and `failed_tasks=0`;
- `/cms/` and `/cms/tasks` return HTTP 200;
- a read-only Playwright pass over `/cms/tasks` had `0` relevant `[db-sync]`, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, and non-stream request-failed signals.

## Boundaries

This review accepts only the deployment and read-only validation. It does not prove the upload-time browser lifecycle behavior under a fresh upload; that is the next validation step already authorized by the user in Task 147 Option A.

This review does not declare production readiness, release-readiness, L3, pressure PASS, go-live readiness, or large-scale stability.

No upload, pressure/batch/soak/broader serial validation, cleanup/repair/reparse/re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, broad warning suppression, or readiness/go-live claim was performed or accepted.

## Next Step

Dispatch the second role-safe step under the already approved Task 147 Option A: TestAcceptanceEngineer should run exactly one controlled fresh upload from `/Users/concm/prod_workspace/Luceon2026/testpdf` and specifically verify upload-time plus post-terminal db-sync console/network behavior, task/material/MinerU/AI coherence, and terminal progress semantics.
