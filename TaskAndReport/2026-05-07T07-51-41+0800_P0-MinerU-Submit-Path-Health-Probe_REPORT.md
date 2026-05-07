# Lucode Revised Completion Report: P0 MinerU Submit-Path Health Probe

Report time: 2026-05-07T07:51:41+0800

## Basis

This revised report is based on:

- Lucia task brief: `TaskAndReport/2026-05-07T06-32-38+0800_P0-MinerU-Submit-Path-Health-Probe_TASK.md`
- Lucia return review: `TaskAndReport/2026-05-07T06-40-14+0800_P0-MinerU-Submit-Path-Health-Probe_LUCIA_REVIEW.md`

Lucode executed the listed next action from `TaskAndReport/TASK_TRACKING_LIST.md`: amend Git metadata to the repository GitHub noreply identity, rebase latest `origin/main`, rerun focused checks, write revised report, and push the corrected branch.

## Branch And HEAD

- Branch: `lucode/p0-mineru-submit-path-health-probe`
- Corrected implementation HEAD: `5b21ae3392a4f334b02e0ac2d75f616d4286fdfb`
- Final pushed branch HEAD also includes this report/tracking commit; verify with `git log -1 --oneline` on `origin/lucode/p0-mineru-submit-path-health-probe` after push.
- Base after rebase: `origin/main` at `7989842 docs: add next actor task workflow`

## Git Metadata Correction

Corrected commit metadata for `5b21ae3392a4f334b02e0ac2d75f616d4286fdfb`:

- Author: `shcming2023 <141931970+shcming2023@users.noreply.github.com>`
- Committer: `shcming2023 <141931970+shcming2023@users.noreply.github.com>`

## Files Changed

Implementation files:

- `server/upload-server.mjs`
- `scripts/tier2-standard-check.mjs`
- `server/tests/dependency-health-smoke.mjs`
- `.env.example`

Repository workflow files:

- `TaskAndReport/2026-05-07T07-51-41+0800_P0-MinerU-Submit-Path-Health-Probe_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Implementation Summary

- Added opt-in MinerU submit-path probing to `/ops/dependency-health`.
- Kept default dependency-health lightweight: ordinary calls still only use MinerU `/health`.
- Added explicit opt-in controls:
  - Query: `/ops/dependency-health?mineruSubmitProbe=true`
  - Env: `DEPENDENCY_HEALTH_MINERU_SUBMIT_PROBE=true`
- Added bounded submit probe using a minimal synthetic PDF posted directly to active local MinerU `/tasks`.
- Submit probe does not create Luceon `Material`, `ParseTask`, MinIO objects, or DB rows. It may create a synthetic task inside MinerU itself.
- Extended MinerU dependency-health fields with `healthOk` and `submitProbe` details.
- When submit probing is enabled, `dependencies.mineru.ok` requires both `/health` success and `/tasks` task-id success.
- Updated Tier 2 Standard check to request `mineruSubmitProbe=true` and fail if submit probe is not OK.
- Extended focused smoke coverage for `/health` down, default cheap behavior, submit failure, submit success, and Ollama-down parse non-blocking behavior.

## Submit-Probe Evidence

From `node server/tests/dependency-health-smoke.mjs`:

- `/health` down -> `health.ok=false`, `blocking=true`, `dependencies.mineru.ok=false`, `mineru.healthOk=false`.
- `/health` OK and submit probe disabled -> `mineru.healthOk=true`, `submitProbe.enabled=false`, `mineru.ok=true`, MinerU `/tasks` call count remains `0`.
- `/health` OK and `/tasks` submit fails with probe enabled -> `submitProbe.ok=false`, `submitProbe.status=503`, `mineru.ok=false`, `blocking=true`.
- `/health` OK and `/tasks` returns `task_id` with probe enabled -> `submitProbe.ok=true`, `submitProbe.taskId` present, `mineru.ok=true`, `blocking=false`.
- Ollama down remains non-blocking for parse: `ollama.ok=false`, `ollama.blockingParse=false`, `blocking=false`, and `POST /tasks` still succeeds when MinerU and MinIO are OK.

## Commands Run

```text
git status --short --branch
exit 0
output: ## main...origin/main

git fetch origin
exit 0

git pull --ff-only origin main
exit 0
output: Already up to date.

git switch lucode/p0-mineru-submit-path-health-probe
exit 0

git rebase origin/main
exit 0
output: Successfully rebased and updated refs/heads/lucode/p0-mineru-submit-path-health-probe.

GIT_COMMITTER_NAME='shcming2023' GIT_COMMITTER_EMAIL='141931970+shcming2023@users.noreply.github.com' git commit --amend --no-edit --author='shcming2023 <141931970+shcming2023@users.noreply.github.com>'
exit 0
new corrected implementation commit: 5b21ae3392a4f334b02e0ac2d75f616d4286fdfb

node server/tests/dependency-health-smoke.mjs
exit 0
result: 31 passed, 0 failed

npx pnpm@10.4.1 exec tsc --noEmit
exit 0

git diff --check
exit 0

npx pnpm@10.4.1 run build
exit 0
result: build completed; Vite emitted the existing chunk-size warning only.
```

## Checks Skipped

- Full Tier 2 Standard was not rerun in this correction pass because Lucia's return review only required focused checks after metadata amend and rebase.
- No destructive Docker, MinIO, DB, volume, or production cleanup commands were run.

## GitHub Sync Status

- Corrected branch will be force-pushed with lease to `origin/lucode/p0-mineru-submit-path-health-probe`.
- Tracking records the corrected implementation HEAD because the report/tracking commit cannot self-reference its own final hash.
- No merge to `main` was performed by Lucode.

## Risks And Residual Technical Debt

- The submit probe can create a synthetic task inside MinerU. It does not create Luceon DB, task, material, or MinIO records.
- Lucia noted a non-blocking validation ergonomics follow-up: `scripts/tier2-standard-check.mjs` can still produce an unhelpful JSON parse error when `BASE_URL` points at a frontend-only route returning HTML.

## Required Next Review

Lucia review is required. Director decision is not required unless Lucia wants to promote the result into a release or readiness gate.
