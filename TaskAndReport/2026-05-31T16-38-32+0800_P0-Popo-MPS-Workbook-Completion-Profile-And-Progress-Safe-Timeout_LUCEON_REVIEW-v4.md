# Task 313 Luceon Review v4

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313`

Reviewed commit: `a83e9f5dc1a1541374a820230c5d939787e01f7f`

Review time: `2026-05-31T16:38:32+0800`

Result: `CHANGES_REQUIRED_REAL_RAW_PROGRESS_GLOB_MISMATCH`

## Checks

Luceon verified the retry v3 branch:

```bash
git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313
git show origin/lucode/313:luceon_service/service.py | wc -l
git show origin/lucode/313:luceon_service/app.py | wc -l
```

Results:

```text
diff-check: pass
service.py: 670 lines
app.py: 94 lines
```

The empty-adapter issue from Review v3 is fixed.

## Findings

### P0 - Progress glob still does not match actual Popo raw output files

The submitted `_get_live_progress` only scans:

```python
inf_raw_dir.glob("chunk_*.json")
```

at `luceon_service/service.py:205-207`.

Luceon checked the existing real workbook run directory from Task 312:

```text
/Users/concm/prod_workspace/MineruPopo/runtime/work/luceon-task-1779854322261-toc-rebuild-v6-1780196066079/outputs/inference_raw
```

Observed files are shaped as:

```text
title_chunk_0000.json
contd_chunk_0003.json
image_chunk_0006.json
```

Concrete count:

```text
chunk_*.json = 0
*_chunk_*.json = 27
```

Therefore the retry v3 progress code would still report:

```text
inference_chunks_completed=0
last_completed_chunk=null
active_chunk=chunk_0.json
```

even after real Popo chunks have completed. That fails the Task 313 requirement to prevent long workbook jobs from running without truthful partial-progress evidence.

### P0 - Progress directory depth is incomplete

Real raw output files are under:

```text
outputs/inference_raw/mineru/<material_id>/*_chunk_*.json
```

The submitted code scans only:

```text
outputs/inference_raw/chunk_*.json
```

It misses both the `mineru/<material_id>/` directory depth and the actual filename prefix.

### P1 - Submitted ledger/report commit reference is inconsistent

The actual reviewed remote HEAD is:

```text
a83e9f5dc1a1541374a820230c5d939787e01f7f
```

The submitted report and ledger mention older/non-HEAD commit refs (`31ccd6b...` / `183160...`). This is not the main blocker, but it weakens handoff traceability and should be corrected in the next submission.

## UAT Decision

Production UAT is not started.

The branch is much closer than prior attempts: diff hygiene passes and mounted adapter modules are non-empty. However, the core progress detector still does not observe real Popo workbook chunk artifacts. Running a multi-hour UAT now would not verify the required progress-safe behavior; it would repeat the previous "long running with no truthful chunk progress" failure mode.

## Required Corrections

Lucode should submit a narrow v4 correction:

1. Derive progress from actual raw files under `outputs/inference_raw/mineru/<material_id>/`.
2. Match real Popo chunk files such as `title_chunk_0000.json`, `contd_chunk_0003.json`, `image_chunk_0006.json`, and any future `<task>_chunk_<index>.json` emitted by `write_raw_record`.
3. Parse chunk metadata from the raw record JSON fields (`task`, `chunk_index`, `range`, `pages`, `parsed`) instead of only filename guesses.
4. Report completed chunks by task family and chunk index, for example `title: 12`, `contd: 9`, `image: 7`, with an aggregate total.
5. Keep `git diff --check` clean and update the report/ledger with the actual remote HEAD.

No source/hash rename, DB/MinIO cleanup, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim is authorized.
