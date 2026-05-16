# Luceon2026 Handoff

Last updated: 2026-05-16

## Current Entry Point

Start here:

1. `README.md`
2. `AGENTS.md`
3. `docs/codex/PROJECT_STATE.md`
4. `docs/prd/README.md`
5. `docs/prd/Luceon2026-PRD-v0.4.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/codex/REPOSITORY_STRUCTURE.md`
8. `docs/deploy/README.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`

Development workspace:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:

`/Users/concm/prod_workspace/Luceon2026`

GitHub:

`https://github.com/shcming2023/Luceon2026`

Package manager:

`npx pnpm@10.4.1`

## 6.9.1 Status

The repository is being preserved as milestone `6.9.1`.

The current main process has run through in the latest evidence sequence:

- user-started 24-PDF run,
- 24/24 MinerU parses completed,
- 23/24 reached review-pending/review,
- 1/24 failed in AI after MinerU completion,
- MinerU queue and active diagnostics ended clean,
- the progress semantics boundary was accepted with residuals.

This is a rollback milestone, not a release/go-live declaration.

## Collaboration State

The previous multi-thread role team has been dissolved and archived. There is no active ProductManager, Architect, DevelopmentEngineer, TestAcceptanceEngineer, Lucia, or Lucode workflow.

Archived role/workflow material is retained under:

- `archive/team-model-retired-2026-05-16/`
- `archive/legacy-roles-2026-05-15/`
- `archive/phase1-governance-2026-05-11/agents-workflows/`

`TaskAndReport/` remains historical evidence. Do not delete it.

## First Commands In A Fresh Checkout

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 run test:static
```

Optional broader checks when needed:

```bash
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check
```

## Safety Boundary

Do not mutate production runtime, DB rows, MinIO objects, Docker volumes, model files, secrets, local overrides, or external sample files unless the user explicitly authorizes that operation.

The local sample library remains read-only:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

## Historical Lookup

For detailed historical evidence, use:

- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/*_REPORT.md`
- `TaskAndReport/*_DIRECTOR_REVIEW.md`
- `TaskAndReport/*_DECISION.md`
- `archive/`
