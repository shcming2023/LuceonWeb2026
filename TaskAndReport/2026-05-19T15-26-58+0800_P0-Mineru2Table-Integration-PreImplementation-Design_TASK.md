# P0 Mineru2Table Integration Pre-Implementation Design

- Task ID: `TASK-20260519-152658-P0-Mineru2Table-Integration-PreImplementation-Design`
- Issued at: `2026-05-19T15:26:58+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Status: `待执行`
- Priority: `P0`
- Scope type: implementation-level design only; no source-code implementation

## 1. Background

Task 220 is accepted at documentation level only. It establishes the next asset chain:

```text
PDF -> Raw Material -> Clean Material
```

The accepted contract says:

- Raw Material is the durable prerequisite asset layer formed by current PDF intake, MinerU parsed artifacts, AI metadata, and review state.
- Mineru2Table is the first Clean Material preparation service: it rebuilds TOC/chapter/table/logical structure from Raw Material evidence.
- `RawMaterial2CleanMaterial` is a later, separate cleaning stage and must not be collapsed into Mineru2Table.
- Every derived asset must keep provenance back to source object refs, hashes, task IDs, service versions, options, output hashes, and review/failure evidence.

The current repository already contains a disabled CleanService foundation, but it is not a real Mineru2Table integration and is not production-accepted.

## 2. Current Evidence

Current GitHub `origin/main` at task issue time:

- HEAD inspected by Luceon: `dd4c0548576c2d4ccf97eb5c81f50d4b4f9b4874`
- Task 220 status: `完成关闭`; decision `ACCEPTED_DOCS_LEVEL`; no implementation/runtime acceptance.
- Task 219 remains open for `Lucode`; do not modify or close it as part of Task 221.
- `AGENTS.md` and `.agents/` are ignored and not Git-tracked; do not edit or synchronize them.

Relevant accepted documents:

- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `TaskAndReport/2026-05-19T15-10-18+0800_P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability_LUCEON_REVIEW.md`

Relevant current code facts observed by Luceon:

- Disabled CleanService foundation exists under `server/services/cleanservice/`.
- Current CleanService config is disabled by default through `CLEANSERVICE_ENABLED`.
- Existing clean state labels include `等待目录重建`, `目录结构已完成`, `部分完成待复核`, and `成本待决策`.
- Existing smoke tests include `server/tests/cleanservice-foundation-smoke.mjs` and `server/tests/cleanservice-worker-shell-smoke.mjs`.
- `CleanServiceWorker` is not wired into `server/upload-server.mjs`.
- `createCleanServiceClient` currently requires an injected transport; there is no real HTTP transport to `/api/v1/jobs` yet.
- Current worker-shell input selection allows `artifactManifestObjectName`, `markdownObjectName`, or `parsedPrefix`; the Task 220 asset-chain contract requires the next implementation plan to decide the canonical Raw Material ObjectRef path, especially MinerU `content_list_v2.json`.
- Current worker-shell defaults `assetVersion` to `v1` or metadata, but there is no accepted Luceon-owned version allocator yet.
- Real Mineru2Table dispatch remains blocked by the accepted Task 203/204 boundary: external Mineru2Table has not yet proven CleanService Protocol v1 support.

No runtime command, upload, production mutation, external Mineru2Table change, or business-code implementation is authorized by this task.

## 3. Objective

Produce a design-only implementation blueprint that can become the basis for later Luceon-issued code tasks.

The design must reconcile:

1. Task 220's `PDF -> Raw Material -> Clean Material` contract.
2. Existing disabled CleanService foundation code.
3. CleanService Protocol v1 and the Mineru2Table adaptation plan.
4. The current Phase 1 mainline and Task 219 residual risk.
5. The external Mineru2Table protocol blocker.

The output should answer: exactly what future code tasks are needed, in what order, with which file boundaries, tests, runtime gates, and acceptance evidence before real Mineru2Table dispatch can be considered.

## 4. Write Boundary

Allowed files:

- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_DESIGN.md`
- `TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Read-only inspection is allowed for directly relevant source and docs:

- `server/services/cleanservice/**`
- `server/upload-server.mjs`
- `server/services/queue/task-worker.mjs`
- `server/services/ai/**`
- `server/services/tasks/task-client.mjs`
- `server/lib/task-actions-routes.mjs`
- `server/lib/progress-snapshot.mjs`
- `server/tests/cleanservice-*.mjs`
- `src/store/types.ts`
- `src/app/utils/taskView.ts`
- `src/app/utils/taskTerms.ts`
- task/detail/list UI files only for state-surface mapping
- accepted PRD, architecture, contract, and TaskAndReport files referenced above

Forbidden files and areas:

- `src/**` edits
- `server/**` edits
- `package.json`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- `docker-compose*.yml`
- `.env*`, secrets, runtime overrides, local config
- `AGENTS.md`
- `.agents/**`
- external Mineru2Table repositories
- sample files, MinIO objects, DB rows, Docker volumes, model files, production data

Do not update `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, PRD, architecture, or contract files in this task. This task should produce a reviewable design artifact, not promote new project truth before Luceon acceptance.

## 5. Required Design Content

The design file must include all sections below.

### 5.1 Current-State Inventory

List the relevant current modules and summarize what each already does and does not do. Include at least:

- CleanService config/client/states/metadata-summary/output-verifier/worker shell.
- Existing smoke tests and what they prove.
- Existing ParseTaskWorker and AI metadata worker boundaries.
- Existing task/material metadata fields that identify Raw Material evidence.
- Whether and where CleanService is currently wired into runtime startup.

### 5.2 Gap Matrix

Provide a matrix from the accepted contract to current implementation state:

| Requirement | Current evidence | Gap | Future task needed |
| --- | --- | --- | --- |

Cover at least:

- Raw Material ObjectRef selection and canonical `content_list_v2.json` path.
- `materialId`, `parseTaskId`, `assetVersion`, and clean `job_id`.
- MinIO input and output ObjectRefs.
- HTTP transport to `POST /api/v1/jobs` and `GET /api/v1/jobs/{job_id}`.
- callback/HMAC route and polling fallback.
- service admission circuit.
- output/provenance verifier.
- cost soft/hard behavior.
- partial/unresolved-anchor state mapping.
- retry/cancel/reparse/re-AI interaction boundary.
- UI read surface and operator review entry.
- real external Mineru2Table protocol dependency.

### 5.3 Proposed Implementation Sequence

Break the future implementation into small Luceon-dispatchable tasks. Each task must have:

- purpose;
- write boundary;
- feature flag / disabled-by-default posture;
- positive and negative acceptance criteria;
- minimum tests;
- what remains explicitly out of scope.

The sequence must start with mock/protocol-safe work and must not jump directly to real Mineru2Table production dispatch.

### 5.4 Data And State Contract

Propose the exact bounded metadata shapes for:

- `task.metadata.cleanServiceJobs.toc-rebuild`;
- `material.metadata.cleanMaterials.toc-rebuild`;
- job request records;
- provenance and output summaries;
- clean-stage event payloads.

Do not store large clean artifacts in DB. Use ObjectRefs and summaries only.

### 5.5 Raw Material ObjectRef Decision

Design how Luceon should select the input ObjectRef for Mineru2Table.

The design must distinguish:

- future canonical raw layout (`eduassets-raw/mineru/{materialId}/v{N}/content_list_v2.json`);
- current legacy parsed layout (`eduassets-parsed/parsed/{materialId}/...`);
- whether a compatibility bridge is needed;
- how to avoid pseudo-provenance for legacy assets;
- what evidence proves the selected ObjectRef is valid before dispatch.

### 5.6 Runtime And Safety Gates

Define gates for:

- `CLEANSERVICE_ENABLED=false` default behavior;
- no runtime startup unless explicitly enabled;
- no submit when endpoint/API key/protocol identity is missing;
- per-service admission circuit;
- active concurrency `<=1`;
- no blocking of current Phase 1 AI metadata unless a later explicit task changes that policy;
- no automatic retry in the first implementation step;
- no production deployment or validation until Luceon explicitly authorizes it.

### 5.7 Test And Verification Plan

Provide a staged test plan:

1. pure unit/smoke tests for request building, metadata patches, cost state, and output verifier;
2. mock HTTP transport tests for protocol success/partial/failure/timeout/cost limit;
3. callback/HMAC idempotency tests;
4. disabled worker startup/no-op tests;
5. UI state mapping tests, if UI read surface is proposed;
6. external Mineru2Table protocol fixture/E2E requirements, still separate from Luceon runtime wiring;
7. production validation boundary, explicitly deferred.

### 5.8 Open Decisions

Separate decisions into:

- Lucode recommendations;
- Luceon-owned acceptance decisions;
- Director/User-owned product or production decisions.

Do not silently decide unresolved product questions by implementation convenience.

## 6. Mandatory Data Governance Red Lines

Because this task concerns AI data processing, educational assets, and future clean outputs, preserve these red lines:

1. ID-only extraction: model/service outputs that select source content must reference stable Block IDs or source references. They must not invent or rewrite free text as if it were source truth.
2. Asset hash locking: image/audio/resource assets must preserve original hash names through the pipeline. Services must not rename original resource hashes by convenience.
3. Pure layout/code generation boundary: if later LaTeX/TikZ or code-like clean output is introduced, it must use standard packages and avoid custom commands/macros unless a future task explicitly authorizes otherwise.

## 7. Acceptance Criteria

Positive acceptance:

- A design file is created at the required `*_DESIGN.md` path.
- The design is implementation-level: concrete file/module impact, state contract, sequence, tests, and acceptance gates are specified.
- The design explicitly reconciles Task 220's asset chain with the existing disabled CleanService foundation.
- The design does not treat existing worker-shell code as production-ready real Mineru2Table dispatch.
- The design blocks real dispatch until external Mineru2Table proves CleanService Protocol v1 support.
- The design keeps Task 219 open and avoids modifying its row except by explicitly saying it is a separate unresolved task.
- The report lists exact files changed, final branch/HEAD, validation commands, and exact exit codes.
- `git diff --check` passes.

Negative acceptance:

- Do not implement or modify `server/**` or `src/**`.
- Do not wire `CleanServiceWorker` into runtime startup.
- Do not add routes, DB schema, UI behavior, Docker config, MinIO buckets, runtime env, or production settings.
- Do not run upload, submit-probe, pressure/batch/soak, retry/reparse/re-AI/cancel/repair/reset, or production deployment.
- Do not mutate production runtime, DB rows, MinIO objects, Docker volumes, model files, secrets, sample files, or external Mineru2Table repositories.
- Do not claim Clean Material implementation, real Mineru2Table E2E, production validation, readiness, L3, pressure PASS, production上线, or go-live.
- Do not edit `AGENTS.md` or `.agents/**`.
- Do not migrate, rename, delete, or rewrite existing assets.

## 8. Required Report

Create a report named:

`TaskAndReport/2026-05-19T15-26-58+0800_P0-Mineru2Table-Integration-PreImplementation-Design_REPORT.md`

The report must include:

- final branch and HEAD;
- files changed;
- design artifact path;
- summary of implementation sequence proposed;
- explicit statement that no source/runtime/data mutation occurred;
- validation commands and exact exit codes;
- remaining questions for Luceon/Director/User;
- ledger row update summary.

## 9. Suggested Branch

Use a scoped branch such as:

`lucode/task-221-mineru2table-preimplementation-design`
