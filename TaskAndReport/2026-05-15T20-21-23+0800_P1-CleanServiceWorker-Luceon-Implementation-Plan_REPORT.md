# Architect Report: P1 CleanServiceWorker Luceon Implementation Plan

- Task ID: `TASK-20260515-202123-P1-CleanServiceWorker-Luceon-Implementation-Plan`
- Assignee: Architect
- Based on Director task brief: `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_TASK.md`
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- HEAD before this report commit: `1a176ec`
- Report date: 2026-05-16

## Scope Confirmation

I followed the Director task brief. This is a planning-only Architect report.

I did not implement code, edit canonical docs, mutate runtime/production, edit Docker/DB/MinIO/MinerU/Ollama/model/secret/config/sample files, run submit-probe/upload/pressure/retry/reparse/re-AI/cleanup/repair, edit PRD truth, role contracts, `PROJECT_STATE`, or `HANDOFF`, or claim implementation acceptance, production readiness, release readiness, L3, pressure PASS, production上线, or go-live.

Files changed by this task:

- `TaskAndReport/2026-05-15T20-21-23+0800_P1-CleanServiceWorker-Luceon-Implementation-Plan_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Current Architecture Facts

Current runtime remains PRD v0.4 Phase 1:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

Relevant current code facts:

- `server/upload-server.mjs` owns `POST /tasks`, dependency health, MinerU admission checks, MinIO context construction, worker startup, and AI `onComplete` backfill.
- `server/services/queue/task-worker.mjs` implements `ParseTaskWorker`, with FIFO pending-task scan, active concurrency `<=1`, MinerU result ingestion, parsed artifact manifest writing, task/material updates, and AI job creation.
- `server/services/ai/metadata-worker.mjs` implements `AiMetadataWorker`, with pending AI job scan, strict no-skeleton behavior, evidence-pack selection, provider failure classification, and terminal callback into upload-server.
- `server/services/mineru/admission-circuit.mjs` provides a reusable admission-circuit pattern backed by `settings`.
- `server/services/logging/task-events.mjs` writes slim task events to db-server.
- `server/services/tasks/task-client.mjs` is the current task/material db-server client.
- Frontend task state display is concentrated in `src/app/utils/taskView.ts`, `src/app/utils/taskTerms.ts`, `src/app/pages/TaskManagementPage.tsx`, `src/app/pages/TaskDetailPage.tsx`, and `src/app/components/MetadataTab.tsx`.
- Current task/material types in `src/store/types.ts` have permissive metadata extension but fixed top-level status unions that do not yet include CleanService-specific status fields.

## Implementation Plan Summary

Introduce CleanService support as a separate Luceon orchestration layer, not as a tail added directly into `ParseTaskWorker` or `AiMetadataWorker`.

The safest route is:

1. Add protocol/client/circuit foundations without enabling runtime dispatch.
2. Add `CleanServiceWorker` behind configuration and mock protocol tests.
3. Persist CleanService job state under task/material metadata using bounded summaries.
4. Add callback/polling reconciliation and output/provenance verification.
5. Add UI read surfaces and explicit partial/failure/cost states.
6. Only after Mineru2Table protocol evidence exists, enable real `toc-rebuild` dispatch in a controlled validation task.

## Module And File Impact Map

| Area | Likely files/modules | Planned responsibility |
| --- | --- | --- |
| CleanService client | `server/services/cleanservice/client.mjs` | Submit `POST /api/v1/jobs`, query `GET /api/v1/jobs/{job_id}`, normalize protocol responses/errors, sign/verify callback support helpers where needed. |
| CleanService worker | `server/services/cleanservice/cleanservice-worker.mjs` | Scan eligible tasks, allocate `assetVersion`, submit jobs, reconcile terminal state, enforce active concurrency `<=1`, write task/material summaries, log events. |
| Service config | `server/services/cleanservice/config.mjs` or upload-server config section | Register `toc-rebuild` endpoint, API key env, callback secret env, cost policy, input/output roles, timeout, polling interval. |
| Admission circuit | `server/services/cleanservice/admission-circuit.mjs` | Generalize MinerU-style circuit per `serviceName`; store under settings such as `cleanServiceAdmissionCircuits.toc-rebuild`. |
| Provenance/output verifier | `server/services/cleanservice/output-verifier.mjs` | Validate required artifacts and `provenance.json` ObjectRefs before task state is treated as clean-stage success. |
| Asset version allocator | `server/services/cleanservice/asset-version.mjs` | Luceon-owned version allocation; inspect DB summary and/or MinIO prefixes; no service-owned version assignment. |
| Callback route | `server/lib/cleanservice-routes.mjs` plus `server/upload-server.mjs` mounting | Receive terminal webhook, verify HMAC, update job state idempotently, emit task events. |
| Upload-server wiring | `server/upload-server.mjs` | Construct cleanservice minio context/config, start/stop worker, mount callback/status ops routes. Keep current `POST /tasks` behavior unchanged until enablement task. |
| DB state surface | db-server generic `/tasks`, `/materials`, `/settings` via existing clients | Store bounded summaries in `task.metadata.cleanServiceJobs` and `material.metadata.cleanMaterials`; avoid large artifacts in DB. |
| Task actions | `server/lib/task-actions-routes.mjs` | Later clear or preserve CleanService metadata correctly on retry/reparse/re-ai/cancel; do not add until lifecycle semantics are accepted. |
| Audit | likely `server/lib/consistency-routes.mjs` and related tests | Later detect missing provenance, orphan clean prefixes, dangling clean jobs; read-only first. |
| Frontend labels | `src/app/utils/taskTerms.ts`, `src/app/utils/taskView.ts` | Add product-facing clean-stage labels without overloading parse/AI states. |
| Task UI | `src/app/pages/TaskDetailPage.tsx`, `src/app/pages/TaskManagementPage.tsx` | Show clean-stage status, output entry, unresolved anchor count, provenance, cost/token summary, partial/failure boundary. |
| Metadata/clean output UI | likely new component under `src/app/components/` | Separate clean-output review/read surface from AI metadata review. |
| Tests | `server/tests/cleanservice-*.mjs`, UAT later | Mock protocol, callback idempotency, cost failure, output verification, audit read-only, UI status mapping. |

## CleanServiceWorker Lifecycle

Proposed worker lifecycle:

1. `start()`: load service registry, run delayed recovery scan, then tick on interval.
2. `scanAndProcess()`: fetch tasks, find earliest eligible task with parsed MinerU output and no completed/active clean job for `toc-rebuild`.
3. Eligibility gate:
   - task state is a Director-approved clean-stage candidate, initially likely after MinerU parse completion;
   - `metadata.markdownObjectName` / `metadata.parsedPrefix` / `artifactManifestObjectName` and target `content_list_v2.json` evidence are present;
   - service admission circuit is closed;
   - cost policy does not require pre-dispatch user decision;
   - no canceled task and no active clean job.
4. Allocate `assetVersion` in Luceon.
5. Write a bounded `cleanServiceJobs.toc-rebuild` record in task metadata with `status=queued`, `jobId`, `assetVersion`, `submittedAt`, and sink prefix.
6. Submit `POST /api/v1/jobs`.
7. Reconcile terminal state by webhook or polling.
8. Verify outputs/provenance before marking clean stage complete or review-needed.
9. Emit task events and update material summaries.
10. On restart, scan non-terminal jobs and query service by `job_id` before resubmitting. Do not duplicate jobs.

Queue ownership should be independent from `ParseTaskWorker` and `AiMetadataWorker`. Heavy-stage concurrency should start at `<=1` for current local single-machine constraints.

## State And Data Contract

Recommended bounded task metadata shape:

```json
{
  "cleanServiceJobs": {
    "toc-rebuild": {
      "serviceName": "toc-rebuild",
      "jobId": "luceon-task-123-toc-rebuild-1",
      "status": "queued|processing|completed|review-pending|failed|paused-budget-review|skipped",
      "assetVersion": "v1",
      "input": {
        "bucket": "eduassets-raw",
        "object": "mineru/<materialId>/v1/content_list_v2.json"
      },
      "sink": {
        "bucket": "eduassets-clean",
        "prefix": "toc-rebuild/<materialId>/v1/"
      },
      "artifacts": {
        "floodedContent": "...",
        "logicTree": "...",
        "readableTree": "...",
        "skeleton": "...",
        "provenance": "..."
      },
      "stats": {
        "costCnyActual": 0.184,
        "tokensTotal": 160157,
        "unresolvedAnchorCount": 2
      },
      "error": {
        "code": "quota_exceeded",
        "message": "...",
        "retriable": false
      },
      "updatedAt": "..."
    }
  }
}
```

Material summary should remain smaller:

```json
{
  "cleanMaterials": {
    "toc-rebuild": {
      "latestVersion": "v1",
      "status": "review-pending|completed|failed|skipped",
      "prefix": "toc-rebuild/<materialId>/v1/",
      "provenanceObjectName": "...",
      "updatedAt": "..."
    }
  }
}
```

Do not store large clean artifacts in DB. Store ObjectRefs and summaries only.

## MinIO ObjectRef Flow

Future new assets should use the canonical raw/clean layout only after implementation is authorized. For the current codebase, the first implementation phase should support a compatibility adapter:

- current parsed artifacts may still live under `eduassets-parsed` / `parsed/{materialId}/`;
- canonical future jobs should target `eduassets-raw` and `eduassets-clean`;
- until the new raw layout exists, a feature-flagged bridge must either copy/normalize only in a scoped task or remain mock-only.

Important boundary: no legacy asset migration or pseudo-provenance is authorized by this plan.

## Asset Version And Provenance Model

Luceon assigns `assetVersion` before submission.

Minimum allocator behavior:

1. Check task/material summary for existing `cleanMaterials[serviceName].versions`.
2. Check MinIO prefix for existing `eduassets-clean/{serviceName}/{materialId}/vN/` only when the new layout is active.
3. Allocate `max(N)+1`.
4. Write allocation before submit to preserve idempotency.
5. On repeated job submission, keep the same `jobId` and `assetVersion`.

Output success requires:

- all required artifact refs present;
- `provenance.json` present;
- provenance service identity matches expected `serviceName/protocol`;
- provenance input object matches submitted input;
- cost/token stats recorded when service uses LLM.

## Callback, Polling, And Idempotency

Preferred strategy: webhook first, polling fallback.

- Webhook route verifies HMAC using `callback_secret_ref`.
- Callback handler is idempotent by `job_id` and terminal state.
- Worker polls non-terminal jobs at a conservative interval for recovery and webhook loss.
- If service returns 200 idempotency hit for a repeated job, Luceon must reconcile rather than create a new version.

Do not rely only on service memory. Mineru2Table must provide persistent job evidence before real integration.

## Admission, Backpressure, Timeout, And Retry

Use a per-service admission circuit, not the MinerU circuit itself.

Circuit opens on:

- `/health` unhealthy;
- submit path failure;
- repeated job query failure;
- callback authentication mismatch;
- output/provenance verification failure pattern;
- service hard-limit semantics returned inconsistently.

Backpressure:

- active CleanService heavy-stage count starts at `<=1`;
- no parallel jobs for same `(serviceName, materialId)`;
- do not dispatch if current MinerU/AI pressure track is still using the same local machine unless Director authorizes.

Retry:

- automatic retry should be off in the first release;
- retryable protocol errors can be recorded as manual retry candidates;
- non-retriable errors (`invalid_input_ref`, `quota_exceeded`, schema errors) must require human decision or implementation fix.

Timeout:

- separate submit timeout, job polling timeout, and stale-processing timeout;
- stale-processing should query service truth before any state change;
- no retry/reparse/re-AI side effect should happen inside planning/validation tasks unless explicitly authorized.

## Error Taxonomy And No-Silent-Fallback Behavior

Map service errors explicitly:

| Protocol code | Luceon task/material handling |
| --- | --- |
| `invalid_input_schema` | implementation/schema failure; stop and report |
| `invalid_input_ref` | raw/parsed artifact reference bug or missing input; stop, no fake clean output |
| `forbidden_storage_target` | config/security failure; open circuit |
| `unauthorized` | secret/API key/callback auth failure; open circuit |
| `service_unhealthy` | keep queued or blocked; open circuit |
| `upstream_unavailable` | record retryable service failure; no auto retry initially |
| `quota_exceeded` | hard-limit failed; non-retriable without User/Director decision |
| `processing_failed` | failed/manual retry candidate depending on details |
| `processing_failed_permanent` | failed/non-retriable |

Partial output and unresolved anchors must not be represented as `completed` unless product rules define an explicit `review-pending` or partial-review state.

## Cost-Limit Enforcement

Two-layer behavior:

- Luceon soft limit `¥5`: before or during clean-stage processing, if projected/actual cost crosses the soft limit, pause the task as `paused-budget-review` and route a Director/User decision.
- Service hard limit `¥8`: pass as `options.max_cost_cny=8.0`; if exceeded, the service must stop with `quota_exceeded` and `retriable=false`.

Required records:

- projected/actual `cost_cny`;
- token counts;
- soft/hard threshold values;
- whether Director/User decision is required;
- no hidden continuation after soft-limit pause.

## Operator UI And Evidence Surfaces

Initial product-facing labels should be decided by ProductManager, but Architect recommends these working labels:

| Internal state | Operator label |
| --- | --- |
| `clean-pending` | 清洗待执行 |
| `clean-running` | 目录重建中 |
| `clean-review-pending` | 清洗结果待复核 |
| `clean-completed` | 清洗完成 |
| `clean-failed` | 清洗失败 |
| `paused-budget-review` | 成本待确认 |
| `clean-skipped-legacy` | 旧资产未清洗 |

Task detail should expose:

- clean-stage status and update time;
- service name/version/protocol;
- output object refs;
- provenance object ref;
- unresolved anchor count;
- token/cost summary;
- error code/retriable flag;
- next action.

Task list should show simple operator language and keep technical details folded.

## Migration Boundary

Existing materials remain legacy. No immediate migration, cleanup, or pseudo-provenance.

Implementation should treat legacy assets as:

- visible in existing library behavior;
- not automatically eligible for CleanService unless separately re-ingested or explicitly selected by a future task;
- clearly labeled if UI exposes the clean-stage absence.

## Required Mineru2Table2026 Dependency Evidence

Before Luceon real integration, Director should require evidence from Mineru2Table2026 for:

1. `GET /health` returns service identity and dependency checks.
2. `POST /api/v1/jobs` accepts MinIO ObjectRef input.
3. `GET /api/v1/jobs/{job_id}` returns persistent job state after restart.
4. Repeated `job_id` is idempotent.
5. Required outputs are written to MinIO.
6. `provenance.json` is written and hash-bearing.
7. Webhook terminal delivery and HMAC signing work, or polling-only fallback is explicitly accepted.
8. `quota_exceeded` is returned for `¥8` hard-limit breach.
9. Old multipart routes are retained and marked deprecated.
10. Integration test evidence exists against MinIO fixture or real compatible MinIO.

## Phased Dispatch Proposal

### Phase A: Luceon Planning Follow-up

Role: Architect
Scope: refine exact state names, callback endpoint, DB metadata shape, and worker enablement flag after ProductManager answers UI/state questions.
No code.

### Phase B: Mineru2Table External Dependency

Role: DevelopmentEngineer or separate external-repo thread
Scope: implement/verify CleanService Protocol v1 in Mineru2Table2026.
No Luceon runtime integration.

### Phase C: Luceon Mock Protocol Foundation

Role: DevelopmentEngineer
Scope: add CleanService client, config, circuit, output verifier, callback route, and mock tests. Keep disabled by default.
Validation: unit/mock only.

### Phase D: CleanServiceWorker Disabled Integration

Role: DevelopmentEngineer
Scope: add worker scaffold, task metadata summaries, idempotency, and polling/callback reconciliation against mock service. Feature flag disabled for production.

### Phase E: UI Read Surface

Role: DevelopmentEngineer
Scope: add task labels, task detail clean-stage panel, error/cost/provenance display. No real service dispatch.

### Phase F: Real Mineru2Table Local E2E

Role: TestAcceptanceEngineer after DevelopmentEngineer implementation
Scope: one controlled local or staging E2E against protocol-compatible Mineru2Table, with MinIO fixture/sample and no release-readiness claim.

### Phase G: Production Boundary Decision

Role: Director/User
Scope: decide whether to authorize production deployment/validation. This is separate from implementation acceptance.

## Validation Plan

| Layer | Owner | Examples |
| --- | --- | --- |
| Unit | DevelopmentEngineer | client normalization, HMAC verify, asset version allocator, error mapping |
| Contract/mock | DevelopmentEngineer | fake CleanService returns completed, failed, partial, timeout, quota exceeded, duplicate job |
| Worker smoke | DevelopmentEngineer | eligible task -> queued job -> terminal callback -> metadata summary |
| Audit read-only | DevelopmentEngineer/TestAcceptanceEngineer | missing provenance, dangling job, orphan clean prefix detection without cleanup |
| UI local | DevelopmentEngineer/TestAcceptanceEngineer | labels and folded diagnostics for clean pending/running/review/failed/cost pause |
| Real E2E | TestAcceptanceEngineer | MinIO-backed Mineru2Table `toc-rebuild` on one controlled sample |
| Production read-only | TestAcceptanceEngineer | health/config/status only, no submit/upload unless separately authorized |
| Release boundary | Director/User | separate decision; never inferred from mock/unit/E2E alone |

No validation layer should claim pressure PASS, L3, production readiness, release readiness, or go-live unless a later task explicitly authorizes and proves that boundary.

## Open Questions Requiring ProductManager/User Decision

1. Does `toc-rebuild` gate all AI metadata, or only future chapter-level AI/enrichment workflows?
2. What exact operator-facing labels should be used for clean-stage statuses?
3. How should `¥5` soft-limit pause appear in task detail and task ledger?
4. Is future hash-based `materialId` global, or scoped only to new CleanService-enabled assets?
5. How should legacy assets be labeled in library and task views?
6. Should CleanService partial output with unresolved anchors map to `review-pending`, a new clean-specific review state, or a folded diagnostic under existing task state?
7. Who owns cross-repo byte-identical protocol sync: Director manually, GitHub workflow, or paired task briefs?

## Risks

- `upload-server.mjs` is already a large coordination point; direct embedding would increase coupling.
- Current status unions and UI labels may hide CleanService partial/failure semantics if added hastily.
- New `eduassets-raw` / `eduassets-clean` layout can conflict with current `eduassets` / `eduassets-parsed` assumptions unless feature-gated.
- Callback security and byte-identical protocol sync are easy to under-specify.
- Cost-limit handling touches product decision flow, not only code.
- Mineru2Table protocol compatibility is an external dependency and should block real Luceon dispatch.

## Commands Run

| Command | Exit | Purpose |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required initial state check |
| `rg -n "\\| Architect \\|" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Locate Architect task |
| `sed -n ...` required task/docs/reviews | 0 | Required reading |
| Targeted `rg` over `server/`, `src/`, `docs/`, `TaskAndReport/` | 0 | Ground module planning in current code |
| `sed -n ...` selected current code files | 0 | Inspect worker, MinIO, task event, route, UI state surfaces |
| `git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git log -1 --oneline` | 0 | Record branch/HEAD |

## Skipped Checks

- No TypeScript/build/unit tests were run because this task is planning-only.
- No runtime, production, upload, pressure, submit-probe, retry, reparse, re-AI, cleanup, or repair checks were run because the task explicitly forbids them.
- No external Mineru2Table2026 repository work was done because the task forbids editing that repo.

## GitHub Sync Status

Pending at report-write time. The task brief requires commit and push if repository files are changed. I will commit and push this report plus the task-ledger update after local diff/status validation.

## Director Review

Director review is required. The recommended Director action is to accept, return for revision, or dispatch the next planning/dependency task. Implementation should not begin until Director has reviewed this plan and the Mineru2Table protocol dependency path is explicitly assigned.

