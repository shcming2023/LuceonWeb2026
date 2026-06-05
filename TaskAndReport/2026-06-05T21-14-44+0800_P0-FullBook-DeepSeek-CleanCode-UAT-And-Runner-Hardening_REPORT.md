# P0 FullBook DeepSeek CleanCode UAT And Runner Hardening Report

## 1. Scope

Director authorized a true full-book CleanCode run:

- Source material: `4134323036518274`
- Source RawCode bundle: `TaskAndReport/evidence/2026-06-05_PackBoundaryFix_CleanCode_Batch_UAT/rawcode-output/rawcode/4134323036518274/v339-pack-boundary-fix`
- Cleaner: true LLM API
- Locked model: `deepseek-v4-flash`
- Upstream rerun: none
- Production DB/MinIO/runtime worker writes: none

This UAT reused existing MinerU and official MinerU-Popo outputs. It did not rerun MinerU or MinerU-Popo.

## 2. Execution Summary

The full book was completed across controlled resumable batches:

- Initial full run: `TaskAndReport/evidence/2026-06-05_FullBook_DeepSeek_CleanCode_UAT_v2`
- Resume from sample 45: `TaskAndReport/evidence/2026-06-05_FullBook_DeepSeek_CleanCode_UAT_v3_remaining_from_45`
- Resume from sample 88 after image-ref hardening: `TaskAndReport/evidence/2026-06-05_FullBook_DeepSeek_CleanCode_UAT_v5_remaining_from_88`
- Final resume from sample 89: `TaskAndReport/evidence/2026-06-05_FullBook_DeepSeek_CleanCode_UAT_v6_remaining_from_89`

Final merged chapter-level result:

- Completed cleaning units: `111 / 111`
- Remaining: `0`
- `PASS`: `30`
- `NEEDS_REVIEW`: `81`
- `BLOCKED`: `0`
- Review items emitted: `229`
- Missing `review_items.json`: `0`
- Missing `review_patch_contract.json`: `0`

The high `NEEDS_REVIEW` count is expected for this stage: the model cleaned content but correctly surfaced OCR, formula, visual placement, and source ambiguity cases for manual review instead of inventing source truth.

## 3. Asset Fidelity Check

Final merged CleanCode asset check:

- Clean Markdown image references: `1751`
- Image refs mapped to `image_map.json`: `1751`
- Unknown or mutated image refs: `0`
- Missing local physical image files: `0`

This satisfies the asset hash preservation gate for the generated CleanCode evidence.

## 4. UAT-Discovered Root Causes And Fixes

Three real runner defects were exposed by the full-book workload and fixed on `main`:

1. LLM JSON parse failure on LaTeX backslashes
   - Symptom: DeepSeek returned JSON strings containing LaTeX commands such as `\mathsf` that were invalid JSON escapes.
   - Fix: `0b679b4 Repair LLM JSON LaTeX escapes`

2. LLM-mutated image hash refs
   - Symptom: one image hash filename character was changed by the model, violating asset hash preservation.
   - Fix: `f2cdac9 Restore mutated image refs from source blocks`

3. Validator checked pre-postprocess image refs
   - Symptom: postprocessor restored the correct image hash, but validator still blocked based on the raw model response.
   - Fix: `2a2c265 Validate postprocessed image refs`

These were runner/adapter hardening fixes only. MinerU and MinerU-Popo were not modified.

## 5. Verification

Focused smoke passed on current `main@2a2c265`:

```text
node server/tests/rawcode2cleancode-runner-smoke.mjs
RawCode2CleanCode UAT runner smoke passed.
```

Smoke coverage includes:

- approved model gate
- no production side effects
- LLM JSON LaTeX escape repair
- LLM-mutated image ref restoration
- validator check against final postprocessed image refs
- review item and patch contract emission

Secret hygiene check:

- Evidence scan found no API key, authorization header, or bearer token text in the full-book UAT evidence directories.

## 6. Acceptance Boundary

Accepted:

- The RawCode -> CleanCode true LLM pipeline can process the whole Math 2022 book from existing RawCode artifacts.
- The pipeline preserves unit boundaries, source refs, review surfaces, and image hash references.
- Non-publishable uncertainty is captured as review items instead of being silently accepted.
- No hard `BLOCKED` units remain in the final merged full-book result.

Not accepted:

- Final publishable CleanCode without manual review.
- CleanLaTeX generation.
- PDF regeneration.
- Product review workbench UX.
- DB/MinIO publication of this local UAT evidence.
- MinerU/MinerU-Popo quality improvement or rerun.
- Production readiness, L3, pressure PASS, or go-live.

## 7. Recommended Next Step

Proceed to productizing the manual review loop:

- ingest `review_items.json` and `review_patch_contract.json` into a review workbench;
- let reviewers accept/edit/keep unresolved/request reparse per item;
- only produce accepted CleanCode after all blocking review items are closed.
