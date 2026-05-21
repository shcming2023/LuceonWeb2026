# Luceon Review - TASK-20260521-122652-P0-CleanService-Mineru2Table-Worker-Transport-Factory-And-Retriable-Error-Semantics

Review Time: 2026-05-21T12:44:30+0800

Reviewer: Luceon

Decision: ACCEPTED_CODE_TEST_LEVEL_MOCK_WIRING_ONLY

## 1. Scope Reviewed

This review covers Task 229 only:

- CleanService worker/client factory path;
- mock-only Mineru2Table HTTP transport wiring;
- missing-endpoint explicit failure behavior;
- 4xx/5xx/timeout retriable semantics;
- legacy parsed-only no-submit behavior.

This review does not accept real dispatch to `127.0.0.1:8000`, runtime
enablement, scheduler/upload-server wiring, webhook callback integration,
MinIO/LLM end-to-end behavior, UAT, L3, production readiness, release readiness,
pressure PASS, or go-live.

## 2. Remote Evidence Rechecked

Luceon fetched and reviewed:

```text
origin/lucode/task-229-worker-factory-retriable
5c759a1d5e270c6a63edbfd55daab88823b6c568
```

Implementation diff from merge base:

```text
M server/services/cleanservice/protocol.mjs
A server/services/cleanservice/worker-factory.mjs
A server/tests/cleanservice-worker-factory-smoke.mjs
```

Luceon verified `git diff --check` on the implementation branch diff: exit 0.

## 3. Code Review Notes

Accepted implementation facts:

- `worker-factory.mjs` constructs a production-shaped worker/client stack but
  does not activate a scheduler, timer, upload-server route, or runtime loop.
- Transport is created only when `config.enabled` and `config.endpoint` are both
  present.
- Default config remains disabled and returns `disabled-noop`.
- Enabled-without-endpoint path keeps transport null and fails explicitly without
  HTTP.
- Legacy parsed-only evidence remains `skipped-policy` and makes zero HTTP
  requests.
- `normalizeCleanServiceTransportError()` now preserves
  `error.retriable === true`, fixing the 5xx retriable propagation gap found in
  Task 228 review.

No `src/**`, Docker/Compose/env/secrets, DB migrations, MinIO/LLM code, webhook
callback, output ingestion, or RawMaterial2CleanMaterial scope was changed.

## 4. Verification Rerun By Luceon

Luceon first reviewed and ran checks in detached worktree:

```text
/tmp/luceon-task-229-review.CWhv3w
```

Then Luceon merged the implementation branch into local `main` and reran key
checks on the integrated mainline.

Integrated implementation merge:

```text
Merge commit: 4e953d0534868412044b57e85d26c3070242f78c
Merged branch: origin/lucode/task-229-worker-factory-retriable
```

Checks rerun on integrated main:

```bash
node --check server/services/cleanservice/worker-factory.mjs
node --check server/services/cleanservice/protocol.mjs
node --check server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-raw-material-adapter-smoke.mjs
node server/tests/cleanservice-asset-version-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
```

Observed result:

```text
CleanService Worker Factory & Retriable Semantics Smoke: PASS 8/8
CleanService HTTP Transport Smoke: PASS 7/7
CleanService Worker Shell Smoke: PASS
CleanService Foundation Smoke: PASS
Raw Material Adapter Smoke: PASS
Asset Version Allocator Smoke: PASS
tsc --noEmit: exit 0
```

The factory smoke proves:

- disabled/default factory path makes zero HTTP requests;
- enabled mock factory path submits exactly one mock `POST /api/v1/jobs`;
- missing endpoint makes zero HTTP requests and reports failure;
- legacy parsed-only makes zero HTTP requests;
- 4xx is non-retriable;
- 5xx is retriable at normalized client result;
- timeout remains retriable;
- tests do not target the real `127.0.0.1:8000` service.

## 5. Runtime Boundary Rechecked

Luceon performed read-only runtime boundary checks:

```text
Mineru2Table main HEAD: af80ced635755384a2c878110013c3e2d8f9cb9a
docker inspect mineru2table-api ports:
{"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"8000"}]}
```

Read-only health remains:

```json
{
  "status": "unhealthy",
  "service_name": "toc-rebuild",
  "protocol_version": "v1",
  "checks": {
    "minio": "unconfigured",
    "llm": "not_configured",
    "dependencies": "ok"
  }
}
```

No real `POST` was made by Luceon.

## 6. Acceptance

Task 229 is accepted at code/test level:

```text
Luceon has a mock-verified worker/client factory path for Mineru2Table HTTP
transport, default-disabled behavior is preserved, missing endpoint is explicit,
and retriable transport errors are normalized correctly.
```

Accepted boundary:

- mock wiring only;
- no real dispatch;
- no runtime activation;
- no data or environment mutation.

## 7. Next Step

The next mainline step cannot be a silent implementation task because real
dispatch would create at least a Mineru2Table job-store write and may read/write
MinIO and call LLM depending on configuration.

Task 230 is therefore dispatched as a read-only preflight and authorization
dossier. It must not submit a job. Its purpose is to prepare the exact evidence
and Director decision needed before any controlled real loopback dispatch.

## 8. Final Boundary

This is not:

- real loopback dispatch;
- UAT;
- L3;
- production readiness;
- release readiness;
- pressure PASS;
- go-live.
