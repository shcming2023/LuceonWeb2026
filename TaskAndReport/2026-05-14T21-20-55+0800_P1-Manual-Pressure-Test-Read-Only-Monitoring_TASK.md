# Task Brief: P1 Manual Pressure Test Read-Only Monitoring

- Task ID: `TASK-20260514-212055-P1-Manual-Pressure-Test-Read-Only-Monitoring`
- Created: 2026-05-14T21:20:55+0800
- Created by: Director
- Assigned role: `TestAcceptanceEngineer`
- Expected report: `TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-14T21-15-12+0800_P1-Next-Step-After-Db-Sync-Hardening-Validation-Pass_DECISION.md`

## Context

The db-sync hardening validation chain is closed at bounded validation level:

- Task 146 accepted code/test hardening for upload-time db-sync lifecycle noise;
- Task 148 accepted scoped production deployment/read-only validation;
- Task 149 accepted exactly-one production upload validation;
- Task 149 proved the db-sync warning class did not recur in one controlled upload;
- no pressure, batch, soak, L3, release-readiness, production-readiness, go-live, or production上线 claim has been made.

The user has now chosen the next validation route:

- the user will clean the environment manually;
- the user will manually submit one pressure test of roughly 20+ PDFs, with mixed large and small files;
- TestAcceptanceEngineer must monitor the pressure test every 30 minutes by heartbeat;
- TestAcceptanceEngineer must comprehensively record the pressure-test process until all submitted work succeeds, fails, or becomes hung/deadlocked;
- after the pressure test has fully ended, TestAcceptanceEngineer writes the report and hands it to Director for review.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/PROJECT_STATE.md`
4. `docs/codex/HANDOFF.md`
5. `docs/prd/Luceon2026-PRD-v0.4.md`
6. `docs/codex/TEST_POLICY.md`
7. `docs/codex/REPOSITORY_STRUCTURE.md`
8. `TaskAndReport/README.md`
9. `TaskAndReport/TASK_TRACKING_LIST.md`
10. this task brief
11. `TaskAndReport/2026-05-14T21-15-12+0800_P1-Upload-Time-Db-Sync-Hardening-Exactly-One-Controlled-Upload-Validation_DIRECTOR_REVIEW.md`

If a local role file for `TestAcceptanceEngineer` is missing, do not stop merely because of that missing file. Use this task brief plus `AGENTS.md`, `TEAM_CONTRACT.md`, and `TaskAndReport/README.md` as the controlling context. Stop only if the task row or this task brief is missing locally.

## Workspaces And Runtime Anchors

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production UI: `http://localhost:8081/cms/`
- Upload proxy base: `http://localhost:8081/__proxy/upload`
- DB proxy base: `http://localhost:8081/__proxy/db`
- MinerU endpoint: `http://127.0.0.1:8083`
- User-selected pressure-test source: expected from `/Users/concm/prod_workspace/Luceon2026/testpdf` or another user-controlled local source, but TestAcceptanceEngineer must not modify source files.

## Objective

Monitor one user-submitted production pressure test of roughly 20+ mixed-size PDFs with a 30-minute heartbeat cadence, record the full process, and produce a final evidence report after the run reaches one of these outcomes:

- `SUCCESS`: every pressure-test task reaches a coherent terminal success/review state and runtime returns idle/non-blocking;
- `FAILED`: one or more pressure-test tasks reaches terminal failed state, or systemic service errors make the pressure test fail;
- `HUNG_OR_STALLED`: the system is alive but pressure-test work stops making observable progress for the configured stall threshold;
- `MACHINE_OR_SERVICE_DOWN`: production UI/proxy/core services become unreachable enough that monitoring cannot continue normally.

This task is validation monitoring only. It is not production-readiness approval, release-readiness approval, L3 PASS, pressure PASS, go-live readiness, or production上线.

## User-Owned Actions

The following actions belong to the user, not TestAcceptanceEngineer:

- cleaning the environment;
- selecting the files;
- submitting the 20+ PDF pressure test;
- deciding whether to retry if the user-side upload action itself fails before tasks are created.

TestAcceptanceEngineer should ask the user to send a short note in the test thread when manual submission has started or completed, if the user has not already done so. If no note appears, TestAcceptanceEngineer may infer start time from new tasks after its baseline snapshot.

## Mandatory Heartbeat Setup

In the TestAcceptanceEngineer thread, create or update a heartbeat automation for this task:

- cadence: every 30 minutes;
- scope: same thread, no new thread;
- purpose: run one monitoring pass, append observations to the draft report or local monitoring notes, and continue until final outcome;
- stop condition: once final report is written and task row is handed to Director, the TestAcceptanceEngineer heartbeat should be deleted or paused.

Suggested concise heartbeat instruction for that thread:

```text
You are Luceon2026 TestAcceptanceEngineer. In this same thread, run one monitoring pass for Task 151 P1 Manual Pressure Test Read-Only Monitoring. Do not upload, clean, repair, restart, mutate data, or sync GitHub unless explicitly authorized. Read TaskAndReport/TASK_TRACKING_LIST.md and the Task 151 brief, sample production status and pressure-test task progress, append evidence, and if all pressure-test work has succeeded, failed, or stalled, write the final report and update the row to Director.
```

## Pre-Submission Baseline

On the first run, before or as close as possible before the user submits the pressure test, record:

- development workspace `git status --short --branch`;
- production `git status --short --branch`;
- production `git log -1 --oneline`;
- `docker compose ps` in production;
- frontend `/cms/` HTTP status;
- upload health;
- dependency-health without adding unnecessary active workload. Prefer no Ollama chat probe while pressure work is active; if no workload has started, one bounded preflight chat probe may be recorded if safe;
- MinerU admission circuit;
- active task through `/__proxy/upload/ops/mineru/active-task`;
- direct MinerU `/health`;
- baseline task count and latest task IDs;
- baseline material count if practical;
- host resource snapshot: uptime/load, memory pressure or equivalent memory summary, disk space, and lightweight process summary for Docker, Node, MinerU/Python, and Ollama.

If baseline cannot be captured before manual submission, record that exact reason and capture the earliest possible snapshot.

## Monitoring Cadence

Every 30-minute heartbeat monitoring pass should record:

- timestamp and elapsed time from detected pressure-test start;
- whether user manual submission has happened;
- current count of pressure-test tasks believed to belong to this run;
- per-task summary: task id, material id if visible, file name if visible, state, stage, progress, message, MinerU task id, AI job id if visible, updatedAt/completedAt if visible;
- aggregate counts by state/stage, including pending/running/review-pending/failed;
- oldest non-terminal task age and last observed progress time;
- active-task endpoint;
- admission circuit;
- direct MinerU health;
- upload health;
- dependency health without unnecessary chat load during active pressure work;
- Docker service health;
- lightweight host resource snapshot;
- browser/UI spot-check if the UI is responsive and doing so does not interfere with the run;
- any console/network errors if browser observation is performed;
- whether task list and task detail progress semantics remain operator-readable;
- whether db-sync warnings, `/settings`, `/secrets`, `Failed to fetch`, HTTP 5xx, or non-stream request failures appear;
- whether runtime appears to be progressing, failing, or stalled.

Do not spam Ollama with repeated chat probes during active pressure work. The goal is observation, not extra load.

## Stall / Hang Criteria

Use conservative judgment, but report `HUNG_OR_STALLED` if:

- at least one pressure-test task remains non-terminal;
- no task state/stage/progress/message/updatedAt/MinerU/AI evidence changes for two consecutive 30-minute monitoring passes;
- runtime endpoints remain reachable enough to prove the system is not simply down; and
- no clear active MinerU or AI progress explains the wait.

Report `MACHINE_OR_SERVICE_DOWN` if:

- production UI/proxy/core services are unreachable or repeatedly failing across two monitoring passes; or
- the machine/runtime is too unresponsive to capture normal evidence.

If a task fails explicitly before the stall threshold, report `FAILED` with the first failure and all available evidence.

## Allowed Operations

Allowed:

- read task ledger and task brief;
- create/update the TestAcceptanceEngineer heartbeat in the same thread;
- read production UI and read-only endpoints;
- use browser read-only observation;
- run read-only shell commands such as `git status`, `git log`, `docker compose ps`, `docker stats --no-stream`, `curl`, `uptime`, disk/memory/process snapshots;
- maintain a local/draft monitoring log;
- write the final `*_REPORT.md`;
- update Task 151 row to `已回报待 Director 审查` when final report is complete.

## Forbidden Operations

Forbidden:

- uploading files;
- cleaning environment;
- deleting tasks/materials/files;
- failed-task repair;
- reparse or re-AI;
- direct DB or MinIO mutation;
- `docker compose down`, `docker compose down -v`, Docker volume/data cleanup;
- Docker rebuild/restart/up/down unless a future Director task explicitly authorizes it;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- model pull/delete/replace;
- config/secret/sample mutation;
- modifying source test PDFs;
- broad GitHub sync on every heartbeat;
- declaring L3, pressure PASS, release readiness, production readiness, go-live readiness, or production上线.

## Report Requirements

Write the final report only after the pressure test fully reaches `SUCCESS`, `FAILED`, `HUNG_OR_STALLED`, or `MACHINE_OR_SERVICE_DOWN`:

`TaskAndReport/2026-05-14T21-20-55+0800_P1-Manual-Pressure-Test-Read-Only-Monitoring_REPORT.md`

The report must include:

- exact task brief path;
- required reading completed;
- heartbeat automation id/cadence/status;
- whether baseline was captured before user submission;
- user manual submission start/end time if known;
- detected pressure-test task set and method used to identify it;
- file names/sizes/hashes if safely available from task/material metadata or user-provided list; do not hash source files if that would add heavy load during active pressure;
- timeline table for every 30-minute monitoring pass;
- per-task final state table;
- aggregate duration and throughput observations;
- MinerU observations;
- Ollama/AI observations;
- MinIO/DB/upload/frontend observations;
- host resource observations;
- browser/UI/operator-readability observations;
- console/network noise observations;
- exact final outcome: `SUCCESS`, `FAILED`, `HUNG_OR_STALLED`, or `MACHINE_OR_SERVICE_DOWN`;
- first failure or first stall evidence if applicable;
- commands run and exit codes;
- skipped checks and exact reasons;
- risks/blockers/residual debt;
- explicit statement that TestAcceptanceEngineer did not upload, clean, repair, reparse, re-AI, mutate DB/MinIO/Docker volume/data, restart services, mutate models/config/secrets/samples, or claim readiness/L3/go-live.

Update row 151 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- while monitoring: keep `Status=执行中`, `Next Actor=TestAcceptanceEngineer`;
- final report complete: set `Status=已回报待 Director 审查`, `Next Actor=Director`, and populate report path.

Do not push to GitHub from the TestAcceptanceEngineer thread unless Director explicitly instructs it.
