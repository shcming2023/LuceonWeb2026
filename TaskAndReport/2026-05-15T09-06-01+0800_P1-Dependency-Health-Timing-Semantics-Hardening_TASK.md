# Task Brief: P1 Dependency Health Timing Semantics Hardening

- Task ID: `TASK-20260515-090601-P1-Dependency-Health-Timing-Semantics-Hardening`
- Created: 2026-05-15T09:06:01+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_REPORT.md`
- Based on Architect report: `TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T09-06-01+0800_P1-Production-Source-Drift-And-Override-Boundary-Read-Only-Classification_DIRECTOR_REVIEW.md`

## Context

Task 162 identified dependency-health timing semantics as a remaining release-readiness blocker. During read-only checks, one short client window timed out while a later longer call succeeded with Ollama chat OK after cold-before-chat behavior. Director later saw a warm dependency-health result complete quickly, so this is not a simple outage; it is a health/readiness semantics issue.

The project needs dependency-health to distinguish:

- hard dependency failures;
- slow but successful cold-before-chat Ollama readiness;
- warm resident-before-chat readiness;
- non-blocking Ollama AI readiness caveats versus parse/upload blockers.

This task is code/test hardening in the repository only. It does not authorize production deployment.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/prd/Luceon2026-Stability-PRD-v0.1.md` if present
8. `docs/codex/TEST_POLICY.md`
9. `docs/codex/REPOSITORY_STRUCTURE.md`
10. `TaskAndReport/README.md`
11. `TaskAndReport/TASK_TRACKING_LIST.md`
12. Task 162 report and Director review
13. Task 163 report and Director review
14. This task brief

If the task row, role file, or required Task 162/163 evidence is missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Harden dependency-health timing semantics so that operator/readiness surfaces do not confuse a slow but successful Ollama cold-before-chat probe with a hard dependency failure.

The implementation should be conservative and preserve strict no-skeleton behavior.

## Scope

Focus areas:

- dependency-health implementation in `server/upload-server.mjs` and related helpers;
- Ollama health/chat probe timeout and response fields;
- focused tests, especially `server/tests/dependency-health-smoke.mjs` and any narrow new smoke that is useful;
- documentation or task-report notes only if needed to clarify accepted client timeout/readiness expectations.

Expected behavior:

1. A successful but slow Ollama chat probe should remain `ok=true` / `blocking=false`, with explicit timing and warm/cold state fields that make the delay understandable.
2. A timeout or hard Ollama failure should remain visibly classified, without silently degrading AI recognition or introducing skeleton fallback.
3. Parse/upload readiness must not be blocked solely because AI/Ollama is slow or unavailable, unless existing strict semantics already require blocking.
4. Client/operator timeout expectations should be explicit enough that a 10s external curl timeout is not mistaken for service failure when the configured probe can legitimately run longer.
5. Existing dependency-health, AI metadata, MinerU admission, and pressure-semantics tests should continue to pass.

## Allowed Operations

Allowed:

- edit repository source/tests/docs within the narrow scope above;
- add or update focused tests;
- run local checks needed for this change:
  - `git diff --check`;
  - `node --check` on changed server files;
  - relevant smoke tests;
  - `npx pnpm@10.4.1 exec tsc --noEmit`;
  - `npx pnpm@10.4.1 run build` if frontend/types are touched or if needed by local policy.
- write the DevelopmentEngineer report and update row 164 locally.

## Forbidden Operations

Forbidden:

- production deployment, production fast-forward, rebuild, restart, rollback, or config mutation;
- upload, pressure/batch/soak/fresh serial validation;
- cleanup/cancel/repair/retry/reparse/re-AI;
- destructive DB/MinIO/Docker volume/data mutation;
- Docker down, Docker volume/data cleanup, prune;
- service start/stop/restart/rebuild in production, including MinerU/Ollama/supervisor mutation;
- settings/secrets/config/model/sample mutation;
- automatic retry/requeue;
- skeleton fallback weakening or representing skeleton fallback as real AI recognition;
- PRD truth, role contract, project state, or handoff changes;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report

Write:

`TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_REPORT.md`

The report must include:

1. Confirmation this work was based on this Director task brief.
2. Files changed.
3. Explanation of the timing semantics before and after.
4. Exact checks run and exit codes.
5. Any skipped checks and exact reasons.
6. Risks/blockers/residual debt.
7. Explicit statement that no production deployment/mutation, upload, retry/reparse/re-AI, destructive operation, skeleton fallback weakening, or readiness/go-live claim was made.

Update row 164 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
