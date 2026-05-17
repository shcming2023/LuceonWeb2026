# TASK-20260517-161936-P1-Settings-Surface-Effective-Semantics-Cleanup

## 1. Task Summary

- Task ID: `TASK-20260517-161936-P1-Settings-Surface-Effective-Semantics-Cleanup`
- Issued at: `2026-05-17T16:19:36+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Priority: `P1`
- Suggested branch: `lucode/task-214-settings-effective-semantics`
- Development workspace:
  - Host: `/Users/concm/Dev_workspace/Luceon2026`
  - Container: `/workspace/dev/Luceon2026`
- Shared local control plane:
  - Host: `/Users/concm/prod_workspace/Luceon2026/TaskAndReport`
  - Container: `/workspace/ops/Luceon2026/TaskAndReport`
- Expected report path:
  - `TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_REPORT.md`

## 2. Background

After Task 213, the retired LaTeX and normal Settings-page consistency/orphan cleanup surfaces were removed. The next issue is that the remaining Settings tabs still mix:

- currently effective production controls;
- compatibility fields that are still persisted but no longer govern the mainline;
- half-finished management surfaces that look authoritative but do not drive the current AI/MinerU pipeline.

Current mainline remains:

`upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`

Luceon read-only inspection found:

- `AI 识别配置` is partially useful, but the active strict runtime primarily uses local Ollama and required model semantics. The page still implies multi-provider fallback and external provider management.
- `MinerU 配置` has effective local fields, but still carries old cloud/API fields in types/seed data and should not surface cloud/API semantics as active controls.
- `存储配置` is mostly valid and should remain MinIO-focused. `tmpfiles` should not return as a user-selectable normal path.
- `备份与监控` is really backup/capacity/recovery. "监控" is misleading because runtime monitoring belongs in System Health/Ops pages.
- `字典与标签` currently does not drive AI metadata classification as a real control plane. Production DB currently has empty `flexibleTags` and `aiRules`; AI metadata uses the worker's taxonomy/normalization path, not this Settings panel as a live taxonomy source.

Also note: ignored local runtime file `server/db-data.json` may contain historical secret-like values. Do not copy or print those values. Do not include them in reports. Do not mutate local production data.

## 3. Goal

Make `SettingsPage` expose only settings whose effect is real and understandable in the current system.

This is a UI/wording/governance cleanup task, not a mainline behavior rewrite.

## 4. Required Scope

### 4.1 AI Recognition Settings

Refocus the tab as local Ollama recognition configuration.

Required:

- Remove or hide user-facing wording that claims active multi-provider priority/fallback behavior.
- Do not present Moonshot/Kimi/OpenAI as normal active choices.
- Keep useful local controls:
  - Ollama API address/model display or edit if already supported;
  - test connection;
  - auto-fetch installed Ollama models;
  - timeout where it is meaningful;
  - Markdown input limit;
  - thinking mode toggle;
  - prompt text editing only if it remains clearly described as prompt configuration and does not claim to override strict runtime semantics beyond what code actually supports.
- Replace misleading help text such as "按优先级顺序依次尝试各提供商" with current local-Ollama semantics.

Do not change AI worker behavior in this task.

### 4.2 MinerU Settings

Refocus the tab as local MinerU configuration.

Required:

- Keep effective local controls:
  - local endpoint;
  - local timeout;
  - local backend;
  - local max pages;
  - OCR language;
  - OCR / formula / table toggles;
  - connection test.
- Do not surface current-stopped cloud MinerU/API Key/API endpoint/API mode/model version controls as active UI.
- If retained in comments/types for compatibility, ensure they are not presented as current user-facing controls.
- Clarify that empty `localEndpoint` falls back to the runtime default `http://host.docker.internal:8083` where appropriate, so the user is not misled by an empty field.

Do not change local MinerU adapter behavior in this task.

### 4.3 Storage Settings

Keep MinIO as the only normal storage surface.

Required:

- Keep MinIO endpoint, port, SSL, access/secret key, original bucket, parsed bucket, presigned expiry, and connection test.
- Do not restore `tmpfiles` as a normal user-selectable storage backend.
- If the page has disabled/hidden backend controls, clean up wording so the operator understands MinIO is the current mainline.

Do not change MinIO runtime semantics or bucket/data contents in this task.

### 4.4 Backup And Capacity

Rename/refocus "备份与监控" to "备份与容量" or an equivalent name that does not imply runtime monitoring.

Required:

- Keep capacity stats, capacity thresholds, object-store breakdown, JSON metadata export, full asset export, and the existing Danger Zone import/recovery controls.
- Make high-risk import/replace wording clear.
- Do not add cleanup, repair, orphan deletion, or pressure-test controls here.
- Do not move runtime dependency health into this tab.

Do not execute any import/export operation as part of implementation.

### 4.5 Dictionary And Tags

The current `字典与标签` surface should not look like an active AI taxonomy/rule control plane.

Required choose one conservative implementation:

- Preferred: hide the `字典与标签` tab from normal Settings navigation for now, while leaving underlying components/routes/data intact for future redesign; or
- If Lucode believes it must remain visible, convert it to a clearly labeled read-only/diagnostic surface and remove mutating controls from this Settings page.

Do not delete backend flexible-tags or ai-rules endpoints.
Do not remove existing data models.
Do not implement a new taxonomy system in this task.

## 5. Explicit Non-Goals

Do not:

- change AI worker/provider selection behavior;
- change MinerU adapter/worker behavior;
- change MinIO runtime behavior;
- change DB schema or data format;
- delete backend routes;
- delete data models solely because UI no longer exposes them;
- mutate production runtime/data;
- edit `server/db-data.json`, `server/secrets.json`, local `.env`, MinIO objects, Docker volumes, or sample files;
- copy or print secret/token/API key values;
- run upload, submit-probe, pressure test, backup import, full export, destructive cleanup, repair, reparse, or re-AI;
- declare production readiness, release readiness, L3, pressure PASS, or go-live readiness.

## 6. Expected Files

Likely files:

- `src/app/pages/SettingsPage.tsx`
- `src/app/components/MetadataSettingsPanel.tsx` only if needed to hide/diagnostic-label the dictionary surface
- `src/store/seedData.ts` only for comments/default text if needed
- `src/store/types.ts` only if comments must be clarified without data model removal

Avoid backend edits unless a compile error or direct UI contract issue requires a minimal non-behavioral adjustment.

## 7. Required Checks

Run and report exact commands plus exit codes:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Run these search checks and summarize output:

```bash
rg -n "Moonshot|Kimi|OpenAI|多提供商|按优先级|fallback|兜底" src/app/pages/SettingsPage.tsx src/app/components/MetadataSettingsPanel.tsx
rg -n "cloud|云端|apiKey|apiEndpoint|apiMode|modelVersion|MinerU API Key|https://mineru.net" src/app/pages/SettingsPage.tsx
rg -n "tmpfiles|storageBackend.*tmpfiles" src/app/pages/SettingsPage.tsx
rg -n "字典与标签|AI 规则|上传后自动执行|并行执行规则|置信度阈值" src/app/pages/SettingsPage.tsx src/app/components/MetadataSettingsPanel.tsx
rg -n "备份与监控" src/app/pages/SettingsPage.tsx
```

Expected:

- The AI Settings page should not advertise active external multi-provider fallback.
- The MinerU Settings page should not expose cloud/API-key fields as active controls.
- The Storage Settings page should not expose tmpfiles as a normal choice.
- The Settings navigation should not expose a misleading active `字典与标签` control plane, unless deliberately converted to read-only/diagnostic wording.
- `备份与监控` should be replaced by `备份与容量` or equivalent.

## 8. Required Report

Write:

`TaskAndReport/2026-05-17T16-19-36+0800_P1-Settings-Surface-Effective-Semantics-Cleanup_REPORT.md`

Report must include:

- task brief path;
- branch and HEAD;
- files changed;
- implementation summary by each Settings tab;
- commands run with exit codes;
- search evidence summary;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- whether Luceon review is required.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Task 214 status: `Lucode 已回报待 Luceon 审查`
- Task 214 Next Actor: `Luceon`
- Include report path and branch/HEAD.

## 9. Handoff Boundary

After Lucode report, Luceon will review code, decide acceptance, and separately decide whether to perform production deployment/read-only validation.
