# P1 Pressure Test AI Timeout Failure Architecture Diagnosis - Director Review

Review time: 2026-05-15T05:48:28+0800

Task: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_TASK.md`

Report reviewed: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_REPORT.md`

Result: `ACCEPTED_ARCHITECTURE_DIAGNOSIS_AI_TIMEOUT_REMEDIATION_REQUIRED_WITH_PRESSURE_RESIDUE_FOLLOWUP`

## Director Judgment

Accepted at architecture-diagnosis level.

The Architect report correctly identifies the pressure-test AI failures as AI metadata / Ollama timeout failures, not as a global MinIO, Docker, or service-down incident. The failed AI rows were strict-mode failures, and strict no-skeleton fallback behaved correctly.

This is not a pressure PASS, L3 PASS, release-readiness claim, production-readiness claim, or go-live claim.

## Evidence Checked

- Task 151 had already established the pressure test failed: 24 user-submitted pressure tasks, 20 `review-pending/review`, 3 `failed/ai`, and 1 `running/mineru-processing`.
- Task 152 report identified three AI timeout failures:
  - two first-pass provider timeouts around the 180000ms deadline;
  - one JSON repair timeout around the 180000ms deadline after first-pass success.
- Source review confirmed strict mode config in `server/services/ai/metadata-worker.mjs` sets Ollama timeout to 180000ms, uses two-pass repair, and drives repair with larger `num_predict` values.
- Source review confirmed `server/services/ai/providers/ollama.mjs` already captures provider-level timeout details, but worker-level terminal failure metadata is not yet explicit enough for safe manual retry/re-AI decisions.
- Source review confirmed `server/upload-server.mjs` dependency health currently mixes Ollama service/model/generation semantics in a way that can become noisy during heavy pressure windows.
- Runtime spot-check remained non-destructive:
  - upload health: OK;
  - dependency health: OK / non-blocking;
  - direct Ollama `/api/version` reachable;
  - direct Ollama `/api/ps` showed `qwen3.5:9b` resident with `keep_alive` horizon;
  - MinerU admission circuit closed;
  - one pressure residue task still active in `mineru-processing`.

## Important Caveat

The AI-timeout diagnosis is accepted, but the pressure-test aftermath is not fully settled because task `task-1778765417422` remains active in MinerU processing. Current evidence says MinerU API is still processing and the container-visible log source is stale. That active task must not be stopped, cleaned, retried, reparsed, re-AIed, or otherwise mutated without later explicit authorization.

Director is therefore issuing a separate read-only follow-up task for TestAcceptanceEngineer to track this pressure residue task to terminal state, clear stall/hang evidence, or a bounded blocked report.

## Follow-Up Tasks

1. `TASK-20260515-054828-P1-Pressure-Residue-MinerU-Active-Task-Read-Only-Followup`
   - Assigned to `TestAcceptanceEngineer`.
   - Purpose: read-only follow-up on the currently active pressure residue MinerU task.

2. `TASK-20260515-054828-P1-AI-Timeout-Classification-And-Manual-Retry-Eligibility-Contract`
   - Assigned to `DevelopmentEngineer`.
   - Purpose: implement code/test-level AI timeout phase classification and manual retry eligibility metadata, without auto-retry or skeleton fallback.

## Boundaries

Not authorized by this review:

- pressure PASS, L3 PASS, release-readiness, production-readiness, or go-live;
- any upload, cleanup, repair, retry, reparse, or re-AI;
- destructive DB, MinIO, Docker volume, or data mutation;
- Docker down, broad restart/rebuild, service ownership mutation, model pull/delete/replace, config/secret/sample mutation;
- automatic failed-task recovery or generic auto-retry for the three failed AI tasks.

