# P0 Popo Rerun Historical Task Eligibility Relaxation SafeBoundary

## Background

The current Popo rerun path is operational:

```text
TaskDetail -> POST /tasks/:id/toc-rebuild -> mineru-popo adapter -> host Mac MPS worker -> clean artifacts
```

However, historical tasks such as `task-1780127147233` can contain valid MinerU artifacts and AI metadata while the task state is `canceled` or `failed`. The current backend gate only permits manual Popo toc-rebuild when task state is:

```text
review-pending | completed
```

This blocks legitimate operator-initiated reruns for historical artifact-backed tasks.

## Goal

Relax Popo rerun eligibility from a task-state-first gate to an artifact-first gate, without weakening data safety boundaries.

The operator should be able to invoke **Popo rerun** for historical tasks when the source artifacts are present and safe to consume, even if the task state is `failed` or `canceled`.

## In Scope

Implement a narrow distinction between:

1. Legacy/manual local toc-rebuild.
2. Popo CleanService rerun mode.

For Popo CleanService rerun mode only, allow eligible historical tasks with states:

```text
review-pending
completed
failed
canceled
```

Eligibility must still require:

- associated Material exists;
- MinIO storage backend is active;
- MinerU result zip exists;
- Markdown artifact exists or resource validation confirms required parsed evidence;
- CleanService is enabled and endpoint is configured;
- no current toc-rebuild job is `running` or `pending`;
- rerun uses a new asset version / prefix and must not overwrite existing artifacts;
- operator action remains explicit from UI.

## Out of Scope

Do not:

- bulk rerun historical tasks;
- auto-start Popo reruns;
- delete, move, or clean any DB records or MinIO objects;
- overwrite existing toc-rebuild versions;
- bypass source artifact validation;
- widen legacy/manual local toc-rebuild semantics unless required for shared helper extraction;
- make readiness, release-readiness, pressure PASS, or go-live claims.

## Required Product Behavior

On TaskDetail:

- If a task is `failed` or `canceled` but has the required MinerU artifacts, the **调用 Popo 重新目录重建** action should be available.
- The older **目录重建 (TocRebuild)** action may remain restricted if it uses legacy/manual local semantics.
- Disabled text should explain the real missing prerequisite, not only say the task must be `review-pending/completed`.
- Existing completed toc-rebuild artifacts must not block Popo rerun when `forceNewVersion=true`; the new run must create the next version.
- If another toc-rebuild job is running, the action must stay disabled or return a clear conflict.

## Required Backend Behavior

- `POST /tasks/:id/toc-rebuild` with `mode=cleanservice-rerun` or `cleanservice=true` must use the relaxed artifact-first gate.
- The relaxed gate must still reject missing Material, missing MinerU zip, missing Markdown/source artifact, missing CleanService config, missing MinIO client, and currently running/pending toc-rebuild jobs.
- The response should preserve async semantics:
  - `202` when queued/running;
  - clear `409`/`503` errors when blocked.
- The generated job must use a new version/prefix and must not overwrite existing object refs.

## Validation Requirements

Use the current local runtime and at least one historical task such as:

```text
task-1780127147233
```

Required checks:

1. Before fix, confirm current block:

```text
409 Only review-pending/completed tasks can run toc-rebuild manually
```

2. After fix, confirm the UI exposes **调用 Popo 重新目录重建** when artifacts are present.
3. Trigger one explicit Popo rerun for the selected historical task.
4. Confirm:
   - async job is accepted;
   - job reaches completed or a clear Popo failure state;
   - no existing toc-rebuild version is overwritten;
   - new artifact refs are recorded under a new version/prefix;
   - `rebuilt_markdown.md` and `readable_tree.md` are readable if completed.
5. Run focused code checks:

```bash
git diff --check
npx tsc --noEmit
npm run build
```

## Acceptance Criteria

- Historical `failed` / `canceled` tasks with valid MinerU artifacts can explicitly start Popo rerun.
- Missing artifacts remain blocked with clear messages.
- Existing completed/failed/canceled toc-rebuild metadata does not prevent rerun when `forceNewVersion=true`.
- Running/pending toc-rebuild still blocks duplicate concurrent reruns.
- No broad workflow redesign, no bulk operation, and no destructive cleanup is introduced.

## Reporting

Write a short execution report in `TaskAndReport/` containing:

- changed files;
- exact task id used for validation;
- before/after eligibility evidence;
- generated job id and version/prefix if a real rerun was executed;
- readback evidence for key artifacts;
- explicit boundary statement.
