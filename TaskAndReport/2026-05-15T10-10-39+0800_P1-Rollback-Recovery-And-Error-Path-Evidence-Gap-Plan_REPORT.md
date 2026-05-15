# Architect Report: P1 Rollback Recovery And Error Path Evidence Gap Plan

- Task ID: `TASK-20260515-101039-P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan`
- Task brief: `TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_TASK.md`
- Role: `Architect`
- Report time: `2026-05-15T10:34+0800`
- Recommendation: `READ_ONLY_EVIDENCE_FIRST`

## Current Accepted Readiness Context

This report is based on a Director task brief. Required reading was completed: `AGENTS.md`, `docs/codex/TEAM_CONTRACT.md`, `docs/codex/roles/architect.md`, `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, `docs/prd/Luceon2026-PRD-v0.4.md`, `docs/codex/TEST_POLICY.md`, `docs/codex/REPOSITORY_STRUCTURE.md`, `TaskAndReport/README.md`, `TaskAndReport/TASK_TRACKING_LIST.md`, Task 162 report and Director review, Task 163 report and Director review, Task 164 report and Director review, Task 166 report and Director review, Task 167 decision, and this task brief.

Accepted context:

- Task 163 accepted production source drift as conditionally clear after record. Five production dirty files are EOL-only/no semantic diff; `docker-compose.override.yml` is expected production-local override for strict AI model/fallback semantics and MinIO console local-only binding.
- Task 164/166 accepted and deployed dependency-health Ollama timing semantics. Production now exposes `readinessState`, `readinessSeverity`, `probeTimeoutMs`, `recommendedClientTimeoutMs`, `blockingAi`, `readinessBlocking`, and related fields.
- Task 167 records user approval that known pressure-window `failed/ai` residuals may remain visible manual retry candidates for this readiness track. They must not be hidden, counted as success, or flattened into systemic failure.

This task is read-only architecture analysis. It is not a pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness declaration.

Current read-only production snapshot:

- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD: `1716add Dispatch dependency health production validation`
- Production status: `main...origin/main` with the same Task 163 classified local-boundary dirty files.
- Docker: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy.
- `/cms/` and `/cms/tasks`: HTTP `200`.
- Upload health: HTTP `200`, `ok=true`.
- Dependency health: HTTP `200`, `ok=true`, `blocking=false`; Ollama `readinessState=resident-chat-succeeded`, `readinessSeverity=info`, `blockingAi=false`, `readinessBlocking=false`, `blockingParse=false`, `probeTimeoutMs=15000`, `recommendedClientTimeoutMs=20000`.
- MinerU admission circuit: closed.
- Active-task diagnostics: no active task, queued tasks `0`, takeover-required count `0`, historical AI failure count `6`.
- Direct MinerU `/health`: healthy, queued `0`, processing `0`, failed `0`.

## Rollback / Recovery Evidence Matrix

| Area | Existing evidence | Missing evidence | Risk created by gap |
| --- | --- | --- | --- |
| Source rollback | Git-based fast-forward deployments have been recorded, including production `91c1352 -> 1716add`. `DEPLOY.md` documents `git pull` and `docker compose up -d --build`; `PRODUCTION_RUNTIME_OWNERSHIP.md` records service owners. | No documented rollback rehearsal to a prior Git HEAD, no documented reverse deployment command, and no acceptance criteria for post-rollback health. | If a deployed change regresses production, the team has source-control primitives but not rehearsed rollback evidence. |
| Docker/service rollback | Compose service ownership is documented. Recent deployments used scoped `docker compose up -d --build upload-server` or frontend/upload-server commands, preserving volumes. | No controlled rollback/recreate rehearsal, no service-level restart recovery evidence for upload-server/frontend/db-server/minio under release scope, and no explicit blast-radius checklist. | Recovery may be improvised during an incident, especially if dependency services are recreated unexpectedly. |
| Production-local override preservation | Task 163 accepted `docker-compose.override.yml` as expected production-local boundary: strict no-skeleton, `qwen3.5:9b`, MinIO console `127.0.0.1:19001:9001`. Task 166 preserved the dirty override across fast-forward. | No automated pre/post deploy assertion for exact override values. No cleaner environment-specific override mechanism. | A future deploy or cleanup could accidentally remove strict AI or local-only MinIO console semantics. |
| DB recovery / backup boundary | `db-server.mjs` atomically writes `db-data.json`, creates `.bak`, restores from `.bak` if the main DB is missing or corrupt, and exposes `/backup/export` plus `/backup/import` with pre-import backup. UI describes metadata JSON backup and full backup flows. | No release-track read-only evidence of current DB backup file presence/freshness, export shape, or restore rehearsal. Import/restore is mutating and not rehearsed in this task. | DB recovery exists in code but has not been proven for the current production dataset and cannot be assumed for a release decision without evidence or risk acceptance. |
| MinIO artifact preservation / recovery | MinIO uses Docker volume `cms-minio-data`. Parsed artifacts use `artifact-manifest.json`; recent validations confirmed raw/parsed artifact preservation in specific tasks. Full backup endpoints exist for DB plus MinIO content. | No current read-only full-backup inventory evidence, no restore rehearsal, no object-count/hash sample verification for critical recent tasks, and no MinIO volume backup runbook. | Raw/parsed artifacts are central to review workflow; without backup/restore evidence, artifact loss recovery remains an operational risk. |
| Task-state recovery / failed-task handling | Accepted evidence exists for completed-after-local-timeout takeover, active-task diagnostics, historical AI failure separation, manual-only AI residual classification, retry/reparse/re-AI UI affordances, and no automatic retry/requeue for strict AI residuals. | No current release-level matrix proving each failed-state action path end-to-end under production. Existing recovery evidence is piecemeal across incidents and code smokes. | Operators may see the right semantics but still lack a rehearsed procedure for deciding retry/reparse/re-AI/cancel/recover during release incidents. |

## Error-Path Matrix

| Error path | Existing evidence | Missing evidence / boundary |
| --- | --- | --- |
| Upload dependency failure | `/tasks` checks dependency-health before accepting non-Markdown MinerU work; current production upload health is OK. UI has dependency-health banner and upload modal error behavior. | No current controlled read-only evidence pack of how upload UI/API presents each blocked dependency. Full proof of upload failure requires failure injection or simulated/dev tests. |
| MinerU `/health` failure | `dependency-health-smoke` covers MinerU down; `PRODUCTION_RUNTIME_OWNERSHIP.md` states health checks. | Current production MinerU is healthy, so failure rendering is not live-proven. A live `/health` failure test requires service mutation/failure injection. |
| MinerU `/tasks` submit failure | `mineru-submit-circuit-breaker-smoke.mjs` covers `/health` OK but submit HTTP 500: task remains pending/dependency-blocked, material blocked, durable admission circuit opens, next task is not submitted. Prior project state records submit-probe/admission-circuit acceptance. | No current production submit-failure rehearsal. Dependency-health submit-probe can collect read-only-ish readiness only by creating a synthetic MinerU task upstream; task brief did not need it and it was not run here. |
| MinerU long-running / local-timeout / still-processing | Prior accepted tasks covered long-running MinerU, local-timeout still processing, completed-after-timeout takeover, active-task diagnostics, and current active-task is idle. | No current release-level long-run rehearsal after latest HEAD; pressure residue has been resolved, but no new long-run case was created by this task. |
| MinIO unavailable or bucket/object failure | Code checks MinIO in dependency-health and `/tasks`; `uploadBufferToMinIO` retries and then fails explicitly. Some smokes cover MinIO read/write/persist failures. Current dependency-health says MinIO OK. | Live MinIO-down behavior requires service mutation/failure injection. Current backup/export object inventory evidence can still be collected read-only. |
| DB unavailable or proxy `502` / API failure | Prior db-sync warning hardening accepted browser/runtime evidence. `db-server` has atomic writes and backup import/export. Current Docker shows db-server healthy, and CMS routes return 200. | Live DB-down/proxy-502 behavior requires service mutation/failure injection. Current read-only DB health/export evidence can be collected, but restore is mutating. |
| Ollama missing model / tags failure / cold timeout / warm timeout / chat HTTP failure | Task 164 tests cover model missing, tags failure, service unreachable, cold timeout, warm timeout, chat HTTP error, and resident/cold success. Task 166 proves production exposes the new fields for resident success. | Production naturally observed resident success only. Missing model, timeout, and chat HTTP failure require config/model/service mutation or test harness simulation. |
| Strict no-skeleton AI failure path | `ai-metadata-repair-hardening-smoke`, `worker-smoke`, and `ai-failure-classification-smoke` cover strict no-skeleton failure, manual retry eligibility, and no automatic retry. Pressure-window residuals are accepted as visible manual retry candidates. | No production mutation should be used to fabricate new failed AI tasks before release. Existing failed/ai tasks can be inspected read-only if Director wants a final operator-facing evidence pack. |
| UI/task-page partial success and failed AI residuals | Task 160 accepted UI/runtime pressure semantics: `21 review-pending/review`, `3 failed/ai`, and no whole-run/systemic flattening. Task 167 accepts residual policy. | A final read-only UI/operator evidence pack can still capture current task list/detail wording for failed/ai residuals and successful review-pending tasks. |

## Evidence Categories

### Already Accepted Evidence

- Scoped production deployment/read-only validation through production HEAD `1716add`.
- Classified production source/override boundary.
- Dependency-health timing semantics in production.
- MinerU admission/active-task surfaces and current idle state.
- AI strict no-skeleton behavior at code/test level.
- AI residual policy: known `failed/ai` cases may remain visible manual retry candidates.
- DB write backup behavior and backup/import endpoints exist in code.
- Full backup/export/import UI and endpoints exist, but not release-rehearsed.

### Read-Only Evidence Still Collectable Now

A `TestAcceptanceEngineer` read-only evidence pack can collect:

- production `git status`, HEAD, and exact local override content;
- Docker service status and listener status;
- upload health, dependency-health with Ollama fields, admission circuit, active-task diagnostics, direct MinerU health, `/cms/` and `/cms/tasks`;
- DB health/export response shape without import;
- read-only task/API sample for representative `review-pending`, `failed/ai`, and completed/review rows, without retry/reparse/re-AI;
- MinIO object inventory/count for selected existing materials/tasks, without deletion/import/restore;
- browser-only task list/detail screenshots or notes for partial success and failed AI residual semantics.

This would close many documentation/evidence gaps, but it would still not prove actual rollback or live failure injection.

### Controlled Mutation / Rehearsal Evidence Requiring Explicit User Approval

These require a new decision because they mutate runtime state or service availability:

- source rollback rehearsal to a prior HEAD and forward recovery;
- Docker service restart/recreate rehearsal;
- DB restore/import rehearsal, even with a backup;
- full backup import/restore rehearsal for DB plus MinIO;
- MinIO unavailable simulation or bucket/object failure injection;
- DB unavailable/proxy `502` simulation;
- MinerU service stop/restart or submit-failure simulation;
- Ollama missing-model/timeout/service-down simulation;
- any upload, retry, reparse, re-AI, repair, cancel, cleanup, or automatic retry/requeue validation.

### Evidence Not Recommended Before Release Without Risk Acceptance

Do not attempt destructive or high-blast-radius tests on the current production data path before release unless the user explicitly chooses that tradeoff:

- Docker volume deletion/prune or destructive restore drill;
- MinIO object deletion or replace-mode full import;
- model deletion/pull/change to simulate Ollama missing model;
- broad service kill/restart chains while production evidence is otherwise stable;
- artificial corruption of DB files or MinIO artifacts.

These should be accepted as operational risk or rehearsed later in a disposable clone/staging environment.

## Recommended Next Step

Recommendation: `READ_ONLY_EVIDENCE_FIRST`.

Rationale:

- The remaining blocker is not a known implementation failure. It is an evidence gap.
- A controlled rollback/failure-injection rehearsal would be useful, but it requires service/data/runtime mutation and explicit user approval.
- Before asking the user to approve mutation, Director should collect the maximum remaining read-only evidence so the user can decide whether to accept residual operational risk or authorize a limited rehearsal.

Precise next task recommendation:

- Target role: `TestAcceptanceEngineer`
- Task type: `P1 Rollback Recovery And Error Path Read-Only Evidence Pack`
- Scope:
  - collect current production read-only evidence for rollback/recovery surfaces and error-path observability;
  - inspect docs/runbooks/endpoints and current runtime state;
  - capture representative task list/detail semantics for existing `review-pending` and `failed/ai` tasks;
  - inspect DB backup/export shape and MinIO inventory for selected existing artifacts without import/export restore, deletion, or mutation;
  - produce a final matrix marking each remaining gap as `closed by read-only evidence`, `requires user-approved rehearsal`, or `accepted operational risk candidate`.
- Forbidden:
  - no rollback, fast-forward, deploy, rebuild, restart, stop, kill, attach, failure injection, upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, destructive mutation, service/config/secret/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim.

After that evidence pack, Director should record a user decision with three realistic options:

1. accept residual rollback/failure-injection risk and proceed to a final read-only release-candidate preflight;
2. authorize a narrowly scoped rehearsal in a disposable clone/staging path;
3. authorize a narrowly scoped production rehearsal with explicit risk acceptance.

## Forbidden Operations Confirmation

This Architect task did not perform upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, Docker down/volume cleanup/prune, rollback, fast-forward, deploy, rebuild, restart, stop, kill, attach, failure injection, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, PRD truth/role contract/project-state/handoff edits, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness claim.

## Recommended Next Actor

`Director`

Director should review this evidence-gap plan and, if accepted, issue the read-only evidence pack task to `TestAcceptanceEngineer` before asking the user to approve or reject any controlled rollback/failure-injection rehearsal.
