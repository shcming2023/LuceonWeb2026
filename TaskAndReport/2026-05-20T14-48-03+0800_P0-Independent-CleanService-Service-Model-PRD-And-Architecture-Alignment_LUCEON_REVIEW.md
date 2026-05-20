# Luceon Review: P0 Independent CleanService Service Model PRD And Architecture Alignment

- **Task ID**: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- **Review Time**: 2026-05-20T14:48:03+0800
- **Reviewed Branch**: `origin/lucode/task-223-independent-cleanservice-service-model`
- **Reviewed HEAD**: `22133fee610db9ccc0e39f4c82e4a9233d0c4c23`
- **Base**: `origin/main@68364bc193dabf554b517898b623bcf9f550c041`
- **Decision**: `CHANGES_REQUIRED_DOC_STATUS_REPORT_AND_CONTENT_GAPS`

## Summary

Task 223 is not accepted yet.

The architectural direction is aligned with the Director discussion: Mineru2Table and future RawMaterial2CleanMaterial should remain independently developed and independently Docker-deployed services, coordinated by Luceon through API contracts and MinIO ObjectRefs. The submitted branch also stayed inside the documentation/control-plane boundary: no `server/**`, `src/**`, Docker, runtime, DB, MinIO, model, or sample assets were modified.

However, the branch cannot be promoted as a project truth source yet because the report evidence is not final-branch accurate, several documents prematurely mark decisions as approved, and two required contract areas remain under-specified.

## Verification Performed

- `git rev-parse origin/main` -> `68364bc193dabf554b517898b623bcf9f550c041`
- `git rev-parse origin/lucode/task-223-independent-cleanservice-service-model` -> `22133fee610db9ccc0e39f4c82e4a9233d0c4c23`
- `git merge-base --is-ancestor origin/main origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`
- `git diff --check origin/main..origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`
- `git diff --name-status origin/main..origin/lucode/task-223-independent-cleanservice-service-model` -> exit `0`

Actual final branch diff:

```text
A	TaskAndReport/2026-05-20T14-31-29+0800_P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment_REPORT.md
M	TaskAndReport/TASK_TRACKING_LIST.md
M	docs/architecture/Luceon2026-Asset-Pipeline-Vision.md
A	docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md
M	docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
M	docs/contracts/CleanService-Protocol-v1.md
A	docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md
M	docs/prd/README.md
```

## Findings

### F1. Report evidence is not final-branch accurate

`TaskAndReport/2026-05-20T14-31-29+0800_P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment_REPORT.md:22` says the task changed 7 files, but the final branch changes 8 files, including the report itself. Lines 61-75 record `git diff --name-status --cached origin/main`, not the required final-branch audit `git diff --name-status origin/main..HEAD`, and the recorded output omits the report file. The report also lacks the full final HEAD even though Task 223 required branch and HEAD evidence.

Required correction: update the report with the full final branch HEAD, the exact `git diff --name-status origin/main..HEAD` output, the exit code, and an 8-file deliverable count that includes the report.

### F2. Several documents prematurely claim approval or runtime certainty

- `docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md:3` says `Approved Product Requirement Addendum`.
- `docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md:3` says `Accepted`, and line 7 says `Approved By: Luceon`.
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md:52` says Option A is "approved for stable production integration and scale deployment".
- `TaskAndReport/2026-05-20T14-31-29+0800_P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment_REPORT.md:101` says the mainline pipeline is "fully operational".

Task 223 is a documentation alignment review, not production validation or pre-approval. These must be changed to pending/proposed/candidate wording until Luceon accepts the branch. Runtime claims must stay at path-boundary level only, such as "no runtime files were modified"; do not claim operational status from this docs-only task.

### F3. CleanService Registry is still not defined as a registry contract

The report claims the architecture document "defines the stable CleanService Registry fields" at report line 35. The actual architecture document only has a short "CleanService Directory" table at `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md:103-111`, and grep finds only `serviceName` at line 65 plus a UI phrase at the PRD addendum line 52. This does not meet Task 223's requirement to explicitly define the service registry model.

Required correction: add a concrete registry section/table covering at least `serviceName`, `serviceType`, implementation repository, container/service identity, endpoint binding, protocol version, enabled/admission status, input bucket/object contract, output bucket/prefix contract, cost policy, feature flag/gate, integration state, owner, and review boundary.

### F4. RawMaterial2CleanMaterial and product-level MinIO contracts are incomplete

The architecture and protocol documents cover `toc-rebuild` outputs well enough at `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md:90-99` and `docs/contracts/CleanService-Protocol-v1.md:182-232`. But the PRD addendum stops at legacy policy and does not explicitly state what Mineru2Table reads from MinIO, what it writes, and what the future RawMaterial2CleanMaterial stage should consume and produce.

Search evidence: the final branch does not contain required RawMaterial2CleanMaterial output names such as `raw2clean`, `clean_blocks`, `clean_markdown`, `quality_report`, or `unresolved_items` in the PRD/architecture/protocol docs.

Required correction: add a product/architecture contract section that distinguishes:

- Mineru2Table input: canonical Raw Material ObjectRefs, especially MinerU `content_list_v2.json` plus any allowed resource refs.
- Mineru2Table output: the 7 required files under `eduassets-clean/toc-rebuild/{materialId}/v{N}/`.
- RawMaterial2CleanMaterial input: canonical Raw Material plus accepted `toc-rebuild` structural outputs.
- RawMaterial2CleanMaterial proposed output prefix and minimum proposed files, clearly marked as future/proposed if not yet finalized.

### F5. PRD index now conflicts with its own uniqueness rule

`docs/prd/README.md:7-8` registers both the current PRD body and the new addendum under current PRD, while `docs/prd/README.md:14` still says `Luceon2026-PRD-v0.4.md` is the only valid PRD.

Required correction: clarify that v0.4 remains the current PRD body and approved addenda are governed supplements under v0.4, not competing current PRDs. Until this review is accepted, the new addendum should be marked pending/proposed rather than approved.

### F6. "Pure stateless workers" conflicts with required persistent job state

`docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md:37` says CleanServices are "pure stateless workers". But `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md:38-42` requires ObjectRef processing, durable persistent job state, `/api/v1/jobs`, and callbacks, while lines 76-84 require non-terminal and terminal states to survive service restart.

Required correction: describe CleanServices as isolated service-owned workers with their own bounded job store/state, while keeping Luceon as the authority for material/task/version/review/cost semantics. Do not call them stateless if the contract requires restart-surviving job state.

### F7. Target security should be separated from current Mineru2Table deployment facts

`docs/contracts/CleanService-Protocol-v1.md:152-155` defines target bearer auth and loopback/internal ingress. The adaptation plan records the current service on port 8000 at `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md:31-36`, but it should explicitly mark current-vs-target gaps: current Mineru2Table deployment/API shape is not evidence that target auth/network policy is already satisfied.

Required correction: add a short current-vs-target note so future readers do not confuse protocol direction with current runtime compliance.

## Accepted Evidence

- Branch is based on current `origin/main`.
- Final branch path boundary is docs/control-plane only.
- `git diff --check origin/main..origin/lucode/task-223-independent-cleanservice-service-model` passed.
- Task 219 and Task 222 remain separate and untouched by this review decision.
- No source, Docker, runtime, DB, MinIO, model, or sample asset mutation was observed in the reviewed diff.

## Required Resubmission

Lucode should correct the same branch or a clearly named successor branch with only documentation/report/ledger changes. Do not modify `server/**`, `src/**`, Docker/Compose/config/runtime files, production data, MinIO objects, DB records, model files, sample files, AGENTS.md, or `.agents/**`.

The corrected report must include the full final branch HEAD, exact final `git diff --name-status origin/main..HEAD` output, exact exit codes, and a no-runtime/no-data boundary statement without UAT, L3, production readiness, or go-live claims.
