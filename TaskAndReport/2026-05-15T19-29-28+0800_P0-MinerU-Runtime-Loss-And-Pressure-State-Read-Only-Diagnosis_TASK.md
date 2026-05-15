# Task: P0 MinerU Runtime Loss And Pressure State Read-Only Diagnosis

- Task ID: `TASK-20260515-192928-P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis`
- Assignee: `DevelopmentEngineer`
- Issued by: `Director`
- Issued at: 2026-05-15T19:29:28+0800
- Priority: P0
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/development-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T12-56-42+0800_P1-Manual-24-PDF-Pressure-Monitoring_REPORT.md`
- `TaskAndReport/2026-05-15T19-29-28+0800_P1-Manual-24-PDF-Pressure-Monitoring_DIRECTOR_REVIEW.md`

## Background

The User manually reset the test environment and manually submitted a 24-PDF pressure run. TestAcceptanceEngineer monitored the run and reported a blocked result:

- 5 tasks reached `review-pending`;
- the run did not terminally complete;
- MinerU became unreachable;
- no 8083 listener and no expected tmux session were visible at the stop-condition snapshot;
- upload and Ollama remained healthy.

Director read-only spot-check after the report found:

- `dependency-health?mineruSubmitProbe=false`: MinerU `connect ECONNREFUSED`, `blocking=true`;
- no visible listener on TCP 8083;
- no visible tmux session;
- active-task diagnostics showed retryable submit failures;
- the 24 pressure tasks had evolved to 5 `review-pending`, 6 `failed`, and 13 `pending`.

This task is to diagnose and reconcile the current state. It does not authorize recovery mutation.

## Objective

Produce a read-only diagnosis and recovery plan for the MinerU runtime loss and pressure-run state drift.

You must determine:

1. whether MinerU is currently down, running elsewhere, or hidden behind a different ownership mechanism;
2. what process/session/launchd/script is supposed to own MinerU in this production environment;
3. what happened to the 24 pressure-run tasks after the TestAcceptanceEngineer final snapshot;
4. which tasks are completed, failed retry candidates, pending, or internally inconsistent;
5. whether recovery can be scoped to MinerU-only restart/relaunch, or whether worker/DB state reconciliation is also required;
6. what exact user/Director approval would be required before any mutating recovery.

## Allowed Operations

Read-only operations only:

- `git status`, `git rev-parse`, `git log`;
- read production git status and local dirty-file summary;
- read-only HTTP checks against upload, DB, dependency-health with `mineruSubmitProbe=false`, admission circuit, active-task diagnostics, tasks/materials/ai jobs;
- direct MinerU read-only health/task API attempts;
- process/listener/session inventory such as `lsof`, `ps`, `pgrep`, `tmux list-sessions`, `launchctl list | grep -i mineru`, and read-only log tails;
- read-only Docker status such as `docker compose ps`;
- read-only inspection of scripts/docs that define MinerU ownership.

## Forbidden Operations

Do not:

- start, stop, restart, relaunch, kill, attach to, or mutate MinerU, upload-server, DB, MinIO, Docker, Ollama, sidecar, or supervisor;
- run manual or extra MinerU submit-probe;
- upload files;
- retry, reparse, re-AI, repair, cancel, reset, close/open circuits, or mutate tasks;
- clean DB/MinIO/Docker data;
- run `docker compose up`, `docker compose down`, `docker compose down -v`, Docker prune, or volume commands;
- mutate config, secrets, models, sample files, production source files, or runtime data;
- declare pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

If a mutating recovery appears necessary, report the exact proposed command(s), expected blast radius, and why approval is required. Do not execute them.

## Required Evidence

Your report must include:

- confirmation that it is based on this Director task brief;
- branch/HEAD in the development workspace;
- production HEAD and dirty-file summary;
- commands/endpoints run with exit codes and whether they were read-only;
- current dependency-health without submit-probe;
- current admission circuit and active-task diagnostics;
- process/listener/session/launchd evidence for MinerU ownership;
- current 24 pressure-run task counts and a table of non-terminal/failed task IDs with state/stage/retry count/material/file when available;
- log evidence around the MinerU disappearance if available;
- classification of the incident root shape:
  - service down,
  - ownership mismatch,
  - worker-state drift,
  - expected long-running parse still alive elsewhere,
  - or inconclusive;
- recommended recovery options with risk and required approval level;
- explicit statement that no forbidden operation was performed.

## Completion Report

Write:

`TaskAndReport/2026-05-15T19-29-28+0800_P0-MinerU-Runtime-Loss-And-Pressure-State-Read-Only-Diagnosis_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews diagnosis and decides whether to request user approval for scoped recovery or issue an implementation fix.
- Required Output: Director review.

Commit and push the report and ledger update to GitHub `main`.

## Acceptance Criteria

Director can accept this task only if the report gives a precise enough current-state diagnosis to decide the next recovery step without guessing.
