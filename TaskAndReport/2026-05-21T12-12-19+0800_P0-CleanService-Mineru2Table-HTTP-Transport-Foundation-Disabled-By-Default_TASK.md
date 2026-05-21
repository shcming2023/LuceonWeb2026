# TASK-20260521-121219-P0-CleanService-Mineru2Table-HTTP-Transport-Foundation-Disabled-By-Default

Issued At: 2026-05-21T12:12:19+0800

Owner: lucode

Reviewer: luceon

Priority: P0

Status: 待执行

## 1. Mainline Objective

Add the first Luceon-side HTTP transport foundation for the independent
Mineru2Table service, while keeping it disabled by default and validated against
a mock HTTP server only.

This task answers the next mainline question:

```text
Can Luceon construct and submit a CleanService Protocol v1 Mineru2Table job
request from canonical Raw Material evidence through a bounded HTTP transport
layer, without enabling real runtime dispatch yet?
```

## 2. Current Evidence

The external Mineru2Table service is ready for wiring preparation at config and
read-only runtime level:

- Mineru2Table `main`:
  `af80ced635755384a2c878110013c3e2d8f9cb9a`
- local container:
  `mineru2table-api`
- host publication:
  `127.0.0.1:8000->8000/tcp`
- read-only health:
  HTTP 200 with `status=unhealthy`, `minio=unconfigured`,
  `llm=not_configured`
- Protocol v1 path surface:
  `/api/v1/jobs` POST, `/api/v1/jobs/{job_id}` GET,
  `/api/v1/jobs:from-storage` POST

Task 222 already established canonical Raw Material adapter and asset version
allocation boundaries:

- canonical input must use `eduassets-raw` `content_list_v2.json`;
- legacy parsed-only evidence remains `skipped-policy` / no-submit;
- `CLEANSERVICE_ENABLED=false` remains disabled-noop by default.

## 3. Critical Path Scope

Implement only the Luceon-side transport foundation needed for mock-safe
contract proof.

Required behavior:

1. Add or extend a CleanService Mineru2Table transport module under the existing
   CleanService service boundary.
2. Build a Protocol v1 job request from canonical Raw Material ObjectRef and
   bounded metadata already available from the CleanService adapter.
3. Submit the request through HTTP only when an explicit test/config path enables
   that transport.
4. Keep production/default runtime disabled so no automatic real POST occurs.
5. Cover the transport with a local mock HTTP server smoke test.
6. Preserve legacy parsed-only `skipped-policy` and ensure it cannot submit.

The preferred validation target is a mock server that captures exactly one
`POST /api/v1/jobs` request and returns a fake accepted job response.

## 4. Environment And Write Boundary

Primary Luceon workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed files/modules:

- `server/services/cleanservice/**`
- focused tests under `server/tests/**` for CleanService transport behavior
- existing test fixtures only when needed for focused smoke tests
- `TaskAndReport/2026-05-21T12-12-19+0800_P0-CleanService-Mineru2Table-HTTP-Transport-Foundation-Disabled-By-Default_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Conditionally allowed only if the existing codebase requires it:

- a small config-helper change under `server/**` for reading transport settings
- no broad runtime wiring

Forbidden files/operations:

- no frontend `src/**` changes;
- no DB migrations;
- no Docker/Compose/env file edits;
- no `.env` or secret mutation;
- no MinIO object mutation;
- no real LLM call;
- no real `POST` to `http://127.0.0.1:8000/api/v1/jobs`;
- no live Mineru2Table job submission;
- no upload-server route wiring unless a minimal existing CleanService worker
  call boundary already requires it and the report proves no runtime activation;
- no `AGENTS.md` or `.agents/**` tracking, deletion, or citation as project
  facts.

## 5. Required Contract Semantics

The outgoing mock `POST /api/v1/jobs` payload must be auditable and bounded.

It should include, using the existing protocol naming where already documented:

- stable service/job intent for `toc-rebuild`;
- material identifier and asset version context;
- canonical Raw Material input ObjectRef:
  bucket/prefix/object identity for `content_list_v2.json`;
- target output bucket/prefix reference;
- idempotency or request identity field if already established by the local
  protocol;
- callback/webhook fields only if the existing contract requires them; if not
  implemented, explicitly record as deferred;
- no copied source text beyond stable block/source references;
- no invented source truth.

If exact protocol field names differ in the current code/contracts, follow the
current repository contract and record the chosen shape in the report.

## 6. Data Governance Red Lines

For this task, the following are mandatory:

1. **ID-only extraction**: any model- or clean-service-facing source selection
   must reference stable Block IDs / source references only; no generated source
   truth is allowed.
2. **Asset hash locking**: image/audio/resource hash names must not be renamed
   by this transport layer.
3. **Pure structure boundary**: this task may transport structure-rebuild job
   requests only; it must not implement RawMaterial2CleanMaterial or free-text
   rewriting.

## 7. Fast Validation Target

Minimum useful proof:

```text
With default settings, CleanService remains disabled and performs zero HTTP
POSTs. With a focused mock transport setting in a smoke test, Luceon sends one
Protocol v1-shaped POST /api/v1/jobs to a mock server and records/returns the
accepted job identity without touching the real Mineru2Table service.
```

Required smoke coverage:

- disabled/default mode makes no HTTP request;
- canonical Raw Material request sends exactly one mock `POST /api/v1/jobs`;
- legacy parsed-only `skipped-policy` path makes no HTTP request;
- mock 4xx/5xx response is recorded as an explicit dispatch failure, not
  silently treated as success;
- timeout/network failure is bounded and reported;
- no test calls real `127.0.0.1:8000`.

## 8. Stop Rule

Stop and report instead of widening scope if:

- existing CleanService worker boundaries cannot support transport injection
  without broad runtime rewiring;
- DB schema changes are needed;
- the implementation would require editing Docker/Compose/env/secrets;
- any acceptance proof would require a real Mineru2Table job;
- the request payload cannot be built from canonical Raw Material ObjectRef
  without inventing data;
- the task starts to include webhook callback handling, MinIO output ingestion,
  UI state changes, or RawMaterial2CleanMaterial.

## 9. Deferrable Side Work

Record but do not implement:

- real loopback dispatch to `mineru2table-api`;
- enabling transport in production/local runtime;
- bearer/API-token enforcement between Luceon and Mineru2Table;
- webhook callback endpoint integration;
- MinIO output verification;
- operator UI states for clean jobs;
- RawMaterial2CleanMaterial service integration;
- retry/backoff hardening beyond focused mock failure semantics.

## 10. Positive Acceptance Criteria

Luceon can accept this task if:

- changed files stay within the allowed boundary;
- default runtime remains disabled/noop;
- mock transport smoke tests pass;
- request payload is protocol-shaped and provenance-safe;
- legacy parsed-only evidence cannot submit;
- non-2xx and network errors are explicit;
- `git diff --check` passes;
- changed JS/MJS files pass syntax checks;
- relevant focused smoke tests pass;
- `tsc --noEmit` passes if the repository currently requires it for server
  changes;
- report and ledger are updated with exact commit/branch evidence.

## 11. Negative Acceptance Criteria

Return the task if:

- any real `POST` reaches `127.0.0.1:8000`;
- `CLEANSERVICE_ENABLED=false` no longer stays disabled-noop;
- legacy parsed-only assets become dispatch-eligible;
- source text is copied or invented instead of using ObjectRefs/source IDs;
- Docker, DB, MinIO, model, sample, volume, secret, or production data is
  mutated;
- the task claims UAT, L3, production readiness, release readiness, pressure
  PASS, or go-live.

## 12. Report Requirements

Create the report at:

```text
TaskAndReport/2026-05-21T12-12-19+0800_P0-CleanService-Mineru2Table-HTTP-Transport-Foundation-Disabled-By-Default_REPORT.md
```

The report must include:

- changed-file audit;
- final branch and commit SHA;
- exact mock request payload shape, with sensitive values omitted;
- focused smoke test commands and exit codes;
- syntax/type-check commands and exit codes;
- explicit no-real-Mineru2Table-job statement;
- residual risks and deferred side work;
- ledger update to `Ready for luceon Review`.

## 13. Review Boundary

Passing this task means only:

```text
Luceon has a disabled-by-default, mock-verified HTTP transport foundation for
Mineru2Table Protocol v1 job submission.
```

It does not mean:

- real loopback dispatch is enabled;
- real MinIO/LLM behavior is validated;
- webhook callbacks work;
- Clean Material assets are produced;
- UAT, L3, production readiness, release readiness, pressure PASS, or go-live is
  achieved.
