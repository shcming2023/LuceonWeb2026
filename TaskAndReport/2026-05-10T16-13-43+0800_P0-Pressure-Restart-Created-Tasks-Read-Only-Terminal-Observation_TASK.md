# Lucode Task: P0 Pressure Restart Created Tasks Read-Only Terminal Observation

- Task ID: `TASK-20260510-161343-P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation`
- Created At: `2026-05-10T16:13:43+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 下达待执行
- Basis: Task 75 accepted as inconclusive with 20 created production validation tasks still non-terminal.

## Objective

Observe only the 20 production validation tasks created by Task 75 until they reach terminal/manual-review state or until a bounded observation timeout is reached.

This task must not create new uploads, retry sample 21, attempt samples 22-24, repair failed tasks, clean data, or mutate production runtime.

## Target Task IDs

Observe only these Task 75 created task IDs:

- `task-1778400448971`
- `task-1778400452107`
- `task-1778400454526`
- `task-1778400456661`
- `task-1778400460190`
- `task-1778400468632`
- `task-1778400473241`
- `task-1778400478684`
- `task-1778400481740`
- `task-1778400487246`
- `task-1778400490743`
- `task-1778400493794`
- `task-1778400498868`
- `task-1778400501915`
- `task-1778400507058`
- `task-1778400513155`
- `task-1778400516082`
- `task-1778400518537`
- `task-1778400521108`
- `task-1778400526749`

## Required Observation

Use read-only runtime and DB/API endpoints to collect:

- per-task final or latest state/stage/message;
- material state for each target material;
- AI metadata job state if created;
- parsed artifact presence if MinerU completed;
- admission-circuit state;
- dependency-health with `mineruSubmitProbe=true`;
- active-task/queue state;
- Ollama `/api/ps`.

## Stop / Report Conditions

Report when one of these occurs:

- all 20 target tasks reach `review-pending`, `completed`, `failed`, or another terminal/manual-review state;
- any target task becomes blocked in a way that requires Director/Lucia decision;
- observation reaches 60 minutes from task start;
- dependency-health becomes blocking or admission circuit opens.

## Forbidden Scope

- Do not create any new upload.
- Do not retry sample 21 or attempt samples 22-24.
- Do not repair, retry, delete, close, or mutate failed tasks.
- Do not delete DB rows, MinIO objects, Docker volumes, logs, samples, or artifacts.
- Do not mutate secrets, models, timeouts, config, override, strict AI flags, or MinIO binding.
- Do not run pressure tests or broad restarts.
- Do not claim pressure PASS, production release readiness, L3, full-site acceptance, or manual pressure-test readiness.

## Required Report

Create:

`TaskAndReport/2026-05-10T16-13-43+0800_P0-Pressure-Restart-Created-Tasks-Read-Only-Terminal-Observation_REPORT.md`

The report must classify the observed result as one of:

- `CREATED_TASKS_TERMINAL_OBSERVED`
- `CREATED_TASKS_RUNTIME_BLOCKED`
- `CREATED_TASKS_OBSERVATION_TIMEOUT`
- `CREATED_TASKS_INCONCLUSIVE`
