# P0 Popo TocRebuild Repeatable Real RawMaterial Closure To Main Report

Task ID: `TASK-20260531-074623-P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main`

Reported at: `2026-05-31T09:32:00+0800`

Executor: Luceon

Result:

```text
BLOCKED_POPO_SERVICE_RUNTIME_TIMEOUT_RESOURCE_BOUNDARY
```

## Summary

Task 310 was executed in the production/control runtime as corrected by the Task310 environment decision. The dev container MinIO credential/data absence was not treated as the task blocker.

The production/control runtime had real Raw Material samples and healthy services at preflight. The first selected sample was accepted by the main application and the Popo adapter, generated a new isolated Clean Material version, and then failed before producing `rebuilt_markdown.md`.

Per the stop-on-first-failure rule, no second sample was triggered.

This is a mainline blocker for the current phase:

```text
real Raw Material -> Popo/toc-rebuild -> readable rebuilt_markdown.md -> operator review
```

is not yet repeatably proven on real Raw Material.

## Environment

Workspace:

```text
/Users/concm/prod_workspace/Luceon2026
```

Branch:

```text
codex/popo-async-toc-rebuild
```

Relevant services observed before execution:

```text
Luceon dependency-health: ok=true, blocking=false
Popo adapter: http://127.0.0.1:18082/health ok=true, busy=false
Host MPS worker: http://127.0.0.1:18083/health ok=true, device=mps, mps_available=true, model_loaded=true
```

## Preflight Sample Matrix

The database contained 7 tasks/materials. Real Raw Material candidates with both MinerU zip and Markdown present included:

| Task | Material | Task State | Raw Material Inputs | Existing toc-rebuild | Eligibility |
| --- | --- | --- | --- | --- | --- |
| `task-1780132950215` | `2787656755020028` | `review-pending` | `parsed/2787656755020028/mineru-result.zip`, `parsed/2787656755020028/full.md` | completed `v3`, job `luceon-task-1780132950215-toc-rebuild-v3-1780135742145` | selected first |
| `task-1779854322261` | `3926938009250504` | `review-pending` | `parsed/3926938009250504/mineru-result.zip`, `parsed/3926938009250504/full.md` | failed `v2` | eligible but not triggered because first sample failed |
| `task-1780127147233` | `3138335640538270` | `canceled` | `parsed/3138335640538270/mineru-result.zip`, `parsed/3138335640538270/full.md` | failed `v9` | not preferred for first proof because task state is historical canceled |
| `task-1780092248601` | `4283493985420113` | `canceled` | `parsed/4283493985420113/mineru-result.zip`, `parsed/4283493985420113/full.md` | skipped/canceled `v2` | not preferred for first proof because task state is historical canceled |
| `task-1780097186416` | `uat-prog-1780097171018` | `failed` | no zip/markdown | none | ineligible |
| `task-1780097160203` | `uat-prog-1780097159296` | `failed` | no zip/markdown | none | ineligible |

Proxy readback before execution confirmed HTTP 200 for the selected candidates:

```text
parsed/2787656755020028/mineru-result.zip size=638810
parsed/2787656755020028/full.md size=4308
parsed/3926938009250504/mineru-result.zip size=18207111
parsed/3926938009250504/full.md size=105254
```

## Execution Evidence

First selected sample:

```text
taskId=task-1780132950215
materialId=2787656755020028
```

Request:

```bash
curl -sS -X POST --max-time 20 \
  "http://127.0.0.1:8081/__proxy/upload/tasks/task-1780132950215/toc-rebuild" \
  -H 'Content-Type: application/json' \
  --data '{"trigger":"operator-manual","mode":"cleanservice-rerun","cleanservice":true,"forceNewVersion":true}'
```

Response:

```json
{
  "ok": true,
  "accepted": true,
  "status": "running",
  "taskId": "task-1780132950215",
  "materialId": "2787656755020028",
  "jobId": "luceon-task-1780132950215-toc-rebuild-v4-1780189806166",
  "assetVersion": "v4",
  "prefix": "toc-rebuild/2787656755020028/v4/"
}
```

Job polling result:

```json
{
  "job_id": "luceon-task-1780132950215-toc-rebuild-v4-1780189806166",
  "status": "timeout",
  "service_name": "toc-rebuild",
  "protocol_version": "v1",
  "material_id": "2787656755020028",
  "parse_task_id": "task-1780132950215",
  "asset_version": "v4",
  "error": {
    "code": "timeout",
    "message": "Job exceeded maximum execution time",
    "retriable": false
  },
  "stats": {
    "engine": "mineru-popo",
    "cost_cny_actual": 0,
    "unresolved_anchor_count": 0,
    "tokens": {
      "total": 0
    }
  }
}
```

Main application task metadata after asynchronous apply:

```text
metadata.cleanServiceJobs.toc-rebuild.jobId=luceon-task-1780132950215-toc-rebuild-v4-1780189806166
metadata.cleanServiceJobs.toc-rebuild.assetVersion=v4
metadata.cleanServiceJobs.toc-rebuild.status=failed
metadata.cleanServiceJobs.toc-rebuild.cleanState=failed
metadata.cleanServiceJobs.toc-rebuild.error.code=timeout
metadata.cleanServiceJobs.toc-rebuild.error.message=Job exceeded maximum execution time
```

Material metadata after asynchronous apply:

```text
metadata.cleanMaterials.toc-rebuild.latestVersion=v4
metadata.cleanMaterials.toc-rebuild.status=failed
metadata.cleanMaterials.toc-rebuild.cleanState=failed
metadata.cleanMaterials.toc-rebuild.jobId=luceon-task-1780132950215-toc-rebuild-v4-1780189806166
metadata.cleanMaterials.toc-rebuild.prefix=toc-rebuild/2787656755020028/v4/
metadata.cleanMaterials.toc-rebuild.error.code=timeout
metadata.cleanMaterials.toc-rebuild.error.message=Job exceeded maximum execution time
```

No `rebuilt_markdown.md`, `readable_tree.md`, `logic_tree.json`, `metrics.json`, or `provenance.json` pass evidence exists for `v4`.

## Runtime Failure Evidence

The host MPS worker log during the run showed Qwen3-VL attention allocation failure:

```text
RuntimeError: Invalid buffer size: 120.93 GiB
INFO: 127.0.0.1:57926 - "POST /generate HTTP/1.1" 422 Unprocessable Entity
```

The same pane also contained a nearby earlier allocation failure:

```text
RuntimeError: Invalid buffer size: 119.28 GiB
INFO: 127.0.0.1:52494 - "POST /generate HTTP/1.1" 500 Internal Server Error
```

This evidence points to a Popo service/runtime input-size or image-token budget boundary. The main application lifecycle layer correctly recorded the final clean state as `failed`, so this is not the Task 309 historical-canceled rerun bug.

## Classification

Blocker class:

```text
Popo service/output blocker
```

Specific blocker:

```text
Real Raw Material can enter toc-rebuild and create a new version, but Popo generation can exceed host MPS/Qwen3-VL resource limits and time out before producing reviewable Clean-stage artifacts.
```

Secondary observation:

```text
The adapter exposed final timeout as job status=timeout while Luceon metadata applied status=failed/cleanState=failed. This is acceptable for failure honesty, but still not pass evidence.
```

## Stop Rule Applied

The first selected sample failed before producing readable `rebuilt_markdown.md`.

The task required sequential hard-cap execution and stop-on-first-failure. Therefore, the second eligible sample was not triggered.

## Changed Files

No business code was changed for this execution.

Durable project records changed:

```text
TaskAndReport/2026-05-31T07-46-23+0800_P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
```

## Checks

Runtime checks:

```text
dependency-health ok=true blocking=false
Popo adapter health ok=true before execution
Host MPS worker health ok=true before execution
Selected Raw Material proxy readback HTTP 200 before execution
Popo job API terminal status=timeout
Task/material metadata readback status=failed/cleanState=failed
```

Repository check:

```text
git diff --check
```

Full TypeScript/build checks were not rerun because no business code was changed and the task stopped at runtime-output blocker evidence.

## Residual Risk And Boundary

This report does not claim:

```text
PASS
mainline readiness
production readiness
release readiness
pressure PASS
L3
go-live
```

No DB/MinIO cleanup, object deletion, object overwrite, credential change, model change, sample mutation, bulk rerun, scheduler work, UI polish, or production release action was performed.

## Recommended Next Mainline Action

Issue one focused follow-up to make Popo/toc-rebuild handle real Raw Material within a bounded resource envelope:

```text
reduce/slice Popo visual input per call, enforce max image/page/token budget, persist deterministic failure detail quickly, and prove at least 2 new real samples produce readable rebuilt_markdown.md or explicit review-needed artifacts.
```

Do not broaden into UI polish, historical migration, launchd hardening, pressure testing, or generalized cleanup before this resource-bound output blocker is resolved.
