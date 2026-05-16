# Director Review: P1 Mineru2Table CleanService Protocol Evidence Gap Review

- Task ID: `TASK-20260516-083529-P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review`
- Reviewed at: `2026-05-16T08:43:44+0800`
- Reviewed by: `Director`
- Report reviewed: `TaskAndReport/2026-05-16T08-35-29+0800_P1-Mineru2Table-CleanService-Protocol-Evidence-Gap-Review_REPORT.md`
- Luceon report commit reviewed: `912fbc4`
- External Mineru2Tables HEAD spot-checked: `43754fa`
- Result: `ACCEPTED_EVIDENCE_GAP_REAL_DISPATCH_BLOCKED_USER_DECISION_REQUIRED`

## Judgment

Accepted.

The Architect report is read-only, evidence-grounded, and correctly separates current Mineru2Table capability from Luceon CleanService Protocol v1 requirements.

Director spot-checked the same external checkout at `/Users/concm/prod_workspace/Mineru2Tables`:

- external repo is `main` at `43754fa`;
- live `/health` returns only basic `status`, `version`, `timestamp`, and `llm_status`;
- OpenAPI paths are `/health`, `/api/v1/extract`, `/api/v1/tasks`, and `/api/v1/tasks/{task_id}`;
- `api_server.py` uses `UploadFile` routes and in-memory `_task_store`;
- no `/api/v1/jobs`, MinIO ObjectRef submit/status, durable job state, protocol provenance, signed callback, or hard cost-stop evidence was found.

## Accepted Finding

Mineru2Table is a useful standalone TOC/table processing service, but it is not yet a CleanService Protocol v1 service.

Luceon real Mineru2Table dispatch remains blocked.

The accepted blocker list includes:

- no `POST /api/v1/jobs`;
- no `GET /api/v1/jobs/{job_id}`;
- no persistent job store;
- no idempotency by Luceon-owned `job_id`;
- no MinIO ObjectRef input/output support;
- no protocol `provenance.json`;
- no signed callback/webhook contract;
- no CleanService structured error model;
- no `options.max_cost_cny=8.0` hard stop semantics;
- no protocol identity fields across health/status/provenance.

## Director Decision

Task 203 is accepted and closed.

Because the next meaningful step would mutate an external repository/service, Director recorded Task 204 as a User decision instead of dispatching implementation automatically.

Director recommends Option A in Task 204: authorize a scoped external Mineru2Table CleanService Protocol v1 foundation implementation task. The scope should be code/test level in the external repository only, with no production deployment, no service restart, no Luceon runtime wiring, and no readiness claim.

## Boundaries Not Accepted

This review does not authorize:

- Luceon real Mineru2Table dispatch;
- runtime startup wiring;
- production deployment or validation;
- upload, pressure/batch/soak, submit-probe, retry/reparse/re-AI/cancel/repair/reset;
- DB/MinIO/Docker volume/data cleanup;
- external repository mutation before User authorization;
- legacy asset migration/backfill/hiding/deletion;
- global material ID replacement;
- release readiness, production readiness, L3, pressure PASS, production上线, or go-live.

