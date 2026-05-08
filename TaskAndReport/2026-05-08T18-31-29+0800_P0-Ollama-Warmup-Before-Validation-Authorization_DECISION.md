# Director Decision Needed: P0 Ollama Warmup Before Validation Authorization

Task:
P0 Ollama Warmup Before Validation Authorization

Task ID:
`TASK-20260508-183129-P0-Ollama-Warmup-Before-Validation-Authorization`

Owner:
Director

Recorded by:
Lucia

Recorded at:
2026-05-08T18:31:29+0800

Project:
Luceon2026

## Decision Question

May Lucia authorize Lucode to perform a bounded, non-mutating Ollama warm-up/readiness stabilization step before the single controlled adaptive evidence-pack production validation upload?

## Context

Task 34 and task 36 both stopped before upload because upload-server dependency-health timed out on Ollama `qwen3.5:9b` readiness.

Task 35 diagnosed that the model exists and becomes ready without mutation, but first probes may spend about `6.7s` to `8.9s` in model load and dependency-health can still hit its `15000ms` smoke timeout when the model is not resident.

Task 36 confirmed the issue recurs: immediate dependency health failed at `15001ms`, while a direct read-only chat afterward loaded the model and succeeded.

## Lucia Recommendation

Approve a narrow warm-up authorization:

- Allow one bounded non-mutating direct Ollama readiness warm-up before the controlled upload.
- Require warm dependency-health with `mineruSubmitProbe=true` to pass after warm-up and immediately before upload.
- Then allow at most one controlled validation upload using the already approved large-PDF sample.
- Preserve model `qwen3.5:9b`.
- Preserve existing timeout policy.
- Preserve strict no-skeleton behavior.
- Preserve production-local override values.
- Keep all data and artifacts intact.
- Do not claim production release readiness.

## Non-Goals

This decision must not authorize:

- Production release-readiness declaration.
- Docker mutation, production deploy, fast-forward, rebuild, restart, rollback, or service restart.
- Ollama restart/kill/start/reload.
- Model pull/delete/change/switch.
- Timeout/config/secret/override changes.
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning, task/artifact/log deletion.
- More than one controlled validation upload.
- Skeleton fallback or silent degradation.

## Required Director Output

Please choose one:

1. `APPROVE_WARMUP_VALIDATION_RETRY`: Lucia may issue a Lucode task for bounded non-mutating Ollama warm-up followed by exactly one controlled validation upload if warm dependency-health passes.
2. `REQUEST_DIAGNOSIS_ONLY`: no upload yet; Lucode should further diagnose model residency/resource pressure without mutation.
3. `HOLD`: pause adaptive evidence-pack production validation until Director gives a different release-readiness route.

## Autonomy Rule

If this Director decision remains unanswered after two Lucia heartbeat checks, Lucia may choose the conservative default only if it remains within the non-mutating warm-up boundary above. Lucia may not use autonomy to approve production release readiness, Docker/service mutation, model/timeout/config/secret changes, data deletion, or broader release acceptance.
