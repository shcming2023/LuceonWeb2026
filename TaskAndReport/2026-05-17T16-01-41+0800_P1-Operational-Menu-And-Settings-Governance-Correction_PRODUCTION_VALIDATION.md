# Production Validation: Task 213 Operational Menu And Settings Governance Correction

- Time: 2026-05-17T16:01:41+0800
- Validator: Luceon
- Scope: minimal production deployment and read-only validation for accepted Task 213 governance/UI cleanup.
- Result: DEPLOYED_AND_SMOKE_VALIDATED

## 1. Deployment Scope

Applied the accepted Lucode correction from local branch:

- Source workspace: `/Users/concm/Dev_workspace/Luceon2026`
- Source branch: `lucode/task-213-operational-menu-governance-correction`
- Accepted source HEAD: `828d5b1`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`

Only these accepted correction files were applied from the Lucode branch into production workspace:

- `AGENTS.md`
- `docs/codex/PROJECT_HISTORY.md`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- `src/app/pages/SettingsPage.tsx`

TaskAndReport whitespace-only edits from the Lucode branch were not imported as runtime changes. The local production control-plane report/review files remained owned by Luceon.

## 2. Pre-Deployment Checks

Production workspace checks before Docker deployment:

```bash
git diff --check
git diff --cached --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

All exited `0`.

Targeted grep checks:

```bash
rg -n "set this to true or false|allowBuilds" pnpm-workspace.yaml pnpm-lock.yaml
rg -n "cleanup-orphans|audit/orphans|orphanStats|handleScanOrphans|handleCleanupOrphans|switchTab\\('consistency'\\)|activeTab === 'consistency'|一致性检查" src/app/pages/SettingsPage.tsx
rg -n "一致性检查|cleanup-orphans|audit/orphans|LatexToolPage|backup/latex|LaTeX 工具" dist
```

All produced no blocking hits.

## 3. Deployment Command

Ran:

```bash
docker compose up -d --build cms-frontend
```

Observed behavior:

- `cms-frontend` rebuilt successfully.
- Compose also rebuilt/recreated `cms-db-server` and `cms-upload-server` because of the current compose dependency/build graph.
- No `docker compose down`, no volume cleanup, no prune, no DB/MinIO data cleanup, no upload, no submit-probe, and no pressure test were run.
- Final containers:
  - `cms-frontend`: healthy
  - `cms-db-server`: healthy
  - `cms-upload-server`: healthy
  - `cms-minio`: healthy

## 4. Post-Deployment Read-Only Validation

HTTP checks:

```text
200 http://127.0.0.1:8081/cms/
200 http://127.0.0.1:8081/cms/settings
200 http://127.0.0.1:8081/cms/audit
200 http://127.0.0.1:8081/__proxy/db/health
200 http://127.0.0.1:8081/__proxy/upload/health
200 http://127.0.0.1:8081/__proxy/upload/ops/dependency-health
```

Deployed JS asset check:

```bash
curl -fsS http://127.0.0.1:8081/cms/assets/index-B944MRSs.js -o /tmp/luceon-deployed-index.js
rg -n "一致性检查|cleanup-orphans|audit/orphans|LatexToolPage|backup/latex|LaTeX 工具" /tmp/luceon-deployed-index.js
```

Result: no hits.

Smoke test:

```bash
BASE_URL=http://127.0.0.1:8081 MINIO_CONSOLE_URL=http://127.0.0.1:19001 npx pnpm@10.4.1 run test:smoke
```

Result:

```text
通过 12 / 失败 0 / 跳过 0
```

## 5. Boundaries

This validation confirms only the minimal production deployment and read-only smoke validation for Task 213.

It does not declare:

- production readiness
- release readiness
- L3
- pressure PASS
- go-live readiness

No production data mutation, upload validation, submit-probe, pressure test, cleanup, repair, reparse, re-AI, model mutation, secret/config mutation, or sample-file mutation was performed.

## 6. Residual Note

The current compose graph rebuilt/recreated `cms-db-server` and `cms-upload-server` while targeting `cms-frontend`. This completed healthy and did not mutate volumes, but the dependency/build graph should be considered in future "frontend-only" deployment expectations.
