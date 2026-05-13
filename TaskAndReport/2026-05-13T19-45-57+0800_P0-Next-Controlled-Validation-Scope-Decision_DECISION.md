# TASK-20260513-194557-P0-Next-Controlled-Validation-Scope-Decision

- Role: User decision requested by Director
- Created: 2026-05-13T19:45:57+0800
- Trigger: Task 98 accepted as exactly-one controlled upload validation boundary PASS.
- Current production HEAD: `de2d23f`
- Current known successful validation task: `task-1778672291622`

## Current Facts

Task 98 confirms that the latest production path can complete one controlled PDF upload through MinerU parsing, MinIO artifacts, Ollama AI metadata, deterministic AI JSON repair, and the safe `review-pending` human-review terminal state.

This is meaningful progress, but it is still only one sample. It does not prove pressure, long-run stability, batch behavior, L3, release readiness, or production go-live readiness.

The main residual issue is MinerU operator observability: fast-complete tasks can still show diagnostic-only progress and transient false failed/corrected events caused by unreadable or empty log observation. The final state self-corrects, but the task history can confuse monitoring.

## Decision Needed

Choose the next validation direction.

## Options

### Option A: Recommended - small stage-queued validation

Authorize TestAcceptanceEngineer to perform a scoped, non-pressure validation using up to three PDFs from:

`/Users/concm/prod_workspace/Luceon2026/testpdf`

Boundaries:

- enumerate available PDFs first and record names, sizes, and hashes;
- upload one PDF at a time only;
- wait for terminal state before the next upload;
- stop immediately on the first systemic failure or dependency-blocking signal;
- verify task page semantics, DB/API terminal state, AI job state, active-task state, and admission circuit after each sample;
- do not repair historical failed tasks;
- do not run pressure, batch-concurrent, soak, cleanup, destructive data/volume commands, model operations, restart, rebuild, or release-readiness claims.

Reason: this is the smallest useful step from "one known sample works" toward "the line can repeat safely" without pretending to be a pressure test.

### Option B: Fix MinerU progress observability first

Authorize DevelopmentEngineer to focus on the remaining transient false failed/corrected MinerU progress events and log-source observability before any new validation uploads.

Reason: this reduces operator confusion before collecting more runtime evidence.

Risk: this delays proof that the complete upload-to-review path repeats across more than one sample.

### Option C: Hold

Do not authorize new uploads or code work yet.

Reason: safest in the narrow sense.

Risk: project remains at single-sample evidence and cannot move closer to production readiness.

## Director Recommendation

Choose Option A, while keeping the MinerU observability issue explicitly recorded as P1 residual debt. If Option A exposes repeated confusing task-page behavior or new false failures, stop the validation and route the next task to DevelopmentEngineer for the observability fix.

This recommendation does not authorize production readiness, L3, pressure PASS, release readiness, destructive mutation, model changes, failed-task repair, or broad restarts.

## Heartbeat Auto-Advance Boundary

If this same decision remains unanswered for two consecutive Director heartbeat wakeups, Director may apply the recommendation conservatively by creating a scoped TestAcceptanceEngineer task for Option A only after confirming that active parse/AI queues are clean and the admission circuit is closed.

Auto-advance still may not declare production readiness, L3, pressure PASS, release readiness, destructive mutation, model changes, failed-task repair, cleanup, broad restart, or sample mutation.

## User Decision

At 2026-05-13T19:50:02+0800, the user approved Option A:

> 同意Option A：从 /Users/concm/prod_workspace/Luceon2026/testpdf 做最多 3 个 PDF 的“小样本串行验证”，一次一个、终态后再下一个，遇到系统性失败立刻停，不做压力、不做清理、不声明上线。

## Director Interpretation

The approval authorizes one scoped TestAcceptanceEngineer validation task:

- source folder: `/Users/concm/prod_workspace/Luceon2026/testpdf`;
- sample count: up to 3 PDFs;
- execution mode: strictly serial, one upload at a time, next upload only after the previous task reaches terminal state;
- stop condition: stop immediately on dependency-blocking signal, admission-circuit open state, upload failure, terminal failed state, unresolved active-task drift, or other systemic failure evidence;
- output: a `TaskAndReport/*_REPORT.md` plus tracking-list update for Director review.

Explicitly not authorized: pressure, batch-concurrent, soak, cleanup, failed-task repair, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, sample mutation, model operation, service restart/rebuild, L3, production-readiness, release-readiness, or go-live declaration.

Task 100 is issued to TestAcceptanceEngineer under this boundary.
