# Luceon2026 Codex Operating Rules

Last updated: 2026-05-03

This repository is the durable project memory for Luceon2026. Codex thread history is useful working context, but it is not the source of truth. Any Codex thread that joins this project must read this file first, then read the relevant role handoff in `docs/codex/roles/`.

## Project Direction

Luceon2026 is moving toward a single primary development and validation host:

- Home Mac mini will host the long-lived Codex working environment.
- Work laptops will access the Mac mini through remote desktop.
- GitHub remains the code and documentation source of truth.
- OneDrive may hold a working copy, but it must not be treated as the version-control source.

Current repository and deployment anchors:

- Development working copy: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/Luceon2026`
- GitHub repository: `https://github.com/shcming2023/Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

Keep the development working copy synchronized with the GitHub repository. Treat GitHub plus repository documents as durable truth; treat OneDrive as a working location only.

The intended Mac mini layout is:

- `~/dev/Luceon2026` for Codex development work.
- `~/staging/Luceon2026` for staging and production-like validation.
- `/opt/luceon2026` for production deployment.

Keep dev, staging, and production data, containers, and compose project names isolated.

## Active Roles

Read the role files before acting:

- `docs/codex/roles/lucia.md`: architecture control, task writing, review, and final judgment.
- `docs/codex/roles/lucode.md`: implementation work from an independent IDE/work computer, strictly from lucia-approved task briefs.
- `docs/codex/roles/luplan.md`: PRD and documentation source-of-truth maintenance.
- `docs/codex/roles/luceonhmm.md`: UAT deployment, real-environment validation, dependency debugging, failure analysis, and evidence capture.
- `docs/codex/roles/cota.md`: Director-side cross-project Codex collaboration advisor for role boundaries, task routing, and coordination quality, including XxwlAs2026/cosh setup guidance.
- `docs/codex/roles/lutest.md`: archived legacy role only. Do not route new work there.

Target role model after the Mac mini migration:

- `lucia`: code-facing architecture, task control, L1 gate review, and release judgment.
- `lucode`: implementation, code revision, local developer checks, GitHub synchronization, and completion reporting.
- `luplan`: PRD, decisions, project state, and changelog maintenance.
- `luceonhmm`: UAT deployment, real-environment validation, dependency debugging, failure analysis, rollback support, and evidence capture.
- `cota`: Director-side cross-project collaboration advisor. cota does not execute implementation, validation, deployment, PRD maintenance, or final judgment; cota may help port this collaboration model to XxwlAs2026 as `cosh`.
- `lutest`: retired. Do not route new validation work to `lutest`.

## Coordination Mode

Luceon2026 uses Lucia-centered coordination. Autonomous task queues are not active.

Lucia must issue tasks to `lucode`, `luceonhmm`, and `luplan` using `docs/codex/TASK_BRIEF_TEMPLATE.md`. Each task brief is the execution contract and must include scope, allowed files or operations, forbidden changes, evidence requirements, and report format.

Execution agents report back to Lucia using the corresponding report format. They do not automatically write task results into a queue, PRD, changelog, project-state file, handoff file, or other durable project facts.

Only facts confirmed by Lucia or Director may be promoted by luplan into `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, PRD, changelog, role handoffs, or durable project memory.

Risk guardrails:

- `lucode` must not start implementation from vague oral instructions or self-created tasks.
- `luceonhmm` must not report unjudged evidence as final `PASS`; it reports evidence or `PASS_CANDIDATE` for Lucia judgment.
- `luplan` must not promote pending validation, unreviewed reports, or compatibility-only results as confirmed project facts.

## Role Boundaries

Lucia must not write business implementation code. Lucia writes tasks, review findings, validation criteria, and final judgments.

lucode writes business implementation code only from lucia-approved task briefs. lucode runs Antigravity in `/workspace/ops/Luceon2026` with host/IDE working copy reference `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`, synchronizes through GitHub, must minimize changes, and must not perform production deployment or real-environment validation.

luplan must not write business implementation code or perform deployment. luplan updates PRD, decisions, changelog, project-state documents, and handoff docs only when asked.

luceonhmm must not write business implementation code or PRD facts. luceonhmm runs UAT, L2/L3, and production-like validation; debugs deployment dependencies; analyzes failures; and reports evidence to lucia.

No role may claim Lite mock, skeleton fallback, partial local checks, or pending evidence as current L2/UAT or production validation.

## Runtime Dependencies

The current server-side dependency baseline includes:

- conda-deployed MinerU
- Docker-deployed MinIO
- Ollama with the project-required 9b model

These are important project prerequisites, not optional extras. lucia may inspect their reachable state when defining tasks and risk boundaries. luceonhmm may directly debug these prerequisites during UAT, deployment validation, failure reproduction, and evidence capture.

The previous online MinerU v4 + local Ollama `qwen3.5:0.8b` Tier 2 Standard line is retired from the current main gate and retained only as legacy / compatibility-only context. When a validation task specifically targets online MinerU v4 compatibility, that task's explicit online MinerU requirements still apply. Do not confuse local conda MinerU availability with a completed real online compatibility run.

## Validation Gates

L1 is the fast code gate. It should be runnable on any development host and may include:

```bash
npx tsc --noEmit
npm run build
npm run local:check
npm run test:smoke
```

L2 is near-production validation. The current main L2/UAT baseline is the local real runtime stack:

- conda-deployed MinerU
- Docker-deployed MinIO
- Ollama `qwen3.5:9b`
- `DISABLE_AI_SKELETON_FALLBACK=true`
- no required `MINERU_ONLINE_API_BASE_URL` or `MINERU_ONLINE_API_TOKEN`

Confirmed current local runtime validation facts:

- `P1-real-runtime-uat-local-mineru-minio-ollama9b = PASS`, scoped to local real runtime UAT only.
- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple = PASS`, scoped to strict no-skeleton local real runtime UAT.
- `P0-metadata-tab-review-architecture-first-pass = PASS`, scoped to MetadataTab information architecture on one real `review-pending` sample.
- `P1-fix-metadata-current-tags-persistence-contract = PASS`, scoped to single-tag add + refresh persistence on one real `review-pending` sample.

Skeleton fallback must never be reported as real AI recognition. Pending validation gaps must remain pending until Lucia or Director confirms them.

L3 is the Home Mac mini staging or production validation. Only L3 can be treated as production truth.

## Safety Rules

- Do not commit secrets or tokens.
- Do not echo full API tokens in reports.
- Do not run `docker compose down -v`, wipe MinIO, wipe DB data, delete Docker volumes, or clean production data without explicit Director approval.
- Do not edit `.agents/**` unless Director explicitly authorizes it.
- Do not broaden a task beyond the signed scope.
- Do not hide skipped or unavailable checks.
- Report environment identity with every L2/L3 validation result.

## Handoff Discipline

Before changing machines or retiring a thread, update:

- `docs/codex/PROJECT_STATE.md`
- the relevant file in `docs/codex/roles/`
- `docs/codex/HANDOFF.md`

Each handoff must include current HEAD, test status, blockers, next action, and whether the result is L1, L2, or L3.
