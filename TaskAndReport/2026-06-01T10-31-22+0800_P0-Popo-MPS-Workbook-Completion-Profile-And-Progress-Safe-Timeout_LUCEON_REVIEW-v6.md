# Luceon Review v6: P0 Popo MPS Workbook Completion Profile And Progress-Safe Timeout

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313@a588d816e7a83e70ff41b2775bd2dfe79b8475ab`

Review time: `2026-06-01T10:31:22+0800`

Result: `ACCEPTED_PRODUCTION_UAT_WORKBOOK_MPS_COMPLETED_AND_METADATA_APPLIED`

## Summary

Accepted.

Retry v5 closes the Task 313 blocker. The same workbook-class Raw Material completed on the Home Mac mini MPS path, produced readable clean artifacts, and the Luceon outer task metadata now reflects the real output state as `completed`.

The previous v7 false `protocol-failure` did not recur. The patch-scope fix preserves the full-content safety gate for new CleanService metadata while avoiding rejection from unrelated historical task/material metadata such as legacy AI `rawPreview` and `aiClassificationV02.evidence`.

Luceon also removed generated Python bytecode from the delivery branch and added Python bytecode ignores before integration. No `__pycache__` or `.pyc` files remain in the accepted tree.

## Static Review

Accepted commit after hygiene cleanup:

```text
origin/lucode/313@a588d816e7a83e70ff41b2775bd2dfe79b8475ab
```

Three-dot diff scope:

```text
.gitignore
TaskAndReport/2026-05-31T15-50-06+0800_P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
docker-compose.popo.yml
luceon_service/__init__.py
luceon_service/app.py
luceon_service/service.py
server/services/cleanservice/metadata-apply-executor.mjs
server/tests/cleanservice-metadata-apply-executor-smoke.mjs
```

No tracked Python bytecode remains:

```text
git ls-tree -r --name-only origin/lucode/313 | rg '__pycache__|\.pyc$'
Exit Code 1, no matches
```

## Checks

```text
git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313
Exit Code 0

node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
All apply-executor smoke cases passed successfully, including Case 12 and Case 13.

node --check server/services/cleanservice/metadata-apply-executor.mjs
Exit Code 0

node --check server/tests/cleanservice-metadata-apply-executor-smoke.mjs
Exit Code 0

python3 -m py_compile luceon_service/app.py luceon_service/service.py
Exit Code 0
```

## Production UAT

Runtime deployment:

```text
docker compose -f docker-compose.yml -f docker-compose.popo.yml up -d --build upload-server mineru-popo
```

Runtime health:

```text
http://127.0.0.1:18082/health
ok=true, service=toc-rebuild, engine=mineru-popo

http://127.0.0.1:8081/__proxy/upload/health
ok=true, service=upload-server

host MPS worker:
ok=true, device=mps, model_loaded=true, serialized_generation=true, last_error=null
```

Active MPS profile:

```text
POPO_MPS_RENDER_SCALE=0.5
POPO_MPS_CHUNK_SIZE=10
POPO_MPS_MIN_PIXELS=3136
POPO_MPS_MAX_PIXELS=589824
POPO_MAX_NEW_TOKENS=256
POPO_JOB_TIMEOUT_SECONDS=3600
```

Triggered workbook rerun:

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
progress.elapsed_seconds=1288
progress.inference_chunks_completed=32
progress.chunks_by_task={"title":12,"contd":9,"image":11}
progress.last_error=null
```

Outer Luceon final state:

```text
status=completed
taskIntent=completed
assetVersion=v8
error=null
sourceInput.sha256=0bacdd76c1d3eb30ad1ed708c9a475a6455c629d184e3ec86647063cf4f23538
```

Successful metadata apply log:

```text
[apply-executor] Writing task metadata for task-1779854322261...
[apply-executor] Writing material metadata for 3926938009250504...
```

Artifact proxy readback:

```text
rebuilt_markdown.md HTTP 200 size=88102
readable_tree.md HTTP 200 size=12013
logic_tree.json HTTP 200 size=356871
metrics.json HTTP 200 size=241
provenance.json HTTP 200 size=742
```

## Acceptance Notes

Task 313 positive acceptance is satisfied:

- workbook sample produced readable `rebuilt_markdown.md` under Home Mac mini MPS;
- generated artifacts remain under `toc-rebuild/3926938009250504/v8/`;
- source input hash and parsed object reference remain unchanged;
- job status and metadata are now consistent with output reality;
- progress was visible during the long run and preserved the real raw chunk family breakdown.

Small-sample rerun was not repeated in this final pass because the accepted change targets metadata apply scope and the larger workbook UAT exercised the same Popo/CleanService completion path more strictly. Prior small-sample pass evidence from Task 312 remains preserved.

## Decision

Task 313 is accepted and integrated into `codex/popo-async-toc-rebuild`.

No source/hash rename, DB/MinIO cleanup, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim was performed or accepted.
