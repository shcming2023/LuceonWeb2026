# Lucode Task: P0 Bounded 24 PDF Pressure Restart Under Entry Circuit

- Task ID: `TASK-20260510-155451-P0-Bounded-24-PDF-Pressure-Restart-Under-Entry-Circuit`
- Created At: `2026-05-10T15:54:51+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 下达待执行
- Director Authorization: `TASK-20260510-155052-P0-Next-Validation-Step-After-Entry-Circuit-Deployment`
- Basis: Task 73 accepted the deployed durable admission circuit and non-destructive runtime surfaces.

## Objective

Run exactly one bounded restart of the previously failed 24-PDF pressure-validation track under the deployed durable MinerU admission circuit.

This task tests whether the new entry circuit prevents uncontrolled intake when the local production line becomes unable to accept MinerU submissions. It does not establish production release readiness by itself.

## Exact Scope

- Maximum sample count: `24` PDFs.
- Use the same pressure-validation set referenced by `TASK-20260510-074514-P0-24-PDF-Pressure-Test-Failure-Field-Report`.
- If the exact same 24-PDF set cannot be identified from prior evidence, stop and write a blocked report. Do not substitute other samples.
- One run only. Do not retry failed uploads, failed tasks, or failed stages in this task.
- Keep the external sample library read-only if inspected. Do not copy samples into the repo and do not mutate, rename, move, delete, normalize, or pollute samples.

## Required Preflight

Before creating any upload, collect and report:

- development `main` HEAD and `origin/main`;
- production deployed HEAD;
- production override summary, preserving strict AI/model and MinIO console local-only settings;
- `GET /__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`;
- `GET /__proxy/upload/ops/mineru/admission-circuit`;
- `GET /__proxy/upload/ops/mineru/active-task`;
- Ollama `/api/ps`;
- active parse/AI counts.

Preflight must pass before the run starts:

- dependency health `blocking=false`;
- MinerU submit probe HTTP `202`;
- admission circuit `open=false`;
- active parse and AI running counts are `0`;
- no takeover-required task is present.

## Stop Rules

Stop creating new uploads immediately and write a report if any of these occurs:

- dependency health becomes blocking;
- admission circuit opens;
- any upload returns HTTP `503` or `MINERU_ADMISSION_CIRCUIT_OPEN`;
- MinerU submit probe fails or times out;
- active MinerU heavy-stage count exceeds `1`;
- active Ollama/AI metadata heavy-stage count exceeds `1`;
- production service becomes unreachable;
- any operation would require failed-task repair, DB/MinIO/Docker volume mutation, secret/model/config/override mutation, broad restart, rollback, or cleanup.

Do not repair, retry, delete, or manually mutate prior failed tasks. Do not close or alter historical failed tasks.

## Pass / Fail Boundary

This task may report only one of these bounded outcomes:

- `PRESSURE_RESTART_PASS_CANDIDATE`: all 24 intended PDFs were accepted through intake without admission-circuit opening, heavy stages stayed within limits, and all created tasks reached `review-pending` or `completed` without skeleton fallback or silent degradation.
- `PRESSURE_RESTART_BLOCKED_BY_ADMISSION`: the durable admission circuit or submit-probe correctly stopped intake; this is useful circuit evidence but not pressure PASS.
- `PRESSURE_RESTART_FAILED`: any created task failed at upload, MinerU, parsed artifact, or AI metadata stage, or the run violated stop rules.
- `PRESSURE_RESTART_INCONCLUSIVE`: the exact 24-PDF set could not be identified, evidence was incomplete, or runtime observation could not safely continue without forbidden action.

Do not claim L3, full-site acceptance, production release readiness, manual pressure-test readiness, or final release readiness.

## Required Evidence

The report must include:

- exact sample identity list for the 24 PDFs, including source paths or prior task/material IDs where available;
- per-sample upload/task/material IDs for newly created validation artifacts;
- per-sample final state, stage, and AI job state;
- admission-circuit state before, during, and after the run;
- dependency-health submit-probe evidence before and after the run, and at the first stop condition if stopped;
- active-task/queue snapshots showing heavy-stage counts;
- Ollama `/api/ps` before and after;
- explicit list of skipped/forbidden actions.

## Forbidden Scope

- No production release-readiness declaration.
- No L3/full-site acceptance or manual pressure-test readiness declaration.
- No failed-task repair, retry, deletion, closure, or cleanup.
- No DB row deletion, MinIO object deletion, Docker volume deletion/pruning.
- No secret/model/timeout/config/override mutation.
- No broad stack restart, rollback, or unrelated recovery.
- No sample-library mutation, sync, copy into repo, deletion, rename, or pollution.
- No skeleton fallback or silent degradation.

## Required Report

Create:

`TaskAndReport/2026-05-10T15-54-51+0800_P0-Bounded-24-PDF-Pressure-Restart-Under-Entry-Circuit_REPORT.md`
