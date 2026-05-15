# Luceon2026 Codex Operating Rules

Last updated: 2026-05-15

This repository is the durable operating record for Luceon2026. Chat history can provide working context, but GitHub, repository documents, source code, task reports, and verified runtime evidence are the project truth sources.

## Project Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Active branch: `main`
- Package manager: `npx pnpm@10.4.1`
- Task and report registry: `TaskAndReport/`
- Local test sample library: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

The local test sample library may be used as a read-only source of validation inputs. It is outside this repository, may continue to receive new samples, must not be synchronized to GitHub, and must not be deleted, moved, renamed, modified, or polluted during Luceon testing.

Before material project work, synchronize with GitHub and inspect the current repository state:

```bash
git status --short --branch
git fetch origin
git pull --ff-only origin main
```

If the worktree is dirty, do not overwrite unrelated changes. Work with the current state, keep the edit scope explicit, and report any blocking conflict.

## Active Team Model

The active Luceon2026 collaboration model is a Director-dispatched, multi-thread role model:

- `Director`: project director, task dispatcher, report reviewer, task-ledger owner, and final workflow coordinator.
- `ProductManager`: 产品经理, responsible for requirements, PRD alignment, user value, scope boundaries, and acceptance criteria.
- `Architect`: 架构师, responsible for architecture route, module boundaries, technical risk, integration contracts, and implementation plan review.
- `DevelopmentEngineer`: 开发工程师, responsible for scoped implementation, developer checks, and code-level evidence.
- `TestAcceptanceEngineer`: 测试验收工程师, responsible for validation plans, UAT/runtime verification, acceptance evidence, and pass/fail boundary reporting.

Each role should operate in its own thread. The Director is the only routine dispatcher and reviewer. The ProductManager, Architect, DevelopmentEngineer, and TestAcceptanceEngineer do not self-create project scope; they execute only task briefs assigned by the Director through `TaskAndReport/`.

Historical `Lucia` and `Lucode` task records are retained for traceability only. Their retired role files live under `archive/legacy-roles-2026-05-15/`, not under the active `docs/codex/roles/` directory. They are not active project roles after 2026-05-13 unless the Director explicitly reactivates them in repository documents.

Current role truth is defined in:

- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/director.md`
- `docs/codex/roles/product-manager.md`
- `docs/codex/roles/architect.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/TASK_BRIEF_TEMPLATE.md`
- `TaskAndReport/README.md`

## Coordination Flow

1. User and Director discuss goals, priorities, risks, release boundaries, and decisions that require owner judgment.
2. Director converts the agreed next step into one or more standalone task briefs under `TaskAndReport/`.
3. Director updates `TaskAndReport/TASK_TRACKING_LIST.md` with status, next actor, next action, required output, task brief link, and expected report path.
4. The assigned role thread receives a `check task` command, reads the task ledger, reads its task brief, executes only the assigned scope, and writes a standalone `*_REPORT.md`.
5. The assigned role updates the task row to `已回报待 Director 审查` or a blocked status, with report path, branch/HEAD, next actor, next action, and required output.
6. Director receives `Director, check task`, reviews pending reports and evidence, writes a `*_DIRECTOR_REVIEW.md` when a formal judgment is made, and updates the task ledger.
7. Director either accepts and closes the task, returns a correction task to the same or another role, records technical debt, or issues the next task brief.
8. If Director cannot or should not decide alone, Director records a concrete decision row with `Next Actor=User`, then discusses the decision with the user. After the user decides, Director records the decision and continues dispatch.

## Check Task Shortcut

The task ledger uses these canonical `Next Actor` values:

- `Director`
- `ProductManager`
- `Architect`
- `DevelopmentEngineer`
- `TestAcceptanceEngineer`
- `User`
- `None`

Supported role shortcuts:

- `Director, check task`: Director reads `TaskAndReport/TASK_TRACKING_LIST.md`, reviews rows with `Next Actor=Director`, checks rows with `Next Actor=User`, writes review or decision records when needed, updates the task ledger, and issues the next task brief when appropriate.
- `产品经理, check task` or `ProductManager, check task`: ProductManager reads the task ledger and executes the earliest open row where `Next Actor=ProductManager`.
- `架构师, check task` or `Architect, check task`: Architect reads the task ledger and executes the earliest open row where `Next Actor=Architect`.
- `开发工程师, check task` or `DevelopmentEngineer, check task`: DevelopmentEngineer reads the task ledger and executes the earliest open row where `Next Actor=DevelopmentEngineer`.
- `测试验收工程师, check task` or `TestAcceptanceEngineer, check task`: TestAcceptanceEngineer reads the task ledger and executes the earliest open row where `Next Actor=TestAcceptanceEngineer`.

If a row names a role as `Next Actor`, a branch-state-only or general status reply is not sufficient. The role must execute the listed `Next Action` or write a blocked report and update the row.

## Role Boundaries

Director owns task dispatch, report review, task-ledger state, cross-role sequencing, and escalation to the user when owner judgment is required. Director may discuss decisions with the user, but must not silently convert uncertain product or release decisions into accepted project facts.

ProductManager owns PRD alignment, requirement clarification, scope boundaries, operator/user impact, acceptance criteria, and product-risk reporting. ProductManager does not implement code or declare technical feasibility without architecture or implementation evidence.

Architect owns technical route, module boundaries, interface contracts, deployment/runtime constraints, risk analysis, and architecture review. Architect does not implement routine code unless a Director task explicitly assigns a documentation or analysis change.

DevelopmentEngineer owns scoped implementation and developer validation assigned by Director. DevelopmentEngineer must not change PRD truth, role contracts, release judgments, or task scope unless explicitly assigned.

TestAcceptanceEngineer owns validation design, test execution, UAT/runtime evidence, and acceptance-boundary reporting. TestAcceptanceEngineer may recommend pass/fail outcomes, but Director records the final task acceptance and user-owned release decisions.

No role may commit secrets, hide skipped checks, broaden scope silently, restore deprecated heuristic chapter-preprocessing logic, or configure silent fallback for core parsing or AI recognition paths.

## Current Technical Guardrails

- The current Phase 1 mainline is upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Chapter preprocessing, if reintroduced or extended, must preserve the full-text reasoning direction.
- Deprecated heuristic chapter preprocessing, including any `chapterPreprocessV2.ts`-style main path, must not be restored.
- Core preprocessing and AI recognition failures must fail explicitly. Silent degradation is not allowed.
- Skeleton fallback must not be represented as real AI recognition.

## Required Reading For New Role Threads

Every new role thread must read these files before acting:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. The active role file under `docs/codex/roles/`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. The current assigned task brief under `TaskAndReport/`, when one exists for that role.

## Safety Rules

- Do not commit secrets, API tokens, local private credentials, or machine-only artifacts.
- Do not run destructive production, MinIO, DB, Docker volume, or data cleanup commands without explicit Director task authorization and, when needed, explicit user approval.
- Do not change unrelated files while executing a scoped task.
- Do not treat partial local checks as UAT, L2, L3, or production acceptance.
- Do not promote pending, failed, or unreviewed evidence into confirmed project facts.
- Keep GitHub synchronized before and after completed work that changes repository files when the task brief requires sync.
- Do not copy local sample-library files into the repository for commit. Reports may reference sample paths, sizes, hashes, and observed validation results, but the source sample files must remain external and unchanged.
