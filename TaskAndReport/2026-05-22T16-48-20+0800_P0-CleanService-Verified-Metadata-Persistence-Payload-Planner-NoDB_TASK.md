# TASK-20260522-164820-P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB

## 1. Mainline Objective

Build the next narrow implementation slice after Task 249.

Task 248 proved Luceon can verify Mineru2Table's seven `toc-rebuild`
artifacts. Task 249 proved Luceon can construct a bounded, persistence-ready
metadata candidate from a verified output.

Task 250 must answer the next mainline question:

> Can Luceon turn a verified CleanService metadata candidate into exact,
> shallow-merge-safe DB PATCH payloads without writing the database, dispatching
> a job, activating the worker, or touching runtime state?

This task is intentionally a dry-run persistence payload planner only. It must
not call the real Luceon DB.

## 2. Current Evidence

Accepted evidence on current `main`:

- Current Luceon main is at
  `c63145754238c12d57244d1aad1a520c7368c12d`.
- Task 245 produced a real standalone Mineru2Table success-path `v2` run for
  `materialId=1842780526581841`.
- Task 246 accepted the `v2` seven-artifact output quality threshold for
  minimal orchestration planning.
- Task 248 accepted `verifyCleanServiceOutputArtifacts(...)` at code/test
  level.
- Task 249 accepted `buildVerifiedCleanOutputMetadataCandidate(...)` at
  code/test level.

Accepted Task 249 boundary:

- the candidate builder preserves verifier-provided `sourceInput`;
- it blocks missing source traceability with
  `BLOCKED_VERIFIER_CONTRACT_GAP`;
- it preserves prompt/completion/total tokens;
- it does not persist anything.

Current code gap:

- no module currently converts the Task 249 candidate into exact task/material
  DB PATCH payloads;
- the existing DB server performs shallow metadata merges, so a future PATCH
  must be pre-merged locally to avoid replacing unrelated metadata branches;
- cost-source handling must be explicit before any future DB persistence.

## 3. Critical Path Scope

Implement only a mock-safe, in-memory persistence payload planner.

Suggested public API shape:

```js
const plan = buildCleanMetadataPersistencePlan({
  candidate,
  existingTask,
  existingMaterial,
  now: () => '2026-05-22T16:48:20.000Z',
});
```

Exact names may differ if they match local style, but the behavior and tests
below are mandatory.

The planner must produce dry-run payloads only:

```js
{
  ok: true,
  shouldApply: true,
  dryRun: true,
  serviceName: 'toc-rebuild',
  materialId,
  parseTaskId,
  taskPatch: { metadata: { ... } },
  materialPatch: { metadata: { ... } },
  audit: { ...bounded summary... }
}
```

The planner must never call `updateTask`, `updateMaterial`, `fetch`, MinIO,
Mineru2Table, DeepSeek, Docker, or any scheduler/worker.

## 4. True Preconditions

No runtime precondition is allowed for this task.

Tests must use in-memory fixtures shaped like:

- accepted Task 249 candidates;
- existing task/material records with unrelated metadata branches;
- blocked/non-persistable candidate outputs.

Do not connect to:

- real Luceon DB;
- real MinIO;
- real Mineru2Table;
- real DeepSeek or any LLM endpoint;
- Docker or Compose.

## 5. Environment And Write Boundary

Work in:

```text
/workspace/dev/Luceon2026
```

Allowed files:

```text
server/services/cleanservice/metadata-persistence.mjs              # new narrow module
server/services/cleanservice/metadata-summary.mjs                  # only if needed for cost-source preservation
server/tests/cleanservice-metadata-persistence-smoke.mjs           # new focused smoke
server/tests/cleanservice-output-ingestion-candidate-smoke.mjs     # only if metadata-summary cost behavior changes
TaskAndReport/2026-05-22T16-48-20+0800_P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Read-only unless a stop rule proves a narrow change is required:

```text
server/services/cleanservice/output-verifier.mjs
server/services/cleanservice/protocol.mjs
server/services/cleanservice/cleanservice-worker.mjs
server/services/cleanservice/worker-factory.mjs
server/services/cleanservice/http-transport.mjs
server/services/cleanservice/config.mjs
server/services/tasks/task-client.mjs
server/db-server.mjs
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

## 6. Required Planner Behavior

### 6.1 Pre-Merged PATCH Payloads

The planner must accept `existingTask` and `existingMaterial` inputs and
produce PATCH payloads that are safe for the current shallow-merge DB behavior.

Required behavior:

- preserve unrelated `existingTask.metadata` fields;
- preserve unrelated `existingTask.metadata.cleanServiceJobs` entries;
- set or replace only
  `existingTask.metadata.cleanServiceJobs['toc-rebuild']`;
- preserve unrelated `existingMaterial.metadata` fields;
- preserve unrelated `existingMaterial.metadata.cleanMaterials` entries;
- set or replace only
  `existingMaterial.metadata.cleanMaterials['toc-rebuild']`;
- never mutate the input `candidate`, `existingTask`, or `existingMaterial`
  objects.

The generated `taskPatch` and `materialPatch` must be ready for a later task to
pass to `/tasks/:id` and `/materials/:id`, but this task must not send them.

### 6.2 Persistable Candidate Gate

If `candidate.shouldPersist !== true` or `candidate.ok !== true`, return a
non-apply plan:

```js
{
  ok: false,
  shouldApply: false,
  dryRun: true,
  taskPatch: null,
  materialPatch: null,
  reason: 'candidate-not-persistable',
  errors: [...]
}
```

Do not generate DB PATCH payloads for false-completed, zero-token,
protocol-failure, missing-source, or verifier-contract-gap candidates.

### 6.3 Required Traceability Gate

For a persistable candidate, require the bounded source and output evidence
already accepted by Task 249:

- `materialId`;
- `parseTaskId` when available;
- `assetVersion`;
- `jobId`;
- task summary for `cleanServiceJobs['toc-rebuild']`;
- material summary for `cleanMaterials['toc-rebuild']`;
- source input bucket;
- source input object;
- source input sha256;
- source input size when available or compensated;
- seven artifact ObjectRefs;
- non-zero tokens total.

If any hard traceability field is missing, return `shouldApply=false` with a
specific reason such as:

```text
missing-source-input
missing-artifact-ref:<role>
missing-token-total
missing-task-summary
missing-material-summary
```

### 6.4 Cost Source Handling

Before DB persistence is ever allowed, cost handling must be explicit.

The planner and/or candidate builder must distinguish:

- cost copied from job stats;
- cost copied from verification/candidate summary;
- cost unavailable.

Rules:

- preserve `costCnyEstimated` when present;
- preserve `costCnyActual` when present, including `0.0`;
- never treat `0.0` actual cost as missing;
- do not invent cost values;
- include a bounded `costSource` or equivalent audit field in the plan;
- focused tests must cover a job-stats cost path and a verification/candidate
  cost path when job stats are absent.

If the existing verifier/candidate contract cannot supply cost from the
metrics-only path without widening into `output-verifier.mjs`, do not edit the
verifier in this task. Instead, record `BLOCKED_COST_SOURCE_CONTRACT_GAP` in
the report and keep the planner safe.

### 6.5 ID-Only / Source-Reference-Only Metadata

The planner must not put full artifact contents into the DB PATCH payload.

Allowed metadata:

- object refs;
- hashes;
- token and cost counters;
- clean state;
- warnings and errors;
- source input references;
- timestamps;
- bounded audit labels.

Forbidden metadata:

- full `readable_tree.md`;
- full `flooded_content.json`;
- full `logic_tree.json`;
- full `skeleton.json`;
- full `unresolved_anchors.json`;
- full `metrics.json`;
- full `provenance.json`;
- model-generated free text treated as source truth.

## 7. Data Governance Red Lines

This task touches AI-derived Clean Material metadata, so the following are hard
requirements:

1. ID-only/source-reference-only persistence: store ObjectRefs, hashes,
   counters, states, warnings, and bounded audit summaries only.
2. Asset hash locking: preserve artifact object names and hashes as supplied.
   Do not rename objects or invent hashes.
3. Pure structure boundary: do not generate LaTeX/TikZ/code output, and do not
   introduce custom macro-style output semantics.

## 8. Deferrable Side Work

Do not implement these in Task 250:

- real DB reads or writes;
- `updateTask` or `updateMaterial` calls;
- worker polling;
- worker activation;
- upload-server wiring;
- manual trigger API;
- real MinIO live reading;
- real Mineru2Table job dispatch;
- real LLM calls;
- dashboard/cockpit UI;
- batch scheduling;
- cleanup or reuse of Task 242 `v1` polluted prefix;
- RawMaterial2CleanMaterial.

Record any useful follow-up in the report residual debt section.

## 9. Stop Rules

Stop and report `BLOCKED_SCOPE_WOULD_EXPAND` if this task appears to require
editing worker/protocol/transport/upload-server wiring to pass.

Stop and report `BLOCKED_RUNTIME_DEPENDENCY_REQUIRED` if real DB, real MinIO,
real Mineru2Table, real Docker state, or real LLM access is needed for tests.

Stop and report `BLOCKED_COST_SOURCE_CONTRACT_GAP` if metrics-only cost
preservation requires changing `output-verifier.mjs`.

Stop and report `BLOCKED_METADATA_SHAPE_AMBIGUITY` if a safe shallow-merge PATCH
payload cannot be built without overwriting unrelated metadata branches or
storing full artifact contents.

## 10. Positive Acceptance Criteria

Luceon will accept this task if:

- the branch changes only allowed files;
- persistence planning is pure/in-memory;
- a Task 249-shaped persistable candidate produces both `taskPatch` and
  `materialPatch`;
- generated patches preserve unrelated existing metadata branches;
- generated patches update only `toc-rebuild` under `cleanServiceJobs` and
  `cleanMaterials`;
- blocked/non-persistable candidates produce no DB PATCH payloads;
- source input bucket/object/sha256/size remain present;
- all seven artifact ObjectRefs remain present;
- non-zero token totals remain present;
- cost handling preserves `0.0` actual cost and records a clear cost source;
- no full artifact content is stored in either patch;
- existing CleanService smoke tests remain green.

## 11. Negative Acceptance Criteria

Luceon will reject or return the task if it:

- writes Luceon DB records;
- sends any `POST /api/v1/jobs`;
- calls DeepSeek/LLM;
- connects to or mutates real MinIO;
- modifies Docker, Compose, env, credentials, package files, or external
  Mineru2Table code;
- wires anything into automatic worker execution;
- changes `CLEANSERVICE_ENABLED=false` default semantics;
- mutates input fixtures while building a plan;
- overwrites unrelated metadata branches in the dry-run patch;
- stores full artifact content in metadata summaries;
- claims UAT, L3, production readiness, pressure PASS, release readiness, or
  go-live.

## 12. Required Checks

Run and report exact commands and exit codes:

```bash
node --check server/services/cleanservice/metadata-persistence.mjs
node --check server/services/cleanservice/metadata-summary.mjs
node --check server/tests/cleanservice-metadata-persistence-smoke.mjs
node server/tests/cleanservice-metadata-persistence-smoke.mjs
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
TaskAndReport/2026-05-22T16-48-20+0800_P0-CleanService-Verified-Metadata-Persistence-Payload-Planner-NoDB_REPORT.md
```

The report must include:

- final branch and HEAD;
- exact changed file list;
- exact validation command outputs and exit codes;
- focused fixture coverage summary;
- bounded sample shape of the dry-run `taskPatch` and `materialPatch` without
  full artifact contents;
- explicit cost-source conclusion;
- explicit statement that no real DB write, POST, LLM, Docker, env, or real
  MinIO mutation occurred;
- residual debt and next suggested mainline task.

Update `TaskAndReport/TASK_TRACKING_LIST.md` to `Ready for luceon Review` only
after implementation and checks are complete.

## 14. Review Boundary

Acceptance of Task 250 will mean only:

- Luceon has a mock-safe dry-run planner that converts a verified CleanService
  metadata candidate into exact, shallow-merge-safe task/material PATCH
  payloads;
- the output is ready for a later separately authorized DB persistence task to
  consume.

It will not mean:

- real DB persistence is implemented;
- CleanService worker orchestration is active;
- Mineru2Table dispatch or polling is wired;
- the system passed UAT, L3, pressure testing, production readiness, release
  readiness, or go-live.
