# P0 Independent CleanService Service Model PRD And Architecture Alignment

- Task ID: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- Issued at: `2026-05-20T14:31:29+0800`
- Issuer: `Luceon`
- Next Actor: `Lucode`
- Status: `待执行`
- Priority: `P0`
- Scope type: product/architecture documentation alignment only; no runtime implementation

## 1. Background

Director and Luceon have confirmed the next-stage architecture principle:

```text
Luceon main project = asset ledger, task orchestration, review, audit, UI, provenance, and acceptance control plane.
Mineru2Table, RawMaterial2CleanMaterial, and later AI processing services = independently developed and independently Docker-deployed services.
Integration = API-based CleanService collaboration with Luceon-owned identity, versions, cost, review, and provenance.
```

This task starts the new phase by aligning PRD and architecture docs before additional code work. Do not jump directly to real dispatch or service wiring.

## 2. Current Evidence

Repository state observed by Luceon before issuing this task:

- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- `origin/main`: up to date at task issue time.
- Task 220: accepted docs-level; establishes `PDF -> Raw Material -> Clean Material`.
- Task 221: accepted design-level; establishes safe implementation sequence and canonical Raw Material ObjectRef direction.
- Task 222: still `未接受已退回 / Lucode` for report/ledger evidence correction only. Its implementation evidence is close but not accepted yet.
- Task 219: still open and separate; do not modify or close it.

Existing relevant docs:

- `docs/prd/Luceon2026-PRD-v0.4-CleanService-Addendum.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`

External Mineru2Table deployment facts observed read-only by Luceon:

- Workspace: `/Users/concm/prod_workspace/Mineru2Tables`
- GitHub repository: `https://github.com/shcming2023/Mineru2Table2026`
- Current local HEAD observed: `43754fa0f3d18051b2d9a3ab4b3cf769a0d47239`
- Docker container observed: `mineru2table-api`
- Port observed: `0.0.0.0:8000->8000`
- `/health` response observed: `status=healthy`, `version=1.0.0`, `llm_status=not_configured`
- Current exposed API shape observed from OpenAPI/source: `/health`, `/api/v1/extract`, `/api/v1/tasks`, `/api/v1/tasks/{task_id}`.
- Current exposed API is useful standalone service evidence, but it is not yet CleanService Protocol v1 evidence.

No external Mineru2Table mutation, production deployment, runtime wiring, MinIO/DB/Docker volume mutation, upload, submit-probe, or real dispatch is authorized by this task.

## 3. Objective

Create the PRD/architecture alignment artifacts for the independent CleanService service model.

The output must make the following project facts explicit:

1. Mineru2Table is the first independent CleanService implementation for `toc-rebuild`.
2. RawMaterial2CleanMaterial is a later independent service and must not be collapsed into Mineru2Table.
3. Future services are separately developed, separately Docker-deployed, and integrated through a stable CleanService API contract.
4. Luceon remains the orchestration/control plane and owns task state, material identity, `assetVersion`, review, provenance, cost semantics, and audit.
5. Real integration remains blocked until protocol evidence and later implementation tasks are accepted.

## 4. Write Boundary

Allowed documentation files:

- optional new `docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md`
- `docs/prd/README.md`
- `docs/architecture/Luceon2026-Asset-Pipeline-Vision.md`
- `docs/contracts/CleanService-Protocol-v1.md`
- `docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md`
- optional new `docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md`

Allowed task-control files:

- `TaskAndReport/2026-05-20T14-31-29+0800_P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Read-only inspection is allowed for:

- relevant Task 220/221/222 files;
- `server/services/cleanservice/**`;
- `/Users/concm/prod_workspace/Mineru2Tables` source/docs/OpenAPI/Docker files;
- current read-only `/health` and OpenAPI checks against `http://127.0.0.1:8000`.

Forbidden files and areas:

- `server/**` source edits;
- `src/**` edits;
- `package.json`, lockfiles, Docker/Compose files, `.env*`, secrets, runtime overrides, local config;
- `AGENTS.md`;
- `.agents/**`;
- external Mineru2Table source edits, commits, pushes, restarts, rebuilds, or deployments;
- MinIO objects, DB rows, Docker volumes, model files, sample files, production data;
- any upload, submit-probe, pressure, retry, reparse, re-AI, repair, cleanup, migration, or backfill operation.

## 5. Required Content

### 5.1 PRD Alignment

Add or update product documentation so it clearly states:

- Luceon's current Phase 1 mainline remains `upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`.
- The new phase introduces optional future CleanService stages as independent service integrations.
- Independent services must not block or silently alter the current Phase 1 path unless a later explicit product decision says so.
- Operators must be able to distinguish:
  - Raw Material available;
  - `toc-rebuild` pending/running/completed/partial/failed/skipped;
  - RawMaterial2CleanMaterial pending/running/completed/partial/failed/skipped;
  - legacy parse-only assets.
- No partial, skeleton, raw parse, or fallback output may be represented as successful Clean Material.

### 5.2 Independent Service Model

Document the target service model:

| Responsibility | Luceon main project | Independent service |
| --- | --- | --- |
| Asset identity | owns `materialId`, `parseTaskId`, `assetVersion`, `job_id` | consumes identities, must not reassign them |
| Storage authority | owns ObjectRef contract and metadata summaries | reads allowed input refs, writes allowed output refs |
| Runtime | orchestrator/worker/registry | separate Docker service/repo |
| State | task/material metadata, operator review, audit | job state and service logs |
| Cost | soft limit, user decision, audit | hard limit enforcement and token/cost stats |
| Failure | product state and review semantics | structured service errors |

Include a `CleanService Registry` concept with at least:

- `serviceName`;
- `serviceType` / capability;
- implementation repository;
- Docker service/container name;
- endpoint and health path;
- protocol version;
- input asset type and required ObjectRefs;
- output asset type and required ObjectRefs;
- cost policy;
- feature flag / admission status;
- current integration status (`planned`, `mock-safe`, `protocol-ready`, `runtime-wired`, etc.).

### 5.3 Mineru2Table MinIO Contract

Define exactly what Mineru2Table should read from MinIO:

```text
eduassets-raw/
  mineru/{materialId}/{rawVersion}/
    content_list_v2.json
    raw_material_manifest.json        # optional but recommended
    assets/...                        # optional resource refs; original hash names preserved
```

Minimum required input ObjectRef:

```text
eduassets-raw/mineru/{materialId}/{rawVersion}/content_list_v2.json
```

Define exactly what Mineru2Table should write to MinIO:

```text
eduassets-clean/
  toc-rebuild/{materialId}/{assetVersion}/
    logic_tree.json
    flooded_content.json
    readable_tree.md
    skeleton.json
    unresolved_anchors.json
    provenance.json
    metrics.json                      # or token_stats.json, but choose and document one canonical name
```

The docs must state:

- Raw Material is never overwritten by Mineru2Table.
- Mineru2Table outputs are Clean Material preparation outputs, not final Clean Material.
- Luceon DB/API metadata stores only bounded summaries and ObjectRefs, not large artifact bodies.
- Original image/audio/resource hash names must remain locked.
- `provenance.json` is mandatory for successful completion.

### 5.4 RawMaterial2CleanMaterial Boundary

Define RawMaterial2CleanMaterial as a later independent service with:

- separate repository/deployment boundary, even if the repository name is not decided yet;
- input: Raw Material plus accepted or partial `toc-rebuild` outputs;
- output: final normalized Clean Material assets;
- distinct review/acceptance state from Mineru2Table;
- no permission to overwrite Raw Material or Mineru2Table outputs.

Propose initial output names for discussion, such as:

```text
eduassets-clean/
  raw2clean/{materialId}/{assetVersion}/
    clean_blocks.json
    clean_markdown.md
    clean_manifest.json
    quality_report.json
    unresolved_items.json
    provenance.json
    metrics.json
```

Mark these as proposed unless the docs already establish them as accepted contract.

### 5.5 Current Mineru2Table API Gap And Transition Strategy

Document the gap between current Mineru2Table deployment and target protocol:

- Current standalone API: `/api/v1/extract`, `/api/v1/tasks`, `/api/v1/tasks/{task_id}` with uploaded `.json` or `.zip`.
- Target CleanService Protocol: `/api/v1/jobs`, `/api/v1/jobs/{job_id}`, MinIO ObjectRefs, idempotent `job_id`, provenance, HMAC callback, structured errors, cost hard stop, service identity.
- Current `/health` being healthy is not business-processing acceptance, especially when `llm_status=not_configured`.

Provide a recommendation matrix for:

| Option | Description | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| A | Modify Mineru2Table to implement CleanService Protocol v1 | canonical, scalable | requires external repo work | recommended or not |
| B | Luceon adapter against current multipart `/api/v1/tasks` | faster prototype | not canonical; file-copy and provenance risks | transition only or reject |
| C | Hybrid temporary adapter plus protocol implementation | staged | more complexity | conditions |

The recommendation must be explicit. If recommending a temporary adapter, define hard limits and sunset conditions.

### 5.6 Future Task Sequence

Propose the next tasks after this PRD/architecture alignment, but do not execute them:

1. close Task 222 evidence-only correction;
2. accept/revise this Task 223 documentation alignment;
3. Mineru2Table external protocol implementation task in `/Users/concm/prod_workspace/Mineru2Tables` or its GitHub repo, if authorized;
4. Luceon CleanService Registry / transport mock-safe implementation;
5. single-sample controlled integration only after both protocol sides are accepted.

Keep Task 219 separate.

## 6. Mandatory Data Governance Red Lines

Because this task concerns AI data processing and educational assets, preserve these red lines:

1. ID-only extraction: service/model outputs that select source content must reference stable Block IDs or source references. They must not invent, rewrite, or hallucinate free text as source truth.
2. Asset hash locking: image/audio/resource assets must preserve original hash names through the pipeline. Services must not rename original resource hashes by convenience.
3. Pure layout/code-generation boundary: if later LaTeX/TikZ or code-like clean output is introduced, it must use standard packages and avoid custom commands/macros unless a future task explicitly authorizes otherwise.

## 7. Acceptance Criteria

Positive acceptance:

- PRD/architecture docs clearly encode the independent CleanService service model.
- Mineru2Table MinIO input/output contract is explicit and traceable.
- RawMaterial2CleanMaterial is separated from Mineru2Table.
- Current Mineru2Table deployment facts are described as current evidence without overclaiming protocol readiness.
- Transition strategy is explicit and contains a recommendation.
- Task 219 and Task 222 boundaries remain untouched except for noting their status.
- Report includes exact branch, final HEAD, changed files, validation commands, and exit codes.

Negative acceptance:

- no source/runtime implementation;
- no `server/**` or `src/**` edits;
- no Docker/Compose/config/secret edits;
- no external Mineru2Table mutation;
- no production deployment, restart, upload, submit-probe, pressure, retry, reparse, re-AI, cleanup, migration, or backfill;
- no DB/MinIO/Docker volume/model/sample mutation;
- no readiness, UAT, L3, pressure PASS, release, production-ready, or go-live claim;
- no tracking or synchronization of `AGENTS.md` or `.agents/**`.

## 8. Required Verification

Lucode must run and record exact commands and exit codes:

```bash
git diff --check origin/main..HEAD
git diff --name-status origin/main..HEAD
```

If Markdown or docs validation tooling already exists and is safe/non-mutating, run it and record the command. Do not invent unsupported "Markdown valid" claims without a command and exit code.

If read-only Mineru2Table checks are used as evidence, record exact commands and outputs, for example:

```bash
git -C /Users/concm/prod_workspace/Mineru2Tables rev-parse HEAD
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/openapi.json
```

Do not restart or rebuild the Mineru2Table container.

## 9. Report Requirements

The report must include:

- final branch name and full final branch HEAD;
- exact files changed;
- exact `git diff --name-status origin/main..HEAD` output;
- exact validation commands and exit codes;
- a short summary of the product/architecture decisions made;
- a list of remaining Luceon/User decisions;
- a clear statement that no source/runtime/production/data/external-repo mutation occurred.

After completion, update Task 223 in the ledger to `Ready for luceon Review`, set `Next Actor=Luceon`, and push the branch.
