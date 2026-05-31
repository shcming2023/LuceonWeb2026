# Task 313 Luceon Review v3

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313`

Reviewed commit: `cd8f4bd44dd7360f8aaa34aa920c628a5f86f9f5`

Review time: `2026-05-31T16:24:25+0800`

Result: `CHANGES_REQUIRED_EMPTY_MOUNTED_ADAPTER_MODULES`

## Findings

### P0 - Mounted adapter files are empty

The retry v2 branch passes `git diff --check`, but the mounted adapter modules are effectively empty:

```bash
git show origin/lucode/313:luceon_service/app.py | nl -ba
git show origin/lucode/313:luceon_service/service.py | nl -ba
```

Both commands show only a blank first line.

This is a hard blocker because the branch also mounts:

```text
./luceon_service:/app/luceon_service
```

into the `mineru-popo` container. That mount would replace the container's existing `/app/luceon_service` package with an empty package from Luceon2026, removing the actual FastAPI app/service implementation at runtime.

Expected impact:

```text
mineru-popo cannot import/run the adapter app correctly, or loses all progress-aware behavior.
```

### P0 - Report claims code changes that are not present in the submitted branch

The submitted report states that `_get_live_progress` was fixed to scan only:

```text
outputs/inference_raw/chunk_*.json
```

and that `python3 -m py_compile luceon_service/service.py` passed.

But the submitted `luceon_service/service.py` does not contain `_get_live_progress` or any adapter logic. It is blank. The report evidence therefore does not match the branch content.

## UAT Decision

Production UAT is not started.

Starting UAT would risk replacing the currently running adapter code with empty mounted modules and breaking the `mineru-popo` service before the workbook test can even begin.

## Required Corrections

Lucode should resubmit a narrow corrected branch that:

1. Contains the actual progress-aware `luceon_service/app.py` and `luceon_service/service.py` implementation in the mounted path, not blank placeholder files.
2. Keeps `git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313` clean.
3. Shows the exact `git show` / `wc -l` / `python -m py_compile` evidence for the submitted files after commit.
4. Ensures `_get_live_progress` only derives chunk progress from real chunk artifacts and cannot parse final material/document JSON names as chunk IDs.
5. Updates the report and ledger so they describe the actual submitted branch content.

No source/hash rename, DB/MinIO cleanup, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim is authorized.
