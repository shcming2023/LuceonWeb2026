# TASK-20260517-161936-P1-Settings-Surface-Effective-Semantics-Cleanup Production Validation

- Validation time: `2026-05-17T17:24:22+0800`
- Validator: `Luceon`
- User authorization: Task 215 Option A approved by User
- Accepted source branch/head: `lucode/task-214-settings-effective-semantics` / `b33db90`
- Production integration scope: `src/app/pages/SettingsPage.tsx`

## Deployment Performed

Integrated the accepted Task 214 frontend Settings cleanup into the production workspace and rebuilt/restarted only the frontend service.

Command:

```bash
git fetch /Users/concm/Dev_workspace/Luceon2026 lucode/task-214-settings-effective-semantics:refs/remotes/local-lucode/task-214-settings-effective-semantics
git checkout refs/remotes/local-lucode/task-214-settings-effective-semantics -- src/app/pages/SettingsPage.tsx
docker compose up -d --build --no-deps cms-frontend
```

Result:

- `cms-frontend` image rebuilt successfully.
- `cms-frontend` container recreated and started.
- `--no-deps` was used; `cms-upload-server`, `cms-db-server`, and `cms-minio` were not intentionally restarted.
- Compose reported existing orphan container `cms-minio-init`; no orphan cleanup was performed.

## Pre-Deploy / Integration Checks

```bash
git diff --check
git diff --cached --check
git show --check --stat --oneline refs/remotes/local-lucode/task-214-settings-effective-semantics -- src/app/pages/SettingsPage.tsx
```

Result: passed.

```bash
npx pnpm@10.4.1 exec tsc --noEmit
```

Result: passed, exit `0`.

```bash
npx pnpm@10.4.1 run build
```

Result: passed, exit `0`; Vite built successfully.

```bash
rg -n "MetadataSettingsPanel|activeTab === 'dictionary'|dictionary|providers\\.slice\\(0, 1\\)|备份与监控|tmpfiles|storageBackend.*tmpfiles" src/app/pages/SettingsPage.tsx
```

Result: no matches.

## Container State After Deploy

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | rg '^cms-(frontend|upload-server|db-server|minio)'
```

Observed:

- `cms-frontend`: healthy after rebuild/recreate
- `cms-upload-server`: healthy, existing uptime preserved
- `cms-db-server`: healthy, existing uptime preserved
- `cms-minio`: healthy, existing uptime preserved

## Read-Only HTTP Validation

Used Node `fetch` because this host shell did not have `curl` available.

```bash
/cms/ 200
/cms/settings 200
/cms/settings?tab=dictionary 200
/cms/audit 200
/__proxy/db/health 200
/__proxy/upload/health 200
/__proxy/upload/ops/dependency-health 200
```

`/cms/settings?tab=dictionary` returns the SPA shell as expected; source validation confirms `dictionary` is no longer accepted by `SettingsPage` as an active tab.

## Deployed Asset String Validation

```bash
docker exec cms-frontend sh -lc '<asset grep checks>'
```

Expected strings present:

- `备份与容量`
- `本地大模型配置`
- `未找到本地 Ollama`

Deprecated Settings strings absent:

- `备份与监控`
- `字典与标签`
- `MetadataSettingsPanel`
- `按优先级顺序依次尝试`
- `Ollama 作为本地兜底`

Note: broad bundle searches can still find generic terms such as `AI 规则` or `兜底` from other non-Settings pages or strict failure/status wording. This validation only treats the Task 214 Settings-surface strings and route/source evidence as acceptance criteria.

## Not Performed

No upload, submit-probe, pressure test, backup import/export, cleanup, repair, reparse, re-AI, DB/MinIO/Docker volume cleanup, model/secret/sample/data mutation, GitHub sync, readiness/L3/pressure PASS, production上线, or go-live claim was performed.

## Result

`DEPLOYED_AND_READ_ONLY_VALIDATED`
