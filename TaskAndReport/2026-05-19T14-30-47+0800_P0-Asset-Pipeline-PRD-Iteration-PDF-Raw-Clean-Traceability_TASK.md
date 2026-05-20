# P0 Asset Pipeline PRD Iteration: PDF -> Raw Material -> Clean Material Traceability

- Task ID: `TASK-20260519-143047-P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability`
- Issued at: `2026-05-19T14:30:47+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Status: `待执行`
- Priority: `P0`
- Scope type: PRD / architecture contract documentation only

## 1. Background

Director has confirmed the next Luceon2026 development direction:

```text
PDF source asset -> Raw Material -> Clean Material
```

The current Phase 1 mainline already turns PDF into Raw Material:

```text
upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

The next architecture line must introduce `Mineru2Table` as the first structured step from Raw Material toward Clean Material:

```text
Raw Material -> Mineru2Table toc/chapter/table rebuild -> RawMaterial2CleanMaterial -> Clean Material
```

Each layer is a valuable data asset, not a disposable intermediate file. Later layers must derive from earlier layers with explicit provenance. Earlier layers must remain inspectable, recoverable, and usable as evidence for later clean outputs.

## 2. Current Evidence

Current GitHub `origin/main` at task issue time:

- HEAD inspected by Luceon: `a90b124` (`Review Task 219 pressure regression closure`)
- `docs/prd/Luceon2026-PRD-v0.4.md` defines the current task-centered Phase 1 mainline and still treats CleanService as outside v0.4.
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md` is marked as a historical ProductManager draft and future boundary, not the active next-stage PRD.
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md` already names `Source`, `RawMaterial`, `CleanMaterial`, and `Downstream`, but it remains future planning and does not yet encode Director's newly confirmed product chain as the next PRD iteration.
- `docs/contracts/CleanService-Protocol-v1.md` and `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md` define a future protocol direction, but real Mineru2Table dispatch remains blocked until product/PRD boundaries are upgraded and accepted.
- `TaskAndReport/TASK_TRACKING_LIST.md` still has Task 219 open for `Lucode`; this task is documentation/PRD planning and must not be used to bypass Task 219's required correction.

No runtime command, upload, production mutation, external Mineru2Table change, or business-code implementation is authorized by this task.

## 3. Objective

Revise the PRD/documentation layer so Luceon2026's next-stage product contract clearly states:

1. `PDF`, `Raw Material`, and `Clean Material` are separate durable asset stages.
2. `Raw Material` is the current MinerU + AI metadata output stage and is the prerequisite for all later clean work.
3. `Mineru2Table` is the first Clean Material preparation service, responsible for reconstructing chapter/table/TOC structure from Raw Material evidence.
4. `RawMaterial2CleanMaterial` is a later cleaning stage that consumes traceable Mineru2Table/Raw Material outputs and produces Clean Material.
5. Each forward transformation must preserve source references, object refs, hashes, task IDs, service versions, options, output hashes, and failure evidence.
6. No later layer may overwrite, rename, or erase the prior layer by implication.

## 4. Write Boundary

Allowed files:

- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- A new `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not edit unless directly necessary:

- `README.md`
- `docs/codex/roles/**`
- `docs/codex/LUCODE_EXTERNAL_WORKFLOW.md`
- `archive/**`

Forbidden files and areas:

- `src/**`
- `server/**`
- `docker-compose*.yml`
- `package.json`
- `pnpm-lock.yaml`
- `pnpm-workspace.yaml`
- Runtime override files, secrets, `.env*`, local config, sample files, MinIO/DB/Docker volumes, or any production data.
- External Mineru2Table repositories or local runtime services.

## 5. Required PRD Decisions To Encode

The revised PRD/addendum must include a concise decision table covering at least:

| Decision | Required contract |
| --- | --- |
| Asset chain | `PDF -> Raw Material -> Clean Material`, with each layer durable and traceable. |
| Raw Material meaning | Source PDF plus MinerU parsed artifacts plus AI metadata/review state; raw outputs remain evidence and must not be overwritten by clean outputs. |
| Mineru2Table role | First clean-preparation service: chapter/TOC/table/logical structure reconstruction from Raw Material evidence. |
| RawMaterial2CleanMaterial role | Later cleaning stage that consumes Raw Material and Mineru2Table outputs to produce clean normalized material. |
| Provenance | Every derived asset must point back to source object refs, hashes, task IDs, service version, options, and output hashes. |
| Versioning | Luceon owns `materialId`, `parseTaskId`, `assetVersion`, clean job identity, acceptance state, and review semantics. |
| Review | Clean outputs can be `pending`, `running`, `review-needed`, `completed`, `partial`, `failed`, or `skipped`; partial/unresolved outputs must be visible. |
| Legacy boundary | Existing assets stay legacy unless a separate migration task is authorized. |
| Implementation sequence | PRD acceptance first, then architecture/contract reconciliation, then mock worker, then real Mineru2Table protocol implementation, then Luceon integration, then production validation. |

## 6. Mandatory Data Governance Red Lines

Because this task concerns AI data processing and clean educational assets, preserve these red lines in the PRD or contract text where relevant:

1. ID-only extraction: model/service outputs that select source content must reference stable Block IDs or source references. They must not invent or rewrite free text as if it were source truth.
2. Asset hash locking: image/audio/resource assets must preserve original hash names through the processing pipeline. Services must not rename original resource hashes by convenience.
3. Pure layout/code generation boundary: if any later LaTeX/TikZ or code-like clean output is introduced, it must use standard packages and avoid custom commands/macros unless a future task explicitly authorizes otherwise.

## 7. Acceptance Criteria

Positive acceptance:

- PRD/addendum now clearly states the next-stage asset pipeline as `PDF -> Raw Material -> Clean Material`.
- The docs distinguish current implemented Phase 1 from future Clean Material work without downgrading existing 6.9.1 evidence.
- The docs state that Raw Material is a durable asset layer and prerequisite, not a temporary buffer.
- Mineru2Table's role is specified as chapter/TOC/table/logical-structure reconstruction from Raw Material evidence.
- RawMaterial2CleanMaterial is named as a later cleaning stage and is not collapsed into Mineru2Table.
- Provenance, version, review, partial-output, no-silent-fallback, cost, and legacy boundaries remain explicit.
- The report lists exact files changed, summarizes product decisions encoded, and notes any questions that still need Director confirmation.
- `git diff --check` passes.

Negative acceptance:

- Do not implement or wire CleanServiceWorker, Mineru2Table dispatch, RawMaterial2CleanMaterial, UI actions, API routes, DB schema, MinIO bucket creation, runtime config, Docker changes, or production deployment.
- Do not claim Clean Material implementation, real Mineru2Table E2E, release readiness, L3, production readiness, pressure PASS, production上线, or go-live.
- Do not migrate, rename, delete, or rewrite existing assets.
- Do not represent raw MinerU output, skeleton output, placeholder output, or AI-generated free text as successful Clean Material.
- Do not remove Task 219 or mark it complete.
- Do not edit `AGENTS.md` or role files as part of this task.

## 8. Required Report

Create a report named:

`TaskAndReport/2026-05-19T14-30-47+0800_P0-Asset-Pipeline-PRD-Iteration-PDF-Raw-Clean-Traceability_REPORT.md`

The report must include:

- final branch and HEAD;
- files changed;
- concise summary of PRD/product decisions encoded;
- explicit statement that no code/runtime/data mutation occurred;
- validation commands and exact exit codes;
- remaining questions for Luceon/Director, if any;
- ledger row update summary.

## 9. Suggested Branch

Use a scoped branch such as:

`lucode/task-220-asset-pipeline-prd-iteration`

