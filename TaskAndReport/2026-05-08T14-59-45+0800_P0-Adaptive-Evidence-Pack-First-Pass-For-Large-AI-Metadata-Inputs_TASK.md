# P0 Adaptive Evidence-Pack First-Pass For Large AI Metadata Inputs

Task:
P0 Adaptive Evidence-Pack First-Pass For Large AI Metadata Inputs

Task ID:
`TASK-20260508-145945-P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T14:59:45+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T14-59-45+0800_P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/2026-05-08T14-44-54+0800_P0-Large-PDF-Soak-Validation_REPORT.md`
- `TaskAndReport/2026-05-08T14-48-15+0800_P0-Large-PDF-Soak-Validation_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T14-54-38+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_REPORT.md`
- `TaskAndReport/2026-05-08T14-59-45+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

The large-PDF soak validation failed in the AI metadata stage after MinerU and MinIO succeeded. Lucode diagnosis showed that the current AI worker selected a legacy sample of about `78084` characters for a `104823` character parsed Markdown document with `parsedFilesCount=99`. The evidence-pack path did not trigger under the existing threshold, and Ollama `qwen3.5:9b` timed out after about `300000ms`.

Strict no-skeleton behavior was correct and must remain unchanged.

## Objective

Implement adaptive first-pass AI metadata input selection so medium-large and large parsed documents use evidence-pack mode before they reach timeout-prone legacy sample sizes.

The implementation must reduce large first-pass input size while preserving the current strict failure semantics.

## Required Implementation Scope

1. Add a centralized input-selection helper, for example `shouldUseEvidencePack()` or an equivalent local helper consistent with existing code style.
2. Select evidence-pack mode when any of the following triggers are true:
   - Markdown length is greater than `50000`.
   - `sourceMeta.fileSize` is greater than `10000000` bytes.
   - `sourceMeta.parsedFilesCount` is greater than `50`.
3. Preserve ordinary short-document behavior on the current legacy sampler path.
4. Preserve existing evidence-pack behavior for very large documents.
5. Preserve strict no-skeleton behavior and explicit provider failure behavior.
6. Add or preserve structured AI input-selection observability, including:
   - sampling mode;
   - original Markdown length;
   - selected input length;
   - trigger reason or reasons;
   - input hash.

Use existing result metadata or task-event patterns where possible. Do not introduce a broad event system if a focused metadata field is sufficient and consistent with the local implementation.

## Non-goals

- Do not modify production runtime.
- Do not deploy, restart, rebuild, rollback, or mutate production services.
- Do not delete DB rows, MinIO objects, Docker volumes, tasks, artifacts, logs, or secrets.
- Do not change Ollama model selection or timeout policy in this task.
- Do not implement chunked or multi-pass extraction in this task.
- Do not add skeleton fallback or silent degradation.
- Do not represent parse-only output as successful AI metadata recognition.
- Do not claim production release readiness.

## Required Tests

Add or extend tests so the following behaviors are explicitly covered:

- A medium-large Markdown input below the old `150000` threshold but above the new `50000` threshold selects evidence-pack mode.
- A source file size greater than `10000000` bytes selects evidence-pack mode.
- A parsed file count greater than `50` selects evidence-pack mode.
- The large-PDF-like shape from task 29 (`104823` chars, `99` parsed files, about `15MB` source file) selects evidence-pack mode and selected content remains below `30000` characters before prompt wrapping.
- Ordinary short Markdown still uses the legacy sampler path.
- Strict provider timeout/failure behavior remains explicit and does not create skeleton metadata.
- AI input-selection metadata includes sampling mode, original length, selected length, trigger reason, and input hash.

Prefer extending `server/tests/ai-metadata-evidence-pack-smoke.mjs` unless the existing test structure clearly requires a separate focused smoke test.

## Required Checks

Run and report exact exit codes:

- `git status --short --branch`
- `git fetch origin`
- If local `main` is behind `origin/main` and clean, `git pull --ff-only origin main`
- `node server/tests/ai-metadata-evidence-pack-smoke.mjs`
- `node server/tests/ai-metadata-real-sample-smoke.mjs`
- `node server/tests/dependency-health-smoke.mjs`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `git diff --check`

Runtime validation against production artifacts is out of scope for this task and must be assigned separately after Lucia review.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs_REPORT.md`

The report must include:

- Files changed.
- Exact implemented thresholds.
- Behavior summary for each trigger.
- Test additions and what each protects.
- Exact command results and exit codes.
- Confirmation that strict no-skeleton behavior remains preserved.
- Confirmation that no production runtime mutation, data cleanup, secret change, or release-readiness claim occurred.
- Residual validation needed before production release-readiness can be reconsidered.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push implementation/report changes to GitHub.

## Acceptance Criteria

- Large first-pass AI metadata inputs select evidence-pack mode under the approved adaptive thresholds.
- Short documents retain existing legacy sampling behavior.
- Existing strict AI failure semantics remain unchanged.
- Focused smoke tests cover the threshold behavior and pass.
- TypeScript and production build pass.
- No production readiness claim is made.
