# Lucode Completion Report: P0 Adaptive Evidence-Pack First-Pass For Large AI Metadata Inputs

## 1. Task Brief

- Based on Lucia task brief: `TaskAndReport/2026-05-08T14-59-45+0800_P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs_TASK.md`
- Assignee: Lucode
- Report time: 2026-05-08T15:09:50+0800
- Implementation branch: `lucode/p0-adaptive-evidence-pack-first-pass`
- Implementation HEAD: `8c1acd1 feat: use evidence pack for large ai metadata inputs`
- Report/main base: `3740cdb docs: assign adaptive ai evidence pack task`
- GitHub sync: implementation branch pushed to `origin/lucode/p0-adaptive-evidence-pack-first-pass`

## 2. Files Changed On Implementation Branch

- `server/services/ai/metadata-worker.mjs`
- `server/tests/ai-metadata-evidence-pack-smoke.mjs`

Report/list changes are recorded separately on `main`.

## 3. Implementation Summary

Implemented centralized adaptive AI input selection in `metadata-worker.mjs`:

- Added `shouldUseEvidencePack(markdownContentOrLength, sourceMeta)`.
- Added explicit thresholds:
  - Markdown length greater than `50000`.
  - `sourceMeta.fileSize` greater than `10000000` bytes.
  - `sourceMeta.parsedFilesCount` greater than `50`.
- Worker now selects `evidence-pack-v0.3` whenever any threshold is triggered.
- Ordinary short documents remain on `legacy-sampler-v0.2`.
- Existing evidence-pack behavior for very large documents is preserved because those documents still satisfy the new thresholds.
- Strict no-skeleton and explicit provider failure behavior were not changed.

Added structured input-selection observability:

- `aiClassificationSamplingMode`
- `aiClassificationInputOriginalLength`
- `aiClassificationInputSampledLength`
- `aiClassificationInputHash`
- `aiClassificationInputSelectionReasons`
- `aiClassificationInputSelectionThresholds`
- `aiClassificationRawTrace.input.triggerReasons`
- `aiClassificationRawTrace.input.thresholds`
- `aiClassificationRawTrace.input.observed`
- `ai-content-truncated` event payload now includes sampling mode, selected length, trigger reasons, input hash, thresholds, and observed values.

## 4. Trigger Behavior

| Trigger | Implemented behavior | Test evidence |
| --- | --- | --- |
| Markdown length `> 50000` | Selects evidence-pack mode with reason `markdown-length`. | `Test 2A`, `Test 3`, `Test 3A` in `ai-metadata-evidence-pack-smoke`. |
| Source file size `> 10000000` | Selects evidence-pack mode with reason `source-file-size`. | `Test 2A`, `Test 3A`. |
| Parsed files count `> 50` | Selects evidence-pack mode with reason `parsed-files-count`. | `Test 2A`, `Test 3A`. |
| Task 29 large-PDF-like shape | `104823` chars, `15157403` bytes, `99` parsed files selects evidence-pack mode and stays below `30000` selected chars before prompt wrapping. | `Test 3A`. |
| Short Markdown | Keeps legacy sampler mode and empty selection reasons. | `Test 4`. |

## 5. Test Additions

Extended `server/tests/ai-metadata-evidence-pack-smoke.mjs`:

- Added direct threshold coverage for each approved trigger.
- Added boundary assertion that exactly `50000` chars / `10000000` bytes / `50` parsed files does not trigger evidence-pack mode.
- Added task-29-like worker integration case using:
  - `104823` Markdown chars;
  - `15157403` source bytes;
  - `99` parsed files.
- Asserted selected evidence-pack input remains below `30000` chars.
- Asserted input-selection metadata includes mode, original length, selected length, trigger reasons, thresholds, observed values, and input hash.
- Preserved short-document legacy sampler coverage.

Existing real-sample smoke was rerun to protect existing strict/provider/skeleton semantics.

## 6. Command Results

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Clean before sync; implementation branch clean after commit. |
| `git fetch origin` | 0 | Synced before task execution. |
| `git pull --ff-only origin main` | 0 | Already up to date at check start; later main included Lucia task issue commit `3740cdb`. |
| `node server/tests/ai-metadata-evidence-pack-smoke.mjs` | 0 | Passed. Added threshold and task-29-like assertions. |
| `node server/tests/ai-metadata-real-sample-smoke.mjs` | 0 | Passed. Existing skeleton/provider behavior unchanged. |
| `node server/tests/dependency-health-smoke.mjs` | 0 | Passed: 31 passed / 0 failed. |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | Passed. |
| `npx pnpm@10.4.1 run build` | 0 | Passed. Vite emitted existing chunk-size warning only. |
| `git diff --check` | 0 | Passed. |

## 7. Explicit Guardrail Confirmation

- Strict no-skeleton behavior remains preserved.
- No skeleton fallback was added.
- No silent degradation was added.
- No Ollama model or timeout policy was changed.
- No chunked or multi-pass extraction was implemented.
- No production runtime mutation was performed.
- No deploy, restart, rebuild, rollback, DB cleanup, MinIO cleanup, Docker volume operation, task/artifact deletion, secret change, or release-readiness claim occurred.

## 8. Residual Validation Needed

Before production release-readiness can be reconsidered, Lucia should assign separate validation for:

- Reviewing and merging the implementation branch.
- Deploying the accepted code through the approved production path, if authorized.
- Re-running a controlled large-PDF AI validation against production/runtime artifacts.
- Confirming the same task-29-like shape no longer sends the old roughly `83k` first-pass payload.
- Confirming AI metadata can complete, or if it still fails, that the failure is explicit with preserved parse artifacts and no skeleton.

## 9. Review Requirement

Lucia review is required. Director decision is only required if Lucia wants production deployment/runtime mutation or production release-readiness reconsideration.

