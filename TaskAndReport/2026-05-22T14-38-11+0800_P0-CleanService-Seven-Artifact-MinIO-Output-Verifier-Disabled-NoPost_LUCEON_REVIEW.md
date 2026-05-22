# Task 248 Luceon Review

## Decision

`CHANGES_REQUIRED_PROVENANCE_INPUTS_ARRAY_COMPATIBILITY_GAP`

Task 248 is not accepted yet. The implementation is directionally correct and
the submitted branch stays within the expected code/test/control-plane scope,
but the async artifact verifier rejects the current Mineru2Table provenance
shape that Task 245/246 accepted as the real successful `v2` sample.

## Reviewed Evidence

- Remote branch: `origin/lucode/TASK-20260522-142123`
- Reviewed remote HEAD: `6d64212c25ad0afa64bf1251b3b3e9613612f200`
- Claimed/ledger HEAD mismatch: submitted ledger records
  `d59da662be746ef475d2927167f8fc0cd4ffae79`, but the physical remote branch
  HEAD is `6d64212c25ad0afa64bf1251b3b3e9613612f200`.
- Diff scope:
  - `TaskAndReport/2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md`
  - `TaskAndReport/TASK_TRACKING_LIST.md`
  - `server/services/cleanservice/output-verifier.mjs`
  - `server/tests/cleanservice-output-verifier-smoke.mjs`
- `git diff --check origin/main..origin/lucode/TASK-20260522-142123`: exit 0.
- No `server/services/cleanservice/cleanservice-worker.mjs`,
  `protocol.mjs`, `worker-factory.mjs`, `http-transport.mjs`, Docker, env,
  package, frontend, docs architecture, private role, or external
  Mineru2Table source files were modified.

## Positive Findings

- `REQUIRED_CLEAN_ARTIFACTS` now contains the seven required roles, including
  `unresolved_anchors` and `metrics`.
- A new async verifier fetches artifact contents through an injected reader and
  does not require real MinIO.
- The focused smoke suite covers successful `v2`-style output, zero-token
  false-completed rejection, missing token rejection, wrong assetVersion prefix,
  empty markdown, invalid JSON, missing object, unresolved anchors, and
  `input size_bytes=0` compensation.
- Focused checks run by Luceon in an isolated worktree passed:

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

All commands above exited 0 in Luceon's review worktree.

## Blocking Finding

### F1. Async verifier rejects current Mineru2Table `provenance.inputs[0]` shape

Current external Mineru2Table provenance generator writes input provenance as:

```text
provenance.inputs[0].bucket
provenance.inputs[0].object
provenance.inputs[0].sha256
provenance.inputs[0].size_bytes
```

Luceon verified this from the local deployed source file:

```text
/Users/concm/prod_workspace/Mineru2Tables/src/core/provenance/generator.py
```

The submitted `verifyCleanServiceOutputArtifacts(...)` implementation only
checks:

```text
provenanceObj.input.bucket
provenanceObj.input.object
provenanceObj.input.sha256
provenanceObj.input.size_bytes
```

Therefore a Task 245-shaped real provenance object with `inputs: [...]` fails
the verifier even when bucket/object/SHA are correct.

Luceon reproduced the failure with an in-memory fixture matching the real
`inputs[0]` shape. The result was:

```json
{
  "ok": false,
  "cleanState": "protocol-failure",
  "errors": [
    "provenance-input-bucket-mismatch",
    "provenance-input-object-mismatch",
    "provenance-input-sha256-mismatch"
  ],
  "warnings": [],
  "unresolvedAnchorCount": 0
}
```

This violates the Task 248 mainline acceptance target: accept a Task 245-shaped
`v2` success fixture while still rejecting Task 242 false-completed output.

## Narrow Return Requirements

Lucode should make a narrow correction only:

1. Update the async verifier to normalize provenance input from both supported
   shapes:
   - preferred/current service shape: `provenance.inputs[0]`;
   - backward-compatible shape, if kept: `provenance.input`.
2. Use the normalized input for bucket/object/SHA checks and `size_bytes=0`
   warning/compensation.
3. Update `cleanservice-output-verifier-smoke.mjs` so its positive provenance
   fixture uses the real current `inputs: [{ ... }]` shape.
4. Add or adjust a regression assertion proving `inputs[0].size_bytes=0`
   produces `warnings.includes('input-size-bytes-zero')` and compensated
   `inputSizeBytes`.
5. Correct the report and ledger branch HEAD to the physical remote HEAD after
   the amended branch is pushed.

Do not widen the task into worker wiring, trigger API, polling, DB persistence,
real MinIO verification, Docker/env changes, or real job dispatch.

## Review Boundary

This review performed no runtime/data mutation: no `POST /api/v1/jobs`, no LLM
call, no MinIO object write/delete/cleanup, no DB write, no Docker operation,
and no external Mineru2Table code change.

No UAT, L3, pressure-pass, release readiness, production readiness, or go-live
claim is made or accepted.
