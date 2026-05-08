# Task: P0 MinerU Completed After Local Timeout Takeover Code Fix

- Task ID: `TASK-20260509-004345-P0-MinerU-Completed-After-Local-Timeout-Takeover-Code-Fix`
- Issued At: `2026-05-09T00:43:45+0800`
- Issued By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: `下达待执行`

## Background

Task 45 diagnosed a production stuck state for sample 3:

- Luceon task: `task-1778249434820`
- Material: `mat-1778249419780`
- MinerU task id: `ec9452cc-94e4-4b36-bb64-efba86f38cf6`

Read-only evidence shows MinerU completed and exposes a ZIP result, while Luceon remains `running` / `mineru-processing` with `localTimeoutOccurred=true`, material remains `processing`, and no AI metadata job exists.

This indicates a code-level terminal-state propagation / result-ingestion takeover gap after local MinerU timeout.

## Objective

Implement a safe code-level correction so a local-MinerU Luceon task that timed out locally but later reports `completed` through the MinerU API is taken over without resubmitting MinerU work:

1. detect the completed MinerU API state for an existing `mineruTaskId`,
2. transition Luceon task to `result-fetching`,
3. fetch and ingest the existing MinerU result through the normal parsed-artifact path,
4. create the downstream AI metadata job only after parsed artifacts are stored successfully,
5. preserve strict failure semantics if result fetching or ingestion fails.

## Scope

Likely relevant code area:

- `server/services/queue/task-worker.mjs`
- related queue/diagnostic smoke tests under `server/tests/`

You may adjust nearby helpers if required by the existing architecture, but keep the change narrowly scoped.

## Non-Goals

- Do not mutate production `task-1778249434820` or `mat-1778249419780`.
- Do not run production recovery.
- Do not create new production uploads.
- Do not restart, rebuild, redeploy, or mutate production services.
- Do not change model, timeout, config, secret, production override, Docker volume, DB production data, MinIO production objects, samples, or logs.
- Do not restore deprecated heuristic chapter preprocessing.
- Do not add skeleton fallback or silent degradation.
- Do not claim production release readiness.

## Acceptance Criteria

- Existing local-MinerU tasks with `localTimeoutOccurred=true` and an existing `mineruTaskId` can be reconciled when the MinerU API later reports a completed status.
- Completed takeover must not resubmit the document to MinerU.
- Completed takeover must enter the same result ingestion path as normal completed MinerU tasks.
- Parsed artifact storage and AI metadata job creation must remain ordered: no AI job before successful parsed artifact storage.
- Failed result fetch / invalid ZIP / missing result must fail explicitly or remain safely blocked with diagnostic evidence; no skeleton fallback.
- Existing failed-state correction and stale-observation behavior must not regress.
- Unit/smoke coverage must include the local-timeout-then-completed takeover case.

## Required Checks

Run at minimum:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
```

Also run the focused queue/MinerU smoke test(s) you update or add. If a full production build is reasonably available for the touched code, run:

```bash
npx pnpm@10.4.1 run build
```

Do not run production recovery or production mutation checks.

## Required Report

Create a report in `TaskAndReport/` with:

- Implementation summary.
- Files changed.
- Exact checks run and results.
- Evidence that no production recovery or mutation occurred.
- Explanation of how the takeover path avoids re-submission.
- Residual risk and whether a separate Director-authorized production recovery task is still needed for `task-1778249434820`.
