# Lucia Review: P0 Pressure Restart Created Tasks Read-Only Terminal Observation

- Reviewed task: `TASK-20260510-161343-P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation`
- Review time: `2026-05-10T17:19:43+0800`
- Reviewed by: Lucia
- Report: `TaskAndReport/2026-05-10T16-13-43+0800_P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation_REPORT.md`
- Review decision: `ACCEPTED_OBSERVATION_TIMEOUT_WITH_PROGRESS_OBSERVABILITY_GAP`

## Decision

Lucia accepts the Task 76 report as scoped read-only observation evidence.

The result is not pressure-test PASS, not manual pressure-test readiness, not L3/full-site acceptance, and not production release readiness. It proves that the already-created Task 75 set did not reach terminal/manual-review state within the 60-minute observation window, while dependency-health, MinerU submit admission, admission circuit, and Ollama remained non-blocking.

## Evidence Reviewed

Lucode reported:

- `1` target task remained `running/mineru-processing`: `task-1778400448971`.
- `19` target tasks remained `pending/upload`.
- No AI metadata jobs were created for the target 20 tasks.
- Dependency-health stayed non-blocking.
- MinerU submit probe stayed successful.
- Admission circuit stayed closed.
- Ollama `qwen3.5:9b` stayed reachable.
- Native MinerU logs showed backend `pipeline` still processing a 632-page PDF, slowly progressing in OCR detection within batch `2/10`.
- The task page/API-facing semantic remained generic: `MinerU 正在解析` / `50%`.

Lucia independently rechecked after the report:

- `dependency-health?mineruSubmitProbe=true`: `ok=true`, `blocking=false`, MinerU submit-probe HTTP `202`, Ollama chat OK.
- `/ops/mineru/admission-circuit`: `state=closed`, `open=false`, counts `parseRunning=1`, `parsePending=19`, `aiPending=0`, `aiRunning=0`.
- `/ops/mineru/active-task`: active task remained `task-1778400448971`, `running/mineru-processing`, `progress=50`, message `MinerU 正在解析`, with `_synthetic_warn=mineru-status-query-timeout`.
- `/api/ps`: `qwen3.5:9b` remained resident.

## Assessment

The current evidence supports a long-running local production-line governance finding, not a single failed upload or a generic dependency outage:

- Intake/admission is currently healthy.
- The durable MinerU admission circuit is closed.
- The active MinerU runtime appears alive enough to accept submit probes.
- The first created pressure task is still occupying the single MinerU heavy-processing slot.
- The remaining 19 tasks are queued behind it.

However, Director cannot safely judge long-running progress from the task page because the operator-facing task semantics do not expose the meaningful MinerU runtime signals that are visible in native logs: backend, window/batch, page range, current phase, OCR progress, last observed log time, and whether progress is live, stale, missing, or timed out.

This is a release-blocking observability and operations-governance debt for local long-running production use. It must be repaired before another pressure restart or production release-readiness decision can be credible.

## Accepted Boundaries

- No new upload was created by Task 76.
- Sample 21 was not retried.
- Samples 22-24 were not attempted.
- No failed task was repaired, retried, deleted, or cleaned.
- No DB, MinIO object, Docker volume, log file, sample file, model, timeout, secret, production override, or runtime config was modified.
- No pressure PASS, L3/full-site PASS, manual pressure-test readiness, or production release readiness is claimed.

## Follow-Up

Lucia issued:

`TASK-20260510-171943-P1-Task-Page-MinerU-Progress-Semantics-Restoration`

This follow-up is code-level only. It must restore operator-facing MinerU progress/log semantics on the task page and related API surface without creating uploads, mutating production task data, retrying historical pressure tasks, or declaring release readiness.

