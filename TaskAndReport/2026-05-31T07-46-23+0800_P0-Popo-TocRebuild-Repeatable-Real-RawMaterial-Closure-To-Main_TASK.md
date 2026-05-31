# P0 Popo TocRebuild Repeatable Real RawMaterial Closure To Main

Task ID: `TASK-20260531-074623-P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main`

Issued at: `2026-05-31T07:46:23+0800`

Issued by: Luceon

Execution owner: Luceon

Baseline branch:

```text
origin/codex/popo-async-toc-rebuild@16f7e02c18d84077a299b2d101b145a8d9a07b12
origin/main@16bb3eb26d183fd832712b601adb4a062c13aab4
```

## Mainline Objective

Prove the shortest current phase breakthrough:

```text
real Raw Material / MinerU parsed artifact
-> MinerU-Popo toc-rebuild
-> new versioned eduassets-clean/toc-rebuild/{materialId}/vN/
-> readable rebuilt_markdown.md
-> Luceon task/material metadata apply
-> operator can inspect the Clean-stage primary artifact
```

This task is not a UI polish task, not a broad historical compatibility task, and not an operations hardening task. The only success target is repeatable, real Popo/toc-rebuild output that can be reviewed as Clean-stage primary product.

Execution environment decision:

```text
Run the real-sample execution in /Users/concm/prod_workspace/Luceon2026
against the existing production/control runtime and its existing MinIO data.
```

Do not ask lucode to obtain raw MinIO credentials, do not sync production sample objects into the dev MinIO, and do not treat the dev container's empty MinIO as a blocker for this task. If the production/control runtime reveals a code defect, Luceon may issue a follow-up implementation fix to lucode after capturing exact evidence.

## Current Evidence

Task 308 proved one small PDF Popo run:

```text
task-1780132950215
material_id=2787656755020028
job_id=luceon-task-1780132950215-toc-rebuild-v3-1780135742145
result: completed
primary artifact: rebuilt_markdown.md readable
```

Runtime observed before issuing this task:

```text
Luceon dependency-health: ok=true blocking=false
Popo host worker: http://127.0.0.1:18083/health ok=true, device=mps, model_loaded=true
Popo adapter: http://127.0.0.1:18082/health ok=true, busy=false
```

Task 309 showed two important non-pass conditions:

```text
task-1780127147233 accepted a rerun request and generated v8,
but final metadata readback was status=canceled / cleanState=skipped.

After the Task 309 narrow correction, v9 correctly persisted objective Popo failure as
status=failed / cleanState=failed instead of skipped.
```

Therefore, **202 Accepted, job creation, skipped/canceled clean metadata, or objective failed-state metadata does not count as mainline success**.

## Required Scope

Do now:

1. Select real eligible samples with existing Material, MinerU result zip, parsed Markdown/full Markdown, MinIO accessibility, CleanService endpoint, and no running/pending toc-rebuild job.
2. Run Popo/toc-rebuild sequentially with hard cap 3 and stop-on-first-failure.
3. Produce at least 2 new successful real Popo/toc-rebuild invocations in this task, unless preflight finds fewer than 2 eligible samples. If fewer than 2 exist, stop and report the sample matrix instead of widening scope.
4. Require each passing sample to have:
   - terminal `completed` or explicit `review-needed` CleanService state;
   - new isolated `assetVersion` / prefix;
   - readable `rebuilt_markdown.md` via Luceon proxy;
   - readable `readable_tree.md`, `logic_tree.json`, `metrics.json`, and `provenance.json`;
   - task/material metadata pointing to the same job/version/prefix;
   - no overwrite of existing toc-rebuild versions.
5. If the current code blocks valid `failed` tasks or converts a legitimate rerun into `skipped`, implement the minimum lifecycle fix needed for real repeatability. Prefer excluding `canceled` from pass criteria for this phase unless a narrow, evidence-backed clean-attempt semantics fix is unavoidable.
6. After evidence passes, prepare the Popo branch as merge-ready for `main` with focused checks and an execution report.

## Allowed Write Boundary

Allowed if needed:

```text
server/lib/task-actions-routes.mjs
server/services/cleanservice/**
server/tests/**
src/app/pages/TaskDetailPage.tsx
src/app/components/CleanMaterialSummaryCard.tsx
src/app/components/CleanMaterialArtifactInspector.tsx
docs/contracts/CleanService-MineruPopo-Adapter.md
docker-compose.popo.yml
TaskAndReport/*_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Frontend changes are allowed only when they are necessary to prove that `rebuilt_markdown.md` is the primary inspectable product. Do not redesign the page, refactor layout, or continue Task 307 UI simplification inside this task.

Runtime actions allowed:

```text
read-only health checks
single-sample Popo/toc-rebuild POSTs for selected samples only
focused service rebuild/recreate only if required to run the current Popo branch code
readback through DB/upload proxy/Popo job API
```

## Explicit Non-Goals

Do not:

- perform bulk rerun, broad asset scan, scheduler/daemon activation, or retry queue work;
- run pressure, soak, large-PDF performance closure, or public release validation;
- clean, delete, move, copy, rename, or migrate DB/MinIO data;
- overwrite existing Clean Material versions;
- treat `canceled/skipped` clean metadata as successful output;
- solve all historical `canceled` task semantics unless it is the minimum blocker for this task's real repeatability proof;
- implement launchd/system-service management for the host MPS worker;
- continue UI tidying, evidence drawer polish, ProductsPage cleanup, or orphan component cleanup;
- change secrets, model files, sample source files, ports, SSH tunnel, branch protection, or release gate policy;
- claim readiness, release-readiness, production-readiness, pressure PASS, L3, public launch, or go-live.

## Data Governance Red Lines

Because this task touches AI-assisted document reconstruction and Clean Material:

1. **ID-only / source-ref-only grounding**: Popo/toc-rebuild outputs must remain grounded in MinerU source artifacts and stable source references. Do not invent source truth or free-text educational content as if it came from the source.
2. **Asset hash locking**: image/audio/resource hash names and original object identities must not be renamed or rewritten.
3. **Pure output boundary**: generated Markdown/structure artifacts must use standard Markdown/data formats only. Do not introduce custom macros or unverified package assumptions.
4. **No silent fallback**: raw MinerU output, skeleton files, skipped jobs, or placeholder trees must not be labeled as successful Clean Material.

## Acceptance Criteria

Positive pass requires all of the following:

1. Preflight sample matrix recorded with task id, material id, task state, zip object, parsed Markdown/full Markdown availability, existing toc-rebuild version/status, and eligibility decision.
2. At least 2 new real Popo/toc-rebuild runs complete sequentially, or a stop-rule report proves fewer than 2 eligible samples exist.
3. For every passing run:
   - HTTP request accepted;
   - final job state is `completed` or explicit `review-needed`;
   - `rebuilt_markdown.md` is readable and non-empty through Luceon proxy;
   - required technical artifacts are readable and tied to the same `assetVersion`;
   - task/material metadata agree on service name, job id, version, status, and artifact ObjectRefs;
   - old versions remain present and are not overwritten.
4. If a selected sample fails, stop immediately and classify the failure as:
   - lifecycle semantics blocker;
   - Popo service/output blocker;
   - artifact/object-ref blocker;
   - metadata apply blocker;
   - runtime dependency blocker.
5. Focused checks pass:

```bash
git diff --check origin/main...HEAD
npx tsc --noEmit
npm run build
```

6. Execution report includes curl/API evidence, DB/material readback evidence, proxy-file readback evidence, Popo job evidence, changed files, residual risks, and exact no-readiness/no-go-live boundary.

## Stop Rules

Stop and report instead of expanding scope if:

- Popo host worker or adapter is unhealthy and cannot be recovered by the already documented startup path;
- fewer than 2 eligible real samples exist;
- first selected sample fails before producing readable `rebuilt_markdown.md`;
- fixing the failure requires bulk migration, cleanup, broad status model redesign, scheduler work, or launchd/system-service work;
- the work starts drifting into UI polish rather than proving real Clean-stage output.

## Required Report

Create:

```text
TaskAndReport/2026-05-31T07-46-23+0800_P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main_REPORT.md
```

The report must clearly state one of:

```text
PASS_REPEATABLE_REAL_POPO_TOC_REBUILD_READY_FOR_MAINLINE_REVIEW
BLOCKED_<specific_blocker>
```

Do not use PASS wording if the outcome is only request acceptance, skipped metadata, mock output, or one-off single-sample success.
