# Lucia Review: P0 Stage-Queued Sample Validation Plan And Preflight

Review ID:
`2026-05-08T20-39-35+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_LUCIA_REVIEW`

Reviewed task:
`TASK-20260508-194744-P0-Stage-Queued-Sample-Validation-Plan-And-Preflight`

Reviewed report:
`TaskAndReport/2026-05-08T20-07-50+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_REPORT.md`

Reviewer:
Lucia

Review time:
2026-05-08T20:39:35+0800

## Decision

`RETURNED_FOR_CORRECTION`

Lucode's report contains useful non-destructive preflight evidence, but the proposed plan does not correctly implement Director's stage-queued流水 boundary.

## Accepted Evidence

The following evidence is accepted as preflight facts:

- No production upload was created.
- No production release-readiness claim was made.
- No production deploy, fast-forward, rebuild, restart, rollback, Docker mutation, Ollama restart/start/stop/kill/reload, model/timeout/config/secret/override change, DB/MinIO/Docker volume/task/artifact/log deletion, sample mutation, GitHub sample sync, skeleton fallback, or silent degradation was reported.
- Production override boundary was reported present:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- CMS and DB were reported healthy.
- Dependency-health with MinerU submit probe passed, with Ollama OK but slow at `12740ms`.
- Active parse/task states were `0`; active AI jobs were `0`.
- True sample directory inventory was read-only.

## Blocking Issue

The report's proposed plan says:

- "Submit the next sample only after the current sample has reached a terminal state";
- "Require per-sample terminal state before the next sample upload."

This contradicts Director's correction.

Director clarified that the target model is not full end-to-end serial blocking. Correct meaning:

- after a sample completes upload/storage intake into MinIO, the next sample may be accepted into upload intake;
- MinerU parsing queues by stage;
- Ollama metadata recognition queues by stage;
- the plan must prevent simultaneous heavy MinerU parse jobs and simultaneous heavy Ollama metadata jobs, not prevent stage-overlap entirely.

Therefore the current report cannot be accepted as the next validation-run plan.

## Required Correction

Lucode must submit a revised report for the same task.

The revised plan must:

1. Replace full per-sample terminal blocking with a stage-queued pipeline.
2. Define the exact handoff condition for starting the next upload:
   - previous sample's upload/storage intake has completed;
   - task/material IDs and objectName are recorded;
   - the previous sample is visible in DB and has entered a trackable queued/running parse stage or equivalent durable state.
3. Define how to prove MinerU remains effectively single-worker during validation.
4. Define how to prove Ollama metadata recognition remains effectively single-worker during validation.
5. Preserve true sample directory read-only handling.
6. Keep production upload authorization out of the correction report. The correction is still planning/preflight only.
7. Keep no production release-readiness claim.

## Current Routing

Task 42 is returned to Lucode for correction.

No new validation run is authorized.

## Verification

- `git fetch origin`: completed before review.
- `git show --check --oneline HEAD`: passed for Lucode report commit.
- `git show --stat --name-status --oneline --decorate HEAD`: confirmed Lucode changed only the TaskAndReport report and tracking list.
- `git diff --check`: will be run before committing this review.
