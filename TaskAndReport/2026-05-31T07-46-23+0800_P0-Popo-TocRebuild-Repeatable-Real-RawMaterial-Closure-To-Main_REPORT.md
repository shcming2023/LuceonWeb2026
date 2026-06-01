# P0 Popo TocRebuild Repeatable Real RawMaterial Closure To Main Report

Task ID: `TASK-20260531-074623-P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main`

Reported at: `2026-06-01T11:18:01+0800`

Executor: Luceon

Result:

```text
PASS_REPEATABLE_REAL_POPO_TOC_REBUILD_READY_FOR_MAINLINE_REVIEW
```

## Summary

Task 310 is now closed as PASS.

The earlier blocker was resolved through the Task 313 MPS profile/progress-safe adapter and metadata apply patch-scope work. Luceon then performed the Task 310 closure run in the production/control runtime and verified two real Raw Material samples:

1. small real sample `task-1780132950215` / `2787656755020028`, new `v7`;
2. workbook-class real sample `task-1779854322261` / `3926938009250504`, `v8` from the accepted Task 313 production UAT.

Both samples have readable Clean-stage artifacts, bounded ObjectRefs, and consistent task/material metadata.

No readiness, release-readiness, pressure PASS, L3, public launch, or go-live claim is made.

## Runtime Environment

Workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Branch:

```text
codex/popo-async-toc-rebuild
```

Runtime health before execution:

```text
Popo adapter: http://127.0.0.1:18082/health ok=true, busy=false
Upload server: http://127.0.0.1:8081/__proxy/upload/health ok=true
Host MPS worker: http://127.0.0.1:18083/health ok=true, device=mps, model_loaded=true, last_error=null
```

Active bounded MPS profile:

```text
POPO_MPS_RENDER_SCALE=0.5
POPO_MPS_CHUNK_SIZE=10
POPO_MPS_MIN_PIXELS=3136
POPO_MPS_MAX_PIXELS=589824
POPO_MAX_NEW_TOKENS=256
POPO_JOB_TIMEOUT_SECONDS=3600
```

## Preflight Sample Matrix

| Task | Material | Task State | Raw Material Inputs | Existing toc-rebuild before final closure | Eligibility |
| --- | --- | --- | --- | --- | --- |
| `task-1780132950215` | `2787656755020028` | `review-pending` | `parsed/2787656755020028/mineru-result.zip`, `parsed/2787656755020028/full.md` | completed `v6` | selected for new final closure run |
| `task-1779854322261` | `3926938009250504` | `review-pending` | `parsed/3926938009250504/mineru-result.zip`, `parsed/3926938009250504/full.md` | completed `v8` during Task 313 final UAT | accepted as workbook-class final closure evidence |
| `task-1780127147233` | `3138335640538270` | `canceled` | `parsed/3138335640538270/mineru-result.zip`, `parsed/3138335640538270/full.md` | failed `v9` | not selected; historical canceled state is not needed for mainline proof |
| `task-1780092248601` | `4283493985420113` | `canceled` | `parsed/4283493985420113/mineru-result.zip`, `parsed/4283493985420113/full.md` | canceled `v2` | not selected; historical canceled state is not needed for mainline proof |

## Sample 1: Small Real Raw Material

Request:

```bash
curl -sS -X POST --max-time 30 \
  "http://127.0.0.1:8081/__proxy/upload/tasks/task-1780132950215/toc-rebuild" \
  -H 'Content-Type: application/json' \
  --data '{"trigger":"operator-manual","mode":"cleanservice-rerun","cleanservice":true,"forceNewVersion":true}'
```

Accepted response:

```text
taskId=task-1780132950215
materialId=2787656755020028
assetVersion=v7
jobId=luceon-task-1780132950215-toc-rebuild-v7-1780283738204
prefix=toc-rebuild/2787656755020028/v7/
```

Direct CleanService final state:

```text
status=completed
current_step=succeeded
elapsed_seconds=55
inference_chunks_completed=1
chunks_by_task={"image":1}
last_error=null
```

Outer Luceon final state:

```text
status=completed
taskIntent=completed
assetVersion=v7
artifactCount=8
error=null
sourceInput.object=parsed/2787656755020028/mineru-result.zip
sourceInput.sha256=0075b50890f5c2c5b093a241507bc140f57088fcfc63fe35136a3baf64285855
```

Proxy readback:

```text
rebuilt_markdown.md HTTP 200 size=3296
readable_tree.md HTTP 200 size=297
logic_tree.json HTTP 200 size=13681
metrics.json HTTP 200 size=237
provenance.json HTTP 200 size=740
```

## Sample 2: Workbook-Class Real Raw Material

Workbook final UAT was completed during Task 313 acceptance and is included here because it is the exact blocker sample from Task 310/312.

Evidence:

```text
taskId=task-1779854322261
materialId=3926938009250504
assetVersion=v8
jobId=luceon-task-1779854322261-toc-rebuild-v8-1780279642725
prefix=toc-rebuild/3926938009250504/v8/
```

Direct CleanService final state:

```text
status=completed
current_step=succeeded
elapsed_seconds=1288
inference_chunks_completed=32
chunks_by_task={"title":12,"contd":9,"image":11}
last_error=null
```

Outer Luceon final state:

```text
status=completed
taskIntent=completed
assetVersion=v8
artifactCount=8
error=null
sourceInput.object=parsed/3926938009250504/mineru-result.zip
sourceInput.sha256=0bacdd76c1d3eb30ad1ed708c9a475a6455c629d184e3ec86647063cf4f23538
```

Proxy readback:

```text
rebuilt_markdown.md HTTP 200 size=88102
readable_tree.md HTTP 200 size=12013
logic_tree.json HTTP 200 size=356871
metrics.json HTTP 200 size=241
provenance.json HTTP 200 size=742
```

## Metadata Consistency

Task/material readback confirmed both accepted samples agree on service, version, status, prefix, source input, and artifact count:

```text
task-1780132950215 / 2787656755020028:
task.status=completed
task.assetVersion=v7
task.jobId=luceon-task-1780132950215-toc-rebuild-v7-1780283738204
task.artifactCount=8
material.status=completed
material.latestVersion=v7
material.prefix=toc-rebuild/2787656755020028/v7/

task-1779854322261 / 3926938009250504:
task.status=completed
task.assetVersion=v8
task.jobId=luceon-task-1779854322261-toc-rebuild-v8-1780279642725
task.artifactCount=8
material.status=completed
material.latestVersion=v8
material.prefix=toc-rebuild/3926938009250504/v8/
```

## Changed Files

Task 310 itself does not add new business-code changes beyond the already accepted Task 313 branch contents.

Durable closure records changed:

```text
TaskAndReport/2026-05-31T07-46-23+0800_P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

## Acceptance Boundary

This PASS means:

```text
real Raw Material -> Popo/toc-rebuild -> versioned Clean artifacts -> metadata apply -> operator-inspectable rebuilt_markdown.md
```

is repeatably proven for the current phase on the production/control Home Mac mini MPS path.

This PASS does not mean:

```text
pressure PASS
release readiness
L3
public launch
go-live
all historical canceled tasks repaired
all future large PDFs guaranteed
```

No DB/MinIO cleanup, object deletion, object overwrite, source asset mutation, credential change, model change, scheduler activation, bulk rerun, or UI polish was performed.
