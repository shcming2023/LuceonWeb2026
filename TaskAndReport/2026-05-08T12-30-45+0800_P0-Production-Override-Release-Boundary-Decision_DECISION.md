# P0 Production Override Release Boundary Decision

Decision ID:
`TASK-20260508-123045-P0-Production-Override-Release-Boundary-Decision`

Issued by:
Lucia

Issued at:
2026-05-08T12:30:45+0800

Next Actor:
Director

## Background

Task 22 established that the production workspace has a local `docker-compose.override.yml` containing strict AI/model settings and MinIO console exposure. Task 23 documented that boundary in `docs/deploy/DEPLOY.md`.

The remaining question is not whether the documentation exists. The remaining question is which release boundary the project should use before any production release-readiness naming.

## Decision Required

Director should choose one of the following options:

1. Accept current local-admin MinIO console exposure `19001:9001` for the intended single-operator local production boundary, with exact production HEAD and override confirmation still required before release-candidate naming.
2. Require the MinIO console exposure to be narrowed to local-only binding before release-candidate naming.
3. Require the MinIO console exposure to be removed before release-candidate naming.

Director should also decide whether strict AI/model values remain in production-local `docker-compose.override.yml`, move to `.env`, or are normalized into committed deployment configuration before release-candidate naming.

## Recommended Lucia Position

Lucia recommends option 2 for the MinIO console boundary before any release-candidate naming: narrow the console exposure to local-only binding if operational access remains needed. This preserves administrator observability while reducing unnecessary network exposure.

Lucia recommends preserving strict AI/model values as explicit runtime configuration for now, but requiring exact production HEAD and effective override confirmation before any release-candidate naming. Moving them into committed configuration or `.env` can be handled later as a scoped deployment-configuration cleanup if Director wants a stricter packaging standard.

## Autonomy Boundary

This decision is Director-owned. Lucia may continue non-destructive documentation and analysis if the decision waits for two heartbeat checks, but Lucia may not use autonomy to declare production release readiness, accept an external/multi-user release boundary, mutate production data, change secrets, run destructive Docker/DB/MinIO operations, or perform production restart/rebuild/deploy/rollback.

## Required Output

Director decision on:

- MinIO console boundary: accept current `19001:9001`, narrow to local-only, or remove.
- Strict AI/model configuration placement: keep override, move to `.env`, or normalize into committed deployment configuration.
- Whether Lucia should issue a scoped Lucode task for non-destructive implementation planning or, if explicitly approved, a production-change task.
