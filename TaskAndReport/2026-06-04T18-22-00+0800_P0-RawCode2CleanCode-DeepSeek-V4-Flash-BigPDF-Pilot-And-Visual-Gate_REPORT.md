# P0 RawCode2CleanCode DeepSeek V4 Flash BigPDF Pilot And Visual Gate Report

Task ID: `TASK-20260604-182200-P0-RawCode2CleanCode-DeepSeek-V4-Flash-BigPDF-Pilot-And-Visual-Gate`

Status: `Completed with one PASS candidate and one correct NEEDS_REVIEW candidate`

Branch: `codex/rawcode2cleancode-deepseek-v4-flash-pilot`

## Scope

Run a controlled true API pilot from previous large-PDF artifacts, while enforcing the Director's cost boundary:

```text
Allowed model: deepseek-v4-flash
Forbidden: any other LLM model for this pilot
```

Input source:

- material: `4134323036518274`
- source artifact: Task329 v329 RawCode bundle derived from A800 Math 2022 Popo/CleanLaTeX pack output
- units:
  - `toc-0003` / `1.1 Different types of numbers`
  - `toc-0024` / `4.1 Colectingand classifyingdata`

This task did not rerun MinerU or MinerU-Popo.

## Code Fixes

1. `scripts/rawcode2cleancode-pilot.mjs`
   - Locks the LLM cleaner model to `deepseek-v4-flash`.
   - Rejects any other model before an API call can be made.
   - Adds a validator gate for visual references without matching image references or unresolved review items.

2. `scripts/rawcode2cleancode-runner.mjs`
   - Adds runner-level early rejection for non-approved LLM model selection.

3. `server/tests/rawcode2cleancode-runner-smoke.mjs`
   - Verifies non-approved LLM models are rejected before sample processing.
   - Verifies clean text that references a visual artifact without an asset or review item becomes `NEEDS_REVIEW`.

## True API Pilot Evidence

Evidence directory:

```text
/Users/concm/prod_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_DeepSeek_V4_Flash_BigPDF_Pilot
```

Runner output root:

```text
/Users/concm/prod_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_DeepSeek_V4_Flash_BigPDF_Pilot/runner-output/rawcode2cleancode-real-luceon-prod-uat-20260604T101835624Z-a8f7c1f76995
```

Runner result:

- `ok=true`
- `realRunExecuted=true`
- `attemptedSampleCount=2`
- `completedSampleCount=2`
- `llmApiCall=2`
- `dbWrite=0`
- `minioWrite=0`
- `runtimeWorkerPost=0`
- production side effects: all zero

API response model readback:

- `toc-0003`: `model=deepseek-v4-flash`, total tokens `16647`
- `toc-0024`: `model=deepseek-v4-flash`, total tokens `1857`

No API key or Bearer token string was found in the evidence directory by local grep scan.

## Quality Result

Initial runner result using the pre-existing validator marked both samples `PASS`.

Manual inspection exposed a quality-gate gap in `toc-0024`: the CleanCode text still says "The flow diagram shows...", but the output has no image reference and no unresolved review item. That is not publishable as a clean candidate.

After adding the visual-reference gate, Luceon revalidated the already generated CleanCode offline without making another API call:

```text
offline-revalidation-after-visual-gate.json
```

Final reviewed outcome:

- `toc-0003` / `1.1 Different types of numbers`: `PASS`
- `toc-0024` / `4.1 Colectingand classifyingdata`: `NEEDS_REVIEW`
  - risk: `visual_reference_without_asset_or_review_item`
  - reason: clean text references `flow diagram` / `diagram`, but no image reference or unresolved item is present

## Verification

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node --check scripts/rawcode2cleancode-runner.mjs
git diff --check
```

All checks passed.

## Closure

The true API pilot is now working on previous large-PDF output using only `deepseek-v4-flash`.

The current next blocker is not model invocation. It is asset/reference preservation in the cleaning unit pack and/or LLM output contract: when source text references a visual artifact, the CleanCode candidate must either preserve the asset reference or emit a clear unresolved review item.

No MinerU/MinerU-Popo rerun, no DB write, no MinIO write, no runtime worker post, no credential commit, no production metadata mutation, no final CleanCode publishability/readiness/L3/go-live claim.
