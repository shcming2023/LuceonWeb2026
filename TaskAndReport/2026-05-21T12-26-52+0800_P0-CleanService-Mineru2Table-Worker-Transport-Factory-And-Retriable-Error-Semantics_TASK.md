# TASK-20260521-122652-P0-CleanService-Mineru2Table-Worker-Transport-Factory-And-Retriable-Error-Semantics

Issued At: 2026-05-21T12:26:52+0800

Owner: lucode

Reviewer: luceon

Priority: P0

Status: 待执行

## 1. Mainline Objective

Connect the newly accepted Mineru2Table HTTP transport foundation into a bounded
CleanService worker/client factory path, still disabled by default and still
validated only against mock HTTP.

This task answers the next mainline question:

```text
Can Luceon construct a production-shaped CleanServiceWorker/client stack that
selects the Mineru2Table HTTP transport when explicitly enabled, while keeping
default runtime no-op and preserving error semantics needed for later retry
control?
```

## 2. Current Evidence

Task 228 accepted:

- branch:
  `lucode/task-228-cleanservice-http-transport@4a3ae56bd55aea086c29df81b54f511423da3373`
- implementation merge commit:
  `8281953`
- new transport:
  `server/services/cleanservice/http-transport.mjs`
- new mock smoke:
  `server/tests/cleanservice-http-transport-smoke.mjs`

Luceon reran:

```text
CleanService HTTP Transport Smoke: PASS 7/7
Existing CleanService smokes: PASS 4/4
tsc --noEmit: exit 0
```

Luceon also found a bounded follow-up gap:

```text
The HTTP transport marks 5xx errors as retriable=true, but
createCleanServiceClient() normalization currently returns retriable=false at
the client result.
```

This task must close that gap under mock tests.

## 3. Critical Path Scope

Do only the minimum required for mock-safe worker transport wiring:

1. Add a bounded CleanService factory/composition layer that creates a
   CleanService client/worker with Mineru2Table HTTP transport only when
   config explicitly enables CleanService and provides an endpoint.
2. Preserve default `CLEANSERVICE_ENABLED=false` disabled-noop behavior.
3. Ensure missing endpoint/API configuration does not cause a real request and
   is reported as explicit configuration failure.
4. Propagate transport-level `retriable=true` for 5xx/network-like failures
   through the normalized client result when the transport exposes that flag.
5. Validate the worker/factory stack against a mock HTTP server only.
6. Preserve canonical Raw Material and legacy parsed-only boundaries.

The expected output is not a scheduler or production activation. It is a bounded
factory path that future tasks can call.

## 4. Environment And Write Boundary

Primary Luceon workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed files/modules:

- `server/services/cleanservice/**`
- focused tests under `server/tests/**`
- `TaskAndReport/2026-05-21T12-26-52+0800_P0-CleanService-Mineru2Table-Worker-Transport-Factory-And-Retriable-Error-Semantics_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden files/operations:

- no frontend `src/**` changes;
- no upload-server route wiring;
- no scheduler/timer activation;
- no Docker/Compose/env/secrets edits;
- no DB migrations or DB mutation;
- no MinIO object mutation;
- no real LLM call;
- no real HTTP call to `http://127.0.0.1:8000`;
- no `POST /api/v1/jobs` to the real Mineru2Table service;
- no webhook callback implementation;
- no MinIO output ingestion;
- no RawMaterial2CleanMaterial implementation;
- no `AGENTS.md` or `.agents/**` tracking, deletion, or citation as project
  facts.

## 5. Required Behavior

### Default Disabled Path

With default environment/config:

- worker/client stack is constructible;
- `tickOnce()` remains `disabled-noop` or equivalent no-submit result;
- no transport function is called;
- no HTTP request is made.

### Explicit Mock-Enabled Path

With a mock endpoint and explicit enablement:

- worker/client stack uses Mineru2Table HTTP transport;
- canonical Raw Material evidence submits exactly one mock `POST /api/v1/jobs`;
- request payload remains Protocol v1 shaped and source-reference/ObjectRef
  based;
- response is normalized and persisted consistently with existing CleanService
  metadata semantics.

### Configuration Failure Path

If CleanService is enabled but endpoint is missing:

- no HTTP request is made;
- the result records explicit configuration/transport failure;
- the error is not treated as success.

### Retriable Error Semantics

For mock 5xx or transport errors that carry `retriable=true`:

- normalized client result must preserve `job.error.retriable=true`.

For mock 4xx:

- normalized client result must preserve or produce `job.error.retriable=false`.

Timeouts must remain retriable.

## 6. Data Governance Red Lines

1. **ID-only extraction**: source selection must remain stable Block ID /
   ObjectRef based; do not copy or invent source text.
2. **Asset hash locking**: do not rename image/audio/resource hash names.
3. **Pure structure boundary**: this task only wires `toc-rebuild` job
   submission foundation; do not implement RawMaterial2CleanMaterial or free-text
   rewriting.

## 7. Fast Validation Target

Minimum useful proof:

```text
Default worker factory does nothing; mock-enabled worker factory sends exactly
one Protocol v1 POST to a mock server; 4xx/5xx/timeout error semantics are
normalized correctly; no real local Mineru2Table endpoint is touched.
```

Required smoke coverage:

- disabled/default factory path makes zero HTTP requests;
- enabled mock factory path submits exactly one `POST /api/v1/jobs`;
- missing endpoint makes zero HTTP requests and reports explicit failure;
- legacy parsed-only task makes zero HTTP requests;
- 4xx result is non-retriable;
- 5xx result is retriable at normalized client result;
- timeout remains retriable;
- test suite proves no request targets `127.0.0.1:8000`.

## 8. Stop Rule

Stop and report instead of widening scope if:

- wiring requires changing `upload-server.mjs` or production route behavior;
- scheduler/runtime activation is needed;
- real Mineru2Table calls are needed to prove behavior;
- DB schema changes are needed;
- endpoint/API key handling would require editing env or secrets;
- the scope starts including webhook callbacks, output ingestion, UI states, or
  RawMaterial2CleanMaterial.

## 9. Deferrable Side Work

Record but do not implement:

- real loopback dispatch to the local Mineru2Table service;
- runtime flag enablement;
- API-token enforcement between Luceon and Mineru2Table;
- webhook callback endpoint;
- output ingestion and verifier integration against real MinIO artifacts;
- operator UI state updates;
- backoff scheduler beyond preserving `retriable` semantics.

## 10. Positive Acceptance Criteria

Luceon can accept this task if:

- changed files stay within allowed boundary;
- default runtime remains disabled-noop;
- mock-enabled factory path works;
- missing endpoint is explicit and no-submit;
- 5xx retriable semantics are preserved in normalized client result;
- legacy parsed-only remains no-submit;
- focused smokes pass;
- changed JS/MJS files pass syntax checks;
- `git diff --check` passes;
- `tsc --noEmit` passes;
- report and ledger include exact branch/commit/check evidence.

## 11. Negative Acceptance Criteria

Return the task if:

- any real request reaches `127.0.0.1:8000`;
- default disabled behavior changes;
- legacy parsed-only evidence becomes dispatch-eligible;
- source text is copied or invented;
- Docker, env, secret, DB, MinIO, LLM, model, sample, or production data is
  mutated;
- runtime scheduling or upload-server route wiring is added;
- the report claims UAT, L3, production readiness, release readiness, pressure
  PASS, or go-live.

## 12. Report Requirements

Create the report at:

```text
TaskAndReport/2026-05-21T12-26-52+0800_P0-CleanService-Mineru2Table-Worker-Transport-Factory-And-Retriable-Error-Semantics_REPORT.md
```

The report must include:

- changed-file audit;
- final branch and commit SHA;
- factory/wiring design summary;
- exact mock request payload evidence;
- error semantics evidence for 4xx/5xx/timeout;
- focused smoke commands and exit codes;
- syntax/type-check commands and exit codes;
- explicit no-real-Mineru2Table-call statement;
- residual risks and deferred side work;
- ledger update to `Ready for luceon Review`.

## 13. Review Boundary

Passing this task means only:

```text
Luceon has a mock-verified worker/client factory path for Mineru2Table HTTP
transport, with disabled default behavior and preserved retry semantics.
```

It does not mean:

- real loopback dispatch is enabled;
- real MinIO/LLM behavior is validated;
- webhook callbacks work;
- Clean Material assets are produced;
- UAT, L3, production readiness, release readiness, pressure PASS, or go-live is
  achieved.
