# Task 313 Luceon Review

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Reviewed branch: `origin/lucode/313`

Reviewed commit: `0ce46633181ccc27c5611b645b0079363b106bbe`

Review time: `2026-05-31T16:07:39+0800`

Result: `CHANGES_REQUIRED_DEPLOYMENT_PATH_AND_PROGRESS_EVIDENCE_GAP`

## Findings

### P0 - Progress adapter changes are not in the Docker build context

`docker-compose.popo.yml` still builds `mineru-popo` from:

```text
/Users/concm/prod_workspace/MineruPopo
```

as shown at `docker-compose.popo.yml:14-17`.

However the submitted adapter implementation was added under Luceon2026 repo root:

```text
luceon_service/app.py
luceon_service/service.py
```

Those files are outside the configured `mineru-popo` Docker build context and will not be copied into the running adapter image. In production UAT, only the `POPO_MPS_RENDER_SCALE=0.5` compose change would take effect; the claimed progress-aware adapter behavior would not run.

This blocks UAT because Task 313 requires progress-aware timeout-safe adapter behavior, not only a render-scale change.

### P0 - Progress fields do not satisfy the Task 313 minimum evidence contract

Even if the root-level `luceon_service` files were placed in the correct external overlay, `_get_live_progress` leaves required fields as placeholders:

```text
inference_chunks_total=0
inference_blocks_validated=0
```

at `luceon_service/service.py:160-170`.

The implementation then counts JSON files in `outputs/inference_raw` and `outputs/inference/mineru` as completed chunks at `luceon_service/service.py:196-208`. For the current Popo pipeline, the final `outputs/inference/mineru/<material>.json` is document-level output, not reliable chunk-level progress. This means a long-running workbook can still expose misleading or nearly empty progress, and the timeout result would not prove the active chunk/page/block range.

This does not meet the Task 313 requirement to preserve stage/chunk/block evidence on timeout.

### P1 - Submitted diff contains generated binaries and unrelated report content

The branch adds Python bytecode files:

```text
luceon_service/__pycache__/*.pyc
```

and also adds an unrelated Task 307 report file:

```text
TaskAndReport/TASK-20260529-202355-P0-TaskDetail-Primary-Artifact-Simplification-UI-NoBackendMutation-Report.md
```

This violates the narrow task scope and the expected repository hygiene for Task 313.

### P1 - `git diff --check` fails

Luceon ran:

```bash
git diff --check origin/codex/popo-async-toc-rebuild...origin/lucode/313
```

It failed with trailing whitespace / blank-line issues in:

```text
TaskAndReport/TASK-20260529-202355-P0-TaskDetail-Primary-Artifact-Simplification-UI-NoBackendMutation-Report.md
luceon_service/__init__.py
luceon_service/app.py
luceon_service/service.py
```

The Task 313 brief required `git diff --check` as a minimum check, so this branch is not acceptable as delivered.

### P1 - Report lacks exact verification evidence

The report says only:

```text
本地执行了 Python 语法校验 (type check) 及基本静态构建检查。
```

at report lines 15-16.

It does not include exact commands, exit codes, profile matrix, or any concrete workbook handoff evidence beyond asking Luceon to run UAT. This falls short of the required report contract.

## UAT Decision

Production UAT is not started.

Running UAT now would test an incomplete deployment surface: the progress-aware adapter changes are not in the active `mineru-popo` build context, and the branch already fails static diff hygiene. The result would be misleading.

## Required Corrections

Lucode should resubmit a narrow corrected branch that:

1. Places adapter/progress changes in the actual MinerU-Popo overlay or otherwise makes them part of the `mineru-popo` build context.
2. Removes all `__pycache__` / `.pyc` files and unrelated Task 307 report content.
3. Makes `git diff --check` pass.
4. Implements durable progress fields that satisfy Task 313, especially `inference_chunks_total`, `inference_chunks_completed`, `inference_blocks_validated`, active stage, and timeout-stage evidence.
5. Provides exact check commands and results in the report.

No source/hash rename, DB/MinIO cleanup, upstream algorithm rewrite, UI polish, pressure/readiness/release/L3/go-live claim is authorized.
