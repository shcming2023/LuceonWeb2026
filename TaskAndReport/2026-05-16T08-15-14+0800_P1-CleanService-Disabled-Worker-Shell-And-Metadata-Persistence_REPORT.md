# DevelopmentEngineer Report: P1 CleanService Disabled Worker Shell And Metadata Persistence

- Task: `TASK-20260516-081514-P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence`
- Based on Director task brief: `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_TASK.md`
- Source implementation commit: `474254b` (`Add disabled CleanService worker shell`)
- Outcome: `IMPLEMENTED_DISABLED_WORKER_SHELL_AND_MOCK_METADATA_PERSISTENCE`
- Requires Director review: yes
- Requires follow-up production validation or user decision: no production validation was run; real Mineru2Table dispatch and runtime wiring remain separate future decisions/tasks.

## Branch / HEAD

- Branch: `main`
- Initial task execution HEAD: `a46ebe3`
- Implementation HEAD: `474254b`
- GitHub sync: implementation and this report/ledger update are intended for GitHub `main` per task brief after checks pass.

## Files Changed

- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/tests/cleanservice-worker-shell-smoke.mjs`
- `TaskAndReport/2026-05-16T08-15-14+0800_P1-CleanService-Disabled-Worker-Shell-And-Metadata-Persistence_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No UI, PRD truth, role contract, `PROJECT_STATE`, `HANDOFF`, production, Docker, DB, MinIO, MinerU, Ollama, model, secret, sample, external repository, or current runtime entrypoint file was changed.

## Implementation Summary

Implemented an isolated `CleanServiceWorker` shell under `server/services/cleanservice/cleanservice-worker.mjs`.

The worker shell:

- returns `disabled-noop` when default config is disabled;
- does not scan tasks, submit jobs, or persist metadata when disabled;
- scans tasks only through an injected `taskSource.listTasks()`;
- submits only through an injected `client.submitJob()`;
- persists only through an injected `persistence.persistMetadataPatch()`;
- dispatches at most one eligible task per `tickOnce()`;
- builds deterministic mock job requests using Luceon-owned `job_id`, `material_id`, `parse_task_id`, `asset_version`, input ObjectRefs, sink prefix, callback secret ref, and `¥8` hard cost limit;
- filters eligibility to parsed/completed evidence and avoids canceled/failed tasks;
- avoids duplicate dispatch when `metadata.cleanServiceJobs[serviceName]` already has an active or terminal state;
- preserves the Task 200 metadata patch shape: `task.metadata.cleanServiceJobs[serviceName]` and `material.metadata.cleanMaterials[serviceName]`.

## Runtime Startup Isolation Evidence

The worker shell is not wired into runtime startup.

Evidence:

- No changes were made to `server/upload-server.mjs`, `server/services/queue/task-worker.mjs`, `server/services/ai/metadata-worker.mjs`, frontend files, or Compose files.
- `rg -n "cleanservice|CleanServiceWorker|cleanServiceJobs|cleanMaterials" server/upload-server.mjs server/services/queue server/services/ai src docker-compose.yml docker-compose.override.yml` returned exit `1` with no matches.
- All tests use injected in-memory task source, client, and persistence adapters.

## Mock Dispatch And Metadata Persistence Evidence

`server/tests/cleanservice-worker-shell-smoke.mjs` covers:

- disabled `tickOnce()` returns `disabled-noop` with `scanned=0`, `submitted=0`, `persisted=0`;
- disabled worker makes zero task-source, client, or persistence calls;
- eligibility allows parsed/completed evidence and rejects failed/canceled/no-evidence tasks;
- existing active or terminal `cleanServiceJobs['toc-rebuild']` prevents duplicate dispatch;
- enabled mock config submits only one eligible task per tick even when two eligible tasks are available;
- mock job request uses `luceon-task-clean-1-toc-rebuild-v1`, ObjectRef input role `mineru-artifact-manifest`, and `max_cost_cny=8`;
- persistence receives `taskMetadata.cleanServiceJobs['toc-rebuild']` and `materialMetadata.cleanMaterials['toc-rebuild']`;
- persisted summaries contain ObjectRefs and small stats, with no large artifact content;
- partial unresolved anchors persist `review-pending-partial` with `cleanReview=partial-unresolved-anchors`;
- hard-limit failure persists explicit `hard-limit-failed` / `failed` intent.

## Commands Run and Exit Codes

| Command | Exit | Purpose / Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required initial state check; branch `main...origin/main` |
| `rg -n "\\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Located Task 201 |
| `sed -n ...` on Task 201 brief and required role/project/PRD/CleanService task/report/review docs | 0 | Required reading before implementation |
| `git fetch origin && git pull --ff-only origin main && git status --short --branch && git rev-parse --short HEAD` | 0 | Synced to `a46ebe3`, clean |
| `sed -n ...` on current CleanService modules and tests | 0 | Inspected existing Task 200 foundation |
| `rg -n "markdownObjectName|artifactManifestObjectName|parsedPrefix|mineruStatus|state: 'review-pending'|review-pending" server/services server/tests` | 0 | Inspected parse-completion evidence conventions |
| `node --check` for all changed CleanService `.mjs` files and CleanService tests | 0 | Syntax checks passed |
| `git diff --check` | 0 | No whitespace errors |
| `node server/tests/cleanservice-foundation-smoke.mjs` | 0 | Existing Task 200 focused test still passed |
| `node server/tests/cleanservice-worker-shell-smoke.mjs` | 0 | New worker-shell focused test passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check passed |
| `rg -n "cleanservice|CleanServiceWorker|cleanServiceJobs|cleanMaterials" server/upload-server.mjs server/services/queue server/services/ai src docker-compose.yml docker-compose.override.yml` | 1 | No runtime/entrypoint wiring matches found |
| `git add server/services/cleanservice/cleanservice-worker.mjs server/tests/cleanservice-worker-shell-smoke.mjs && git commit -m "Add disabled CleanService worker shell"` | 0 | Implementation commit `474254b` |

## Skipped Checks and Reasons

- `npx pnpm@10.4.1 run build`: skipped because this task touched only server `.mjs` modules, one server `.mjs` focused test, and TaskAndReport files; no frontend, TypeScript app, shared type, or build-sensitive file was changed.
- Production checks: skipped because the task explicitly says not to run production checks.
- Upload, pressure/batch/soak validation, submit-probe, retry, reparse, re-AI, cleanup, repair, reset, task-state reconciliation, and real Mineru2Table dispatch: skipped because forbidden by the task brief.
- External Mineru2Table2026 repository checks: skipped because external repository work was outside scope.

## Residual Risks / Debt

- This remains an isolated worker shell. It is not a runtime worker, not a production capability, and not real Mineru2Table evidence.
- Persistence is a mock contract only; no real DB adapter, callback route, polling loop, or recovery scan is implemented.
- Eligibility currently uses conservative parsed evidence from task metadata. Future real integration may need a Director-approved compatibility adapter for exact content-list ObjectRefs.
- Future tasks still need explicit decisions/evidence for real Mineru2Table protocol support, callback/polling, UI read surfaces, and production deployment boundaries.

## Director Review

Director review is required. Recommended next action: review this disabled worker shell and mock persistence evidence. If accepted, dispatch the next narrow task separately for callback/polling contract, read-only UI surface, or external Mineru2Table protocol evidence. Real dispatch, production validation, readiness/L3/pressure PASS/go-live remain explicitly unclaimed.
