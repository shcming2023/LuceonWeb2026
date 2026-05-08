# Director Decision Needed: P0 Next Release-Readiness Validation Scope

Task:
P0 Next Release-Readiness Validation Scope

Task ID:
`TASK-20260508-191021-P0-Next-Release-Readiness-Validation-Scope`

Owner:
Director

Recorded by:
Lucia

Recorded at:
2026-05-08T19:10:21+0800

Project:
Luceon2026

## Decision Question

Which release-readiness validation track should Lucia assign next after the controlled adaptive evidence-pack production validation passed?

## Context

Task 38 proved the accepted adaptive evidence-pack path in production for the authorized large-PDF sample:

- bounded non-mutating Ollama warm-up succeeded;
- warm dependency-health passed;
- exactly one controlled upload was created;
- MinerU completed with `parsedFilesCount=99`;
- AI reached `review-pending`;
- adaptive input used `evidence-pack-v0.3`;
- selected input length was `16261`;
- no forbidden mutation or release-readiness claim occurred.

Production release readiness remains unclaimed.

## Lucia Recommendation

Choose the next validation track explicitly because each option changes the evidence boundary and may create production validation artifacts.

Recommended next option:

`CONCURRENCY_VALIDATION_FIRST`

Rationale:

- Large-PDF adaptive evidence-pack behavior is now validated for one controlled sample.
- Concurrency remains one of the major release-readiness gaps.
- A narrow concurrency task can be written with strict limits, no destructive operations, no release-readiness claim, and explicit artifact-count caps.

## Options

1. `CONCURRENCY_VALIDATION_FIRST`
   - Lucia issues a tightly scoped Lucode task for controlled concurrent upload validation.
   - Must cap upload count, use approved samples, preserve strict AI/model/override boundary, avoid destructive operations, and keep production release readiness unclaimed.

2. `ERROR_PATH_MATRIX_FIRST`
   - Lucia issues a Lucode task to validate selected non-destructive error paths.
   - Must avoid cleanup/deletion and avoid broad production mutation.

3. `ROLLBACK_RECOVERY_REHEARSAL_PLAN_ONLY`
   - Lucia issues a planning-only task for rollback/recovery rehearsal boundaries.
   - No production rollback or service mutation until separately approved.

4. `HOLD_FOR_DIRECTOR_REVIEW`
   - Pause additional validation until Director manually reviews current evidence.

## Required Director Output

Please choose one of:

- `CONCURRENCY_VALIDATION_FIRST`
- `ERROR_PATH_MATRIX_FIRST`
- `ROLLBACK_RECOVERY_REHEARSAL_PLAN_ONLY`
- `HOLD_FOR_DIRECTOR_REVIEW`

## Autonomy Rule

If this Director decision remains unanswered after two Lucia heartbeat checks, Lucia may choose only the conservative non-destructive default: issue a planning/preflight task for the next validation scope without creating new production uploads. Lucia may not use autonomy to approve production release readiness, destructive operations, Docker/service mutation, model/timeout/config/secret changes, data deletion, or broader release acceptance.
