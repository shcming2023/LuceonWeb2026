# TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime Report

Report time: 2026-05-24T17:16:00+0800

## Task And Branch

Task:

```text
TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime
```

Task brief:

```text
TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_TASK.md
```

Branch:

```text
lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime
```

Baseline:

```text
origin/main = 8bd4cd36176cf77417f2f982d545502986d5a3b2
```

Final remote branch HEAD is reported in the Lucode handoff after commit and push.
This report is part of that final commit, so it cannot embed its own final hash
without changing it.

## Files Changed

```text
M       server/upload-server.mjs
A       src/app/components/CleanMaterialArtifactInspector.tsx
M       src/app/components/CleanMaterialSummaryCard.tsx
A       TaskAndReport/2026-05-24T16-57-58+0800_P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
```

No files outside the task's allowed surface were edited.

## Implementation Summary

- Added `CleanMaterialArtifactInspector`, embedded in the existing Task 268
  Clean Material card.
- Artifact refs are now selectable and actionable.
- The inspector defaults to `readable_tree.md` when present, otherwise a JSON
  artifact, then the first artifact.
- Markdown artifacts render with the existing `renderMarkdown()` path.
- JSON artifacts are fetched read-only and pretty-printed when parseable, or
  shown as readable text otherwise.
- Each artifact has a direct `打开` link through the existing upload proxy.
- Empty, loading, fetch error, and unsupported-type states are rendered.
- `prefix=null` remains tolerated because inspection uses task artifact refs
  from the Clean Material view, not material prefix.

## eduassets-clean Access

`server/upload-server.mjs` now resolves clean artifact reads through the existing
read-only `/presign` and `/proxy-file` paths:

```text
bucket=clean          -> eduassets-clean
bucket=eduassets-clean -> eduassets-clean
```

The frontend uses artifact ObjectRef buckets when present and falls back to
`eduassets-clean`. Example read-only URLs for the canonical sample:

```text
/__proxy/upload/proxy-file?objectName=toc-rebuild%2F1842780526581841%2Fv4%2Freadable_tree.md&bucket=eduassets-clean
/__proxy/upload/proxy-file?objectName=toc-rebuild%2F1842780526581841%2Fv4%2Flogic_tree.json&bucket=eduassets-clean
```

No write, delete, list-clean, cleanup, runtime execution, or broad storage
configuration behavior was added.

## Artifact Inspection Evidence

Static code/build evidence shows:

- `readable_tree.md` is selected first when available and rendered as Markdown.
- JSON artifacts such as `logic_tree.json`, `metrics.json`, or
  `provenance.json` are selectable and rendered as formatted JSON/readable text.
- Direct open/download uses the existing read-only `proxy-file` route with the
  artifact object and clean bucket.
- Missing artifact refs render `暂无可检查 artifact refs`.
- Fetch failures render `读取失败：...`.
- Unsupported extensions show a clear unsupported preview state while preserving
  the direct open link.

Browser verification was not run in this task. The required static checks passed,
and avoiding runtime/browser data access keeps the task within the NoRuntime
read-only implementation boundary.

## Commands

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | initial branch status checked |
| `git fetch origin --prune --tags` | 0 | fetched latest main |
| `git checkout main` | 0 | returned to main |
| `git pull --ff-only origin main` | 0 | fast-forwarded to `8bd4cd36176cf77417f2f982d545502986d5a3b2` |
| `git checkout -b lucode/TASK-20260524-165758-P0-CleanMaterial-Artifact-Inspect-Surface-ReadOnly-NoRuntime` | 0 | scoped branch created |
| `node --check server/upload-server.mjs` | 0 | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | PASS |
| `npx pnpm@10.4.1 run build` | 0 | PASS; Vite built 1649 modules, with existing >500 kB chunk warning |
| `git diff --check origin/main...HEAD` | 0 | no whitespace errors |

No required check was skipped.

## Boundary Statement

No CleanService runtime run, Mineru2Table POST/query/probe, DB
POST/PATCH/PUT/DELETE, MinIO put/copy/move/delete/write/delete-marker/cleanup,
Docker/Compose operation, job-store edit, upload, retry, reparse, Re-AI, repair,
rollback, batch, pressure test, model/env/secret/sample/source asset mutation,
production deployment, production runtime validation, approval/rejection
workflow, RawMaterial2CleanMaterial implementation, UAT, L3, pressure PASS,
release readiness, production online, or go-live claim was performed.

## Risks And Residual Debt

- This is a minimal artifact inspector, not a batch artifact browser.
- No artifact annotation, approval/reject workflow, version comparison, or
  content editing was added.
- Material-side `prefix=null` remains a deferred metadata normalization debt,
  although artifact inspection works from task artifact refs.
- Browser verification is still a possible Luceon review follow-up if desired.

Luceon review is required.
