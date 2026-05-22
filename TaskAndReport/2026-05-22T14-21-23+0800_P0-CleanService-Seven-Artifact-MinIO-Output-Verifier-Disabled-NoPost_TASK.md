# TASK-20260522-142123-P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost

## 1. Mainline Objective

Build the first implementation slice after Task 247: a strict, mock-safe
CleanService output verifier that can fetch and validate Mineru2Table's seven
`toc-rebuild` artifacts before Luceon ever persists Clean Material metadata.

This task answers one mainline question:

> Can Luceon reliably reject false `completed` Mineru2Table jobs by inspecting
> the actual output artifacts, without activating dispatch, polling, DB writes,
> or automatic worker behavior?

## 2. Current Evidence

Accepted evidence already on `main`:

- Task 245 produced a successful standalone Mineru2Table `v2` run for
  `materialId=1842780526581841`, `assetVersion=v2`, under
  `eduassets-clean/toc-rebuild/1842780526581841/v2/`.
- Task 245 verified exactly seven required output files:
  - `flooded_content.json`
  - `logic_tree.json`
  - `readable_tree.md`
  - `skeleton.json`
  - `unresolved_anchors.json`
  - `metrics.json`
  - `provenance.json`
- Task 245 metrics evidence: prompt tokens `6212`, completion tokens `54`,
  total tokens `6266`, estimated cost `0.006319999999999999`, actual cost `0.0`.
- Task 246 accepted the `v2` output quality threshold for minimal orchestration
  planning:
  - `flooded_content.json` is a JSON array, not a `blocks` mapping.
  - `flooded_content.json` and `skeleton.json` preserve 71 source blocks in
    order.
  - `metrics.json` has non-zero tokens.
  - `provenance.json` points back to the canonical Raw Material ObjectRef and
    source SHA, but has residual `input size_bytes=0` debt.
- Task 247 accepted a docs-level design that puts the seven-artifact verifier
  before trigger API, polling, metadata persistence, dashboard polish, or batch
  automation.

Current code gap:

- `server/services/cleanservice/output-verifier.mjs` currently checks only five
  artifact refs and inline provenance shape. It does not fetch MinIO objects or
  validate seven artifact contents.

## 3. Critical Path Scope

Implement the verifier only.

The implementation must:

1. Keep the existing synchronous `verifyCleanServiceOutput(...)` behavior
   backward-compatible for existing smoke tests.
2. Add a new async verifier path that accepts a completed job plus an injected
   read-only artifact reader/store.
3. Fetch and validate exactly the seven required `toc-rebuild` artifact roles.
4. Return a normalized result that can later be consumed by orchestration and
   metadata persistence code, but do not wire it into the worker yet.

Suggested API shape:

```js
await verifyCleanServiceOutputArtifacts(job, {
  artifactReader,
  expected: {
    serviceName: 'toc-rebuild',
    protocolVersion: 'v1',
    materialId,
    assetVersion,
    jobId,
    rawInput: {
      bucket: 'eduassets-raw',
      object: 'mineru/1842780526581841/v1/content_list_v2.json',
      sha256: 'f05394af3ad6107cdb7324fcffeb13fb43dcbcbaff46f838f291828867e182db',
      sizeBytes: 31543,
    },
  },
});
```

The exact function signature may differ if it better matches existing code, but
the behavior and tests below are mandatory.

## 4. True Preconditions

None that require runtime mutation.

This task must not require:

- real MinIO credentials;
- a running Mineru2Table container;
- `POST /api/v1/jobs`;
- Luceon DB writes;
- worker enablement;
- Docker rebuild/restart;
- cleanup or reuse of Task 242 `v1` polluted output prefix.

All tests must use a fake/in-memory artifact reader or injected fake MinIO
client.

## 5. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed files:

```text
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/output-artifact-reader.mjs          # optional helper only
server/tests/cleanservice-output-verifier-smoke.mjs              # new focused smoke
server/tests/cleanservice-foundation-smoke.mjs                   # only if needed for backward compatibility
TaskAndReport/2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Forbidden files and areas:

```text
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/protocol.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/config.mjs
server/upload-server.mjs
src/**
docs/**
docker-compose.yml
.env
.env.*
package.json
pnpm-lock.yaml
AGENTS.md
.agents/**
/Users/concm/prod_workspace/Mineru2Tables/**
```

Do not edit external Mineru2Table code in this task.

## 6. Required Verifier Behavior

### 6.1 Required Artifacts

The verifier must require all seven roles:

```text
flooded_content
logic_tree
readable_tree
skeleton
unresolved_anchors
metrics
provenance
```

Missing object refs or missing readable objects must return:

```text
ok=false
cleanState=protocol-failure
errors includes missing-artifact:<role> or missing-object:<role>
```

### 6.2 ObjectRef And Prefix Rules

For each artifact:

- require `bucket` and `object`;
- never store full artifact content in the verification summary;
- preserve artifact object names and hashes if supplied;
- if the expected `materialId` and `assetVersion` are provided, require the
  object path to be under:

```text
toc-rebuild/{materialId}/{assetVersion}/
```

Do not accept objects from Task 242 `v1` when the expected version is `v2`.

### 6.3 Content Rules

Minimum content rules:

- `flooded_content.json`: parseable JSON array, non-empty. Do not require a
  `blocks` mapping.
- `logic_tree.json`: parseable JSON, non-empty object or array.
- `readable_tree.md`: UTF-8 text, non-empty after trim.
- `skeleton.json`: parseable JSON, non-empty object or array.
- `unresolved_anchors.json`: parseable JSON. It may be an empty array/object.
- `metrics.json`: parseable JSON with `stats.tokens.total > 0`, or equivalent
  normalized token path if the actual file shape nests tokens differently.
  `cost_cny_actual=0.0` is allowed and must not fail by itself.
- `provenance.json`: parseable JSON with schema `luceon-provenance/v1`, matching
  service name, protocol version, materialId, assetVersion, jobId, and input
  ObjectRef/hash when expected values are provided.

### 6.4 Provenance `input size_bytes=0` Debt

If `provenance.json` has correct input ObjectRef/hash but reports
`size_bytes=0`, the verifier must not silently treat that as perfect.

Required behavior:

- return `ok=true` only if all other hard checks pass;
- include a warning such as `input-size-bytes-zero`;
- if `expected.rawInput.sizeBytes` or reader-provided stat data is available,
  include a compensated `inputSizeBytes` value in the result summary;
- do not mutate the downloaded provenance JSON.

### 6.5 Unresolved Anchors

If unresolved anchors count is greater than zero, the verifier should return:

```text
ok=true
cleanState=review-pending-partial
```

If the count is zero and all hard checks pass:

```text
ok=true
cleanState=completed
```

### 6.6 False Completed Guard

A job with `status=completed` must still fail if:

- any of the seven artifacts is missing;
- any required JSON is invalid;
- `readable_tree.md` is empty;
- `metrics` has zero/missing total tokens;
- provenance input ObjectRef or source SHA mismatches;
- artifact path points to the wrong assetVersion/prefix.

This is the main protection against the Task 242 false-success failure mode.

## 7. Deferrable Side Work

Do not implement these in Task 248:

- manual trigger API;
- polling loop;
- DB metadata persistence;
- material metadata shape migration;
- dashboard/cockpit UI;
- batch scheduling;
- real MinIO live verification against current buckets;
- real Mineru2Table job dispatch;
- RawMaterial2CleanMaterial.

Record any useful follow-up in the report residual debt section.

## 8. Stop Rules

Stop and report `BLOCKED_SCOPE_WOULD_EXPAND` if this task appears to require
editing worker/protocol/transport wiring to pass.

Stop and report `BLOCKED_RUNTIME_DEPENDENCY_REQUIRED` if a real MinIO instance,
real MinIO credentials, real Mineru2Table, or real job output is needed for the
tests. The tests must stay mock-safe.

Stop and report `BLOCKED_ARTIFACT_SHAPE_AMBIGUITY` if the accepted Task 245/246
artifact shapes cannot be represented from existing reports/design and would
force guessing beyond the task evidence.

## 9. Positive Acceptance Criteria

Luceon will accept this task if:

- the branch changes only allowed files;
- `REQUIRED_CLEAN_ARTIFACTS` includes all seven roles;
- the async artifact verifier fetches artifact content through an injected
  read-only reader;
- a Task 245-shaped success fixture passes with `completed`;
- a fixture with `cost_cny_actual=0.0` and non-zero tokens passes;
- a Task 242-shaped false-completed fixture with zero/missing tokens fails with
  `protocol-failure`;
- missing `metrics` and missing `unresolved_anchors` fail;
- invalid JSON and empty markdown fail;
- provenance input ObjectRef/hash mismatch fails;
- `input size_bytes=0` is returned as a warning/compensated summary, not silently
  ignored;
- unresolved anchors greater than zero map to `review-pending-partial`;
- existing CleanService smoke tests remain green.

## 10. Negative Acceptance Criteria

Luceon will reject or return the task if it:

- sends any `POST /api/v1/jobs`;
- calls DeepSeek/LLM;
- touches real MinIO objects or buckets;
- writes Luceon DB records;
- modifies Docker, Compose, env, credentials, package files, or external
  Mineru2Table code;
- wires the verifier into automatic worker execution;
- changes `CLEANSERVICE_ENABLED=false` default semantics;
- stores full artifact content in metadata summaries;
- accepts a completed job with zero tokens;
- accepts Task 242 `v1` polluted output when expecting `v2`;
- claims UAT, L3, production readiness, pressure PASS, release readiness, or
  go-live.

## 11. Required Checks

Run and report exact commands and exit codes:

```bash
node --check server/services/cleanservice/output-verifier.mjs
node --check server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-foundation-smoke.mjs
node server/tests/cleanservice-worker-shell-smoke.mjs
node server/tests/cleanservice-http-transport-smoke.mjs
node server/tests/cleanservice-worker-factory-smoke.mjs
node server/tests/cleanservice-payload-alignment-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

If a package manager command is unavailable, record the exact failure and run the
closest repo-standard equivalent without installing new dependencies.

## 12. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T14-21-23+0800_P0-CleanService-Seven-Artifact-MinIO-Output-Verifier-Disabled-NoPost_REPORT.md
```

The report must include:

- final branch and HEAD;
- exact changed file list;
- exact validation command outputs and exit codes;
- summary of positive and negative fixture coverage;
- statement that no real POST, LLM, DB, Docker, env, or real MinIO mutation
  occurred;
- residual debt and next suggested mainline task.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only
after implementation and checks are complete.
