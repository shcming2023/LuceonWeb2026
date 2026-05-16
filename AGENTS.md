# Luceon2026 Operating Rules

Last updated: 2026-05-16

This repository is the durable operating record for Luceon2026. GitHub `main`, committed source code, PRD/docs, active `TaskAndReport/` records, and verified runtime evidence are the project truth sources.

## Project Anchors

- Luceon governance workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Luceon production validation/deployment workspace: `/Users/concm/prod_workspace/Luceon2026`
- External Lucode development workspace, user-managed outside this machine context: `/Users/caoming/Documents/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Active branch: `main`
- Package manager: `npx pnpm@10.4.1`
- Active task and report registry: `TaskAndReport/`
- Local test sample library: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

The local test sample library may be used as a read-only source of validation inputs. It is outside this repository, must not be synchronized to GitHub, and must not be deleted, moved, renamed, modified, or polluted during Luceon testing.

Before material project work, synchronize with GitHub and inspect the current repository state:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
```

If the worktree is dirty, do not overwrite unrelated changes. Work with the current state, keep the edit scope explicit, and report any blocking conflict.

## Post-6.9.1 Collaboration Model

As of 2026-05-16, the previous Director/ProductManager/Architect/DevelopmentEngineer/TestAcceptanceEngineer multi-thread collaboration model remains retired. The active next-stage model is a two-role, GitHub-mediated workflow:

- `Luceon`: this Codex-side role. Luceon combines the previous Director, Architect, and TestAcceptanceEngineer responsibilities: project direction, architecture judgment, task planning, GitHub task ledger ownership, code/report review, production validation/deployment coordination, acceptance boundaries, and milestone records.
- `Lucode`: an external IDE-side role run by the user outside this environment. Lucode combines the previous DevelopmentEngineer and ProductManager responsibilities: product/requirement refinement, implementation, developer checks, branch/report creation, and GitHub synchronization from the external workspace.

Historical role contracts, old task templates, and old workflow prompts are preserved under:

`archive/team-model-retired-2026-05-16/`

The current Luceon role file is:

`docs/codex/roles/luceon.md`

Do not revive archived role files or old task-routing rules by implication.

## GitHub Control Plane

Luceon and Lucode work in different workspaces and coordinate through GitHub. Local-only task state is not authoritative.

`check task` must be token-efficient. Do not reread the whole repository or the full role/history stack before knowing whether a matching task exists.

When running `check task`, Luceon must:

1. enter the Luceon governance workspace;
2. run `git status --short --branch`;
3. run `git fetch origin --prune --tags`;
4. fast-forward local `main` from `origin/main` when the local worktree is clean;
5. read only `TaskAndReport/TASK_TRACKING_LIST.md` first;
6. if no open row has `Next Actor=Luceon`, stop after a brief no-task reply and do not read extra docs, write files, run checks, or push;
7. if a matching task exists, read only the referenced task brief, report/review files, linked branch, and directly relevant docs needed for that task;
8. if reviewing Lucode work, fetch the reported branch/HEAD and inspect the diff, report, checks, and evidence before accepting, returning, or escalating;
9. commit and push any task ledger, review, planning, or documentation updates that Luceon makes.

If the local worktree is dirty with unrelated changes, do not overwrite them. Either stop and report the dirty state or use a clean temporary clone/worktree for read-only review.

If no matching task exists, the correct steady state is sleeping until the next user instruction, heartbeat, or GitHub-visible task update.

## Active Task Flow

1. User and Luceon discuss goals, risk, architecture, validation boundary, and next step.
2. Luceon writes a task brief and updates `TaskAndReport/TASK_TRACKING_LIST.md` on GitHub `main`.
3. Lucode fetches GitHub, executes only tasks with `Next Actor=Lucode`, works on a scoped branch by default, writes a `*_REPORT.md`, updates the ledger on that branch, and pushes the branch/report to GitHub.
4. Luceon fetches GitHub, reviews Lucode's branch/report, runs required review checks and production validation when authorized, then accepts, returns, merges, or escalates.
5. Luceon records the final decision in `TaskAndReport/`, updates `docs/codex/PROJECT_STATE.md` or `docs/codex/HANDOFF.md` when needed, and pushes GitHub.

Default `Next Actor` values after 6.9.1 are `Luceon`, `Lucode`, `User`, and `None`.

## Current Technical Guardrails

- Current Phase 1 mainline: upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Core preprocessing, parsing, and AI recognition failures must fail explicitly.
- Silent degradation is not allowed for required parsing or AI recognition paths.
- Skeleton fallback must not be represented as real AI recognition.
- Deprecated heuristic chapter preprocessing must not be restored as a main path.
- Online MinerU is compatibility-only unless a future explicit task reactivates it.

## Safety Rules

- Do not commit secrets, API tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands without explicit user approval.
- Do not mutate production services, production data, model files, runtime overrides, or sample files as part of documentation/governance cleanup.
- Do not treat partial local checks as UAT, L2, L3, production readiness, release readiness, production上线, or go-live.
- Do not promote pending, failed, stale, or unreviewed evidence into confirmed project facts.
- Do not copy local sample-library files into the repository for commit. Reports may reference sample paths, sizes, hashes, and observed validation results, but source sample files must remain external and unchanged.

## Context And Documentation Hygiene

- Keep active docs concise and current so future `check task` runs do not need to load old context.
- Update `docs/codex/PROJECT_STATE.md` and `docs/codex/HANDOFF.md` only when project truth, milestone state, runtime boundary, or active workflow changes.
- Keep detailed evidence in `TaskAndReport/`; keep active docs as summaries and pointers.
- Archive superseded workflow docs instead of leaving competing active instructions.
- Avoid broad documentation rewrites when a small update preserves clarity.

## Current Reading Entry

For future development or review, start from:

1. `README.md`
2. `docs/codex/roles/luceon.md`
3. `docs/codex/PROJECT_STATE.md`
4. `docs/codex/HANDOFF.md`
5. `docs/prd/README.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `docs/deploy/README.md`
10. `TaskAndReport/README.md`
11. `TaskAndReport/TASK_TRACKING_LIST.md`
