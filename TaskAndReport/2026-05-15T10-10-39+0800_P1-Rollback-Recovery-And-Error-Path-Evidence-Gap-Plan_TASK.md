# Task Brief: P1 Rollback Recovery And Error Path Evidence Gap Plan

- Task ID: `TASK-20260515-101039-P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan`
- Created: 2026-05-15T10:10:39+0800
- Created by: Director
- Assigned role: `Architect`
- Expected report: `TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_REPORT.md`
- Based on accepted consolidation: `TaskAndReport/2026-05-15T08-55-08+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_DIRECTOR_REVIEW.md`
- Based on accepted dependency-health runtime validation: `TaskAndReport/2026-05-15T10-04-18+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_DIRECTOR_REVIEW.md`
- Based on user decision: `TaskAndReport/2026-05-15T10-04-18+0800_P1-AI-Residual-Release-Boundary-Decision_DECISION.md`

## Context

The release-readiness consolidation identified four blockers:

1. production source/local override drift classification;
2. dependency-health cold-before-chat timing semantics;
3. AI residual release-boundary policy;
4. rollback/recovery and full error-path evidence.

The first three have now been addressed within bounded scope:

- Task 163 classified production source/local override drift as conditionally clear after record.
- Task 164/166 implemented and deployed dependency-health timing semantics; production now exposes the new Ollama readiness/timing fields.
- Task 167 user decision accepted known `failed/ai` residuals as visible manual retry candidates for this readiness track.

The remaining blocker is rollback/recovery and error-path evidence. This task is a read-only Architect task to define the evidence gap and propose the next safe validation steps. It must not perform rollback, failure injection, service restart, data mutation, upload, cleanup, retry, reparse, or re-AI.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/architect.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 162 report and Director review
12. Task 163 report and Director review
13. Task 164 report and Director review
14. Task 166 report and Director review
15. Task 167 decision file
16. This task brief

If the task row, Architect role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`. Do not improvise from partial context.

## Objective

Produce a read-only rollback/recovery and error-path evidence gap plan that answers:

1. What rollback/recovery evidence already exists?
2. What error-path evidence already exists for upload, MinerU, MinIO, DB, Ollama, AI strict-mode failure, and dependency-health/admission-circuit behavior?
3. Which missing evidence can be collected read-only?
4. Which missing evidence requires controlled mutation, service restart, failure injection, upload, or user approval?
5. Which evidence is mandatory before a release-readiness decision, and which can be deferred as operational polish?
6. What exact next task(s) should Director issue, in the safest sequence?

The output should allow Director and User to decide whether the remaining release-readiness blocker can be closed through read-only evidence, limited rehearsal, or explicit risk acceptance.

## Allowed Operations

Allowed:

- read repository docs, source code, task reports, and task ledger;
- inspect existing runbooks/deploy docs under `docs/`, `ops/`, scripts, and compose files;
- run read-only Git status/HEAD checks in development and production;
- run read-only production HTTP checks only if useful:
  - upload health;
  - dependency-health;
  - MinerU admission circuit;
  - active-task diagnostics;
  - direct MinerU `/health`;
  - `/cms/` and `/cms/tasks` HTTP status;
- inspect Docker service status read-only with `docker compose ps`;
- write the Architect report and update row 168 locally.

## Forbidden Operations

Forbidden:

- rollback, fast-forward, deploy, rebuild, restart, stop, kill, attach, or service mutation;
- failure injection;
- PDF upload or any fresh validation artifact;
- pressure/batch/soak/fresh serial validation;
- cleanup, cancel, repair, retry, reparse, or re-AI;
- destructive DB, MinIO, Docker volume, Docker data, or local filesystem mutation;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup, prune;
- MinerU/Ollama/supervisor mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- PRD truth, role contract, project state, or handoff changes;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report Structure

The report must include:

1. **Current Accepted Readiness Context**
   - summarize Task 163, 164/166, and 167 accepted boundaries;
   - confirm this task is read-only and not a readiness declaration.

2. **Rollback / Recovery Evidence Matrix**
   - source rollback;
   - Docker/service rollback;
   - production-local override preservation;
   - DB recovery or backup boundary;
   - MinIO artifact preservation/recovery boundary;
   - task-state recovery or failed-task handling boundary;
   - what evidence exists, what is missing, and what risk each gap creates.

3. **Error-Path Matrix**
   - upload dependency failure;
   - MinerU `/health` failure and MinerU `/tasks` submit failure;
   - MinerU long-running / local-timeout / still-processing behavior;
   - MinIO unavailable or bucket/object failure;
   - DB unavailable or proxy `502` / API failure;
   - Ollama missing model, tags failure, cold timeout, warm timeout, chat HTTP failure;
   - strict no-skeleton AI failure path;
   - UI/task-page operator semantics for partial success and failed AI residuals.

4. **Evidence Categories**
   - already accepted evidence;
   - read-only evidence still collectable now;
   - controlled mutation/rehearsal evidence requiring explicit user approval;
   - evidence that should not be attempted before release and should instead be accepted as operational risk.

5. **Recommended Next Step**
   - one of:
     - `READ_ONLY_EVIDENCE_FIRST`;
     - `CONTROLLED_REHEARSAL_REQUIRED`;
     - `READY_FOR_USER_RISK_ACCEPTANCE_DECISION`;
     - `NO_GO_UNTIL_IMPLEMENTATION_FIX`;
   - include precise proposed next task brief target role and scope.

6. **Forbidden Operations Confirmation**
   - explicitly state no upload, pressure/batch/soak/fresh serial validation, cleanup/repair/reparse/re-AI, destructive mutation, service/config/secret/model/sample mutation, rollback/rebuild/restart/failure injection, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was made.

## Required Report

Write:

`TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_REPORT.md`

Update row 168 in `TaskAndReport/TASK_TRACKING_LIST.md` to:

- Status: `已回报待 Director 审查` or precise blocked status;
- Next Actor: `Director`;
- Report path populated.
