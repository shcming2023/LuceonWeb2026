# P0 Phase 1 Next Iteration Route Decision

Issued at: 2026-05-08T09:58:02+0800

Issuer: Lucia

Next actor: Director

Status: Director decision pending

## Background

The task ledger currently has all implementation, validation, and diagnosis tasks closed. Phase 1 has a validated local real-runtime mainline and production manual-review readiness evidence, but production release readiness is still not claimed.

The collaboration model must not leave Director, Lucia, and Lucode all idle unless Director explicitly closes the iteration stream. Therefore the next project step requires a Director route decision or a bounded Lucia fallback after the heartbeat threshold.

## Current Confirmed Facts

- Current Phase 1 mainline: upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Strict no-skeleton behavior is preserved.
- Production manual-review URL has been validated as `http://localhost:8081/cms/` in prior tasks.
- Production release readiness, staging readiness, L3 readiness, and full-site acceptance remain unclaimed.
- Known open or documented boundaries include release-readiness coverage gaps, large-PDF soak, concurrency, permissions/security, rollback rehearsal, folder upload, error-path validation, monolithic `server/upload-server.mjs`, compatibility-only online MinerU v4, legacy redirects, Vite chunk-size warning, and Docker frontend base-image metadata preflight.

## Decision Required

Director should choose the next iteration route:

1. Production release-readiness gap matrix and validation plan.
2. Phase 2 product and PRD planning.
3. Targeted technical-debt hardening.
4. Another Director-specified route.

## Lucia Recommendation

Lucia recommends option 1 as the default next step because production release readiness remains explicitly unclaimed while manual-review readiness has been established. This path is conservative, evidence-oriented, and does not require destructive production operations.

## Heartbeat Fallback

If this decision remains unanswered after two Lucia heartbeat checks, or if Lucia detects a task-flow deadlock, Lucia is authorized to make the conservative default decision:

Issue a Lucode task for a non-destructive production release-readiness gap matrix and validation plan.

The fallback task must not approve production release readiness, mutate production data, delete DB/MinIO/Docker volumes, change secrets, perform broad architecture rewrites, or materially expand product scope.

## Required Director Output

Director should provide one of:

- Approve option 1.
- Choose option 2.
- Choose option 3.
- Provide another route.
- Explicitly close the iteration stream.
