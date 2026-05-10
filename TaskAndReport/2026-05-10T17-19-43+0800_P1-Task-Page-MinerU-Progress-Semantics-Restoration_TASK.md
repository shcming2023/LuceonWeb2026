# Lucode Task: P1 Task Page MinerU Progress Semantics Restoration

- Task ID: `TASK-20260510-171943-P1-Task-Page-MinerU-Progress-Semantics-Restoration`
- Created At: `2026-05-10T17:19:43+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P1
- Status: 下达待执行
- Basis: Task 76 accepted as observation timeout with an operator-facing MinerU progress observability gap.

## Objective

Restore task-page and API-facing MinerU progress semantics so Director/operator can judge whether a long-running local MinerU parse is advancing, stale, blocked, or unobservable without shell access to native MinerU logs.

This task addresses a local long-running production-line governance gap. It is not a pressure-test restart and not a release-readiness task.

## Problem Statement

During Task 76, the native MinerU logs showed real progress on a 632-page PDF:

- backend `pipeline`;
- processing-window run with total pages and total batches;
- batch/page-window progress such as batch `2/10` and `128/632` pages;
- runtime phases such as OCR detection and OCR recognition;
- slow phase progress that distinguishes "still working slowly" from "dead".

The task page and API-facing task state still exposed only generic semantics:

- `MinerU 正在解析`;
- `50%`;
- no useful phase/batch/page/log freshness signal.

Director specifically noted that an earlier system made MinerU log output visible on the task page with corresponding semantics. That capability is required for production-line observability.

## Required Scope

Implement the smallest maintainable code change that exposes meaningful MinerU progress semantics for local MinerU tasks, preferably reusing existing observer/log parsing structures where available.

Required operator-facing semantics:

- current MinerU backend when known, such as `pipeline`;
- current phase when known, such as `MFR Predict`, `Table-ocr`, `OCR-det`, `OCR-rec`, artifact packaging, or equivalent normalized labels;
- current processing window or batch when known, such as `batch 2/10`;
- page progress when known, such as `128/632 pages`;
- last observed MinerU progress/log timestamp;
- freshness status: live/recent, stale, missing, timed out, or query-timeout;
- a concise Chinese task-page message that distinguishes:
  - waiting for MinerU;
  - submitted to MinerU;
  - MinerU processing and making observable progress;
  - MinerU processing but progress stale/unobservable;
  - MinerU submit/admission blocked;
  - parsed artifact sync / AI metadata pending if those states already exist.

Required technical behavior:

- Preserve existing strict no-skeleton AI behavior.
- Preserve durable admission-circuit behavior.
- Preserve single local MinerU heavy-stage queue assumptions.
- Do not treat `/health` alone as proof of intake readiness.
- Do not mark a task failed only because progress observation is missing or stale.
- Do not mutate terminal tasks merely because a later global log line is observed.
- Avoid exposing secrets, tokens, private host paths, or excessive raw logs in the UI.
- Prefer bounded summarized log/progress events over unbounded raw log streaming.

## Forbidden Scope

- Do not create any new upload.
- Do not retry sample 21 or attempt samples 22-24.
- Do not repair, retry, delete, close, or mutate the Task 75/76 pressure tasks.
- Do not run a pressure test.
- Do not change production DB rows, MinIO objects, Docker volumes, sample files, logs, secrets, models, timeouts, production override, or service ownership.
- Do not run broad production restart/rebuild/rollback.
- Do not declare production release readiness, L3/full-site acceptance, manual pressure-test readiness, or pressure PASS.
- Do not restore deprecated heuristic chapter preprocessing.

## Required Checks

Run the checks appropriate to the changed surface and report exact output:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Add or update focused smoke/unit coverage for MinerU progress/log semantic extraction and task/API/UI mapping. If existing tests cover this area, extend them rather than duplicating broad fixtures.

Suggested additional checks if relevant:

```bash
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-diagnostics-smoke.mjs
node server/tests/mineru-submit-circuit-breaker-smoke.mjs
```

## Required Report

Create:

`TaskAndReport/2026-05-10T17-19-43+0800_P1-Task-Page-MinerU-Progress-Semantics-Restoration_REPORT.md`

The report must include:

- implementation branch and HEAD;
- changed files;
- exact semantics added to API/task page;
- before/after examples using safe non-secret sample log lines or fixtures;
- test commands and exact results;
- confirmation that no production upload, pressure retry, data cleanup, runtime config mutation, or release-readiness claim occurred;
- residual gaps if any MinerU phases remain unparsed or UI-only validation remains pending.

