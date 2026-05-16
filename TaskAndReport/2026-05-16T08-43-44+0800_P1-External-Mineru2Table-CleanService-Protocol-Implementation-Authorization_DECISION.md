# User Decision Required: P1 External Mineru2Table CleanService Protocol Implementation Authorization

- Decision ID: `TASK-20260516-084344-P1-External-Mineru2Table-CleanService-Protocol-Implementation-Authorization`
- Created at: `2026-05-16T08:43:44+0800`
- Created by: `Director`
- Based on: `TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_REPORT.md`
- Director review: `TaskAndReport/2026-05-16T08-43-44+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_DIRECTOR_REVIEW.md`

## Current Fact

Luceon has disabled mock CleanService foundation code, but real Mineru2Table dispatch is blocked.

Current Mineru2Table at `/Users/concm/prod_workspace/Mineru2Tables` supports basic `/health`, old multipart upload extract/tasks routes, in-memory tasks, and output/cost result metadata. It does not yet support CleanService Protocol v1:

- no `/api/v1/jobs`;
- no persistent job state;
- no idempotency by Luceon-owned `job_id`;
- no MinIO ObjectRef input/output;
- no protocol `provenance.json`;
- no signed callback;
- no CleanService structured errors;
- no `¥8` hard stop semantics.

## Why User Decision Is Needed

The next useful step requires mutating an external repository/service, not just Luceon documentation or mock code. Director should not silently authorize external repository implementation work from a check-task heartbeat.

## Options

### Option A: Authorize External Protocol Foundation Implementation

Authorize a scoped DevelopmentEngineer task against `/Users/concm/prod_workspace/Mineru2Tables` to implement CleanService Protocol v1 foundations at code/test level.

Scope should include:

- health identity with `service_name`, `service_version`, `protocol_version`;
- `/api/v1/jobs` submit and `/api/v1/jobs/{job_id}` status;
- durable local job store;
- idempotency by request-owned `job_id`;
- MinIO ObjectRef request/output adapter, initially config/test-fixture friendly;
- required artifact/provenance writer;
- structured error model;
- `options.max_cost_cny=8.0` hard stop semantics;
- focused tests and report.

Forbidden in this option unless separately authorized:

- production deployment;
- service restart;
- Luceon runtime wiring;
- upload/pressure validation;
- DB/MinIO/Docker volume/data cleanup;
- model/config/secret/sample mutation beyond test fixtures;
- readiness/L3/pressure PASS/go-live claim.

### Option B: Do Not Mutate Mineru2Table Yet

Pause external implementation. Continue only Luceon-side disabled mock/UI/protocol work.

Risk: Luceon may overbuild against a protocol the external service does not yet implement.

### Option C: One More Read-Only External Implementation Plan

Ask Architect to write a more detailed external implementation plan for Mineru2Table before any code changes.

Risk: slower progress, but lower implementation ambiguity.

## Director Recommendation

Recommend Option A.

Reason: the core blocker is now clearly external-service protocol support. Continuing Luceon real-integration work before Mineru2Table implements ObjectRef jobs, durable job state, idempotency, provenance, structured errors, and hard cost limits would create fragile adapter code around a nonexistent production contract.

If the user does not respond for two heartbeat cycles, Director should not auto-authorize external repository mutation. The conservative automatic path, if needed, should be Option C: a read-only implementation plan or HOLD record.

