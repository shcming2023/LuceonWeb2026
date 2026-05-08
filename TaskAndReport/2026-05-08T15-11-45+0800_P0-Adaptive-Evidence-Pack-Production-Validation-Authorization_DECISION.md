# Director Decision: P0 Adaptive Evidence-Pack Production Validation Authorization

Decision:
P0 Adaptive Evidence-Pack Production Validation Authorization

Task ID:
`TASK-20260508-151145-P0-Adaptive-Evidence-Pack-Production-Validation-Authorization`

Requested by:
Lucia

Requested at:
2026-05-08T15:11:45+0800

Project:
Luceon2026

## Context

Lucia accepted code-level implementation of adaptive evidence-pack first-pass selection in:

`TASK-20260508-145945-P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs`

The accepted code changes reduce first-pass AI metadata input for medium-large documents before changing model, timeout, or fallback behavior.

## Decision Needed

Director must decide whether to authorize a scoped Lucode production validation task.

Recommended authorization:

- Deploy or apply the accepted `main` code through the existing production path only as needed for this validation.
- Preserve production-local strict AI/model settings.
- Do not change Ollama model or timeout policy.
- Run a controlled large-PDF validation using the existing approved sample boundary.
- Confirm that task-29-like documents no longer use the old about `83k` first-pass payload.
- Confirm whether AI metadata completes or fails explicitly with preserved artifacts and no skeleton fallback.
- Record task ID, artifacts, structured AI input-selection metadata, logs, and validation result.

## Forbidden Unless Separately Approved

- Production release-readiness declaration.
- DB row deletion.
- MinIO object deletion.
- Docker volume deletion or pruning.
- Secret changes.
- Broad production deploy/rollback outside the scoped validation.
- Model or timeout policy changes.
- Skeleton fallback or silent degradation.
- External or multi-user release boundary acceptance.

## Required Output

Director decision:

- Approved: Lucia may issue a scoped Lucode production validation task.
- Not approved: Lucia must keep task flow at code-level acceptance and record production validation as pending.
- Adjusted: Director may narrow sample, runtime action, or validation boundary.

If no Director response is received after two Lucia heartbeat checks, Lucia may not use autonomy to approve production release readiness or destructive operations. Lucia may only continue with non-destructive planning or docs updates.
