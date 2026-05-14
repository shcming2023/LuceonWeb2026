# Task Brief: P1 MinerU Log Observer Runtime Ownership Read-Only Recovery Plan

- Task ID: `TASK-20260514-081241-P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan`
- Issued at: 2026-05-14T08:12:41+0800
- Issued by: Director
- Assigned role: Architect
- Source decision: `TASK-20260514-080747-P1-MinerU-Log-Observer-And-Runtime-Ownership-Recovery-Decision`
- Required report: `TaskAndReport/2026-05-14T08-12-41+0800_P1-MinerU-Log-Observer-Runtime-Ownership-Read-Only-Recovery-Plan_REPORT.md`

## Objective

Produce a read-only recovery plan and preflight checklist for MinerU log observer/runtime ownership. The plan must clarify the authoritative ownership model for MinerU API, `mineru-log-observer`, `luceon-supervisor`, and Ollama before any runtime mutation is authorized.

## Context

Task 109 deployed the read-only production diagnostic endpoint `/ops/mineru/log-channel-ownership`. Production validation accepted the endpoint as live and structured, but it confirmed the remaining ownership gap:

- `summaryState=empty`;
- configured MinerU stdout/stderr log files exist and are readable but empty;
- fallback host logs are missing;
- `mineru-log-observer` sidecar is `not-observed`;
- no `mineru_api`, `luceon-mineru`, `luceon-sidecar`, or `luceon-supervisor` tmux sessions were observed;
- runtime ownership script showed two Ollama listeners (`127.0.0.1:11434` and `*:11434`);
- dependency-health remained healthy, so no runtime mutation was performed.

The User approved Option A: do a read-only recovery plan/preflight first, clarify sidecar/supervisor/MinerU/Ollama ownership and later executable commands.

## Scope

This task is read-only. Architect must inspect repository docs, scripts, task history, and current production runtime surfaces as needed, then write a plan.

Required reading:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md` if present
- `TaskAndReport/2026-05-14T08-05-08+0800_P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-And-Runtime-Validation_REPORT.md`
- `TaskAndReport/2026-05-14T08-07-47+0800_P1-MinerU-Log-Channel-Diagnostics-Production-Deployment-And-Runtime-Validation_DIRECTOR_REVIEW.md`
- `TaskAndReport/2026-05-14T08-07-47+0800_P1-MinerU-Log-Observer-And-Runtime-Ownership-Recovery-Decision_DECISION.md`

Permitted read-only runtime checks:

- `git status --short --branch`
- `git log -1 --oneline`
- `docker ps` / `docker compose ps`
- `lsof` listener inspection
- `tmux ls`
- `launchctl list | grep -i` for MinerU/Ollama/Luceon labels
- `curl` read-only endpoints through `http://localhost:8081/__proxy/upload/`
- `bash ops/runtime-ownership-status.sh`
- source/script inspection with `rg`, `sed`, `cat`, `ls`, `find`

## Required Analysis

The report must answer:

1. What should be the authoritative owner for MinerU API startup?
2. What should be the authoritative owner for `mineru-log-observer`?
3. What should be the authoritative owner for `luceon-supervisor`, if it remains part of the desired runtime model?
4. How should Ollama ownership be represented, given the observed dual listener risk?
5. Which exact commands would a later DevelopmentEngineer task run to recover or attach the sidecar/supervisor, if User approves runtime mutation?
6. Which exact preflight gates must pass before any future runtime mutation?
7. Which exact post-checks prove that `/ops/mineru/log-channel-ownership` moved from `empty/not-observed` to a better observable state?
8. What should remain explicitly forbidden in the next recovery task?

## Deliverable

Write a standalone report at the required report path. Include:

- current observed facts;
- recommended ownership contract;
- future executable command candidates;
- preflight checklist;
- post-validation checklist;
- risks and rollback/hold conditions;
- explicit forbidden operations;
- whether Architect recommends Option A planning complete, scoped runtime recovery next, or HOLD.

Update `TaskAndReport/TASK_TRACKING_LIST.md` row for this task to `已回报待 Director 审查`, `Next Actor=Director`, and link the report.

## Forbidden

- Do not start, stop, restart, kill, or reload MinerU, Ollama, MinIO, DB, Docker, upload-server, supervisor, or sidecar processes.
- Do not run `docker compose up`, `docker compose down`, Docker prune, volume operations, data cleanup, repair, reparse, re-AI, upload, pressure/batch/soak validation, or sample mutation.
- Do not change secrets, model selection, env configuration, launchd entries, tmux sessions, or production override files.
- Do not claim L3, pressure PASS, production readiness, release readiness, go-live readiness, or production上线.
