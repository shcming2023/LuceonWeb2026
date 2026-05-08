# Lucode Completion Report: P0 AI Large-Input Timeout Diagnosis And Remediation Plan

## 1. Task Brief

- Based on Lucia task brief: `TaskAndReport/2026-05-08T14-48-15+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_TASK.md`
- Assignee: Lucode
- Report time: 2026-05-08T14:54:38+0800
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Base HEAD: `5b9a45c docs: accept large pdf soak failure`
- Scope performed: non-destructive diagnosis and remediation plan only.
- Production mutation: none.
- Release readiness claim: none.

## 2. Executive Finding

The large-PDF soak failure is most consistent with an oversized first-pass AI metadata input sent to local Ollama `qwen3.5:9b`, not with MinerU or MinIO failure.

For the #29 large-PDF validation material:

- MinerU completed successfully.
- MinIO artifacts were preserved.
- Parsed markdown length was `104823` characters.
- Parsed files count was `99`.
- Current evidence-pack threshold did not trigger because the worker only switches when `originalLength > 150000 || parsedFilesCount > 1000`.
- The legacy sampler produced `78084` characters.
- The first-pass request payload was approximately `83427` characters after adding the draft prompt.
- Ollama timed out at about `300014ms` against the configured `300000ms` strict-mode timeout.
- Strict no-skeleton fallback was preserved: the job failed explicitly instead of generating fake metadata.

The immediate technical gap is therefore the large-input selection policy. A document of this size is already too large for the current local model/runtime path, but it is still below the evidence-pack threshold, so the system chooses the heavier legacy sample path.

## 3. Current Behavior Observed

### AI worker timeout and strict fallback behavior

Current worker behavior in `server/services/ai/metadata-worker.mjs`:

- Strict mode is enabled by `DISABLE_AI_SKELETON_FALLBACK=true` or `ALLOW_AI_SKELETON_FALLBACK=false`.
- Strict runtime defaults to local Ollama:
  - base URL: `process.env.OLLAMA_API_URL || http://host.docker.internal:11434`
  - model: `process.env.OLLAMA_TIER2_MODEL || qwen3.5:9b`
  - timeout: `300000ms`
  - two-pass JSON repair enabled.
- First pass uses the v0.2 draft prompt.
- If the first pass times out, two-pass repair is not reached.
- In strict mode, `degradeToSkeleton()` throws and the job is marked failed.

This behavior is correct for the no-silent-degradation contract.

### Sampling and truncation behavior

Current worker selection:

- If `originalLength > 150000 || parsedFilesCount > 1000`, use `buildEvidencePack()`.
- Otherwise, use `sampleMarkdown(markdownContent, sourceMeta, 80000)`.

Current sampler behavior:

- Legacy sampler target: `80000` characters.
- Evidence pack target: structured evidence around source facts, shape, front matter, TOC, headings, snippets, and tail, capped around `30000` characters.

Read-only local calculation against the #29 validation artifact:

```json
{
  "markdownLength": 104823,
  "parsedFilesCount": 99,
  "evidencePackWouldTrigger": false,
  "legacySampleLength": 78084,
  "evidencePackLength": 16299,
  "draftPromptLength": 5343,
  "fullPromptLength": 6404,
  "firstPassPayloadCharsApprox": 83427,
  "evidencePackPayloadCharsApprox": 21642,
  "legacyInputHash": "sha256:c36bd67f22d97017f21aa4d27c581f65a1b35162d3784e891a8a1eecc32982e6",
  "packInputHash": "sha256:979a16bdb676511d7bd1d1aba591b31fa374b33a43cff156e67c6a5c056a0149"
}
```

This shows the same document would have produced a much smaller first-pass payload if evidence pack selection had triggered.

### Runtime failure record

The #29 AI metadata job ended with:

- `state`: `failed`
- `metadata.currentPhase`: `first-pass-failed`
- `message`: `AI 识别异常: [AI 严格模式拦截] 不允许降级到骨架模型: AI Provider 调用全部失败: Ollama Provider Error: [TimeoutError] The operation was aborted due to timeout (BaseURL: http://host.docker.internal:11434, Model: qwen3.5:9b, Duration: 300014ms, Timeout: 300000ms)；严格模式禁止骨架兜底`

Diagnostic gap:

- The final job row had `providerId: null` and `model: null` even though the error message included the provider URL and model.
- This does not cause the timeout, but it weakens operations visibility.

## 4. Test Coverage Assessment

Existing tests cover important adjacent behavior:

- `server/tests/ai-metadata-real-sample-smoke.mjs` covers provider timeout classification and skeleton fallback semantics in non-strict paths.
- `server/tests/ai-metadata-evidence-pack-smoke.mjs` covers evidence-pack construction and worker selection for very large documents.

Observed coverage gap:

- No focused test currently covers a medium-large case like `104823` markdown chars and `99` parsed files, where the current threshold still chooses legacy sampling.
- No test asserts a first-pass payload budget for large PDFs.
- No test verifies that a large-PDF-like input selects evidence pack below the current `150000` character threshold.
- Runtime evidence verifies strict no-skeleton behavior, but tests should continue protecting it when sampling policy changes.

## 5. Root-Cause Hypothesis

Primary hypothesis:

The AI timeout is caused by sending an approximately `83k` character first-pass request to local `qwen3.5:9b` under a `300000ms` timeout. The input is too large for the current local runtime path.

Contributing factors:

- The evidence-pack threshold is too high for large PDF workbook-style documents.
- The legacy sampler cap of `80000` characters is too large for local first-pass structured metadata generation.
- There is no adaptive retry that falls back to a smaller evidence pack after a first-pass timeout.
- Dependency health can confirm Ollama reachability, but not model capacity for large metadata prompts.
- Failed job metadata does not persist provider/model in structured fields.

Less likely causes based on current evidence:

- MinerU parse failure: unlikely; parsing completed and artifacts were available.
- MinIO write/read failure: unlikely; parsed artifact was read for diagnosis.
- JSON repair/schema failure: unlikely; first pass timed out before repair could run.
- Silent skeleton fallback: not observed; strict mode blocked skeleton fallback as required.

## 6. Remediation Options

### Option A: Tighter evidence-pack selection for large AI inputs

Lower and broaden the trigger for evidence-pack selection.

Recommended initial thresholds for Lucia review:

- `markdownLength > 50000`, or
- `sourceMeta.fileSize > 10000000`, or
- `parsedFilesCount > 50`.

Expected effect:

- The #29 sample would use evidence pack.
- First-pass payload would fall from about `83k` characters to about `21.6k` characters.
- Strict no-skeleton semantics remain unchanged.

Risks:

- A tighter evidence pack may reduce metadata richness for some documents.
- Evidence-pack content quality must be validated on textbook/workbook samples.

This is the recommended first implementation path.

### Option B: Adaptive timeout retry with smaller input

If first-pass generation times out on a legacy sample, retry once with evidence-pack input before failing.

Expected effect:

- Handles documents that slip through threshold rules.
- Still fails explicitly if the smaller retry also fails.

Risks:

- More implementation scope.
- Longer worst-case wait if not bounded carefully.
- Needs precise UI/job progress messaging to avoid hidden retries.

This is useful after or alongside Option A, but should not become silent fallback.

### Option C: Multi-pass/chunked metadata extraction

Split large parsed markdown into chunks, extract evidence per chunk, then merge into final metadata.

Expected effect:

- More robust for very large textbooks.
- Better preserves coverage across long documents.

Risks:

- Larger design task.
- More model calls and more failure states.
- Requires merge policy, partial evidence policy, and stronger tests.

This is likely the right medium-term architecture, not the smallest P0 fix.

### Option D: Runtime/model capacity tuning

Use a faster model, adjust Ollama context/runtime settings, or increase hardware capacity.

Expected effect:

- May improve pass rate.

Risks:

- Does not fix product-level input budgeting.
- Higher timeout alone can worsen queue blockage.
- Release readiness should not depend only on a bigger local machine.

This should be treated as capacity validation, not the first code remediation.

### Option E: Operator-facing wording improvement

Differentiate:

- MinerU parse complete.
- AI metadata timeout.
- No skeleton fallback generated.
- Operator review can continue only if the product allows parse-only review.

Expected effect:

- Reduces confusion when parsing succeeds but AI fails.

Risks:

- Product decision needed: whether parse-only review is acceptable before AI remediation lands.

## 7. Recommended First Implementation Task

Suggested Lucia task:

`P0 Adaptive Evidence-Pack First-Pass For Large AI Metadata Inputs`

Recommended scope:

- Add a centralized `shouldUseEvidencePack()` or equivalent local helper for AI metadata input selection.
- Trigger evidence-pack mode when any of the following are true:
  - markdown length exceeds a Lucia-approved threshold, initially recommended at `50000`;
  - parsed file count exceeds a Lucia-approved threshold, initially recommended at `50`;
  - source file size exceeds a Lucia-approved threshold, initially recommended at `10MB`.
- Preserve strict no-skeleton behavior.
- Preserve local MinerU mainline behavior.
- Add structured event details for AI input selection:
  - sampling mode;
  - original length;
  - selected length;
  - threshold reason;
  - input hash.
- Do not create fake AI metadata on failure.

Acceptance criteria:

- A synthetic or fixture input matching the #29 shape (`104823` chars, `99` parsed files, about `15MB` source file) selects evidence-pack mode.
- Selected AI input is below `30000` evidence-pack chars before prompt wrapping.
- First-pass prompt payload is substantially smaller than legacy sampler payload.
- Strict provider timeout still fails explicitly and does not create skeleton metadata.
- Existing AI smoke tests continue to pass.
- No production data mutation is required for the implementation task.

## 8. Required Tests For Follow-Up Implementation

Recommended focused tests:

- Extend `server/tests/ai-metadata-evidence-pack-smoke.mjs` with a medium-large input case below the old `150000` threshold.
- Add or extend an AI input-selection smoke that asserts:
  - large markdown chooses evidence pack;
  - large file size chooses evidence pack;
  - high parsed file count chooses evidence pack;
  - ordinary short markdown still uses the cheap legacy sample path.
- Preserve strict no-skeleton tests around provider timeout.
- Add an assertion that large-input events include sampling mode and threshold reason.

Recommended check commands after implementation:

- `node server/tests/ai-metadata-evidence-pack-smoke.mjs`
- `node server/tests/ai-metadata-real-sample-smoke.mjs`
- `node server/tests/dependency-health-smoke.mjs`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`

Runtime validation should be a separate Lucia-approved task if it reuses production/runtime artifacts.

## 9. Commands Run

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Dev workspace clean before report work. |
| `git fetch origin` | 0 | Synced with GitHub. |
| `git pull --ff-only origin main` | 0 | Already up to date. |
| `git log -1 --oneline` | 0 | Base HEAD `5b9a45c docs: accept large pdf soak failure`. |
| `rg` / `sed` reads of task brief, report, review, AI worker, sampler, evidence pack, provider, tests | 0 | Read-only diagnosis. |
| Read-only local calculation using Node imports against preserved #29 parsed markdown | 0 | Produced payload-size evidence above. |
| Read-only backend query of #29 AI job row | 0 | Confirmed strict timeout failure details above. |

## 10. Skipped Checks

- No TypeScript/build/test suite was run for this report because this task was diagnosis/planning only and no source code was changed.
- No runtime rerun was performed because the task explicitly forbids production mutation and artifact cleanup; rerunning AI on production validation artifacts should be a separate Lucia-approved validation task.

## 11. Risks And Residual Decisions

- Lucia should decide the exact first-pass evidence-pack thresholds.
- Product leadership should decide whether parse-complete but AI-failed materials may enter any operator review state before AI remediation is accepted.
- A later task should improve failed AI job structured metadata so `providerId` and `model` are visible outside the error string.
- Capacity validation for Ollama `qwen3.5:9b` should remain separate from input-budget remediation.

## 12. Review Requirement

Lucia review is required before any implementation task is issued.

