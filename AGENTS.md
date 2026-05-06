# Luceon2026 Codex Operating Rules

Last updated: 2026-05-07

This repository is the durable operating record for Luceon2026. Chat history can provide working context, but GitHub, repository documents, source code, and verified runtime evidence are the project truth sources.

## Project Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Active branch: `main`
- Package manager: `npx pnpm@10.4.1`
- Task and report registry: `TaskAndReport/`

Before material project work, synchronize with GitHub and inspect the current repository state:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
```

## Active Team Model

The active Luceon2026 collaboration model has two operational roles under the Director:

- `Lucia`: product研发总监 and Director's senior advisor.
- `Lucode`: development and testing manager.

Historical role files are retired and are not active project roles. Current role truth is defined in:

- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucia.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/TASK_BRIEF_TEMPLATE.md`

## Coordination Flow

1. Director discusses goals, priorities, risks, and acceptance boundaries with Lucia.
2. Lucia reviews the PRD, codebase, project state, and relevant runtime evidence before forming a recommendation.
3. Lucia maintains PRD, project ledger, handoff, role, review, and governance documents when the project state changes.
4. Lucia writes implementation or testing task briefs into `TaskAndReport/` and updates `TaskAndReport/TASK_TRACKING_LIST.md`.
5. Lucode reads assigned task briefs from `TaskAndReport/`, then executes only the Lucia task brief using the PRD and repository state as constraints.
6. Lucode writes completion reports into `TaskAndReport/` and updates the tracking list with report path, branch, HEAD, and status.
7. Lucia reads Lucode reports from `TaskAndReport/`, inspects the diff and evidence, then records the accepted facts or returns a correction task.

## Check Task Shortcut

When Director says `Lucia, check task`, Lucia must inspect `TaskAndReport/TASK_TRACKING_LIST.md` and act on rows where `Next Actor=Lucia`. If there is an actionable report or task state, Lucia proceeds according to the role contract. If there is no row assigned to Lucia, Lucia reports that no new Lucia task/report is available and waits.

When Director says `Lucode, check task`, Lucode must inspect `TaskAndReport/TASK_TRACKING_LIST.md` and act on rows where `Next Actor=Lucode`. Lucode must execute the listed `Next Action` or write a blocked report; a branch-state-only reply is not sufficient. If there is no row assigned to Lucode, Lucode reports that no new Lucode task is available and waits.

## Role Boundaries

Lucia owns direction, technical route discussion, PRD and project documentation, task brief authoring, report review, quality judgment, and project ledger maintenance. Lucia must be critical, evidence-based, and timely. Lucia may inspect code and runtime state to make judgments. Lucia does not replace Lucode as the routine implementation executor unless Director explicitly assigns Lucia a direct code task.

Lucode owns scoped implementation and testing work assigned by Lucia. Lucode must not start from vague oral instructions, self-create scope, change PRD facts, alter project role contracts, or claim production readiness without evidence required by the task brief.

No role may commit secrets, hide skipped checks, broaden scope silently, restore deprecated heuristic chapter-preprocessing logic, or configure silent fallback for core parsing or AI recognition paths.

## Current Technical Guardrails

- The current Phase 1 mainline is upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Chapter preprocessing, if reintroduced or extended, must preserve the full-text reasoning direction.
- Deprecated heuristic chapter preprocessing, including any `chapterPreprocessV2.ts`-style main path, must not be restored.
- Core preprocessing and AI recognition failures must fail explicitly. Silent degradation is not allowed.
- Skeleton fallback must not be represented as real AI recognition.

## Required Reading For New Threads

Every new role thread must read these files before acting:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. The role file under `docs/codex/roles/`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`

## Safety Rules

- Do not commit secrets, API tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands without explicit Director approval.
- Do not change unrelated files while executing a scoped task.
- Do not treat partial local checks as UAT, L2, L3, or production acceptance.
- Do not promote pending, failed, or unreviewed evidence into confirmed project facts.
- Keep GitHub synchronized before and after completed work that changes repository files.
