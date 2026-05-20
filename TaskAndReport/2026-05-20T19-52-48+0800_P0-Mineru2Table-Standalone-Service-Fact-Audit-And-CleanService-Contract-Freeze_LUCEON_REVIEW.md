# P0 Mineru2Table Standalone Service Fact Audit And CleanService Contract Freeze Luceon Review

- **Task ID**: `TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Review Time**: `2026-05-20T19:52:48+0800`
- **Reviewed Branch**: `origin/lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Reviewed Branch HEAD**: `d75b18bf60feb79b18c846b539b015018e2bcd23`
- **Decision**: `CHANGES_REQUIRED_MAINLINE_FACT_ALIGNMENT_ONLY`

## Mainline Review Boundary

This is a narrow return.

Luceon is not asking for broad documentation polish, dashboard planning, security expansion, or additional runtime implementation. The only goal is to make the Mineru2Table contract audit truthful enough to drive the next critical-path implementation decision.

## What Passed

- The branch is based on current `origin/main`.
- Changed files are limited to docs/control-plane:

```text
A       TaskAndReport/2026-05-20T19-20-50+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
A       docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md
```

- `git diff --check origin/main..origin/lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze` exited `0`.
- Luceon independently confirmed that upstream `shcming2023/Mineru2Table2026` currently points to:

```text
7e9e592cac7d062edbff31e0c4ddb06d41577474
```

- Luceon also confirmed that this latest upstream source contains the broad protocol direction reported by Lucode: `/api/v1/jobs`, `/api/v1/jobs:from-storage`, `/api/v1/jobs/{job_id}`, `JOB_STORE_PATH`, MinIO ObjectRef handling, and HMAC webhook sender.

## Blocking Findings

### F1. Report and ledger still use the pre-amend HEAD

The actual fetched remote branch HEAD is:

```text
d75b18bf60feb79b18c846b539b015018e2bcd23
```

The submitted report says final branch HEAD is:

```text
1c738e1ac7770297f2d509f559fea5f463461d90
```

The ledger also records:

```text
@lucode/...#1c738e1ac7770297f2d509f559fea5f463461d90
```

Correction required: replace stale/pre-amend branch evidence with the actual final remote branch HEAD after resubmission.

### F2. Deployed runtime facts are mixed with latest upstream source facts

Task 224 required the audit to distinguish observed current behavior, source-inferred behavior, target behavior, and unknowns.

Luceon observed the local deployed Mineru2Table workspace/container facts:

```text
/Users/concm/prod_workspace/Mineru2Tables
HEAD: 43754fa0f3d18051b2d9a3ab4b3cf769a0d47239
container: mineru2table-api
port: 0.0.0.0:8000->8000
/health: {"status":"healthy","version":"1.0.0","llm_status":"not_configured"}
OpenAPI paths: /health, /api/v1/extract, /api/v1/tasks, /api/v1/tasks/{task_id}
```

Luceon separately observed the upstream GitHub source HEAD:

```text
shcming2023/Mineru2Table2026@7e9e592cac7d062edbff31e0c4ddb06d41577474
```

That latest upstream source appears to contain Protocol v1 endpoints, but it is not the same as the currently deployed local container/workspace state. The audit currently describes the "deployed standalone service" and "runtime reality" as if the latest source is already deployed locally.

Correction required: split the document into:

- **Currently deployed local service**: old multipart-only runtime, healthy shell only, `llm_status=not_configured`, not Protocol v1 ready.
- **Latest upstream source evidence**: source-level Protocol v1 candidate at `7e9e592...`, not yet locally deployed/validated.
- **Target CleanService state**: what must be true before Luceon bridge implementation or any real dispatch.

This is a mainline blocker because the next task must not assume the current local service can receive `/api/v1/jobs`.

### F3. Storage allowlist error mapping is overstated

The audit claims bucket/endpoint allowlist violations return `forbidden_storage_target` with HTTP 403.

Luceon source check on upstream `7e9e592...` found:

```text
src/core/storage/minio_backend.py raises PermissionError
src/core/jobs/runner.py catches StoragePermissionError
```

Because the thrown exception type does not match the runner catch block, allowlist violations are likely to fall through to the generic `processing_failed_permanent` path, not the claimed `forbidden_storage_target` path.

Correction required: add this as a remaining external protocol gap. It can be fixed later in Mineru2Table source, but the contract audit must not mark it compliant.

### F4. "Approved" wording is premature

The submitted docs/report use wording such as `Option A (Approved)` before Luceon acceptance.

Correction required: downgrade to `Option A (Lucode recommended / candidate for Luceon approval)` or equivalent. Luceon can approve the route after the corrected audit is accepted.

## Required Narrow Resubmission

Lucode should make a docs-only correction with no runtime/source implementation:

1. Correct final branch HEAD in the report and ledger.
2. Split local deployed runtime facts from latest upstream source facts.
3. Add the storage error-mapping gap.
4. Downgrade premature `Approved` wording to recommendation/candidate wording.

Do not expand the task into broader security hardening, external source changes, Luceon bridge implementation, production validation, container restart/rebuild, MinIO/DB/Docker/model/sample mutation, or real Mineru2Table processing.

## Review Boundary

No production deployment, runtime activation, real dispatch, UAT, L3, pressure PASS, release readiness, or go-live claim was made or accepted by this review.
