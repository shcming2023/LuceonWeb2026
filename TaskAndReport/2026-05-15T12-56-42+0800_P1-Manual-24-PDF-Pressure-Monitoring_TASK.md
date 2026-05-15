# Task: P1 Manual 24-PDF Pressure Monitoring

- Task ID: `TASK-20260515-125642-P1-Manual-24-PDF-Pressure-Monitoring`
- Assignee: `TestAcceptanceEngineer`
- Issued by: `Director`
- Issued at: 2026-05-15T12:56:42+0800
- Priority: P1
- Project: Luceon2026
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Test PDF source expected for User manual upload: `/Users/concm/prod_workspace/Luceon2026/testpdf`
- GitHub: `https://github.com/shcming2023/Luceon2026`
- Task brief: `TaskAndReport/2026-05-15T12-56-42+0800_P1-Manual-24-PDF-Pressure-Monitoring_TASK.md`
- Expected report: `TaskAndReport/2026-05-15T12-56-42+0800_P1-Manual-24-PDF-Pressure-Monitoring_REPORT.md`

## Required Reading

Before execution, read:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/test-acceptance-engineer.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- `TaskAndReport/2026-05-15T12-45-06+0800_P1-Release-Boundary-Decision-After-One-Real-PDF-Pass_DECISION.md`
- `TaskAndReport/2026-05-15T12-45-06+0800_P1-One-Real-PDF-Post-Recovery-Validation_DIRECTOR_REVIEW.md`

## Background

Task 179 proved one real PDF can complete after MinerU submit-path recovery. User then selected a stricter Option C route before any release-boundary decision.

User has now reported that they manually reset the test environment from the frontend page and cleared test materials. User will manually submit approximately 24 PDF tasks from the frontend page. This task is to monitor that manually started pressure window.

This task does not authorize TestAcceptanceEngineer to upload files, clear data, repair data, retry tasks, reparse tasks, rerun AI, reset circuits, or restart services.

## Objective

Monitor the whole manually submitted 24-PDF pressure window at a 30-minute heartbeat cadence until one of these happens:

1. all observed pressure-run tasks reach terminal states;
2. a system-level failure is confirmed;
3. the run becomes hung/unrecoverable based on repeated no-progress evidence;
4. Director or User explicitly stops the monitoring task.

The monitoring goal is not just count success/failure. It is to determine whether the system can run for a longer pressure window in a stable, observable, and operator-understandable way, and whether anomalies are handled without making the whole system impossible to judge.

## Start Condition

At the first check:

- If User has already submitted the 24 PDFs, identify the pressure-run tasks and begin monitoring immediately.
- If no pressure-run tasks are visible yet, record a waiting snapshot in the thread and continue waiting for User manual submission. Do not write a final report just because no tasks exist before User submission.
- If the environment is not clean before User submission, report the observed residuals but do not clean or mutate anything.

## Monitoring Cadence

Every 30 minutes, record a concise snapshot in the TestAcceptanceEngineer thread. Continue until terminal/failure/hung/stop condition.

Each snapshot should include:

- timestamp;
- total observed pressure-run tasks and counts by task state/stage;
- number of active/running/queued/review-pending/failed tasks;
- current active MinerU task evidence from no-submit diagnostics;
- dependency health without manual submit-probe;
- MinerU admission circuit state;
- UI `/cms/tasks` observation if accessible;
- notable MinerU log/API progress if any task appears stuck;
- notable AI/Ollama states or failures;
- whether the frontend page semantics match backend/log evidence closely enough for a human operator to understand progress.

## Required Observation Sources

Use read-only sources only. Prefer these:

- `/cms/tasks` page observation, including visible state/progress/message semantics;
- `GET /__proxy/upload/health`;
- `GET /__proxy/upload/ops/dependency-health?mineruSubmitProbe=false`;
- `GET /__proxy/upload/ops/mineru/admission-circuit`;
- `GET /__proxy/upload/ops/mineru/active-task`;
- `GET /__proxy/db/tasks`;
- `GET /__proxy/db/materials`;
- `GET /__proxy/db/task-events`;
- `GET /__proxy/db/ai-metadata-jobs`;
- direct MinerU `/tasks/{mineruTaskId}` for tasks already accepted by MinerU, when the ID is available;
- production logs only for read-only progress attribution when needed.

Do not run manual MinerU submit-probe. The only acceptable submit-probe side effect in this validation is the normal upload-path admission behavior triggered by User's manual uploads.

## Special Evaluation Rules

- Do not count a few `failed/ai` outcomes as a system-level pressure failure by default. Record them as AI-stage failures and note whether the rest of the system continues processing and leaves them as visible manual retry candidates.
- Do not mark a MinerU task as hung only because one UI message appears stale. Compare UI, backend task state, direct MinerU task API, and logs. If logs/API show new progress, record "still progressing" and keep monitoring.
- A task may be considered possibly hung only after at least two consecutive 30-minute snapshots show no meaningful progress across UI/backend/direct MinerU/log evidence.
- A system-level failure includes service unreachable, DB/proxy outage that prevents observation, admission circuit open blocking new intake after the manual run, MinerU submit/processing path repeatedly failing at system level, or queue/worker state becoming impossible to interpret.
- The final report must separate:
  - overall pressure-run outcome;
  - task-level parse/MinerU outcomes;
  - task-level AI/Ollama outcomes;
  - UI/progress/log semantic correctness;
  - dependency health stability;
  - residual retry candidates;
  - any recommended next engineering task.

## Forbidden Operations

Do not:

- upload files;
- run another reset/cleanup;
- delete DB/MinIO/Docker data;
- run `docker compose down`, `docker compose down -v`, Docker prune, or Docker volume cleanup;
- restart, stop, kill, relaunch, rebuild, or redeploy services;
- run manual or extra MinerU submit-probe;
- manually close/open/reset admission circuits;
- retry, repair, reparse, rerun AI, cancel, or mutate tasks;
- mutate `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- mutate config, secrets, models, Ollama, MinerU configuration, Docker volumes, DB volumes, or MinIO volumes;
- claim pressure PASS, L3, release readiness, production readiness, production上线, or go-live.

If a destructive or mutating action appears necessary, stop and report a blocked recommendation to Director.

## Required Final Report

When the run reaches a stop condition, write:

`TaskAndReport/2026-05-15T12-56-42+0800_P1-Manual-24-PDF-Pressure-Monitoring_REPORT.md`

The report must include:

- confirmation that work was based on this Director task brief;
- branch and HEAD;
- production HEAD and production dirty-file summary;
- commands/endpoints used and whether they were read-only;
- User manual reset note;
- observed pressure-run task IDs/material IDs if available;
- per-snapshot timeline at 30-minute cadence;
- final task/material/AI counts by state;
- representative examples of successful large/small files if file names are visible;
- all failed tasks with stage, reason, and retry-candidate classification;
- MinerU progress-semantics findings, especially any mismatch between UI wording and backend/direct log progress;
- Ollama/AI findings;
- dependency-health/admission/active-task findings;
- whether the system stayed observable and operator-understandable under pressure;
- blockers, residual risks, and recommended next task(s);
- explicit statement that no upload/cleanup/retry/reparse/re-AI/service restart/submit-probe/destructive operation was performed by TestAcceptanceEngineer.

## Task Ledger Update

After writing the report, update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查`
- Next Actor: `Director`
- Next Action: Director reviews the pressure monitoring report and decides whether to accept evidence, issue engineering follow-up, request more validation, or ask User for a release-boundary decision.
- Required Output: Director review.

Commit and push the report and ledger update to GitHub `main`, unless the development workspace has unrelated dirty changes. If dirty, use a clean temporary clone/worktree and state that in the report.

## Acceptance Criteria

Director can accept this task only if the report provides enough evidence to judge:

- whether the 24-PDF run reached terminal completion, partial completion, system failure, or hung state;
- whether the system remained observable for a human operator during long-running MinerU/AI work;
- whether exceptions were isolated and visible rather than collapsing the whole run;
- whether additional engineering is required before any release-boundary decision.
