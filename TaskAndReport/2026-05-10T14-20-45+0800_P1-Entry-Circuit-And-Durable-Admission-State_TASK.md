# Lucode Task: P1 Entry Circuit And Durable Admission State

- Task ID: `TASK-20260510-142045-P1-Entry-Circuit-And-Durable-Admission-State`
- Created At: `2026-05-10T14:20:45+0800`
- Created By: Lucia
- Next Actor: Lucia until Task 69 is accepted; then Lucode
- Priority: P1
- Status: 挂起
- Related P0 Task: `TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_TASK.md`

## Activation Rule

This task is intentionally created now but must not be executed by Lucode until Task 69 is completed and accepted by Lucia.

P1 depends on P0 because admission control must read a unified runtime ownership and endpoint contract, not ambiguous DB/runtime state.

## Objective

Promote MinerU submit-probe from a diagnostic tool into a shared admission-control fact used by frontend, `POST /tasks`, worker, and ops surfaces.

The first version should stop intake when the local production line is not truly able to accept MinerU submissions.

## Required Behavior

Create a durable MinerU circuit state that can be read consistently by:

- frontend upload/task UI;
- `POST /tasks` or upload intake path;
- MinerU parse worker;
- ops/health or queue-pressure surface;
- Lucia/Lucode evidence collection.

Circuit open triggers must include:

- MinerU `/tasks` HTTP 5xx;
- submit timeout;
- `ECONNREFUSED` or equivalent connection failure;
- repeated submit-probe failure as appropriate.

Circuit close/recovery must require all of:

- submit-probe returns HTTP `202`;
- a cooldown window has elapsed;
- active-task diagnostics are clean enough for intake;
- no current dependency-health blocking condition.

Do not close the circuit based only on MinerU `/health` HTTP 200.

## First-Version Intake Policy

When the circuit is open, pause the upload/intake entry and return a clear operator-facing message:

`MinerU 当前不可接收新任务，文件未收取，请稍后重试。`

Do not promise that the file has been retained or that parsing will happen later unless a durable intake queue exists and is explicitly implemented and verified.

## Required Observability

Add or prepare shared circuit-state evidence so later P2 queue-pressure work can display:

- circuit state;
- reason;
- last submit-probe result;
- last successful submit time;
- cooldown until;
- current parse pending/running counts if readily available;
- current AI pending/running counts if readily available.

## Required Checks

- `git diff --check`;
- focused smoke tests for circuit open/close behavior;
- focused tests proving `/health` 200 alone does not close the circuit;
- `npx pnpm@10.4.1 exec tsc --noEmit`;
- `npx pnpm@10.4.1 run build`;
- if deployed for validation later, production evidence must include GitHub HEAD, production override summary, dependency-health submit-probe, circuit state, queue state, Ollama `/api/ps`, and task success/failure boundary.

## Forbidden Scope

- Do not add another worker lock as the main solution.
- Do not introduce silent fallback.
- Do not claim skeleton fallback as AI recognition.
- Do not add a durable intake queue unless explicitly scoped and verified.
- Do not mutate production DB/MinIO/Docker volumes/secrets/samples.
- Do not run pressure tests in this task unless Lucia separately activates a validation task after P1 acceptance.
- Do not claim L3, production release readiness, or full-site acceptance.

## Required Report

Create:

`TaskAndReport/2026-05-10T14-20-45+0800_P1-Entry-Circuit-And-Durable-Admission-State_REPORT.md`

Report must include:

- files changed;
- circuit state model;
- trigger/close rules;
- frontend/intake behavior;
- ops evidence path;
- test evidence;
- what remains for P2 queue-pressure and P3 Ollama stability.

