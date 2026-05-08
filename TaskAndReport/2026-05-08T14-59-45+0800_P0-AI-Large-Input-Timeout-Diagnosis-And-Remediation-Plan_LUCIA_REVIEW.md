# Lucia Review: P0 AI Large-Input Timeout Diagnosis And Remediation Plan

Review:
P0 AI Large-Input Timeout Diagnosis And Remediation Plan

Task ID:
`TASK-20260508-144815-P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan`

Reviewed by:
Lucia

Reviewed at:
2026-05-08T14:59:45+0800

Decision:
`ACCEPTED_CODE_LEVEL_PLAN`

## Review Basis

- Task brief: `TaskAndReport/2026-05-08T14-48-15+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_TASK.md`
- Lucode report: `TaskAndReport/2026-05-08T14-54-38+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_REPORT.md`
- Relevant prior evidence: `TASK-20260508-142433-P0-Large-PDF-Soak-Validation`
- Current repository state: `main`

## Accepted Findings

Lucia accepts the diagnosis that the large-PDF failure is primarily an AI first-pass input-budget issue, not a MinerU or MinIO failure.

Accepted facts:

- Large-PDF validation task `task-1778222027064` reached terminal `failed` at `stage=ai`.
- MinerU completed and produced parsed artifacts; MinIO raw and parsed artifacts were preserved.
- Parsed Markdown length was `104823` characters and `parsedFilesCount` was `99`.
- Current evidence-pack mode did not trigger because the existing worker threshold is materially higher than this sample shape.
- The legacy sampler selected about `78084` characters, yielding an estimated first-pass request payload of about `83427` characters after prompt wrapping.
- Ollama `qwen3.5:9b` timed out at about `300000ms`.
- Strict no-skeleton behavior remained correct: the task failed explicitly instead of producing skeleton metadata.

## Accepted Remediation Direction

Lucia accepts Lucode's recommended first remediation direction:

`P0 Adaptive Evidence-Pack First-Pass For Large AI Metadata Inputs`

The first implementation should reduce first-pass input size before changing model capacity or timeout policy. The implementation must keep strict failure semantics unchanged.

Accepted initial trigger thresholds for implementation:

- Markdown length greater than `50000`.
- Source file size greater than `10000000` bytes.
- Parsed files count greater than `50`.

If any trigger is true, the worker should select evidence-pack mode for first-pass AI metadata input.

## Boundaries

- This review does not approve production release readiness.
- This review does not authorize production runtime mutation, deployment, rollback, DB mutation, MinIO object deletion, Docker volume deletion, artifact cleanup, or secret changes.
- This review does not authorize skeleton fallback, silent degradation, or parse-only completion being represented as AI-recognized metadata.
- Product decision on parse-complete but AI-failed operator flow remains separate and is not resolved by this implementation task.

## Follow-Up

Lucia issued:

`TASK-20260508-145945-P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs`

Lucode must implement and test the adaptive first-pass selection in repository code only. Production runtime validation must be handled by a later Lucia task after code-level acceptance.
