# Luceon2026 Handoff

Last updated: 2026-05-24

## Current Entry Point

Start here:

1. `README.md`
2. `docs/codex/roles/luceon.md`
3. `docs/codex/LUCODE_LOCAL_WORKFLOW.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/prd/README.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `docs/deploy/README.md`
10. `TaskAndReport/README.md`
11. `TaskAndReport/TASK_TRACKING_LIST.md`

Local private role prompts such as `AGENTS.md` and `.agents/**` may exist in each worktree, but they are ignored by Git and are not shared project fact sources.

Luceon thread workspace:

`/Users/concm/prod_workspace/Luceon2026`

Lucode thread workspace:

`/Users/concm/Dev_workspace/Luceon2026`

GitHub:

`https://github.com/shcming2023/Luceon2026`

Lucode copyable rules:

`docs/codex/LUCODE_LOCAL_WORKFLOW.md`

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

The previous multi-role team has been dissolved and archived. The active model is now a two-thread local collaboration model:

- `Luceon`: this Codex-side role, combining Director, Architect, and TestAcceptanceEngineer duties.
- `Lucode`: local development-thread role in `/Users/concm/Dev_workspace/Luceon2026`, combining DevelopmentEngineer and ProductManager duties.

The two roles coordinate through GitHub and `TaskAndReport/`. `check task` must fetch GitHub first; stale local-only task rows are not authoritative.

Initial Lucode triggering is manual: after Luceon issues or returns a task, the user sends `Lucode, check task` in the Lucode thread. A Lucode heartbeat automation may be added later only after the manual flow is stable.

Luceon may explicitly use Codex subagents for bounded exploration, tests, log analysis, evidence extraction, or review assistance when the user authorizes subagent or parallel-agent work for the current task. Subagents are Luceon-internal helpers, not `TaskAndReport` roles.

Archived role/workflow material is retained under:

- `archive/team-model-retired-2026-05-16/`
- `archive/legacy-roles-2026-05-15/`
- `archive/phase1-governance-2026-05-11/agents-workflows/`

`TaskAndReport/` is active for the new Luceon/Lucode workflow and remains historical evidence. Do not delete it.

## First Commands In A Fresh Checkout

```bash
git status --short --branch
git fetch origin --prune --tags
git pull --ff-only origin main
```

For `check task`, read `TaskAndReport/TASK_TRACKING_LIST.md` first. If there is no open `Next Actor=Luceon` row, stop after a short no-task reply.

Before that no-task reply, Luceon must check the earliest open `Next Actor=Lucode` row for a matching remote `lucode/<task-id-or-short-slug>` branch. If the branch-local ledger row says `Lucode 已回报待 Luceon 审查` or `Next Actor=Luceon`, Luceon should review that branch even though `origin/main` still shows Lucode.

For `Lucode, check task`, run the same GitHub sync from `/Users/concm/Dev_workspace/Luceon2026`, then read `TaskAndReport/TASK_TRACKING_LIST.md` and execute only the earliest open `Next Actor=Lucode` row.

Install and validation commands are task-dependent, not part of every wakeup:

```bash
npx pnpm@10.4.1 install --frozen-lockfile
npx pnpm@10.4.1 run test:static
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

Only use historical lookup when the current task needs it.
