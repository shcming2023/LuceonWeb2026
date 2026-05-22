# TASK-20260522-133544-P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design

## 1. Mainline Objective

Task 245 proved that standalone Mineru2Table can complete one real `toc-rebuild` job and write the expected seven-file output set under a new clean prefix.

Task 246 then accepted the `v2` output as sufficient to proceed to minimal Luceon orchestration planning, with guardrails.

This task asks Lucode to produce an implementation-level design for the next mainline step:

```text
How should Luceon minimally orchestrate Mineru2Table, assign assetVersion, poll/query terminal state, verify MinIO outputs, and persist clean output metadata without disturbing the existing Phase 1 pipeline?
```

This is a design task only. Do not write business/runtime implementation code in this task.

## 2. Director Authorization

The Director approved opening Task 247 after Task 246.

## 3. Current Evidence

Accepted facts from recent Luceon tasks:

- Task 244: DeepSeek auth-only probe passed from inside `mineru2table-api`.
- Task 245: exactly one real Mineru2Table job completed successfully:

  ```text
  luceon-task245-toc-rebuild-1842780526581841-v2-20260522052230
  ```

- Task 245 output prefix:

  ```text
  eduassets-clean/toc-rebuild/1842780526581841/v2/
  ```

- Task 245 required artifacts exist:
  - `flooded_content.json`
  - `logic_tree.json`
  - `readable_tree.md`
  - `skeleton.json`
  - `unresolved_anchors.json`
  - `metrics.json`
  - `provenance.json`

- Task 246 read-only quality review conclusion:

  ```text
  PROCEED_TO_MINIMAL_ORCHESTRATION_DESIGN_WITH_GUARDRAILS
  ```

- Task 246 guardrails:
  - verify all seven artifacts;
  - ensure `metrics.tokens.total > 0`;
  - parse JSON artifacts;
  - ensure Markdown is non-empty;
  - verify source ObjectRef and input SHA;
  - require a new Luceon-assigned `assetVersion`;
  - never reuse failed/stale prefixes.

Known residual debt:

- Mineru2Table false-success guard: Task 242 showed LLM/API failure can be incorrectly marked `completed`.
- `provenance.json` currently records the correct input ObjectRef/hash but has `input size_bytes=0`.
- Current Luceon `server/services/cleanservice/output-verifier.mjs` is not yet sufficient for Task 245/246 guardrails. It does not perform MinIO object reads and does not yet enforce all seven artifacts, non-zero metrics, or provenance content checks.

## 4. Critical Path Scope

Produce a design document that defines the smallest Luceon-side orchestration path for one operator-triggered `toc-rebuild` job.

The design must cover:

1. **Entry point**
   - Proposed minimal operator/API trigger.
   - Disabled-by-default behavior.
   - No scheduler/autoscan activation in the first implementation.

2. **Eligibility**
   - Required Raw Material metadata shape.
   - Legacy parsed-only handling (`skipped-policy` remains valid).
   - Existing job/version duplicate handling.

3. **Asset versioning**
   - How Luceon allocates the next clean `assetVersion`.
   - How failed versions, blocked attempts, and successful versions affect the next version.
   - How to avoid reusing Task 242 `v1` or any stale prefix.

4. **Job request construction**
   - Exact Protocol v1 request fields.
   - `submitted_by`, cost limits, storage endpoint, callback fields.
   - Why MinIO/LLM credentials must not appear in payloads.

5. **Dispatch and polling**
   - Whether first implementation should use polling only, callback only, or both.
   - Timeout and retry semantics.
   - Idempotency semantics by `job_id`.

6. **Output verification**
   - How Luceon verifies all seven MinIO artifacts.
   - JSON parse checks.
   - non-empty Markdown check.
   - `metrics.tokens.total > 0` check.
   - provenance input ObjectRef/hash check.
   - handling of current `input size_bytes=0` service gap.
   - how to classify missing, malformed, skeleton/placeholder, zero-token, or raw-MinerU-like outputs.

7. **Persistence**
   - Proposed `task.metadata.cleanServiceJobs.toc-rebuild` shape.
   - Proposed `materialMetadata.cleanMaterials.toc-rebuild` shape.
   - Which fields are required for audit/recovery.
   - How ObjectRefs should be stored without duplicating file content.

8. **State mapping**
   - Luceon internal clean states.
   - Mapping from Mineru2Table `queued/processing/completed/failed`.
   - Mapping for cost soft limit, hard limit, timeout, protocol failure, and partial unresolved anchors.

9. **Safety and rollout**
   - Feature flags and disabled defaults.
   - Manual single-sample first run.
   - No impact on current Phase 1 upload -> MinerU -> AI metadata -> operator review.

10. **Next implementation task breakdown**
    - Split the future implementation into small mainline-first cards.
    - Identify which fixes are true prerequisites and which are deferrable side work.

## 5. True Preconditions For Later Implementation

The design must explicitly classify these:

- **Hard prerequisite for minimal orchestration implementation**:
  - Luceon output verifier must not trust `completed` alone.
  - Luceon must verify the seven artifacts and metrics/provenance guardrails before persisting `completed`.

- **Hard prerequisite before broad automation/batch mode**:
  - Mineru2Table false-success guard must be fixed.
  - Provenance input size should be fixed or explicitly compensated by Luceon-side verification.

- **Deferrable after minimal manual orchestration**:
  - operator UI cockpit;
  - batch scheduling;
  - unresolved anchor desk;
  - RawMaterial2CleanMaterial;
  - cleanup/migration policy for failed `v1` outputs.

## 6. Environment And Write Boundary

### Luceon Workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed reads:

- `server/services/cleanservice/**`
- directly relevant `server/tests/cleanservice-*.mjs`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- Task 240-246 task/report/review files
- `TaskAndReport/TASK_TRACKING_LIST.md`

Allowed writes:

- `TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_DESIGN.md`
- `TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden writes:

- `server/**`
- `src/**`
- package manifests or lockfiles
- Docker/Compose files
- `.env*`
- PRD/architecture/contract docs
- private role files (`AGENTS.md`, `.agents/**`)
- external Mineru2Table source or deployment files

### Runtime/Data Boundary

Forbidden runtime/data operations:

- `POST /api/v1/jobs`;
- `chat/completions`;
- MinIO object write/delete/cleanup/move/rename;
- DB write;
- Docker build/recreate/restart/down;
- manual job-store edit;
- source file cleanup or sample mutation;
- UAT/L3/readiness/pressure PASS/go-live claim.

Read-only inspection is allowed only if needed to cite already-produced Task 245/246 evidence.

## 7. Deliverables

Create a design file:

```text
TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_DESIGN.md
```

It must include:

- design summary;
- current code gap analysis;
- proposed minimal architecture;
- proposed data shapes;
- state machine / transition table;
- verification gate table;
- failure classification table;
- implementation task breakdown;
- explicit non-goals.

Create a report file:

```text
TaskAndReport/2026-05-22T13-35-44+0800_P0-CleanService-Minimal-Orchestration-And-Metadata-Integration-Design_REPORT.md
```

It must include:

- exact branch/HEAD;
- changed files;
- read-only evidence sources;
- confirmation that no runtime/data mutation or source-code implementation occurred;
- final recommendation for the next implementation task.

Update the ledger row to:

```text
Status = Ready for luceon Review
Next Actor = Luceon
```

## 8. Positive Acceptance Criteria

Luceon can accept the task if:

- the design is implementation-ready enough to generate one or more small coding tasks;
- it directly addresses Task 245/246 evidence;
- it preserves mainline-first scope;
- it does not attempt to design broad UI/batch/CleanMaterial finalization before minimal orchestration;
- it identifies output verification as a required guardrail;
- it includes precise metadata persistence shapes;
- it keeps all runtime and data operations read-only or untouched;
- `git diff --check` passes.

## 9. Negative Acceptance Criteria

Return or block the task if:

- business/runtime code is modified;
- Docker/env/MinIO/DB/runtime state is mutated;
- the design treats `completed` as sufficient without artifact verification;
- the design reuses or cleans Task 242 `v1`;
- the design collapses RawMaterial2CleanMaterial into Mineru2Table;
- the design makes UAT/L3/release/production-readiness claims;
- raw secrets appear in any output.

## 10. AI/Data Governance Red Lines

The design must preserve:

1. **ID/source-reference only**: output verification and provenance may reference source ObjectRefs, block ids, hashes, and metadata, but must not invent source truth.
2. **Asset hash locking**: existing source and generated artifact hashes are evidence and must not be rewritten or renamed.
3. **Pure structure boundary**: Mineru2Table remains `toc-rebuild`; RawMaterial2CleanMaterial is separate and later.

## 11. Review Boundary

Acceptance of Task 247 means only:

```text
Luceon has an implementation-ready design for minimal CleanService orchestration and metadata integration.
```

It does not mean:

- orchestration code is implemented;
- CleanService is activated;
- Luceon DB has clean output records;
- operator UI is updated;
- RawMaterial2CleanMaterial has run;
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
