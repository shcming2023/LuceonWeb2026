# DevelopmentEngineer Report: P1 CleanService Worker Eligibility InputRef Correction

- Task: `TASK-20260516-082738-P1-CleanService-Worker-Eligibility-InputRef-Correction`
- Based on Director correction task brief: `TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_TASK.md`
- Source implementation commit: `061282b` (`Require CleanService input object evidence`)
- Outcome: `INPUT_OBJECT_REF_ELIGIBILITY_GAP_CORRECTED`
- Requires Director review: yes

## Branch / HEAD

- Branch: `main`
- Initial task execution HEAD after sync: `405462e`
- Implementation HEAD: `061282b`
- GitHub sync: implementation and this report/ledger update are intended for GitHub `main` per task brief after checks pass.

## Files Changed

- `server/services/cleanservice/cleanservice-worker.mjs`
- `server/tests/cleanservice-worker-shell-smoke.mjs`
- `TaskAndReport/2026-05-16T08-27-38+0800_P1-CleanService-Worker-Eligibility-InputRef-Correction_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No runtime startup, UI, PRD truth, role contract, `PROJECT_STATE`, `HANDOFF`, production, Docker, DB, MinIO, MinerU, Ollama, model, secret, sample, or external repository file was changed.

## Implementation Summary

Corrected the CleanService worker eligibility and input request construction boundary:

- `isCleanServiceTaskEligible()` now requires concrete MinIO input evidence:
  - non-empty `metadata.artifactManifestObjectName`; or
  - non-empty `metadata.markdownObjectName`; or
  - non-empty `metadata.parsedPrefix` plus `parsedFilesCount > 0`.
- `metadata.mineruStatus="completed"` alone is no longer eligible.
- `buildCleanServiceJobRequest()` now fails explicitly with:
  - `cleanservice-input-object-ref-missing: expected artifactManifestObjectName, markdownObjectName, or parsedPrefix with parsedFilesCount > 0`
- Existing valid precedence remains:
  - artifact manifest preferred over markdown;
  - markdown preferred over parsed prefix;
  - parsed prefix accepted only when non-empty and parsed file count is positive.

## Regression Evidence

The worker smoke now asserts:

- `isCleanServiceTaskEligible({ metadata: { mineruStatus: "completed" } }) === false`
- `buildCleanServiceJobRequest()` throws `cleanservice-input-object-ref-missing` for `mineruStatus=completed` alone.
- Parsed prefix with `parsedFilesCount=0` remains ineligible.
- Parsed prefix with `parsedFilesCount=1` is eligible.
- Artifact manifest request keeps `role="mineru-artifact-manifest"`.
- Markdown request uses `role="mineru-markdown"` and the markdown object.
- Parsed-prefix request uses `role="mineru-parsed-prefix"` and the parsed prefix object.

## Commands Run and Exit Codes

| Command | Exit | Purpose / Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required initial state check; branch `main...origin/main` |
| `rg -n "\\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Located Task 202 |
| `sed -n ...` on Task 202 brief, Task 201 Director review, worker source, and worker smoke test | 0 | Required correction context read |
| `git fetch origin && git pull --ff-only origin main && git status --short --branch && git rev-parse --short HEAD` | 0 | Synced clean `main` to `405462e` |
| `node --check server/services/cleanservice/cleanservice-worker.mjs && node --check server/tests/cleanservice-worker-shell-smoke.mjs` | 0 | Changed `.mjs` syntax checks passed |
| `git diff --check` | 0 | No whitespace errors |
| `node server/tests/cleanservice-foundation-smoke.mjs` | 0 | Existing foundation smoke still passed |
| `node server/tests/cleanservice-worker-shell-smoke.mjs` | 0 | Worker shell regression smoke passed |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check passed |
| `git diff -- server/services/cleanservice/cleanservice-worker.mjs server/tests/cleanservice-worker-shell-smoke.mjs` | 0 | Reviewed scoped source/test diff |
| `git add server/services/cleanservice/cleanservice-worker.mjs server/tests/cleanservice-worker-shell-smoke.mjs && git commit -m "Require CleanService input object evidence"` | 0 | Implementation commit `061282b` |

## Skipped Checks and Reasons

- `npx pnpm@10.4.1 run build`: skipped because this correction touched only server `.mjs` worker/test files and TaskAndReport files; no frontend, TypeScript app, shared type, or build-sensitive file was changed.
- Production checks: skipped because the task explicitly says not to run production checks.
- Upload, pressure/batch/soak validation, submit-probe, retry, reparse, re-AI, cleanup, repair, reset, task-state reconciliation, and real Mineru2Table dispatch: skipped because forbidden by the task brief.
- External Mineru2Table2026 repository checks: skipped because external repository work was outside scope.

## Residual Risks

- This remains an isolated mock worker shell; it is still not runtime-wired and not real Mineru2Table evidence.
- Future real integration still needs exact content-list ObjectRef contract decisions and external service evidence before dispatch.
- Metadata persistence remains an injected mock adapter contract only.

## Director Review

Director review is required. Recommended next action: review the regression fix and close or continue Task 202. Real dispatch, runtime wiring, production validation, readiness/L3/pressure PASS/go-live remain explicitly unclaimed.
