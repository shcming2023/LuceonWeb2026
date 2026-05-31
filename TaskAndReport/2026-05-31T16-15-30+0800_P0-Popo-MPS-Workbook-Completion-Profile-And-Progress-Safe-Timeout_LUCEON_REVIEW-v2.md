# Task 313 Luceon Review v2

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313`

Reviewed commit: `2e609996b4c8b281970211a7d83f053642e4afac`

Review time: `2026-05-31T16:15:30+0800`

Result: `CHANGES_REQUIRED_DIFF_CHECK_AND_PROGRESS_SEMANTICS`

## Findings

### P0 - Required diff hygiene still fails

Luceon ran:

```bash
git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313
```

It failed with trailing whitespace / blank-line findings in:

```text
luceon_service/__init__.py
luceon_service/app.py
luceon_service/service.py
```

This directly contradicts the handoff statement that `git diff --check` has no errors, and fails a required Task 313 check. Production UAT is not started from a branch that fails the minimum static gate.

### P0 - Progress semantics can produce false chunk evidence

The retry branch improves the deployment-path idea by mounting:

```text
./luceon_service:/app/luceon_service
```

However `_get_live_progress` still does not provide reliable chunk/block evidence.

At `luceon_service/service.py:204-223`, it adds every JSON file in both `outputs/inference_raw` and `outputs/inference/mineru` into `completed_chunks`, then extracts the first number from the last filename to produce `active_chunk`.

For the current Popo pipeline, `outputs/inference/mineru/<material_id>.json` is a document-level final output. For the workbook sample this can be:

```text
3926938009250504.json
```

The regex then treats `3926938009250504` as a chunk number and may report a bogus next active chunk such as:

```text
chunk_3926938009250505.json
```

That is not progress evidence and would mislead Luceon during a long-running UAT.

### P0 - Block count calculation is not proven against Popo output shape

At `luceon_service/service.py:210-213`, `inference_blocks_validated` is computed with:

```text
sum(len(page) if isinstance(page, list) else 0 for page in data)
```

The final Popo inference JSON is expected to represent block/inference entries, not necessarily a page -> list-of-blocks shape. If `data` is a list of dict rows, this reports zero; if it is nested differently, it can report the wrong unit. Task 313 required evidence-backed `inference_blocks_validated`, not a shape guess.

### P1 - Report still lacks exact verification commands

The report still says only:

```text
本地执行了 Python 语法校验 (type check) 及基本静态构建检查。
```

It does not include exact commands, exit codes, or focused test output. Given the branch fails `git diff --check`, this absence matters.

### P1 - Ledger row is stale/inconsistent

The submitted Task 313 ledger row is set back to `Ready for luceon Review`, but still carries prior rejection notes in the Notes field. It does not summarize what changed in retry v2 or acknowledge the remaining Luceon Review v1 context cleanly.

## UAT Decision

Production UAT is not started.

The volume mount direction is closer to the required deployment path, but the branch still fails the required static check and the progress fields can create false evidence. Running a workbook UAT now would risk spending hours on a branch that cannot be accepted even if the render-scale change happens to change runtime behavior.

## Required Corrections

Lucode should resubmit a narrow v3 branch that:

1. Makes `git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313` pass.
2. Computes progress from real Popo pipeline units, not final document JSON filenames.
3. Reports `active_chunk`, `inference_chunks_total`, `inference_chunks_completed`, and `inference_blocks_validated` with definitions that match actual files and JSON shapes.
4. Includes exact verification commands and outputs in the report.
5. Keeps the ledger note current and removes stale prior-rejection wording from the resubmitted row.

No source/hash rename, DB/MinIO cleanup, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim is authorized.
