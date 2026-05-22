# Task 248 Luceon Review v2

## Decision

`ACCEPTED_CODE_TEST_LEVEL_WITH_LUCEON_EVIDENCE_CORRECTION`

Task 248 is accepted at code/test level. This does not accept runtime
activation, worker orchestration, polling, trigger API, database persistence,
real Mineru2Table dispatch, UAT, L3, pressure-pass, release readiness, or
go-live state.

## Reviewed Evidence

- Remote branch: `origin/lucode/TASK-20260522-142123`
- Reviewed remote HEAD: `a1ee79f8b1507390d487442ff8c0fbe902338216`
- Diff scope:
  - `server/services/cleanservice/output-verifier.mjs`
  - `server/tests/cleanservice-output-verifier-smoke.mjs`
  - `TaskAndReport/2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md`
  - `TaskAndReport/TASK_TRACKING_LIST.md`
- `git diff --check origin/main..origin/lucode/TASK-20260522-142123`: exit 0.
- No worker, protocol, transport, config, upload-server, frontend, Docker,
  environment, package, private role, or external Mineru2Table source files were
  modified.

## Verification Performed By Luceon

In a detached review worktree, Luceon ran:

```text
node --check server/services/cleanservice/output-verifier.mjs
node --check server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
```

All commands above exited 0.

`npx pnpm@10.4.1 exec tsc --noEmit` initially failed in the detached worktree
because the worktree had no `node_modules`. Luceon linked the primary workspace
`node_modules` into the temporary review worktree and reran the command; it then
exited 0.

Luceon also reran the Review v1 reproduction using the current Mineru2Table
`provenance.inputs[0]` shape. The corrected verifier returned:

```json
{
  "ok": true,
  "cleanState": "completed",
  "errors": [],
  "warnings": ["input-size-bytes-zero"],
  "unresolvedAnchorCount": 0,
  "inputSizeBytes": 31543
}
```

This confirms the verifier now accepts the Task 245/246 real `v2` success shape
while preserving the `input size_bytes=0` warning/compensation.

## Accepted Behavior

- `REQUIRED_CLEAN_ARTIFACTS` now requires all seven `toc-rebuild` roles.
- The async verifier fetches artifact content through an injected reader.
- `flooded_content.json` is validated as a JSON array, not a `blocks` mapping.
- `metrics.json` accepts non-zero token output even when `cost_cny_actual=0.0`.
- Zero or missing tokens are rejected as `protocol-failure`, guarding against
  Task 242 false-completed output.
- Missing `metrics`, missing physical objects, invalid JSON, empty markdown,
  wrong assetVersion prefix, and provenance hash mismatch are rejected.
- Current service provenance shape `provenance.inputs[0]` is supported, with
  `provenance.input` retained only as fallback compatibility.
- `inputs[0].size_bytes=0` is not silently treated as complete provenance
  quality; it produces `input-size-bytes-zero` and compensated `inputSizeBytes`
  when expected raw input size is available.

## Luceon Evidence Corrections

During acceptance Luceon corrected control-plane evidence:

1. The report now records the physical reviewed remote HEAD
   `a1ee79f8b1507390d487442ff8c0fbe902338216`.
2. The report now includes Luceon's supplemental regression checks and the
   `inputs[0]` reproduction result.
3. The ledger row was repaired from the resubmitted row's column drift and
   stale/intermediate short commit references.

## Boundary

No runtime/data action was performed or accepted: no `POST /api/v1/jobs`, no LLM
call, no real MinIO object write/delete/cleanup, no Luceon DB write, no Docker
build/restart/down, no external Mineru2Table source edit, and no worker
activation.

The next mainline task may build the next narrow slice on top of this verifier,
but should keep dispatch/worker activation separately gated.
