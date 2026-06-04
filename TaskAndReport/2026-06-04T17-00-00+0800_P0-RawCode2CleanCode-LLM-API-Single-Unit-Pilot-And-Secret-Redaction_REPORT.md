# P0 RawCode2CleanCode LLM API Single Unit Pilot And Secret Redaction Report

Task ID: `TASK-20260604-170000-P0-RawCode2CleanCode-LLM-API-Single-Unit-Pilot-And-Secret-Redaction`

Status: `Blocked on valid LLM API credential`

Branch: `codex/rawcode2cleancode-llm-api-single-unit-pilot`

## Scope

Run a controlled true LLM cleaner pilot for one real Task329 cleaning unit, without using local Ollama as the quality source.

Chosen pilot unit:

- material: `4134323036518274`
- source asset version: `v329-cleanlatex-pack-generator-a800-math-2022-prod-uat`
- unit: `toc-0024`
- title: `4.1 Colectingand classifyingdata`

## What Was Verified

The existing mainline bridge remains valid:

```text
Task329 cleaning_unit_packs.json
-> scripts/cleanlatex-pack-to-rawcode.mjs
-> RawCode2CleanCode runner manifest
-> one-unit real-mode runner preflight
```

The real-mode runner correctly performed dry-run preflight before attempting the LLM API call.

## Blocking Evidence

The true LLM API phase did not complete because the current environment `OPENAI_API_KEY` was rejected by the API provider with HTTP 401 invalid key.

No key value is recorded in this report.

Local evidence directory:

```text
/Users/concm/Dev_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_LLM_API_Single_Unit_Pilot_DEV
```

The failed run was scrubbed locally to redact API-key-like text from result files.

## Code Fix

The runner now redacts API-key-like tokens from sample processing errors before writing `reason`, `stack`, `runner-result.json`, or `evidence-surface.json`.

Regression coverage added:

- `server/tests/rawcode2cleancode-runner-smoke.mjs`
  - verifies API-key-like text is replaced by `[REDACTED_API_KEY]` in sample processing errors.

## Verification

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/rawcode2cleancode-runner.mjs
git diff --check
```

All checks passed.

## Closure

This task is not a CleanCode quality pass. It is closed only for the safety hardening portion.

The true LLM single-unit pilot remains blocked until a valid LLM API credential and, if needed, API base/model are configured in the execution environment.

No DB writes, no MinIO writes, no runtime worker posts, no production metadata mutation, no readiness/L3/go-live claim.
