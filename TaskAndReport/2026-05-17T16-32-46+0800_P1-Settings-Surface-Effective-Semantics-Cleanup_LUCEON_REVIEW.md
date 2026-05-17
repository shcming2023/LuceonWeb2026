# TASK-20260517-161936-P1-Settings-Surface-Effective-Semantics-Cleanup Luceon Review

- Review time: `2026-05-17T16:32:46+0800`
- Reviewer: `Luceon`
- Reviewed task: `TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_TASK.md`
- Reviewed report: `TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_REPORT.md`
- Reviewed branch/head: `lucode/task-214-settings-effective-semantics` / `d3ae3ea`

## Decision

`CHANGES_REQUIRED`

Do not deploy this implementation to production yet.

The implementation is in the right direction and stays mostly within UI/governance scope, but it still leaves two misleading Settings surfaces reachable or order-dependent.

## Findings

### 1. AI local-provider surface is order-dependent

- File: `src/app/pages/SettingsPage.tsx`
- Evidence: lines `899-903` render `(aiForm.providers ?? []).slice(0, 1)` and update by displayed index.

This hides all providers except the first persisted provider, but it does not guarantee the first provider is Ollama/local. If a legacy or manually changed settings record puts Moonshot/Kimi/OpenAI first, Settings will show that external provider under `本地大模型配置 (Local Provider)` and still expose editable API address/API key/model fields.

This does not satisfy the task requirement: do not present Moonshot/Kimi/OpenAI as normal active choices.

Required correction:

- Select the local Ollama provider explicitly by stable criteria such as `id === "ollama"` or endpoint containing the local Ollama service.
- Render only that provider in this local-provider card.
- When updating the provider, update by original provider identity/index, not by the filtered display index.
- If no Ollama/local provider exists, show a clear no-local-provider message instead of silently showing the first external provider.

### 2. Dictionary/rules surface is still reachable as an active mutating Settings panel

- File: `src/app/pages/SettingsPage.tsx`
- Evidence:
  - line `249` still accepts `dictionary` from the URL tab parameter;
  - lines `1652-1654` still render `MetadataSettingsPanel` when `activeTab === "dictionary"`.
- File: `src/app/components/MetadataSettingsPanel.tsx`
- Evidence:
  - lines `82-88` expose `AI 规则`;
  - lines `178-204` expose mutating rule settings such as upload auto-run and confidence threshold.

The normal navigation tab is hidden, but `/cms/settings?tab=dictionary` can still show the active dictionary/rules control plane. That conflicts with the task goal that Settings should not present a misleading active taxonomy/rule control plane. It also makes the report statement that the panel is retained but not displayed inaccurate.

Required correction, choose one:

- Preferred: remove `dictionary` from Settings-page URL-valid tabs and do not render `MetadataSettingsPanel` from `SettingsPage` for now; keep the component/data/routes in code for future redesign.
- Or convert the direct Settings view to a clearly read-only diagnostic surface with mutating controls removed from that path.

### 3. Minor cleanup after the chosen fix

If the dictionary surface is fully hidden from Settings, remove now-unused imports/types such as `Tag`, `MetadataSettingsPanel`, and `dictionary` from `ActiveTab` and validation lists where no longer needed.

## Checks Re-run By Luceon

- `git diff --check 828d5b1..d3ae3ea`: passed, exit `0`.
- `npx pnpm@10.4.1 exec tsc --noEmit`: passed, exit `0`.
- `npx pnpm@10.4.1 run build`: failed in Luceon host review environment because Rollup optional package `@rollup/rollup-darwin-arm64` is missing from local `node_modules`; this is treated as local dependency-environment evidence, not as a code-level failure. Lucode should still include a successful build from the dev container or a repaired dependency environment in the correction report.

## Required Next Step

Lucode should correct the two findings above, rerun the task's required checks and search commands, rewrite/update the report, and return Task 214 to `Luceon` for review.

No production deploy, production rebuild/restart, upload, submit-probe, pressure test, backup import/export, cleanup, repair, reparse, re-AI, readiness/L3/pressure PASS, or go-live claim was performed or authorized by this review.
