# Task: P0 Controlled Live Task Progress Semantics Validation

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
TaskAndReport/2026-05-13T13-18-55+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation_TASK.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/test-acceptance-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T12-57-08+0800_P0-Post-Sync-Production-Fast-Forward-And-Runtime-Validation_DIRECTOR_REVIEW.md
- TaskAndReport/2026-05-13T12-57-08+0800_P0-Live-Task-Progress-Semantics-Validation-Authorization_DECISION.md

## Background

Task 83 accepted the production fast-forward and non-destructive runtime-surface validation. Production is at accepted code path `301e4da` or later, runtime health surfaces passed, and strict local runtime boundaries were preserved.

Residual gap: current production task data had no populated `progressSemantics`, so task-page MinerU progress semantics were deployed but not observed on a live/current task.

The user approved Option A on 2026-05-13: "只做一次小样本上传，专门观察任务页进度语义和终态，不碰压力测试和上线声明。"

## Objective

Perform exactly one controlled small/medium sample upload in production, then observe whether the task page/API surfaces live MinerU progress semantics and a clear terminal or ongoing state.

This is a validation task, not a release-readiness task.

## Non-Goals

- Do not run a pressure test.
- Do not retry the 24-PDF pressure track.
- Do not perform multiple uploads.
- Do not repair, retry, clean up, or mutate failed historical tasks.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.
- Do not change code, production config, models, secrets, DB schema, MinIO objects, Docker volumes, or sample-library files.

## Allowed Inputs

Use exactly one small/medium PDF sample.

Preferred input source:

- Read-only external sample library:
  `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Selection rule:

- Choose one PDF that is small/medium, likely to parse within a short observation window, and likely to emit MinerU progress logs.
- Record original absolute path, file size, and hash.
- Do not copy the sample into the repository.
- Do not move, rename, edit, normalize, or delete any sample-library file.

If no suitable sample is safely identifiable within the observation time, stop and write a blocked report rather than inventing a test input.

## Required Preflight

Before upload, in production deployment path:

```bash
git status --short --branch
git log -1 --oneline
docker compose ps
curl -fsS http://localhost:8081/__proxy/upload/health
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
curl -sS --max-time 10 http://127.0.0.1:11434/api/ps
```

Preflight must show:

- upload health OK;
- dependency-health `ok=true` and `blocking=false`;
- MinerU admission circuit closed;
- no active/queued Luceon parse task;
- no active/queued Luceon AI task;
- Ollama `qwen3.5:9b` resident or otherwise ready.

If preflight fails, do not upload; write a blocked report.

## Allowed Runtime Action

Exactly one controlled upload through the current production app/API is allowed after preflight passes.

Allowed upload surfaces:

- CMS production route at `http://localhost:8081/cms/tasks`, or
- the production upload API used by the current app if browser automation is not practical.

After upload:

- record task ID and material ID;
- observe task detail page and/or API state;
- capture whether `mineruObservedProgress.progressSemantics` appears;
- capture the user-facing task progress message text;
- observe terminal state or a bounded ongoing state.

Suggested observation window:

- Up to 20 minutes total.
- Poll at reasonable intervals.
- Stop earlier if the task reaches a terminal state (`review-pending`, `completed`, or `failed`) and evidence is sufficient.

If the task is still running at the observation limit, do not repair or retry. Record the latest state, progress semantics, and whether the observation is inconclusive.

## Forbidden Changes

- Do not create more than one upload.
- Do not run batch upload, pressure test, stress test, concurrency test, or 24-PDF retry.
- Do not repair failed tasks or historical tasks.
- Do not reparse or rerun existing tasks.
- Do not delete, prune, recreate, or mutate DB, MinIO, Docker volumes, task rows, artifacts, logs, or sample-library files.
- Do not run `docker compose down -v`, `docker volume rm`, `docker system prune`, or equivalent destructive commands.
- Do not restart MinerU, Ollama, MinIO, or DB.
- Do not pull, delete, reload, replace, or change models.
- Do not change secrets, production overrides, timeout policy, provider configuration, PRD truth, role contracts, project state, or public APIs.
- Do not claim production release readiness, L3, pressure PASS, or full acceptance.

## Required Evidence

Report must include:

- confirmation that work was based on this Director task brief;
- production HEAD and local override status;
- selected sample path, file size, and hash;
- preflight command results and exit codes;
- upload command/browser action and result;
- task ID and material ID;
- task state timeline;
- task-page/API evidence for `progressSemantics`;
- user-facing progress message evidence;
- final or latest observed terminal/ongoing state;
- checks skipped and reasons;
- all forbidden actions that were not performed;
- risks, blockers, residual gaps, and recommendation to Director.

## GitHub Sync Requirements

- Do not push to GitHub from this task.
- If only the report and tracking list are changed, leave final repository synchronization to Director unless the role contract or Director explicitly instructs otherwise.

## Completion Report Storage Requirements

- Write the completion report into `TaskAndReport/` using this naming rule:
  `2026-05-13T13-18-55+0800_P0-Controlled-Live-Task-Progress-Semantics-Validation_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, environment evidence, status, `Next Actor=Director`, next action, and required output.

## Acceptance Criteria

- Exactly one controlled upload is performed only after preflight passes.
- Task-page/API progress semantics and terminal/ongoing state are reported with evidence.
- The task remains scoped and does not become pressure testing, failed-task repair, cleanup, L3, or release-readiness declaration.
