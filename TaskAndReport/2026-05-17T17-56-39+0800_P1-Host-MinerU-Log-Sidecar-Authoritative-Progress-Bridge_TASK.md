# Task: P1 Host MinerU Log Sidecar Authoritative Progress Bridge

## Context

This task follows the 2026-05-17 stuck MinerU regression diagnosis and is code/test level only.

Observed facts:

- A real PDF task stalled in MinerU pipeline at `Table-ocr rec ch: 0/2`.
- Direct host log inspection of `/Users/concm/ops/logs/mineru-api.err.log` showed newer business progress than `cms-upload-server` could see through `/host/mineru-logs/mineru-api.err.log`.
- Host file stat and container file stat diverged:
  - host stderr log size was larger and mtime was later;
  - container-mounted stderr log was stale.
- `/ops/mineru/global-observation` was empty during the incident, indicating the host observer sidecar was not providing authoritative current task progress to Luceon.
- Existing code already contains `ops/mineru-log-observer.mjs` and `/ops/mineru-log-observation`, but the production behavior still depends too much on container-mounted logs and does not make sidecar freshness/absence an explicit operator state.

Milestone comparison:

- `v6.9` did not change the MinerU submit options that produced this run.
- The long-standing residual from Task 205/206 was log-channel ownership/freshness. Task 206 was canceled as not blocking 6.9.1, but the current incident shows it must now be fixed before further long-run validation.

## Role

Next Actor: `Lucode`

Lucode must implement code and tests only. Lucode must not perform production restart, deployment, upload, data cleanup, or runtime recovery.

## Objective

Make host-side MinerU log observation the authoritative progress source for operator-facing live progress, so Luceon no longer depends on Docker Desktop bind-mount freshness for realtime MinerU business logs.

This task should improve observability and state semantics. It must not change MinerU parsing results, AI recognition semantics, or strict no-skeleton policy.

## Required Design Direction

Implement a focused sidecar-first progress architecture:

1. Host observer ownership:
   - Treat `ops/mineru-log-observer.mjs` as the host-side reader of `/Users/concm/ops/logs/mineru-api.log` and `.err.log`.
   - Ensure its emitted snapshot clearly includes `observer`, `sourceContext=host-filesystem`, host log path, size, mtime, activity level, phase, page/window/stage data, and freshness.
2. Upload-server ingestion:
   - Keep `/ops/mineru-log-observation` as the ingestion point or replace it with a compatible narrow route if justified.
   - Persist sidecar-attributed snapshots to active task metadata when there is exactly one attributable active task.
   - Do not allow a stale container-mounted parser result to overwrite a fresher host-side sidecar snapshot.
3. Runtime truth semantics:
   - Add or harden an explicit state for `sidecar_missing`, `sidecar_stale`, `sidecar_fresh`, and `container_mount_stale`.
   - Operator-facing task status should say that log observation is missing/stale when the sidecar is absent instead of pretending the container mount is authoritative.
   - Direct MinerU API status remains lifecycle authority for `processing/completed/failed`; logs remain progress evidence, not terminal truth.
4. Diagnostics:
   - `/ops/mineru/log-channel-ownership` and/or `/ops/mineru/active-task` should expose enough fields to compare:
     - host-side sidecar observation freshness;
     - container-mounted log freshness;
     - direct MinerU status;
     - DB task state/stage.
   - If the sidecar is not running, the endpoint must make that visible and actionable.
5. Startup/ops clarity:
   - If existing `ops/start-luceon-runtime.sh` or `ops/luceon-dependency-supervisor.mjs` is stale, update it so the host observer command is unambiguous.
   - Do not make broad supervisor rewrites; keep this patch focused.

## Allowed Files

Lucode may modify focused files such as:

- `ops/mineru-log-observer.mjs`
- `ops/start-luceon-runtime.sh`
- `ops/luceon-dependency-supervisor.mjs`
- `server/upload-server.mjs`
- `server/lib/ops-mineru-log-parser.mjs`
- `server/lib/progress-snapshot.mjs`
- focused tests under `server/tests/`
- concise docs only if needed to document the new runtime truth boundary

Do not edit unrelated product surfaces or settings pages.

## Required Tests

At minimum add or update focused tests that prove:

1. A fresh host-side sidecar snapshot is preferred over a stale container-mounted log observation.
2. A stale/missing sidecar is surfaced as an observability problem, not as MinerU parse failure.
3. Direct MinerU API `processing/completed/failed` remains lifecycle authority.
4. Terminal or idle stale logs do not imply active parsing.
5. Existing progress semantics smoke tests still pass.

Run available focused checks:

- `git diff --check`
- `node --check` on changed `.mjs` files
- relevant MinerU log/progress smoke tests
- `npx pnpm@10.4.1 exec tsc --noEmit` if frontend/types are touched

If any check cannot be run in Lucode's environment, report the exact reason.

## Forbidden Scope

- No production restart/rebuild/deploy.
- No upload, retry, reparse, re-AI, repair, pressure test, submit-probe, or data cleanup.
- No DB/MinIO/Docker volume mutation.
- No model/secret/sample mutation.
- No broad architecture rewrite.
- No production readiness, pressure PASS, L3, release-readiness, or go-live claim.

## Required Output

Write:

`TaskAndReport/2026-05-17T17-56-39+0800_P1-Host-MinerU-Log-Sidecar-Authoritative-Progress-Bridge_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- status: `Lucode 已回报待 Luceon 审查`
- Next Actor: `Luceon`

The report must include:

- task brief path;
- branch and HEAD;
- files changed;
- implementation summary;
- commands and exit codes;
- skipped checks and exact reasons;
- evidence for each required test;
- residual risks and production validation needs.

## Acceptance Criteria

- Code/test evidence proves sidecar-first progress semantics.
- Container-mounted log staleness can no longer silently degrade operator progress truth when host sidecar evidence is fresher.
- Sidecar absence is explicit and actionable.
- Parsing and AI lifecycle semantics remain unchanged.
- Production deployment remains pending Luceon review and explicit authorization.
