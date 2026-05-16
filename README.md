# Luceon2026

Luceon2026 is the local real-runtime education-material processing CMS. The current Phase 1 mainline is:

`upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`

Production release readiness is not claimed by this README. Current status, open boundaries, and the active Luceon/Lucode collaboration model are recorded in `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, `docs/codex/roles/luceon.md`, and `TaskAndReport/README.md`.

## Repository Truth Sources

- Entry rules: `AGENTS.md`
- Active Luceon role: `docs/codex/roles/luceon.md`
- Current project state: `docs/codex/PROJECT_STATE.md`
- Current handoff: `docs/codex/HANDOFF.md`
- Deployment docs index: `docs/deploy/README.md`
- PRD: `docs/prd/Luceon2026-PRD-v0.4.md`
- Validation policy: `docs/codex/TEST_POLICY.md`
- Test matrix: `docs/codex/TEST_MATRIX.md`
- Active task ledger: `TaskAndReport/TASK_TRACKING_LIST.md`
- Retired role/workflow archive: `archive/team-model-retired-2026-05-16/`
- Milestone 6.9.1 record: `docs/codex/MILESTONE_6.9.1.md`

## Requirements

- Node.js 18+
- Package manager: `npx pnpm@10.4.1`
- Docker / Docker Compose for MinIO and containerized runtime paths
- Local conda MinerU FastAPI for the current standard path
- Host Ollama with model `qwen3.5:9b`

## First Commands

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

## Local Configuration

Create local environment configuration from the template:

```bash
cp .env.example .env
```

Do not commit `.env`, real API keys, tokens, database snapshots, MinIO credentials, or local runtime artifacts. The current standard runtime values are documented in `.env.example` and `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`.

## UAT / Local Smoke Checks

The current local UAT target is usually `http://localhost:8081` or the host LAN address on port `8081`, depending on how the stack is started.

```bash
npx pnpm@10.4.1 run uat:start
npx pnpm@10.4.1 run uat:smoke
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test
```

For the current Tier 2 Standard gate:

```bash
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check
```

## Important Boundaries

- The external sample library may be used read-only: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`.
- Do not copy sample files into this repository.
- Do not mutate production data, MinIO objects, Docker volumes, secrets, model settings, or runtime overrides without explicit user authorization or a future documented governance process.
- Skeleton fallback must not be represented as real AI recognition.
- Online MinerU remains compatibility-only unless explicitly assigned.
