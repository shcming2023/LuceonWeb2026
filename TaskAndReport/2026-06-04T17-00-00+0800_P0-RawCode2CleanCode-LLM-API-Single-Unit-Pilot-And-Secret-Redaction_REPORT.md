# P0 RawCode2CleanCode LLM API Single Unit Pilot And Secret Redaction Report

Task ID: `TASK-20260604-170000-P0-RawCode2CleanCode-LLM-API-Single-Unit-Pilot-And-Secret-Redaction`

Status: `Completed with reviewable CleanCode candidate requiring manual asset review`

Branch: `codex/rawcode2cleancode-duplicate-aware-coverage`

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

## Initial Blocking Evidence

The true LLM API phase did not complete because the current environment `OPENAI_API_KEY` was rejected by the API provider with HTTP 401 invalid key.

No key value is recorded in this report.

Local evidence directory:

```text
/Users/concm/Dev_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_LLM_API_Single_Unit_Pilot_DEV
```

The failed run was scrubbed locally to redact API-key-like text from result files.

## Secret Redaction Fix

The runner now redacts API-key-like tokens from sample processing errors before writing `reason`, `stack`, `runner-result.json`, or `evidence-surface.json`.

Regression coverage added:

- `server/tests/rawcode2cleancode-runner-smoke.mjs`
  - verifies API-key-like text is replaced by `[REDACTED_API_KEY]` in sample processing errors.

## DeepSeek API Pilot After Credential Was Provided

After the Director provided a valid DeepSeek API credential, Luceon reran the same single-unit pilot using the OpenAI-compatible API surface:

- API base: `https://api.deepseek.com/v1`
- model: `deepseek-chat`
- unit: `toc-0024`
- title: `4.1 Colectingand classifyingdata`
- source: real Task329 v329 pack artifact for material `4134323036518274`

The credential was used only as a transient process environment variable. It was not written to `.env`, task reports, committed files, or evidence artifacts.

Production/control evidence directory:

```text
/Users/concm/prod_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_DeepSeek_Single_Unit_Pilot_v2
```

Observed runner summary:

- `ok=true`
- `realRunExecuted=true`
- `completedSampleCount=1`
- `llmApiCall=1`
- `dbWrite=0`
- `minioWrite=0`
- `runtimeWorkerPost=0`
- production side effects: all zero

Generated CleanCode candidate:

```markdown
# 4.1 Collecting and classifying data

Data is a set of facts, numbers or other information. Statistics involves a process of collecting data and using it to try and answer a question. The flow diagram shows the four main steps involved in this process of statistical investigation:

- Identify the question (or problem to be solved)
- Is the question clear and specific?

Exercise 4.1
```

Quality outcome:

- final status: `NEEDS_REVIEW`
- risks: none
- split markers: resolved
- duplicate large text segments: absent
- raw normalized chars: `1337`
- raw de-duplicated normalized chars: `343`
- clean normalized chars: `313`
- duplicate-aware coverage ratio: `0.9125`
- unresolved items: `1`

The remaining `NEEDS_REVIEW` item is correct and useful: the source text references a flow diagram, but the pack did not provide an image reference for that diagram. This is not an LLM failure to clean text; it is a source/asset preservation gap that must remain visible for human review or upstream pack correction.

## Duplicate-Aware Coverage Fix

The first successful DeepSeek run produced faithful de-duplicated text, but the validator still compared clean text against repeated raw text copied multiple times from the pack. That incorrectly made reasonable de-duplication look like low coverage.

`scripts/rawcode2cleancode-pilot.mjs` now computes both:

- `content_coverage_ratio`: clean text over full raw normalized text.
- `deduplicated_content_coverage_ratio`: clean text over unique raw text segments split by blank paragraphs and `<|txt_split|>`.

The validator accepts coverage when either the ordinary ratio is high enough or the de-duplicated ratio is high enough. It still blocks true low-coverage output, residual split markers, duplicate large text segments, missing image files, and unresolved items.

Regression coverage added:

- `server/tests/rawcode2cleancode-runner-smoke.mjs`
  - verifies faithful LLM de-duplication can pass coverage without weakening the other quality gates.

## Verification

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/rawcode2cleancode-runner.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
git diff --check
```

All checks passed.

## Closure

This task is closed as a successful controlled true-LLM single-unit pilot with correct safety behavior.

It does not claim the unit is final publishable CleanCode. The output is a reviewable CleanCode candidate, and the remaining review item is the missing referenced flow diagram/image evidence.

No DB writes, no MinIO writes, no runtime worker posts, no production metadata mutation, no readiness/L3/go-live claim.
