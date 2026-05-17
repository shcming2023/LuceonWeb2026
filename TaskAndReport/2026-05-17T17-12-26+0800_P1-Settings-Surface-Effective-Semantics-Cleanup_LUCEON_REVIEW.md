# TASK-20260517-161936-P1-Settings-Surface-Effective-Semantics-Cleanup Luceon Review

- Review time: `2026-05-17T17:12:26+0800`
- Reviewer: `Luceon`
- Reviewed task: `TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_TASK.md`
- Reviewed report: `TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_REPORT.md`
- Reviewed branch/head: `lucode/task-214-settings-effective-semantics` / `b33db90`

## Decision

`ACCEPTED_CODE_LEVEL_PRODUCTION_DEPLOYMENT_DECISION_REQUIRED`

Task 214 is accepted at code/review level. Production deployment and runtime validation are not performed in this review and require a separate user decision.

## Accepted Scope

The implementation now satisfies the requested Settings-surface semantics cleanup:

- AI Settings no longer renders the first provider by array order. It explicitly finds the local provider via `id === "ollama"` or an endpoint containing `11434`, and updates the original provider index.
- If no local Ollama provider exists, Settings renders a no-local-provider message instead of exposing an external provider under local-provider wording.
- The normal Settings dictionary/rules surface is removed from the Settings route path: `dictionary` is removed from `ActiveTab`, URL-valid tabs, `MetadataSettingsPanel` import, and conditional render path.
- `备份与监控` is replaced by `备份与容量`.
- `tmpfiles` is not exposed as a Settings storage choice.
- MinerU cloud/API settings are not exposed in the active Settings page.

## Luceon Checks

Host development workspace:

```bash
git show --check --stat --oneline HEAD -- src/app/pages/SettingsPage.tsx
```

Result: passed, exit `0`.

```bash
git diff --check 828d5b1..HEAD
```

Result: passed, exit `0`.

```bash
npx pnpm@10.4.1 exec tsc --noEmit
```

Result: passed, exit `0`.

```bash
rg -n "MetadataSettingsPanel|activeTab === 'dictionary'|dictionary|providers\\.slice\\(0, 1\\)|备份与监控|tmpfiles|storageBackend.*tmpfiles" src/app/pages/SettingsPage.tsx
```

Result: no matches.

```bash
rg -n "Moonshot|Kimi|OpenAI|多提供商|按优先级|fallback|兜底" src/app/pages/SettingsPage.tsx src/app/components/MetadataSettingsPanel.tsx
```

Result: no matches.

```bash
rg -n "cloud|云端|apiKey|apiEndpoint|apiMode|modelVersion|MinerU API Key|https://mineru.net" src/app/pages/SettingsPage.tsx
```

Result: only local AI provider `apiEndpoint` / `apiKey` field references remain; no MinerU cloud/API settings are exposed.

Host build note:

```bash
npx pnpm@10.4.1 run build
```

Result: failed in the host dev workspace because local `node_modules` is missing Rollup optional package `@rollup/rollup-darwin-arm64`. This is the same host dependency-environment issue observed in earlier review and is not treated as a code-level failure.

Dev container validation:

```bash
docker exec antigravity-dev-linux sh -lc 'cd /workspace/dev/Luceon2026 && git show --check --stat --oneline HEAD -- src/app/pages/SettingsPage.tsx && npx pnpm@10.4.1 exec tsc --noEmit'
```

Result: passed, exit `0`.

```bash
docker exec antigravity-dev-linux sh -lc 'cd /workspace/dev/Luceon2026 && npx pnpm@10.4.1 run build'
```

Result: passed, exit `0`; Vite built successfully.

## Residuals

- `src/app/components/MetadataSettingsPanel.tsx` remains in the codebase for future redesign, but it is no longer reachable from `SettingsPage`.
- The production runtime has not yet been updated with Task 214.
- No production smoke or browser validation has been run for Task 214.

## Next Decision

Create a user decision item for whether to perform scoped production deployment and read-only validation of accepted Task 214.

Recommended path: approve scoped production deployment of Task 214 only, then run read-only validation for `/cms/settings`, no upload, no submit-probe, no pressure, no data cleanup, and no readiness/go-live claim.

## Boundary

No production deploy, production rebuild/restart, upload, submit-probe, pressure test, backup import/export, cleanup, repair, reparse, re-AI, readiness/L3/pressure PASS, or go-live claim was performed in this review.
