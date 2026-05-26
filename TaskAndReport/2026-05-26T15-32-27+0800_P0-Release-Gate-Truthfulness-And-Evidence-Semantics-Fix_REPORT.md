# P0 Release Gate Truthfulness And Evidence Semantics Fix - Report

Status: `COMPLETED_CODE_TEST_LEVEL`

## Summary

Fixed release-gate evidence semantics so Stage 3/4/5 cannot produce misleading pass records.

## Changes

- `uat/smoke-test.sh`
  - Added dependency-health no-submit check.
  - Added true `PASS/FAIL/SKIP/TOTAL` accounting.
  - Emits `SMOKE_RESULT PASS=<n> FAIL=<n> SKIP=<n> TOTAL=<n>`.
- `uat/release-gate.sh`
  - Parses smoke/stress machine-readable result lines instead of hardcoding pass summaries.
  - Blocks Stage 4 in non-interactive mode rather than treating endpoint reachability as a fault-injection pass.
  - Uses `mineru-down` admission mode for Stage 4.
  - Keeps all conclusion wording as gate evidence only, not readiness/go-live.
- `uat/stress-test-concurrency.sh`
  - Requires at least 5 successful PDF task creations.
  - Fails on submit failures and zero-task runs.
  - Emits `STRESS_RESULT`.
- `uat/fault-injection-worker-crash.sh`
  - Fails if crash was not actually exercised.
  - Fails if no accepted recovery event is present.
- `uat/fault-injection-admission.sh`
  - Missing PDF/Markdown samples now fail mineru-down validation instead of being silently skipped.

## Evidence

- `bash -n uat/smoke-test.sh uat/release-gate.sh uat/stress-test-concurrency.sh uat/fault-injection-admission.sh uat/fault-injection-worker-crash.sh ops/start-luceon-runtime.sh`: `PASS`
- `bash uat/release-gate.sh --help`: `PASS`
- `git diff --check`: `PASS`
- `BASE_URL=http://127.0.0.1:8081 bash uat/smoke-test.sh`: `SMOKE_RESULT PASS=13 FAIL=0 SKIP=0 TOTAL=13`

## Boundary

No fault injection, pressure run, upload, submit-probe, DB write, MinIO write, Docker mutation, readiness, release-readiness, or go-live claim was performed.
