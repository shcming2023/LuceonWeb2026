# Luceon2026 Operating Rules

Last updated: 2026-05-16

This repository is the durable operating record for Luceon2026. GitHub `main`, committed source code, PRD/docs, TaskAndReport history, and verified runtime evidence are the project truth sources.

## Project Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Active branch: `main`
- Package manager: `npx pnpm@10.4.1`
- Historical task and report registry: `TaskAndReport/`
- Local test sample library: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

The local test sample library may be used as a read-only source of validation inputs. It is outside this repository, must not be synchronized to GitHub, and must not be deleted, moved, renamed, modified, or polluted during Luceon testing.

Before material project work, synchronize with GitHub and inspect the current repository state:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
```

If the worktree is dirty, do not overwrite unrelated changes. Work with the current state, keep the edit scope explicit, and report any blocking conflict.

## Milestone 6.9.1 Collaboration State

As of 2026-05-16, the previous Director/ProductManager/Architect/DevelopmentEngineer/TestAcceptanceEngineer multi-thread collaboration model has been dissolved by user decision.

There is no active role-dispatch workflow in this repository now. Historical role contracts, task brief templates, and prior handoff docs are preserved under:

`archive/team-model-retired-2026-05-16/`

`TaskAndReport/` remains a historical evidence registry. Do not delete historical task briefs, reports, reviews, decisions, or `TASK_TRACKING_LIST.md`.

Future role definitions or collaboration workflows must be introduced explicitly as new repository documents. Do not revive archived role files or task-routing rules by implication.

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

## Current Reading Entry

For future development or review, start from:

1. `README.md`
2. `docs/codex/PROJECT_STATE.md`
3. `docs/codex/HANDOFF.md`
4. `docs/prd/README.md`
5. `docs/prd/Luceon2026-PRD-v0.4.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/codex/REPOSITORY_STRUCTURE.md`
8. `docs/deploy/README.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
