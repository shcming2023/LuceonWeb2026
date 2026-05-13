# DevelopmentEngineer Report: P0 AI Metadata Single Pass Finalization Guard

- Task: `TASK-20260513-151715-P0-AI-Metadata-Single-Pass-Finalization-Guard`
- Task brief: `TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_TASK.md`
- Role: DevelopmentEngineer
- Report time: 2026-05-13T15:26:58+0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Root Cause Found

Confirmed the Director-suspected duplicate-processing path in `server/services/ai/metadata-worker.mjs`.

`scanAndProcess()` read an initial `jobs` snapshot, recovered stale running jobs, then read `postRecoveryJobs` and immediately processed the first recovered/pending job. After that processing returned, the function continued and reused the original pre-recovery `jobs` snapshot to find pending jobs. If the same job was present as pending in both snapshots, the worker could process it twice in one scan cycle.

That can explain the Task 90 trace where AI job `ai-job-1778655391785-6d94` recorded an Ollama response success and JSON repair success, then later another Ollama/repair pass ended in failure and overwrote the terminal state.

## Files Changed

- `server/services/ai/metadata-worker.mjs`
- `server/tests/ai-metadata-single-pass-guard-smoke.mjs`
- `TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

- Added a `return` immediately after processing a recovered/pending job, preserving the worker's existing "one job per tick" contract and preventing reuse of the stale pre-recovery snapshot.
- Added a start-of-`processJob()` latest-state guard using `getJobById(job.id)`.
- The guard skips only when the latest known state is explicitly present and not `pending`, preserving compatibility with existing focused tests that call `processJob()` with minimal mock jobs.
- Added focused regression coverage proving:
  - a job present in both the post-recovery snapshot and stale original snapshot is processed once;
  - a stale pending input is skipped when the latest DB state is already terminal `review-pending`.

## Strict No-Skeleton Preservation

Strict no-skeleton behavior was not weakened.

The change only gates duplicate job execution and stale terminal re-entry. It does not change provider selection, prompts, taxonomy, JSON repair semantics, strict failure behavior, `degradeToSkeleton()`, or the strict-mode guard that throws when skeleton fallback would be used.

## Commands Run And Exit Codes

- `git status --short --branch` -> exit 0
- `rg -n "\| [0-9]+ \|.*\| (下达待执行|执行中|退回待修正|修正中) \| DevelopmentEngineer \|" TaskAndReport/TASK_TRACKING_LIST.md` -> exit 0
- `node --check server/services/ai/metadata-worker.mjs` -> exit 0
- `node --check server/tests/ai-metadata-single-pass-guard-smoke.mjs` -> exit 0
- `node server/tests/ai-metadata-single-pass-guard-smoke.mjs` -> exit 0; output included `AI metadata single-pass guard smoke passed`
- `git diff --check` -> exit 0
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> first run exit 1 after the initial guard skipped old mock jobs without `state`; this exposed a compatibility bug in the first patch
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> rerun exit 0; output ended `--- AI Metadata Real Sample Smoke Test Success ---`
- `node server/tests/dependency-health-smoke.mjs` -> exit 0; `65 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit 0
- `npx pnpm@10.4.1 run build` -> exit 0; Vite built successfully with the existing chunk-size warning
- `git log -1 --oneline` -> exit 0; pre-report HEAD observed as `1f40dae Review controlled upload validation failures`

## Skipped Checks And Reasons

- No production deployment: explicitly forbidden by the task brief.
- No validation upload: explicitly forbidden by the task brief.
- No pressure test: explicitly forbidden by the task brief.
- No failed-task repair/reparse/re-AI/cleanup: explicitly forbidden by the task brief.
- No DB/MinIO/Docker volume/model/sample mutation: explicitly forbidden by the task brief.

## Evidence

Focused regression test evidence:

```text
[ai-worker] Picking recovered job: ai-job-duplicate-guard
[ai-worker] Skipping job ai-job-duplicate-guard: latest state is review-pending
AI metadata single-pass guard smoke passed
```

Existing smoke evidence:

```text
--- AI Metadata Real Sample Smoke Test Success ---
Results: 65 passed, 0 failed
✓ built in 1.48s
```

The focused test would have failed before the `scanAndProcess()` early return because the same job would be processed once from `postRecoveryJobs`, then again from the stale original `jobs` snapshot.

## Residual Risk

- This is code/test-level evidence only. It has not been deployed to production.
- The patch prevents duplicate processing within this worker path, but it does not claim to solve every possible external duplicate worker/process deployment scenario.
- Task 90's historical failed job was not repaired or retried.

## Recommendation

Director should review this implementation/report. If accepted, Director may authorize a separate production deployment/runtime validation task before any additional upload validation.

No production readiness, L3, pressure PASS, or release-readiness is claimed.
