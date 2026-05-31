# P0 Popo Deployment Invocation Boundary Diagnosis And Minimal Stabilization

Task ID: `TASK-20260531-093334-P0-Popo-Deployment-Invocation-Boundary-Diagnosis-And-Minimal-Stabilization`

Issued at: `2026-05-31T09:33:34+0800`

Issued by: Luceon

Execution owner: Luceon

## Mainline Objective

Unblock Task 310 without modifying MinerU-Popo's mature upstream pipeline.

Current phase target remains:

```text
real Raw Material
-> MinerU-Popo toc-rebuild
-> readable rebuilt_markdown.md
-> operator review
```

This task focuses only on Luceon's deployment and invocation boundary for MinerU-Popo:

```text
Luceon CleanService adapter / runtime config / host worker backend
-> original MinerU-Popo pipeline entrypoints
-> stable real Raw Material invocation
```

Do not treat this as an upstream MinerU-Popo algorithm refactor.

## Current Evidence

Task 310 established that the dev MinIO credential/data issue is not the blocker. The production/control runtime has real Raw Material and can invoke Popo.

First real Task 310 sample:

```text
taskId=task-1780132950215
materialId=2787656755020028
v4 job=luceon-task-1780132950215-toc-rebuild-v4-1780189806166
```

Observed result:

```text
accepted=true
new assetVersion=v4
adapter final status=timeout
Luceon metadata status=failed / cleanState=failed
no readable rebuilt_markdown.md
```

Host worker failure evidence:

```text
RuntimeError: Invalid buffer size: 120.93 GiB
POST /generate HTTP/1.1 422 Unprocessable Entity
```

Important correction from Luceon read-only review:

```text
This is not evidence that upstream MinerU-Popo is broken.
This is evidence that Luceon's current deployment/invocation boundary is not stable enough.
```

Read-only review facts:

```text
/Users/concm/prod_workspace/MineruPopo remote:
  https://github.com/opendatalab/MinerU-Popo.git

origin/master:
  0484604 Update README_zh.md

local master:
  3c3eb6a Add Luceon host MPS worker backend
  ahead of origin/master by 5 local Luceon overlay commits
```

Original pipeline facts:

```text
post_processing/label_normalization.py
post_processing/run_inference.py
post_processing/inference.py
post_processing/get_json_tree.py
```

Luceon adapter currently calls the original pipeline sequence from `luceon_service/service.py`:

```text
mineru-result.zip
-> *_content_list.json + source PDF extraction
-> label_normalization.py
-> run_inference.py
-> get_json_tree.py
```

Original `inference.py` includes `adaptive_chunk`. Therefore the blocker must not be simplified to "Luceon bypassed all chunking".

v3/v4 comparison:

```text
v3 job luceon-task-1780132950215-toc-rebuild-v3-1780135742145 completed
v4 job luceon-task-1780132950215-toc-rebuild-v4-1780189806166 timed out
normalized input after removing job-specific path is identical
normalized input canonical sha256=d2cb085634607ff4da11456415ed7c2039836706b43590ffa9cb480354814ee6
```

Selected sample shape:

```text
PDF pages=3
rendered page size ~= 596x842 each
native image chunk pages=[1,2,3]
composite size ~= 596x2536
processor image_grid_thw=[[1,158,38]]
pixel_values shape=(6004,1536)
model vision_config.num_position_embeddings=2304
```

This suggests the risk is in the Luceon host-MPS/transformers invocation path and its handling of Popo visual inputs, worker lifecycle, or processor/backend configuration.

## Required Scope

Do now, in one mainline-focused loop:

1. Read-only confirm MinerU-Popo upstream expectations:
   - supported inference backends;
   - expected model runtime path;
   - input data format;
   - dynamic chunking behavior;
   - whether vLLM or another backend is the expected production path.
2. Compare Luceon adapter invocation against the upstream flow:
   - zip extraction;
   - content list selection and conversion;
   - source PDF selection;
   - normalized input;
   - generated page sets/chunks;
   - raw prompt/image payload shape.
3. Classify the blocker into exactly one primary class:
   - wrong backend choice;
   - host-MPS worker lifecycle/resource contamination;
   - processor/model configuration mismatch;
   - adapter input construction error;
   - expected upstream runtime missing from local deployment;
   - other, with evidence.
4. Implement only the minimum Luceon-side stabilization needed to test the classification, if evidence justifies it.
5. Re-run the Task 310 real sample path on at least:
   - the known v3/v4 sample `task-1780132950215`;
   - one additional eligible real Raw Material sample if the first passes.
6. Produce a report that either:
   - proves stable readable `rebuilt_markdown.md` output and reopens Task 310 success path; or
   - records an honest blocker with exact upstream/deployment boundary evidence.

## Allowed Write Boundary

Primary project records:

```text
TaskAndReport/*_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

Luceon2026 code only if needed for invocation boundary or metadata honesty:

```text
server/services/cleanservice/**
server/lib/task-actions-routes.mjs
docs/contracts/CleanService-MineruPopo-Adapter.md
docker-compose.popo.yml
```

MinerU-Popo local overlay only if evidence proves the bug is in Luceon's local wrapper, not upstream core:

```text
/Users/concm/prod_workspace/MineruPopo/luceon_service/**
/Users/concm/prod_workspace/MineruPopo/scripts/run_luceon_service.sh
/Users/concm/prod_workspace/MineruPopo/README_LUCEON.md
```

Any change under `/Users/concm/prod_workspace/MineruPopo` must be explicitly described as Luceon overlay/deployment glue and must not be presented as an upstream MinerU-Popo fix.

## Explicit Non-Goals

Do not:

- modify original MinerU-Popo algorithmic pipeline files unless a later Director decision explicitly authorizes an upstream fork;
- rewrite `post_processing/inference.py`, `label_normalization.py`, `get_json_tree.py`, or original data engine logic as a first response;
- rename or rewrite image hash assets from MinerU outputs;
- clean, delete, migrate, overwrite, or bulk-copy MinIO/DB data;
- run bulk reruns or scheduler work;
- broaden into UI polish, historical task cleanup, launchd hardening, pressure tests, or release readiness;
- claim upstream MinerU-Popo is defective without primary evidence;
- claim readiness, release-readiness, pressure PASS, L3, public launch, or go-live.

## Data Governance Red Lines

Because this task touches AI-assisted document reconstruction:

1. **ID/source-ref grounding**: outputs and diagnostics must remain grounded in MinerU source artifacts, block ids, or source refs. Do not invent educational content.
2. **Asset hash locking**: preserve original image/resource hash names and object identities.
3. **Pure output boundary**: generated Markdown/JSON artifacts must remain standard Markdown/JSON. No custom LaTeX/TikZ/macros.
4. **No silent fallback**: placeholder, skeleton, skipped, or raw MinerU-only output must not be labeled as successful Clean Material.

## Acceptance Criteria

Positive pass requires all of the following:

1. A concise root-cause memo in the report distinguishing:
   - upstream pipeline behavior;
   - Luceon adapter behavior;
   - host worker/backend behavior.
2. Evidence that no upstream core pipeline mutation was used unless explicitly authorized.
3. If a Luceon-side stabilization is implemented:
   - the diff is limited to allowed wrapper/config/invocation files;
   - it is explained as deployment/call-boundary stabilization, not upstream algorithm redesign.
4. Real run evidence:
   - known sample `task-1780132950215` produces a new readable `rebuilt_markdown.md`; or if it fails, the failure is faster and more semantically honest than timeout;
   - if the known sample passes, one additional eligible real Raw Material sample is run sequentially.
5. Metadata evidence:
   - task/material metadata agree with Popo job id, asset version, status, prefix, and artifact refs;
   - failure states remain honest and are not converted to `skipped` or success.
6. Focused checks appropriate to actual changes:

```bash
git diff --check
npx tsc --noEmit        # if Luceon2026 TypeScript/server code changed
npm run build           # if Luceon2026 app/server code changed
python -m py_compile    # if Python wrapper files changed
```

7. Report includes:
   - commands run;
   - runtime health;
   - v3/v4 comparison;
   - selected backend/config;
   - sample run evidence;
   - residual risks;
   - exact no-readiness/no-go-live boundary.

## Stop Rules

Stop and report instead of widening scope if:

- the evidence points to missing official runtime infrastructure that cannot be safely provisioned in this phase;
- the only possible fix requires upstream MinerU-Popo core algorithm changes;
- a second real run would require destructive data operations or bulk rerun;
- the work drifts into UI polish, historical migration, launchd hardening, or release readiness.

## Required Report

Create:

```text
TaskAndReport/2026-05-31T09-33-34+0800_P0-Popo-Deployment-Invocation-Boundary-Diagnosis-And-Minimal-Stabilization_REPORT.md
```

The report must clearly state one of:

```text
PASS_LUCEON_POPO_INVOCATION_BOUNDARY_STABILIZED
BLOCKED_<specific_boundary_blocker>
```
