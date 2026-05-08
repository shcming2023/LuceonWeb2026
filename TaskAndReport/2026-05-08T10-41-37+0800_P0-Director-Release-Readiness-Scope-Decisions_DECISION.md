# P0 Director Release Readiness Scope Decisions

Issued at: 2026-05-08T10:41:37+0800

Issuer: Lucia

Next actor: Director

Status: Director decision pending

## Background

Lucode's release-readiness gap matrix identified several release-scope decisions that remain Director-owned. These decisions affect whether later validation work can claim production release readiness or only manual-review hardening evidence.

## Decision Required

Director should decide:

1. Whether the current iteration target is production release readiness, continued manual-review hardening, Phase 2 product planning, or iteration closure.
2. Whether large-PDF soak, concurrency validation, and rollback rehearsal are mandatory before any production release-readiness claim, or can be deferred after a limited internal release.
3. Whether `/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` should remain a local override, be normalized into documented deployment configuration, or be reviewed in a separate task.
4. Whether Lucia may later authorize Lucode to perform a production restart, rebuild, or rollback rehearsal window.
5. Whether the single-operator/no-auth local deployment boundary is acceptable for the intended release audience.

## Lucia Recommendation

Lucia recommends continuing toward production release readiness, while treating large-PDF soak, concurrency validation, error-path validation, deployment repeatability, and rollback/recovery as P0 evidence gaps.

Lucia does not recommend authorizing restart, rebuild, rollback rehearsal, or production release approval through this decision by default. Those operations should require explicit Director approval.

## Heartbeat Fallback

If this decision remains unanswered after two Lucia heartbeat checks, Lucia may continue only with non-destructive validation and documentation tasks.

Lucia must not use heartbeat fallback to approve production release readiness, authorize production restart/rebuild/rollback, mutate DB/MinIO/Docker volumes, change secrets, broaden product scope, or accept the no-auth boundary for external release.

## Required Director Output

Director should provide a route and any explicit operational permissions or deferrals.
