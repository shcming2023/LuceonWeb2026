# Luceon Review - TASK-20260521-121219-P0-CleanService-Mineru2Table-HTTP-Transport-Foundation-Disabled-By-Default

Review Time: 2026-05-21T12:26:52+0800

Reviewer: Luceon

Decision: ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION

## 1. Scope Reviewed

This review covers Task 228 only:

- Luceon-side CleanService Mineru2Table HTTP transport foundation;
- disabled-by-default behavior;
- mock HTTP `POST /api/v1/jobs` validation;
- legacy parsed-only no-submit behavior;
- explicit non-2xx and timeout failure behavior;
- no real Mineru2Table job submission.

This review does not accept real loopback dispatch, production/runtime enablement,
webhook callback integration, MinIO/LLM end-to-end behavior, Clean Material
output validation, UAT, L3, production readiness, release readiness, pressure
PASS, or go-live.

## 2. Remote Evidence Rechecked

Luceon fetched and reviewed the reported branch:

```text
origin/lucode/task-228-cleanservice-http-transport
4a3ae56bd55aea086c29df81b54f511423da3373
```

The implementation branch was based on the Task 228 dispatch commit
`a611c40133f2c9efe442604ad238a4d4dbbdbab4`; the control-plane report was later
committed to `main` as `038d9b05112202bcac7ea46326b179a494f44842`. Therefore
two-dot diff against current `origin/main` shows report/ledger divergence, but
the implementation delta from the merge base is correctly limited to:

```text
A server/services/cleanservice/http-transport.mjs
A server/tests/cleanservice-http-transport-smoke.mjs
```

Actual line counts after Luceon review:

```text
server/services/cleanservice/http-transport.mjs     173 lines
server/tests/cleanservice-http-transport-smoke.mjs  387 lines
```

Luceon corrected the submitted report line-count evidence accordingly.

## 3. Code Review Notes

Accepted implementation facts:

- `createMineru2TableHttpTransport()` is isolated in a new module.
- No existing runtime module is modified by the branch.
- Disabled default remains enforced by `createCleanServiceClient()` before the
  transport is called.
- The mock smoke captures exactly one canonical `POST /api/v1/jobs` for canonical
  Raw Material evidence.
- Legacy parsed-only evidence persists `skipped-policy` and does not submit.
- 4xx, 5xx, and timeout cases are explicit failures instead of silent success.
- Tests use ephemeral mock ports and do not call the real `127.0.0.1:8000`
  Mineru2Table service.

Luceon correction:

- The submitted report/test label described 5xx as "with retriable". The
  transport error object sets `retriable=true` for 5xx, but the current
  `createCleanServiceClient()` error normalization does not propagate that flag;
  a Luceon probe observed `retriable=false` at the normalized client result.
- This is not a Task 228 blocker because Task 228 required explicit failure, not
  retry/backoff behavior. Luceon does not accept client-level 5xx retriable
  propagation as completed.
- Task 229 is dispatched to wire the transport through a bounded factory path
  and close client-level retriable transport semantics under mock tests.

## 4. Verification Rerun By Luceon

Luceon first reviewed the implementation in an isolated detached worktree at:

```text
/tmp/luceon-task-228-review.yJKQaD
```

Then Luceon merged the branch into local `main` and reran the same core checks on
the integrated mainline.

Integrated implementation merge:

```text
Merge commit: 8281953
Merged branch: origin/lucode/task-228-cleanservice-http-transport
```

Checks rerun on integrated main:

```bash
node --check server/services/cleanservice/http-transport.mjs
node --check server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-raw-material-adapter-smoke.mjs
node server/tests/cleanservice-asset-version-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed result:

```text
CleanService HTTP Transport Smoke: PASS 7/7
CleanService Worker Shell Smoke: PASS
CleanService Foundation Smoke: PASS
Raw Material Adapter Smoke: PASS
Asset Version Allocator Smoke: PASS
tsc --noEmit: exit 0
```

Additional Luceon probes:

```text
disabled default: config.enabled=false, transport called=false,
status=not-enabled, cleanState=not-enabled

5xx normalized client result:
code=transport_error, status message includes 503, retriable=false
```

## 5. Acceptance

Task 228 is accepted at code/test level for the narrow mainline objective:

```text
Luceon now has a disabled-by-default, mock-verified HTTP transport foundation
for Mineru2Table Protocol v1 job submission.
```

Accepted facts:

- default runtime does not call transport;
- canonical Raw Material mock submit sends exactly one `POST /api/v1/jobs`;
- legacy parsed-only path does not submit;
- explicit 4xx/5xx/timeout failures are covered;
- no real Mineru2Table service call is accepted;
- implementation is merged locally into Luceon `main` for final control-plane
  push.

## 6. Final Boundary

This is not:

- real dispatch to `127.0.0.1:8000`;
- runtime enablement;
- webhook callback acceptance;
- MinIO/LLM job behavior validation;
- Clean Material output validation;
- UAT, L3, release readiness, production readiness, pressure PASS, or go-live.

The next mainline task is Task 229: worker/factory wiring under mock-only
validation plus client-level retriable error semantics.
