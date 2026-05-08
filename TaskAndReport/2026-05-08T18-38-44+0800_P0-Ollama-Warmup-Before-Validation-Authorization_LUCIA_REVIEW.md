# Lucia Review: P0 Ollama Warmup Before Validation Authorization

Decision target:

- Task: `TASK-20260508-183129-P0-Ollama-Warmup-Before-Validation-Authorization`
- Decision record: `TaskAndReport/2026-05-08T18-31-29+0800_P0-Ollama-Warmup-Before-Validation-Authorization_DECISION.md`

Director decision:

`APPROVE_WARMUP_VALIDATION_RETRY`

Director approved the Lucia recommendation:

- Allow exactly one bounded non-mutating Ollama warm-up/readiness step before validation.
- Require warm dependency-health with `mineruSubmitProbe=true` to pass afterward.
- If warm dependency-health passes, allow at most one controlled validation upload.
- Still forbid production release-readiness declaration and any service/model/data/config mutation.

## Lucia Interpretation

This approval authorizes a validation procedure change only. It does not authorize:

- production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation;
- Ollama restart/kill/start/reload;
- model pull/delete/change/switch;
- timeout/config/secret/override changes;
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning, task/artifact/log deletion;
- more than one controlled validation upload;
- skeleton fallback or silent degradation;
- production release-readiness declaration.

## Next Action

Issue Lucode task:

`TASK-20260508-183844-P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation`

The task must perform one bounded non-mutating warm-up, verify warm dependency-health, then create at most one controlled upload only if all readiness gates pass.
