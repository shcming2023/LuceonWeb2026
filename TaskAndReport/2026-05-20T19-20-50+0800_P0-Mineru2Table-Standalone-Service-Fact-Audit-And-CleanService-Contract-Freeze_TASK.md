# P0 Mineru2Table Standalone Service Fact Audit And CleanService Contract Freeze

- Task ID: `TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- Issued at: `2026-05-20T19:20:50+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Status: `待执行`
- Priority: `P0`
- Scope type: docs/contract/design audit only; no runtime implementation

## 1. Background

Task 220, Task 221, Task 222, and Task 223 establish the next-stage direction:

```text
PDF -> Raw Material -> Clean Material
```

Mineru2Table is the first independent CleanService candidate for `toc-rebuild`. RawMaterial2CleanMaterial remains a later independent service boundary and must not be collapsed into Mineru2Table.

Task 222 is now accepted at code/test level for the Luceon-side mock-safe foundation:

- canonical Raw Material adapter;
- Luceon-owned `assetVersion` allocator;
- legacy parsed-only `skipped-policy`;
- `CLEANSERVICE_ENABLED=false` disabled-noop safety.

This task does not authorize real dispatch. Its job is to freeze the facts of the currently deployed Mineru2Table standalone service and convert those facts into an implementation-ready CleanService contract gap map.

## 2. Current Evidence From Luceon

Luceon read-only evidence before issuing this task:

- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- Accepted Task 222 branch HEAD: `4be1aeadc0efb724ccc141b720d8baf6eef8c368`
- Mineru2Table workspace: `/Users/concm/prod_workspace/Mineru2Tables`
- Mineru2Table repository: `https://github.com/shcming2023/Mineru2Table2026`
- Mineru2Table local status: `main...origin/main`, clean at observation time
- Mineru2Table local HEAD: `43754fa0f3d18051b2d9a3ab4b3cf769a0d47239`
- Docker container observed: `mineru2table-api`
- Docker image observed: `mineru2tables-mineru2table`
- Port observed: `0.0.0.0:8000->8000/tcp`
- Container health observed: `Up 5 days (healthy)`
- `/health` observed response:

```json
{"status":"healthy","version":"1.0.0","timestamp":"2026-05-20T11:20:24.627795Z","llm_status":"not_configured"}
```

- OpenAPI observed paths:

```text
/health
/api/v1/extract
/api/v1/tasks
/api/v1/tasks/{task_id}
```

Important interpretation:

- `llm_status=not_configured` means current health is service-shell health only, not business-processing acceptance.
- Current Mineru2Table API accepts multipart `.json` or `.zip` uploads.
- Current Mineru2Table async task store is in-memory according to `api_server.py`, so task state is not restart-surviving.
- Current Mineru2Table API does not yet implement Luceon CleanService Protocol v1: no ObjectRef job request, no MinIO pull/write contract, no idempotent `job_id`, no HMAC webhook, no durable job store, no structured CleanService error envelope, and no required seven-file output contract.

## 3. Objective

Create a precise, implementation-ready fact audit and contract freeze for integrating Mineru2Table as an independent CleanService service.

The output must answer:

1. What does the currently deployed Mineru2Table service actually expose?
2. What input shape does it actually accept now?
3. What output shape does it actually return now?
4. What must change for it to satisfy CleanService Protocol v1?
5. Which side should own each change: Mineru2Table external service or Luceon main project?
6. What is the safest next implementation sequence after this audit?

## 4. Write Boundary

Allowed Luceon repository documentation files:

- optional new `docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- `docs/contracts/CleanService-Protocol-v1.md` only for narrow clarifications discovered by the audit
- optional new `docs/codex/decisions/2026-05-20_mineru2table-contract-freeze.md`

Allowed task-control files:

- `TaskAndReport/2026-05-20T19-20-50+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Read-only inspection is allowed for:

- `/Users/concm/prod_workspace/Mineru2Tables` if available in the execution environment;
- otherwise the GitHub repo `https://github.com/shcming2023/Mineru2Table2026`;
- Mineru2Table files such as `api_server.py`, `Dockerfile`, `docker-compose.yml`, `README.md`, `PRD.md`, `requirements.txt`, and `src/core/**`;
- Luceon docs/contracts relevant to CleanService;
- read-only `GET /health` and `GET /openapi.json` against `http://127.0.0.1:8000` if reachable.

Forbidden files and operations:

- no edits to `server/**` or `src/**`;
- no Luceon runtime code, worker, upload-server, frontend, Docker, Compose, lockfile, package, `.env*`, or secret edits;
- no edits, commits, pushes, restarts, rebuilds, or deployments in `/Users/concm/prod_workspace/Mineru2Tables`;
- no POST to `/api/v1/extract` or `/api/v1/tasks`;
- no real LLM/Mineru2Table processing run;
- no MinIO object, DB row, Docker volume, production data, model, or sample mutation;
- no migration, backfill, reparse, retry, repair, re-AI, pressure, upload, submit-probe, cleanup, or production validation;
- no `AGENTS.md` or `.agents/**` tracking/sync changes;
- no readiness, UAT, L3, pressure PASS, production-ready, release-ready, or go-live claim.

## 5. Required Analysis

### 5.1 Current Standalone API Truth

Document the current Mineru2Table API exactly from source and/or OpenAPI:

- routes;
- methods;
- auth mechanism and header name;
- request body types;
- response fields;
- error fields;
- task states;
- cleanup behavior;
- restart-survival limitations;
- Docker port and health behavior;
- environment variables required for LLM processing.

Explicitly distinguish:

- observed current behavior;
- inferred behavior from source;
- target behavior required by CleanService;
- unverified or unknown behavior.

### 5.2 Current Input/Output Contract

Record current input:

- `.json` upload;
- `.zip` upload;
- supported filenames discovered by source, including `content_list_v2.json`, `content_list.json`, and `middle.json`;
- any current local temp-file behavior;
- whether MinIO ObjectRefs are supported now.

Record current output:

- `markdown_tree`;
- `logic_tree`;
- `flooded_data`;
- `token_stats`;
- `processing_time_seconds`;
- async task wrapper fields;
- any files written to `/app/Output` or only returned in API bodies.

Then map current output to the Luceon target seven-file contract:

```text
eduassets-clean/
  toc-rebuild/{materialId}/{assetVersion}/
    logic_tree.json
    flooded_content.json
    readable_tree.md
    skeleton.json
    unresolved_anchors.json
    provenance.json
    metrics.json
```

For each target file, mark:

- available now;
- derivable but not emitted as file;
- missing;
- requires Mineru2Table change;
- requires Luceon-side wrapper only;
- must not be invented.

### 5.3 CleanService Protocol Gap Map

Compare the current API to `docs/contracts/CleanService-Protocol-v1.md`.

At minimum cover:

- `POST /api/v1/jobs` target vs current multipart task create;
- `GET /api/v1/jobs/{job_id}` target vs current task status;
- ObjectRef input from `eduassets-raw/mineru/{materialId}/{rawVersion}/content_list_v2.json`;
- service-owned MinIO read/write credentials;
- idempotent `job_id`;
- `material_id`, `parse_task_id`, `asset_version`;
- HMAC webhook with raw body signature headers;
- structured states and terminal errors;
- cost soft/hard semantics, especially Luceon `¥5` soft review and `¥8` hard stop;
- persistent job store requirement;
- provenance and metrics files;
- ID-only/source-reference governance.

### 5.4 Responsibility Split

Produce a table:

| Requirement | Current Mineru2Table | Target | Owner | Next Task Recommendation |
| --- | --- | --- | --- | --- |

Owner must be one of:

- `Mineru2Table service`;
- `Luceon main project`;
- `Both via protocol`;
- `User decision required`.

### 5.5 Transition Recommendation

Give an explicit recommendation between:

- **Option A**: implement CleanService Protocol v1 inside Mineru2Table first;
- **Option B**: build a Luceon adapter against current multipart `/api/v1/tasks`;
- **Option C**: temporary hybrid adapter with strict sunset.

The default Luceon preference is Option A unless the audit finds a concrete blocker.

If proposing Option B or C, define:

- exact feature flag;
- exact sandbox-only limit;
- no production traffic;
- no real MinIO write until output validation exists;
- sunset condition;
- rollback condition.

## 6. Mandatory Data Governance Red Lines

Because this task concerns AI data processing, educational assets, and future Clean Material, the audit must preserve these red lines:

1. ID-only extraction: service/model outputs that select source content must reference stable Block IDs or source references. They must not invent, rewrite, or hallucinate free text as source truth.
2. Asset hash locking: image/audio/resource assets must preserve original hash names through the pipeline. Services must not rename original resource hashes by convenience.
3. Pure layout/code-generation boundary: if later LaTeX/TikZ or code-like clean output is introduced, it must use standard packages and avoid custom commands/macros unless a future task explicitly authorizes otherwise.

## 7. Acceptance Criteria

Positive acceptance:

- current Mineru2Table API/runtime facts are documented with exact source or command evidence;
- target CleanService gaps are specific enough to become implementation tasks;
- MinIO input/output contracts are restated without ambiguity;
- current `llm_status=not_configured` is not overclaimed as business-processing readiness;
- task output contains a recommended next implementation sequence;
- report includes exact branch, final HEAD, changed files, verification commands, and exit codes.

Negative acceptance:

- no runtime source implementation in Luceon;
- no external Mineru2Table edit or push;
- no service restart/rebuild/deploy;
- no real processing request or LLM call;
- no DB/MinIO/Docker volume/model/sample/production-data mutation;
- no broad PRD rewrite that competes with Task 223;
- no UAT/L3/pressure PASS/release/go-live claim.

## 8. Required Verification

Run and record:

```bash
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

If Markdown-only docs are changed, no runtime test is required.

If any source file is changed despite the boundary, stop and explain why before asking Luceon for review; do not widen scope silently.

## 9. Report Requirements

The report must include:

- final branch name and full final branch HEAD;
- exact files changed;
- exact `git diff --name-status origin/main..HEAD` output;
- exact verification commands and exit codes;
- exact Mineru2Table evidence sources used, including local path or GitHub ref;
- clear current-vs-target status;
- recommendation for the next implementation task;
- a statement that no production/runtime/data/sample/model/Docker/DB/MinIO mutation occurred.

After completion, update the Task 224 ledger row to `Lucode 已回报待 Luceon 审查`, set `Next Actor=Luceon`, and push the branch.
