# Director Review: P1 Db Sync Console Warning Hardening Production Deployment And Read-Only Browser Validation

- Review time: 2026-05-14T14:02:00+0800
- Reviewed task: `TASK-20260514-134808-P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation`
- Reviewed report: `TaskAndReport/2026-05-14T13-48-08+0800_P1-Db-Sync-Console-Warning-Hardening-Production-Deployment-And-Read-Only-Browser-Validation_REPORT.md`
- Reviewer: Director

## Judgment

`ACCEPTED_SCOPED_DEPLOYMENT_AND_READ_ONLY_BROWSER_VALIDATION_PASS_UPLOAD_VALIDATION_DECISION_REQUIRED`

Task 130 is accepted as a scoped production deployment and read-only browser/runtime validation pass for the Task 129 db-sync console-warning hardening.

This is not a PDF upload validation, pressure PASS, L3, release-readiness, or go-live declaration.

## Accepted Evidence

Accepted deployment evidence:

- Production workspace advanced from `5ca2615` to `4eb2e3b Accept db-sync warning hardening`.
- Deployment command `docker compose up -d --build cms-frontend` exited `0`.
- Compose rebuilt/recreated `cms-db-server` and `cms-upload-server` as dependency side effects; all services were healthy afterward.
- Production still has unrelated pre-existing dirty files; the accepted `src/store/appContext.tsx` code is present at production HEAD.

Accepted runtime spot-checks:

- `/__proxy/upload/health` returned `ok=true`.
- `/__proxy/upload/ops/dependency-health?ollamaChatProbe=true` returned `ok=true`, `blocking=false`, MinerU OK, and Ollama resident/chat OK.
- `/__proxy/upload/ops/mineru/admission-circuit` returned closed circuit with parse and AI counts `0`.
- `/__proxy/upload/ops/mineru/active-task` showed no active/current/queued/drift/submit-retryable/takeover-required tasks; only historical AI failures remain listed separately.
- Direct MinerU `/health` was healthy with queued `0`, processing `0`, failed `0`.
- `/cms/`, `/cms/tasks`, and `/cms/ops/health` returned HTTP `200`.

Accepted browser-console evidence:

- Read-only Playwright validation visited `/cms/tasks`, one existing task detail route, and `/cms/ops/health`.
- `[db-sync]` console events: `0`.
- `/settings/*` console events: `0`.
- `/secrets` console events: `0`.
- `Failed to fetch` console events: `0`.
- HTTP 503 network responses: `0`.
- PUT `/settings/*` requests: `0`.
- PUT `/secrets` requests: `0`.
- Only observed request failures were navigation/browser-close SSE aborts for task streams; these are not the Task 128 warning pattern.

Director independently spot-checked production HEAD, Docker health, canonical dependency/admission/active-task endpoints, direct MinerU health, and CMS HTTP routes. The earlier short `/dependency-health` path returns 404 and is not the canonical endpoint; canonical `/ops/dependency-health` passed.

## Residual Boundary

This pass proves that production boot/navigation no longer emits the Task 128 no-op db-sync settings/secrets warning pattern. It does not prove fresh upload behavior, because PDF upload was forbidden in Task 130.

The remaining next boundary is one controlled upload validation, if approved by the user.

## Not Authorized Or Claimed

This review does not authorize or claim:

- production readiness, L3, pressure PASS, release-readiness, or go-live
- PDF upload validation
- pressure, batch-concurrent, or soak validation
- cleanup, repair, reparse, re-AI, or failed-task mutation
- destructive DB, MinIO, Docker volume, Docker down, data, sample, model, secret, settings, or config mutation
- MinerU, Ollama, supervisor, or sidecar ownership changes

## Next Step

Record a User decision for whether to run exactly one controlled upload validation after the db-sync hardening deployment.

