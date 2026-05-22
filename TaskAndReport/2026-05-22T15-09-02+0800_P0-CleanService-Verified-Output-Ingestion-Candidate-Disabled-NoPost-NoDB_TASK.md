# TASK-20260522-150902-P0-CleanService-Verified-Output-Ingestion-Candidate-Disabled-NoPost-NoDB

## 1. Mainline Objective

Build the next narrow implementation slice after Task 248.

Task 248 proved that Luceon can inspect the seven Mineru2Table `toc-rebuild`
artifacts and reject false `completed` output before trusting the job status.
Task 249 must answer the next mainline question:

> After seven-artifact verification passes, can Luceon construct a complete,
> bounded, persistence-ready metadata candidate without writing the database,
> dispatching a job, or activating the worker?

This task is intentionally not a trigger, polling, or persistence task. It only
builds the in-memory candidate shape that a later task can persist.

## 2. Current Evidence

Accepted evidence on current `main`:

- Task 245 produced a real standalone Mineru2Table success-path run for
  `materialId=1842780526581841`, `assetVersion=v2`, under
  `eduassets-clean/toc-rebuild/1842780526581841/v2/`.
- Task 246 accepted the `v2` seven-artifact output as sufficient for minimal
  orchestration planning, with guardrails.
- Task 247 accepted a docs-level design for minimal orchestration and metadata
  integration.
- Task 248 accepted code/test-level implementation of
  `verifyCleanServiceOutputArtifacts(...)`.
- Task 248 verifier behavior accepted by Luceon:
  - requires all seven `toc-rebuild` artifact roles;
  - reads artifacts through an injected reader;
  - accepts current `provenance.inputs[0]` shape;
  - rejects zero/missing token false-completed output;
  - rejects missing objects, invalid JSON, empty markdown, wrong assetVersion
    prefix, provenance mismatch;
  - warns `input-size-bytes-zero` and compensates `inputSizeBytes=31543`.

Current code gap:

- `server/services/cleanservice/metadata-summary.mjs` can build a metadata
  patch from a normalized job, but it does not yet have a focused path that
  consumes the strict Task 248 verifier result and produces a persistence-ready
  candidate with the seven-artifact, warnings, metrics, provenance, and
  source-input summary needed for safe future DB persistence.

## 3. Critical Path Scope

Implement only the candidate builder.

The implementation may either:

1. extend `server/services/cleanservice/metadata-summary.mjs`; or
2. add one narrow helper module under `server/services/cleanservice/**` and keep
   `metadata-summary.mjs` as the public adapter if that better preserves
   existing behavior.

Suggested API shape:

```js
const candidate = buildVerifiedCleanOutputMetadataCandidate({
  job,
  verification,
  now: () => '2026-05-22T00:00:00.000Z',
});
```

Exact names may differ if they match local style, but the behavior and tests in
this task are mandatory.

The candidate must be an in-memory object only. It must not call any DB helper,
HTTP client, worker, scheduler, MinIO client, or Docker command.

## 4. True Preconditions

No runtime precondition is allowed for this task.

Tests must use in-memory fixtures shaped like the accepted Task 248 verifier
outputs and Task 245/246 job evidence. Do not connect to:

- real Mineru2Table;
- real MinIO;
- real DeepSeek or any LLM endpoint;
- real Luceon DB;
- Docker or Compose.

## 5. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed files:

```text
server/services/cleanservice/metadata-summary.mjs
server/services/cleanservice/output-ingestion-candidate.mjs       # optional narrow module only
server/tests/cleanservice-output-ingestion-candidate-smoke.mjs    # new focused smoke
TaskAndReport/2026-05-22T15-09-02+0800_P0-CleanService-Verified-Output-Ingestion-Candidate-Disabled-NoPost-NoDB_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only only, do not edit:

```text
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/protocol.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/config.mjs
server/tests/cleanservice-output-verifier-smoke.mjs
server/tests/cleanservice-foundation-smoke.mjs
server/tests/cleanservice-worker-shell-smoke.mjs
server/tests/cleanservice-http-transport-smoke.mjs
server/tests/cleanservice-worker-factory-smoke.mjs
server/tests/cleanservice-payload-alignment-smoke.mjs
```

Forbidden files and areas:

```text
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

## 6. Required Candidate Behavior

### 6.1 Candidate Shape

For a verified successful or partial `toc-rebuild` result, produce a candidate
object with at least:

```js
{
  ok: true,
  shouldPersist: true,
  serviceName: 'toc-rebuild',
  materialId,
  parseTaskId,
  assetVersion,
  jobId,
  cleanState: 'completed' | 'review-pending-partial',
  metadataPatch: {
    taskMetadata: {
      cleanServiceJobs: {
        'toc-rebuild': { ...bounded job summary... }
      }
    },
    materialMetadata: {
      cleanMaterials: {
        'toc-rebuild': { ...bounded material summary... }
      }
    }
  },
  verificationSummary: { ...bounded verifier summary... }
}
```

The exact field layout may follow existing `buildCleanMetadataPatch(...)`, but
the candidate must be suitable for a later persistence task without requiring
full artifact content.

### 6.2 Required Job Summary Fields

The job summary under `taskMetadata.cleanServiceJobs.toc-rebuild` must include:

- `serviceName`;
- `protocolVersion`;
- `jobId`;
- `status` or `cleanState`;
- `materialId`;
- `parseTaskId`;
- `assetVersion`;
- `submittedAt`, `startedAt`, `finishedAt` when present;
- seven compact artifact ObjectRefs:
  - `flooded_content`;
  - `logic_tree`;
  - `readable_tree`;
  - `skeleton`;
  - `unresolved_anchors`;
  - `metrics`;
  - `provenance`;
- token/cost summary from job stats and/or verification:
  - prompt tokens if available;
  - completion tokens if available;
  - total tokens;
  - estimated cost when available;
  - actual cost when available, including `0.0`;
- `unresolvedAnchorCount`;
- verifier `warnings`, including `input-size-bytes-zero` when present;
- verifier `errors` only if the candidate represents a blocked/non-persistable
  result.

### 6.3 Required Material Summary Fields

The material summary under `materialMetadata.cleanMaterials.toc-rebuild` must
include:

- `serviceName`;
- `latestVersion`;
- `status` or `cleanState`;
- output prefix;
- provenance object name;
- metrics/provenance summary sufficient for later audit;
- `updatedAt`.

Do not store `flooded_content`, `logic_tree`, `readable_tree`, `skeleton`,
`unresolved_anchors`, `metrics`, or `provenance` full file contents.

### 6.4 Raw Input And Provenance Summary

If verifier result includes source input evidence, the candidate must preserve
bounded source traceability:

- input bucket;
- input object;
- input sha256;
- compensated input size when available;
- `input-size-bytes-zero` warning when applicable.

This is metadata only. Do not mutate or rewrite `provenance.json`.

### 6.5 Failure And Blocked Behavior

If the verifier result is not acceptable:

- do not produce a persistable success candidate;
- return `ok=false` or `shouldPersist=false`;
- preserve the failure `cleanState`, errors, and warnings;
- do not silently call it `completed`;
- do not drop the reason for false-completed protection, especially zero or
  missing tokens.

### 6.6 Backward Compatibility

Existing exported functions in `metadata-summary.mjs` must remain backward
compatible:

- `buildCleanTaskSummary(...)`;
- `buildCleanMaterialSummary(...)`;
- `buildCleanMetadataPatch(...)`.

If any existing smoke test depends on those exports, it must continue to pass.

## 7. Data Governance Red Lines

This task touches AI-derived clean output metadata, so the following are hard
requirements:

1. ID-only/source-reference-only persistence: do not persist model-generated
   free text as source truth in the metadata candidate. Store ObjectRefs,
   counters, states, warnings, and bounded audit summaries only.
2. Asset hash locking: preserve artifact object names and hashes as supplied.
   Do not rename objects or invent hashes.
3. Pure structure boundary: this task must not generate LaTeX/TikZ/code output,
   and must not introduce custom macro-style output semantics.

## 8. Deferrable Side Work

Do not implement these in Task 249:

- manual trigger API;
- polling loop;
- worker wiring;
- actual DB persistence;
- upload-server endpoint changes;
- dashboard/cockpit UI;
- batch scheduling;
- real MinIO live reading;
- real Mineru2Table job dispatch;
- cleanup or reuse of Task 242 `v1` polluted prefix;
- RawMaterial2CleanMaterial.

Record any useful follow-up in the report residual debt section.

## 9. Stop Rules

Stop and report `BLOCKED_SCOPE_WOULD_EXPAND` if this task appears to require
editing worker/protocol/transport/upload-server wiring to pass.

Stop and report `BLOCKED_RUNTIME_DEPENDENCY_REQUIRED` if real MinIO, real DB,
real Mineru2Table, real Docker state, or real LLM access is needed for tests.

Stop and report `BLOCKED_VERIFIER_CONTRACT_GAP` if Task 248 verifier output
lacks a field needed for safe candidate construction and fixing it would require
modifying `output-verifier.mjs`.

Stop and report `BLOCKED_METADATA_SHAPE_AMBIGUITY` if the candidate cannot be
made bounded without storing full artifact contents or inventing source truth.

## 10. Positive Acceptance Criteria

Luceon will accept this task if:

- the branch changes only allowed files;
- candidate construction is pure/in-memory;
- a Task 245-shaped verified result creates a persistable `completed`
  candidate;
- `costCnyActual=0.0` is preserved and does not fail by itself;
- non-zero token totals are preserved in the summary;
- all seven artifact ObjectRefs are present in the job summary;
- `provenance.inputs[0]` source ObjectRef/hash and compensated input size are
  preserved as bounded metadata;
- `input-size-bytes-zero` remains visible as a warning;
- unresolved anchors greater than zero produce a
  `review-pending-partial` persistable candidate;
- zero/missing tokens or verifier failure produces a non-persistable candidate;
- existing CleanService smoke tests remain green.

## 11. Negative Acceptance Criteria

Luceon will reject or return the task if it:

- sends any `POST /api/v1/jobs`;
- calls DeepSeek/LLM;
- connects to or mutates real MinIO;
- writes Luceon DB records;
- modifies Docker, Compose, env, credentials, package files, or external
  Mineru2Table code;
- wires anything into automatic worker execution;
- changes `CLEANSERVICE_ENABLED=false` default semantics;
- modifies `output-verifier.mjs` instead of stopping on a verifier contract gap;
- stores full artifact content in metadata summaries;
- accepts a failed verifier result as completed;
- claims UAT, L3, production readiness, pressure PASS, release readiness, or
  go-live.

## 12. Required Checks

Run and report exact commands and exit codes:

```bash
node --check server/services/cleanservice/metadata-summary.mjs
test ! -f server/services/cleanservice/output-ingestion-candidate.mjs || node --check server/services/cleanservice/output-ingestion-candidate.mjs
node --check server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
node server/tests/cleanservice-output-ingestion-candidate-smoke.mjs
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

If a command is unavailable, record the exact failure and run the closest
repo-standard equivalent without installing new dependencies.

## 13. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T15-09-02+0800_P0-CleanService-Verified-Output-Ingestion-Candidate-Disabled-NoPost-NoDB_REPORT.md
```

The report must include:

- final branch and HEAD;
- exact changed file list;
- exact validation command outputs and exit codes;
- positive and negative fixture coverage summary;
- the final candidate shape at a bounded field level, without full artifact
  contents;
- explicit statement that no real POST, LLM, DB, Docker, env, or real MinIO
  mutation occurred;
- residual debt and next suggested mainline task.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only
after implementation and checks are complete.

## 14. Review Boundary

Acceptance of Task 249 will mean only:

- Luceon has a mock-safe, code/test-level metadata candidate builder for
  verified Mineru2Table seven-artifact output;
- the candidate is ready for a later persistence task to consume.

It will not mean:

- DB persistence is implemented;
- CleanService worker orchestration is active;
- Mineru2Table dispatch or polling is wired;
- the system passed UAT, L3, pressure testing, production readiness, release
  readiness, or go-live.
