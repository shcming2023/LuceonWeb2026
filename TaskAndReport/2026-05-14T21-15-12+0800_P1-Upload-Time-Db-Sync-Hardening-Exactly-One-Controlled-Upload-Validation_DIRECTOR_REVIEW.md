# Director Review: P1 Upload-Time Db-Sync Hardening Exactly One Controlled Upload Validation

- Review time: 2026-05-14T21:15:12+0800
- Reviewed task: `TASK-20260514-205742-P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation`
- Task brief: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_TASK.md`
- Report reviewed: `TaskAndReport/2026-05-14T20-57-42+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_REPORT.md`
- Reviewer role: `Director`

## Result

`ACCEPTED_BOUNDED_ONE_UPLOAD_VALIDATION_PASS_WITH_STREAM_ABORT_NOTE`

Task 149 is accepted at the exact assigned boundary: one controlled production upload after Task 146 db-sync lifecycle hardening had been deployed by Task 148.

This review does not declare L3, pressure PASS, release readiness, production readiness, go-live readiness, or production上线.

## Evidence Reviewed

The TestAcceptanceEngineer report is based on the assigned Director task brief and records the required reading, preflight, sample selection, execution window, task/material/MinerU/AI identifiers, browser console/network observations, endpoint observations, skipped checks, and residual risks.

Key accepted evidence:

- exactly one production UI upload was performed;
- sample source was `/Users/concm/prod_workspace/Luceon2026/testpdf/PDF document-4F18-A8A3-62-0.pdf`;
- sample size was `711046` bytes and SHA-256 was `bb491c5782c001a60e9af1c8d531cbf3ce9807f0db341af765c31cc2d75e56f4`;
- new task was `task-1778763994124`;
- new material was `178015320076052`;
- MinerU task was `0705d847-51f2-4444-ab12-defa9256da5c`;
- AI job was `ai-job-1778764001335-531c`;
- final task state was `review-pending`, stage `review`, progress `100`;
- material was `reviewing`, MinerU `completed`, AI `analyzed`;
- parsed artifact count was `9`;
- AI metadata job was `review-pending`;
- `[db-sync] POST /materials failed` count was `0`;
- `[db-sync] PUT /asset-details/... failed` count was `0`;
- `/settings`, `/secrets`, `Failed to fetch`, HTTP `5xx`, and non-stream request failure counts were `0`;
- only 3 stream `eventsource` `net::ERR_ABORTED` events were observed during navigation or teardown;
- terminal task detail/list progress remained operator-readable and did not append the old no-attributed-log diagnostic as the primary `最后可见进度`;
- runtime returned idle/non-blocking after terminal state.

## Director Spot Checks

Director performed read-only spot checks during this review:

- development workspace status was dirty on `development-engineer/p0-post-validation-ollama-mineru-blockers`; no unrelated changes were reverted or cleaned;
- production workspace remained on `89271a1 Dispatch db-sync hardening production deployment`;
- production workspace had pre-existing local modifications; they were recorded but not touched;
- `docker compose ps` showed `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` healthy;
- upload health returned `{"ok":true,"service":"upload-server"}`;
- dependency-health returned `ok=true`, `blocking=false`, MinerU OK, Ollama OK, `chatOk=true`, model resident, keepAlive `24h`;
- MinerU admission circuit was closed;
- active-task endpoint showed no active/current/queued/takeover-required work;
- direct MinerU `/health` showed queued `0`, processing `0`, failed `0`;
- DB task endpoint confirmed `task-1778763994124` as `review-pending`;
- DB material endpoint confirmed material `178015320076052` as `reviewing`, MinerU completed, AI analyzed;
- DB AI job endpoint confirmed `ai-job-1778764001335-531c` as `review-pending`;
- read-only browser task-detail check confirmed `待复核`, parsed artifact progress, no old no-attributed-log text, no db-sync/settings/secrets/Failed-to-fetch console noise, and no request failures.

One Director browser probe using `networkidle` timed out because the task page keeps stream traffic open; it was rerun read-only with `domcontentloaded` and passed. This is not counted as application failure.

## Assessment

The defect class that motivated Task 146 did not recur in the assigned upload-time condition. The earlier upload-time `[db-sync] POST /materials failed` and `[db-sync] PUT /asset-details/... failed` warnings were not observed after deployment, while normal task/material/MinerU/AI convergence still completed.

The remaining `eventsource` aborts are stream lifecycle events during navigation/teardown. They should stay noted, but they are outside the db-sync warning class and were not accompanied by HTTP 5xx, Failed-to-fetch, settings/secrets noise, or non-stream failures.

## Boundaries Preserved

Accepted only:

- one controlled upload validation for the Task 146/148 db-sync lifecycle hardening.

Not accepted or not performed:

- second upload;
- batch/intake/pressure/soak/broader serial validation;
- cleanup, repair, reparse, or re-AI;
- destructive DB, MinIO, Docker volume, or data mutation;
- Docker down or volume cleanup;
- MinerU/Ollama/supervisor mutation;
- model/config/secret/sample mutation;
- L3, pressure PASS, release readiness, production readiness, go-live readiness, or production上线 claim.

## Next Step

The immediate db-sync hardening validation chain is accepted. Because the ledger must not idle and the next step is an owner-level scope decision, Director records Task 150 as a User decision row.

Director recommendation for Task 150: Option A, prepare a concise read-only release/readiness gap assessment and recommended next validation plan before any pressure test or go-live statement.
