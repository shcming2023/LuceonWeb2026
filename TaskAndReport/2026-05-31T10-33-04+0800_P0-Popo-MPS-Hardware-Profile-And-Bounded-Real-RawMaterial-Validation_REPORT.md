# P0 Popo MPS Hardware Profile And Bounded Real RawMaterial Validation Report

Task ID: `TASK-20260531-103304-P0-Popo-MPS-Hardware-Profile-And-Bounded-Real-RawMaterial-Validation`

Result: `BLOCKED_MPS_BOUNDED_PROFILE_JOB_TIMEOUT_BEFORE_WORKBOOK_OUTPUT`

Report time: `2026-05-31T12:15:00+0800`

## Summary

Luceon applied a bounded Home Mac mini / Apple MPS profile without switching hardware and without modifying MinerU-Popo upstream algorithms.

The original workbook failure mode changed:

```text
Before: RuntimeError: Invalid buffer size: 120.93 GiB
After:  Job exceeded maximum execution time
```

This proves the MPS input-budget profile is effective against the immediate attention-buffer explosion, but it is not yet sufficient to complete workbook-class Raw Material inside the current single-job execution window.

## Applied Profile

Luceon2026 deployment profile:

```text
POPO_INFERENCE_BACKEND=host-mps
POPO_MAX_CONCURRENT_JOBS=1
POPO_MAX_NEW_TOKENS=256
POPO_MPS_CHUNK_SIZE=10
POPO_MPS_RENDER_SCALE=1.0
POPO_MPS_MIN_PIXELS=3136
POPO_MPS_MAX_PIXELS=589824
POPO_JOB_TIMEOUT_SECONDS=3600
POPO_GENERATE_TIMEOUT_SECONDS=900
```

Runtime evidence:

```text
mineru-popo env:
POPO_JOB_TIMEOUT_SECONDS=3600
POPO_MPS_CHUNK_SIZE=10
POPO_MPS_RENDER_SCALE=1.0
POPO_MPS_MIN_PIXELS=3136
POPO_MPS_MAX_PIXELS=589824
POPO_MAX_NEW_TOKENS=256

host MPS health:
device=mps
mps_available=true
serialized_generation=true
mps_min_pixels=3136
mps_max_pixels=589824
last_error=null
```

External local MinerU-Popo overlay commits, not pushed upstream:

```text
bd7b1d1 Serialize Luceon host MPS generation
565af83 Add bounded MPS Popo profile
```

## Validation

### Small Real Raw Material

Sample:

```text
taskId=task-1780132950215
materialId=2787656755020028
assetVersion=v6
jobId=luceon-task-1780132950215-toc-rebuild-v6-1780195133589
```

Result:

```text
status=completed
cleanState=null
prefix=toc-rebuild/2787656755020028/v6/
```

This confirms the bounded MPS profile did not regress the known passable real-sample path.

### Workbook-Class Real Raw Material

Sample:

```text
taskId=task-1779854322261
materialId=3926938009250504
assetVersion=v5
jobId=luceon-task-1779854322261-toc-rebuild-v5-1780195242828
profile=POPO_JOB_TIMEOUT_SECONDS=600
```

Result:

```text
status=failed
cleanState=failed
error=Job exceeded maximum execution time
```

After increasing the deployment window:

```text
taskId=task-1779854322261
materialId=3926938009250504
assetVersion=v6
jobId=luceon-task-1779854322261-toc-rebuild-v6-1780196066079
profile=POPO_JOB_TIMEOUT_SECONDS=3600
```

Result:

```text
status=failed
cleanState=failed
error=Job exceeded maximum execution time
```

During the v6 run the host MPS worker continued serving successful serialized generations and no longer reproduced the prior `120.93 GiB` buffer explosion. Observed health before final timeout:

```text
generation_count=43
active_generations=0
last_error=null
```

## Conclusion

Task 312 does not pass the full workbook acceptance gate because no readable workbook-class `rebuilt_markdown.md` was produced.

The current blocker is now narrower and more actionable:

```text
MPS bounded profile prevents the immediate buffer explosion, but workbook-class Raw Material still exceeds the synchronous adapter job window before output materialization.
```

This should not be described as "Popo does not support MinerU large files." The evidence instead points to Luceon deployment/invocation limits on Home Mac mini MPS:

- bounded visual tokens are required;
- serialized MPS generation is required;
- long workbook jobs need a resumable/progress-aware adapter or a faster MPS profile;
- current job JSON remains at `current_step=init`, so long-run progress is not externally observable enough.

## Non-Actions

No source PDF was modified.

No image/audio/resource hash names were renamed.

No DB, MinIO object, Docker volume, model weight, or sample-library cleanup was performed.

No UI polish, pressure PASS, L3, release-readiness, production-readiness, or go-live claim is made.

## Next Mainline Step

Proceed with one focused follow-up only:

```text
P0 Popo MPS Workbook Completion Profile And Progress-Safe Timeout
```

Scope should be limited to completing the same workbook Raw Material by either:

1. selecting a faster bounded MPS profile that still avoids buffer explosion; or
2. making the adapter progress-aware/resumable enough that long MPS workbook jobs are not killed without partial-progress evidence.

Do not broaden into UI cleanup, historical compatibility, or upstream algorithm rewrites.
