# Stage 5 Evidence - Stress And Concurrency Queue Verification

Collected at: `2026-05-26T15:32:27+0800`

Scope: script truthfulness fix and no-mutation ledger entry. No pressure test, batch upload, runtime sample mutation, DB write, MinIO write, Docker mutation, or readiness/go-live claim was performed.

Full-UAT supplement collected at: `2026-05-26T16:16:00+0800` after user authorization for pressure uploads.

## Gate Semantics Fixed

- `uat/stress-test-concurrency.sh` now requires at least 5 successfully created PDF tasks.
- Any task submission failure now contributes to `FAIL`.
- Zero successfully created tasks now exits failure immediately.
- The script emits machine-readable `STRESS_RESULT PASS=<n> FAIL=<n> PDF_TASKS=<n> TOTAL_TASKS=<n> MINERU_VIOLATION=<n> AI_VIOLATION=<n> TERMINAL=<n>`.
- `uat/release-gate.sh --full-gate` records the real `STRESS_RESULT` instead of hardcoding a pass summary.

## Validation

- Shell syntax check passed for `uat/stress-test-concurrency.sh` and `uat/release-gate.sh`.
- `git diff --check` passed.
- Real bounded pressure command passed:
  - `TEST_PDF_DIR=/tmp/luceon-uat-stress2/pdf`
  - `TEST_MD_DIR=/tmp/luceon-uat-stress2/md`
  - `BASE_URL=http://127.0.0.1:8081`
  - `MAX_WAIT_MINUTES=10`
  - `POLL_INTERVAL=5`
  - `bash uat/stress-test-concurrency.sh`
- Result:

```text
STRESS_RESULT PASS=6 FAIL=0 PDF_TASKS=5 TOTAL_TASKS=5 MINERU_VIOLATION=0 AI_VIOLATION=0 TERMINAL=5
```

- Final batch task ids:
  - `task-1779783332644`
  - `task-1779783333310`
  - `task-1779783333912`
  - `task-1779783334501`
  - `task-1779783335206`
- All five reached terminal `review-pending`.

## UAT Finding And Correction

- The first real Stage 5 run reached five terminal tasks, but the script counted unrelated/global historical `ai-running`/`stage=ai` records and produced a false `AI_VIOLATION=31`.
- `uat/stress-test-concurrency.sh` now scopes active MinerU/AI counts to the current tracked batch and non-terminal tasks.

## Status

- Stage 5 fake-pass prevention: `PASS`
- Real pressure/concurrency evidence: `PASS`

## Authorization Required

Stage 5 was performed under explicit UAT authorization. This is bounded pressure evidence only, not readiness or go-live approval.
