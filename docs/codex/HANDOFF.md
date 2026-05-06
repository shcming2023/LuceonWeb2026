# Codex Handoff

Last updated: 2026-05-07

## Current Entry Point

Read these files first:

1. `docs/codex/PROJECT_STATE.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/lucia.md` or `docs/codex/roles/lucode.md`
4. `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`
5. `docs/codex/REPOSITORY_STRUCTURE.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/prd/Luceon2026-PRD-v0.4.md`
8. `TaskAndReport/TASK_TRACKING_LIST.md`

Current active development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- Durable sync source: GitHub `origin/main`
- Package manager: `npx pnpm@10.4.1`

## Current Phase 1 Baseline

The accepted Phase 1 mainline is local real runtime validation:

- Frontend route: `/cms/tasks`
- Parser: local conda MinerU FastAPI
- Storage: Docker MinIO
- AI: host Ollama `qwen3.5:9b`
- Strict AI mode: `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`
- Current Standard path: local MinerU + MinIO + host Ollama
- Online MinerU v4: compatibility-only unless explicitly assigned

Production release readiness is not claimed by this handoff.

## 2026-05-06 Governance Closure

Repository governance archived historical plans and reviews, removed confirmed obsolete code and dependency drift, aligned UAT with current routes and runtime, and updated the project ledger.

Validation commands recorded as PASS:

```bash
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
node server/tests/worker-smoke.mjs
node server/tests/dependency-supervisor-smoke.mjs
BASE_URL=http://localhost:8081 bash uat/smoke-test.sh
DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts
```

## Role Boundary

- `Lucia`: product研发总监, Director's senior advisor, PRD and project-documentation owner, task brief author, report reviewer, and project-ledger maintainer.
- `Lucode`: development and testing manager, scoped implementation executor, test executor, completion reporter, and GitHub synchronization owner for assigned repository changes.

## Known Open Boundaries

- MinerU health checks still need a submit-path probe before production release readiness.
- `server/upload-server.mjs` remains a monolithic server and should not be modularized inside Phase 1 closure.
- Legacy redirects remain for `/cms/source-materials` and `/cms/workspace`.
- Large-PDF soak, concurrent upload, permissions/security, rollback rehearsal, folder upload, and all error-path validation remain outside this governance pass.

## First Commands In A Fresh Checkout

```bash
git status --short --branch
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
npx pnpm@10.4.1 run tier2:standard:check
```

Use `docs/codex/PROJECT_STATE.md` as the current ledger. Do not promote historical archive files back into active truth without new validation evidence.

## 2026-05-07 Team Contract Update

The active collaboration team has been reset to the Director, Lucia, and Lucode model.

- `Lucia`: product研发总监 and Director's senior advisor. Lucia owns goal discussion, implementation route analysis, PRD maintenance, project ledger maintenance, task brief writing, report review, and accepted-fact recording.
- `Lucode`: development and testing manager. Lucode executes only Lucia task briefs, performs scoped implementation and testing, reports evidence, and synchronizes repository changes when required.

Historical role files are not active. Current role truth is stored in:

- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucia.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/TASK_BRIEF_TEMPLATE.md`

## 2026-05-07 TaskAndReport Handoff Update

Lucia task briefs and Lucode reports are now exchanged through `TaskAndReport/`, not through Director chat relay.

- Task ledger: `TaskAndReport/TASK_TRACKING_LIST.md`
- Task brief naming: `YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_TASK.md`
- Report naming: `YYYY-MM-DDTHH-MM-SS+0800_<Task-Name>_REPORT.md`
- Controlled statuses: `下达`, `完成关闭`, `失败关闭`, `取消`, `挂起`, `退回修正`

Current issued task:

- `TASK-20260507-063238-P0-MinerU-Submit-Path-Health-Probe`

Director shorthand is active:

- `Lucia, check task`: inspect `TaskAndReport/` for unreviewed reports or Lucia action.
- `Lucode, check task`: inspect `TaskAndReport/` for actionable `下达` or `退回修正` tasks.
- If no actionable task/report exists, report no new item and wait.
