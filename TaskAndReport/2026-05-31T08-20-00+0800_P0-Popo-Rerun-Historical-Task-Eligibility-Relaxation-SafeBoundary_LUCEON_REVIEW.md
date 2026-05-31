# P0 Popo Rerun Historical Task Eligibility Relaxation SafeBoundary - Luceon Review

Review time: `2026-05-31T08:20:00+0800`

Reviewed branch:

```text
origin/codex/popo-async-toc-rebuild@16f7e02c18d84077a299b2d101b145a8d9a07b12
```

## Decision

`ACCEPTED_NARROW_CANCELLATION_GUARD_FIX_WITH_CONTROL_PLANE_CORRECTION`

Task 309 is accepted and closed.

## Scope Accepted

Accepted only the narrow Task 309 objective:

- historical `failed` / `canceled` tasks with valid artifacts can enter explicit Popo rerun eligibility;
- the async pipeline no longer treats pre-existing task-level `state=canceled` as a new cancellation during the current rerun;
- a Popo objective failure during rerun is persisted as `status=failed` / `cleanState=failed`, not misclassified as `skipped`;
- debug `console.log` lines introduced during diagnosis were removed.

## Evidence Reviewed

Remote diff from `33cdf410630b47ae2f82ea1fd05bc15ad0bf3f07` to `16f7e02c18d84077a299b2d101b145a8d9a07b12` changed:

```text
TaskAndReport/2026-05-31T06-56-00+0800_P0-Popo-Rerun-Historical-Task-Eligibility-Relaxation-SafeBoundary_REPORT.md
TaskAndReport/TASK_TRACKING_LIST.md
server/lib/task-actions-routes.mjs
```

Luceon reviewed the code diff in `server/lib/task-actions-routes.mjs`:

- removed temporary request/prepare debug logs;
- replaced broad `latestTaskBeforeApply?.state === 'canceled'` guards with current-job metadata checks:

```text
activeJob?.jobId === jobId
status/cleanState in canceled/skipped
```

Report evidence for `task-1780127147233` shows the v9 rerun crossed the historical canceled-task boundary and persisted objective Popo failure:

```text
jobId=luceon-task-1780127147233-toc-rebuild-v9-1780182412941
assetVersion=v9
status=failed
cleanState=failed
error.code=popo-command-failed
```

## Checks

Luceon ran checks in a detached review worktree at the reviewed remote commit:

```text
node --check server/lib/task-actions-routes.mjs: passed
npx tsc --noEmit: passed
npm run build: passed
```

Initial branch-level `git diff --check origin/main...origin/codex/popo-async-toc-rebuild` failed on two markdown EOF whitespace issues outside the Task 309 source patch:

```text
TaskAndReport/2026-05-30T18-13-40+0800_P0-MinerU-Popo-Host-Mac-MPS-Worker-Integration-NoDockerModelInference_REPORT.md
TaskAndReport/2026-05-31T06-44-14+0800_P0-Popo-Rerun-Historical-Task-Eligibility-Relaxation-SafeBoundary_TASK.md
```

Luceon corrected those control-plane whitespace issues before closure.

## Boundary

This acceptance does not prove Popo/toc-rebuild successful Clean Material output repeatability. It only proves the historical canceled-task rerun path no longer converts an objective Popo failure into `skipped`.

Task 310 remains the current phase breakthrough task:

```text
at least 2 new real Popo/toc-rebuild successful outputs with readable rebuilt_markdown.md
```

No readiness, release-readiness, production-readiness, pressure PASS, public launch, or go-live claim is made.
