# Task: P1 Manual Clean 24-PDF Pressure Monitoring

Assignee:
TestAcceptanceEngineer

Issued by:
Director

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_TASK.md

Expected report:
TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/TEST_MATRIX.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P0-MinerU-Only-Runtime-Relaunch-And-Read-Only-Verification_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-15T20-21-23+0800_P0-MinerU-Submit-Probe-And-Pressure-State-Reconciliation-Decision_DECISION.md`

## Background

Director accepted Task 187 as scoped MinerU process restoration only. It did not verify pressure PASS or failed-task reconciliation.

User has now manually cleaned/reset the frontend test environment and manually uploaded 24 PDFs from the frontend. This task monitors that new clean pressure window. It replaces the previously recommended submit-probe-only next step for this iteration because the User has chosen a real pressure-window validation.

## Objective

Perform read-only, full-process monitoring of the User-started 24-PDF pressure run.

The purpose is to determine whether the system can remain stable, observable, and operator-understandable during long-running MinerU and AI work. The report must avoid premature failure declarations when MinerU is still genuinely processing.

## Monitoring Cadence

- Take an initial snapshot immediately when this task starts.
- Then monitor at a 120-minute cadence.
- Continue until one of these stop conditions occurs:
  - all observed pressure-run tasks reach terminal states;
  - a system-level failure is confirmed by multi-source evidence;
  - the run is clearly hung or unrecoverable based on repeated no-progress evidence;
  - Director or User explicitly stops the monitoring task.

If all tasks reach terminal states before the next 120-minute heartbeat, write the final report without waiting for the next interval.

## Required Observation Sources

Use read-only sources only. Prefer these:

- `/cms/tasks` page observation, including visible state/progress/message semantics;
- `GET /__proxy/upload/health`;
- `GET /__proxy/upload/ops/dependency-health?mineruSubmitProbe=false`;
- `GET /__proxy/upload/ops/mineru/admission-circuit`;
- `GET /__proxy/upload/ops/mineru/active-task`;
- `GET /__proxy/upload/ops/mineru/log-channel-ownership`;
- `GET /__proxy/db/tasks`;
- `GET /__proxy/db/materials`;
- `GET /__proxy/db/task-events`;
- `GET /__proxy/db/ai-metadata-jobs`;
- direct MinerU `/health`;
- direct MinerU `/tasks/{mineruTaskId}` for already accepted MinerU tasks when the ID is visible;
- read-only tails/stat checks for configured MinerU logs, especially `/Users/concm/ops/logs/mineru-api.err.log` and `/Users/concm/ops/logs/mineru-api.log`, when needed to determine whether processing is still advancing.

Do not run manual submit-probe. The only acceptable submit-path side effect is the normal upload-path behavior already triggered by the User's manual frontend upload.

## Snapshot Requirements

Each snapshot must record:

- timestamp;
- total observed pressure-run tasks and counts by state/stage;
- active/running/queued/review-pending/failed task counts;
- current active MinerU task, if any;
- direct MinerU task status for the active MinerU task when available;
- latest meaningful MinerU log evidence: mtime, size, newest stage/progress snippet, and whether it advanced since the previous snapshot;
- whether the page semantics match backend/API/log progress;
- dependency-health without submit-probe;
- admission circuit state;
- Ollama/AI job state and AI failures;
- DB/proxy/MinIO observation health if relevant;
- whether there is evidence of actual progress, no progress, or ambiguous progress.

## Special Evaluation Rules

Do not lightly declare failure.

If direct MinerU API still reports `processing`, or MinerU logs show new stage/progress evidence, or output artifacts continue appearing, classify the run as still progressing even if the page wording appears stale.

Do not judge from page semantics alone. Compare page state with backend task state, direct MinerU API, log mtime/progress, worker/active-task diagnostics, and output/AI job evidence.

A task can be called hung only after repeated 120-minute snapshots show no meaningful progress across UI, backend, direct MinerU API, logs, and artifacts.

AI-stage failures should be separated from MinerU/system failures. A few `failed/ai` tasks are not automatically a pressure-run system failure if they are visible, bounded, and retryable while the rest of the pipeline continues.

System-level failure examples:

- MinerU 8083 disappears or direct health fails repeatedly;
- dependency-health becomes blocking for parse/AI and stays blocking;
- admission circuit opens and blocks continued intake after the manual run;
- DB/proxy outage prevents observation;
- active/queued tasks become impossible to interpret;
- no UI/backend/API/log/artifact progress across repeated snapshots while work remains non-terminal.

## Forbidden Operations

Do not:

- upload additional files;
- run another reset/cleanup;
- delete DB, MinIO, Docker, volume, or data contents;
- run `docker compose down`, `docker compose down -v`, Docker prune, or Docker volume cleanup;
- restart, stop, kill, relaunch, rebuild, redeploy, or mutate services;
- run manual or extra MinerU submit-probe;
- manually close/open/reset admission circuits;
- retry, repair, reparse, rerun AI, cancel, or mutate tasks;
- mutate `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- mutate config, secrets, models, Ollama, MinerU configuration, Docker volumes, DB volumes, or MinIO volumes;
- claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

If a mutating recovery appears necessary, stop and report a blocked recommendation to Director.

## Required Final Report

Write:

`TaskAndReport/2026-05-15T20-29-08+0800_P1-Manual-Clean-24-PDF-Pressure-Monitoring_REPORT.md`

The report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- production HEAD and production dirty-file summary;
- endpoints/commands used and whether they were read-only;
- User manual clean/reset/upload note;
- observed pressure-run task IDs/material IDs;
- per-snapshot timeline at 120-minute cadence, including initial snapshot;
- final task/material/AI counts by state;
- successful large/small examples if visible;
- all failed tasks with stage, reason, and retry-candidate classification;
- MinerU progress-semantics findings, including page/backend/log/API mismatches;
- Ollama/AI findings;
- dependency-health/admission/active-task findings;
- whether the system stayed observable and operator-understandable under pressure;
- blockers, residual risks, and recommended next tasks;
- explicit statement that TestAcceptanceEngineer did not upload, cleanup, retry, reparse, rerun AI, restart services, run submit-probe, or perform destructive operations.

## Task Ledger Update

After writing the report, update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews the pressure monitoring report and decides whether to accept evidence, issue engineering follow-up, request more validation, or ask User for a release-boundary decision.
- Required Output: Director review.

Commit and push the report and ledger update to GitHub `main`, unless the development workspace has unrelated dirty changes. If dirty, use a clean temporary clone/worktree and state that in the report.

## Acceptance Criteria

Director can accept the task only if the report provides enough evidence to judge:

- whether the 24-PDF run reached terminal completion, partial completion, system failure, or hung state;
- whether MinerU was actually progressing when UI semantics appeared stalled;
- whether the system remained observable for a human operator during long-running work;
- whether failures were isolated and visible rather than collapsing the whole run;
- whether further engineering is required before any release-boundary decision.

