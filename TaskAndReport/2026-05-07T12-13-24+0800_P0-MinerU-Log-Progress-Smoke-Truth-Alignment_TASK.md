# Lucia Task Brief

Task ID: `TASK-20260507-121324-P0-MinerU-Log-Progress-Smoke-Truth-Alignment`

Task name: P0 MinerU Log Progress Smoke Truth Alignment

Issued at: `2026-05-07T12:13:24+0800`

Issuer: Lucia

Assignee: Lucode

Priority: P0

## Background

During Lucia review of tasks 7 and 8, the command `node server/tests/mineru-log-progress-smoke.mjs` failed at Test 4:

- Expected activity level: `failed-confirmed`
- Actual activity level: `log-error-signal`

Lucia verified that `server/lib/ops-mineru-log-parser.mjs` and `server/tests/mineru-log-progress-smoke.mjs` were not modified by the reviewed implementation branch. The failure is therefore handled as existing test-truth drift that must be closed in a separate scoped task.

## Objective

Restore truthful green coverage for `server/tests/mineru-log-progress-smoke.mjs` by aligning the test expectation and parser semantics with the current intended MinerU log activity contract.

## Scope

Allowed files:

- `server/lib/ops-mineru-log-parser.mjs`
- `server/tests/mineru-log-progress-smoke.mjs`
- `docs/codex/PROJECT_STATE.md` only if the accepted semantic contract needs to be recorded
- `TaskAndReport/` report file for this task

## Required Work

1. Inspect the current parser behavior and the historical smoke assertion around error-signal classification.
2. Decide whether the correct canonical label is `failed-confirmed` or `log-error-signal`, based on current UI/operator semantics and existing parser contract.
3. If the current parser behavior is correct, update the smoke test expectation and wording to match it.
4. If the smoke test expectation is correct, update parser behavior narrowly and add regression evidence.
5. Do not use `.skip`, broad suppression, or assertion weakening to make the suite pass.
6. Preserve the completed-window sidecar attribution behavior merged from tasks 7 and 8.

## Non-Goals

- Do not change MinerU parsing, task state transitions, MinIO storage, AI metadata behavior, or production runtime configuration.
- Do not restart services, mutate production tasks, or deploy to `http://localhost:8081/cms/`.
- Do not change completed-window attribution unless a directly related regression is proven.

## Required Checks

Lucode must run and report:

```bash
git status --short --branch
node server/tests/mineru-log-progress-smoke.mjs
node server/tests/mineru-sidecar-completed-window-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
git diff --check
```

## Branch And Report

- Suggested branch: `lucode/p0-mineru-log-progress-smoke-truth-alignment`
- Report file: `TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-MinerU-Log-Progress-Smoke-Truth-Alignment_REPORT.md`
- Do not merge before Lucia review.

## Acceptance Criteria

- `node server/tests/mineru-log-progress-smoke.mjs` passes without `.skip` or weakened assertions.
- Completed-window sidecar smoke remains green.
- Any semantic change is narrow, documented in the report, and grounded in current operator-facing behavior.
