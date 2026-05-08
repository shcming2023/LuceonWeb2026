# Lucia Review: P0 Adaptive Evidence-Pack Production Validation Authorization

Review:
P0 Adaptive Evidence-Pack Production Validation Authorization

Task ID:
`TASK-20260508-151145-P0-Adaptive-Evidence-Pack-Production-Validation-Authorization`

Reviewed by:
Lucia

Reviewed at:
2026-05-08T17:31:00+0800

Decision:
`DIRECTOR_APPROVED_SCOPED_PRODUCTION_VALIDATION`

## Director Decision

Director approved production validation.

Lucia interprets this approval as authorization to issue a scoped Lucode validation task based on the accepted task 33 runbook.

## Authorized Scope

Lucode may:

- Apply the accepted `main` code to the production workspace through the existing production path only as needed for this validation.
- Preserve production-local `docker-compose.override.yml` strict AI/model settings and MinIO local-only console binding.
- Use minimum necessary Docker/Compose actions to apply the accepted upload-server code.
- Run pre-upload readiness checks.
- Create one controlled validation upload using the accepted large-PDF sample if preflight checks pass.
- Collect task, material, AI job, task-event, structured AI input-selection, and log evidence.

## Still Forbidden

This decision does not authorize:

- Production release-readiness declaration.
- DB row deletion.
- MinIO object deletion.
- Docker volume deletion or pruning.
- Secret changes.
- Broad production deploy/rollback outside the scoped validation.
- Model or timeout policy changes.
- Skeleton fallback or silent degradation.
- External or multi-user release boundary acceptance.

## Follow-Up Task

Lucia issued:

`TASK-20260508-173100-P0-Adaptive-Evidence-Pack-Scoped-Production-Validation`

Production release readiness remains unclaimed.
