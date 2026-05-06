# Codex Handoff

Last updated: 2026-05-06

## Current Entry Point

Read these files first:

1. `docs/codex/PROJECT_STATE.md`
2. `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`
3. `docs/codex/REPOSITORY_STRUCTURE.md`
4. `docs/codex/TEST_POLICY.md`
5. `docs/prd/Luceon2026-PRD-v0.4.md`

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

- `lucia`: architecture control, task writing, review, validation criteria, and final judgment.
- `lucode`: implementation and code revision from lucia-approved task briefs.
- `luplan`: PRD, changelog, decision, and project-state maintenance.
- `luceonhmm`: UAT deployment, L2/L3 validation, production-like runtime analysis, rollback support, and evidence capture.
- `cota`: Director-side collaboration advisor.
- `lutest`: retired historical role.

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
