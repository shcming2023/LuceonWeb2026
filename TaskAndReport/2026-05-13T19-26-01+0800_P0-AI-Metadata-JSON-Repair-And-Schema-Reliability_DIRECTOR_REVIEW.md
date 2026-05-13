# Director Review: P0 AI Metadata JSON Repair And Schema Reliability

Review time:
2026-05-13T19:26:01+0800

Reviewed task:
`TASK-20260513-191344-P0-AI-Metadata-JSON-Repair-And-Schema-Reliability`

Reviewed report:
`TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md`

## Decision

`ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

The DevelopmentEngineer implementation is accepted at code/test level.

This is not production deployment, upload validation, production readiness, L3, pressure PASS, release-readiness, or a go-live signal.

## Evidence Accepted

The report credibly identifies the Task 95 AI failure mechanism:

- the repair raw object was retrieved through the existing read-only proxy path from the parsed bucket;
- the object length was `2687`;
- `JSON.parse` failed with `Bad escaped character in JSON at position 2140`;
- the bad content was inside evidence text containing LaTeX-style strings such as `\sqcap`, `\angle`, and `\circ`;
- this is a deterministic JSON string-escape robustness gap, not a reason to weaken strict no-skeleton behavior.

The implementation is appropriately narrow:

- `server/services/ai/providers/base.mjs` adds deterministic repair for invalid JSON string escapes only inside JSON string literals;
- valid JSON escapes remain preserved;
- `parseJsonRobust()` applies normal parsing first, then deterministic invalid-escape repair for direct, fenced, and first-brace/last-brace JSON extraction;
- `server/services/ai/metadata-worker.mjs` applies the same repair in worker-side `extractJson()` and nested `content` parsing;
- `server/tests/ai-metadata-repair-hardening-smoke.mjs` covers the Task 95 LaTeX escape shape;
- strict no-skeleton paths remain unchanged.

## Director Verification

Director independently re-ran:

- `git diff --check` on the scoped files: pass;
- `node --check` for:
  - `server/services/ai/metadata-worker.mjs`;
  - `server/services/ai/providers/base.mjs`;
  - `server/services/ai/providers/ollama.mjs`;
  - `server/services/ai/metadata-standard-v0.2.mjs`;
  - `server/tests/ai-metadata-repair-hardening-smoke.mjs`;
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs`: pass;
- `node server/tests/ai-metadata-single-pass-guard-smoke.mjs`: pass;
- `node server/tests/ai-metadata-real-sample-smoke.mjs`: pass;
- `node server/tests/dependency-health-smoke.mjs`: `65 passed, 0 failed`;
- `npx pnpm@10.4.1 exec tsc --noEmit`: pass;
- `npx pnpm@10.4.1 run build`: pass with the existing Vite large-chunk warning.

## Boundary

Accepted code/test evidence only.

Not yet proven:

- production has this code path deployed;
- the Task 95 sample reaches `review-pending` or another trustworthy non-skeleton terminal result after deployment;
- long-run, batch, pressure, or L3 behavior.

Remaining non-blocking debt:

- Task 95 still exposed P1 MinerU observability debt: stale task metadata retained `log-observation-unreadable`, transient false MinerU failed events self-corrected, and task detail did not expose the terminal MinerU diagnostic as clearly as task list/material view.

## Next Action

Director is issuing:

`TASK-20260513-192601-P0-AI-JSON-Repair-Production-Deployment-And-Runtime-Validation`

Assignee:
`DevelopmentEngineer`

Scope:
minimum necessary production fast-forward and upload-server rebuild/recreate, followed by non-destructive runtime validation only.

Not authorized:
upload, pressure/batch/soak test, failed-task repair, reparse, re-AI, cleanup, destructive DB/MinIO/Docker volume/data mutation, model operation, broad restart/rollback, sample mutation, L3, pressure PASS, production-readiness, or release-readiness claim.
