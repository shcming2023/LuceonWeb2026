# Luceon Review v5: P0 Popo MPS Workbook Completion Profile And Progress-Safe Timeout

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313@ec37d541d86a53c37f8d216658279f7223a3bb39`

Review time: `2026-05-31T18:14:50+0800`

Result: `CHANGES_REQUIRED_METADATA_APPLY_PATCH_SCOPE`

## Summary

Retry v4 successfully closes the Popo/MPS execution and raw-progress observation gap:

- production deployment loaded non-empty adapter code from `./luceon_service`;
- MPS bounded profile was active with `POPO_MPS_RENDER_SCALE=0.5`, `POPO_MPS_CHUNK_SIZE=10`, `POPO_MAX_NEW_TOKENS=256`, and `POPO_JOB_TIMEOUT_SECONDS=3600`;
- the same workbook sample completed through Popo on Home Mac mini MPS;
- CleanService direct job state reached `status=completed`;
- generated clean artifacts under `toc-rebuild/3926938009250504/v7/` were readable through the Luceon proxy.

However, the Luceon outer task still ended as `failed / protocol-failure` because metadata persistence rejected the final patch:

```text
Patches contain full artifact document data or unauthorized structures in metadata
```

This fails Task 313 positive acceptance item 5: job status and metadata must be consistent with output reality.

## Evidence

Production branch and static checks:

```text
git rev-parse origin/lucode/313
ec37d541d86a53c37f8d216658279f7223a3bb39

git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313
Exit Code 0

python3 -m py_compile luceon_service/app.py luceon_service/service.py
Exit Code 0

wc -l luceon_service/service.py luceon_service/app.py
707 luceon_service/service.py
94 luceon_service/app.py
```

Production runtime checks:

```text
http://127.0.0.1:18082/health
ok=true, service=toc-rebuild, engine=mineru-popo

host MPS worker:
ok=true, device=mps, model_loaded=true, serialized_generation=true, last_error=null
```

Workbook rerun:

```text
taskId=task-1779854322261
materialId=3926938009250504
assetVersion=v7
jobId=luceon-task-1779854322261-toc-rebuild-v7-1780220927008
prefix=toc-rebuild/3926938009250504/v7/
```

Direct CleanService completion:

```text
status=completed
current_step=succeeded
progress.elapsed_seconds=1322
progress.inference_chunks_completed=32
progress.chunks_by_task={"title":12,"contd":9,"image":11}
progress.last_error=null
```

Artifact readback:

```text
rebuilt_markdown.md HTTP 200 size=88056
readable_tree.md HTTP 200 size=11690
logic_tree.json HTTP 200 size=334093
metrics.json HTTP 200 size=241
provenance.json HTTP 200 size=742
```

Outer Luceon task readback:

```text
status=failed
cleanState=protocol-failure
assetVersion=v7
error.code=cleanservice_async_failed
error.message=Patches contain full artifact document data or unauthorized structures in metadata
artifacts=null
```

## Diagnosis

The current blocker is not Popo inference, MPS hardware execution, or MinIO artifact generation.

The generated CleanService job file contains bounded ObjectRefs for the seven artifact roles and a normal provenance object. A reconstructed clean candidate with empty existing metadata passes `hasFullContentInMetadata`.

The rejection appears when Luceon builds the apply patch by shallow-merging the existing task/material metadata. The existing workbook metadata contains historical AI fields such as long `rawPreview`, `aiClassificationV02.evidence`, and other large classification structures. The full-content safety gate then scans the entire merged metadata patch and blocks on those pre-existing fields, even though Task 313's new CleanService patch is bounded.

This is a CleanService metadata-apply patch-scope issue: the apply gate must validate the newly written CleanService summaries without reclassifying unrelated historical metadata as newly introduced full artifact content.

## Required Next Fix

Do not change MinerU-Popo core logic. Do not change the MPS profile unless needed to keep the already proven run stable.

Only fix the metadata apply boundary:

1. Preserve the existing full-content safety rule for new CleanService metadata.
2. Avoid failing an otherwise bounded CleanService patch because unrelated pre-existing task/material metadata contains legacy long strings or large arrays.
3. Keep the persistence result consistent with output reality: for the same workbook sample, outer Luceon task status must become `completed` and expose bounded artifact refs for `v7` or a new version.
4. Add a focused regression test proving a bounded CleanService patch can apply over existing metadata that contains legacy `rawPreview` or AI classification arrays, while a new CleanService patch containing full artifact content is still blocked.

## Decision

Task 313 retry v4 is not accepted for merge yet.

Return status: `未接受已退回`

Next actor: `lucode`

No source/hash rename, MinIO cleanup, DB manual repair, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim was performed by Luceon.
