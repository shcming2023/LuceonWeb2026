# Director Review: P1 MinerU Stale Fallback Hygiene And Progress Semantics Hardening

- Task ID: `TASK-20260514-101343-P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening`
- Review time: 2026-05-14T10:43:22+0800
- Reviewed report: `TaskAndReport/2026-05-14T10-13-43+0800_P1-MinerU-Stale-Fallback-Hygiene-And-Progress-Semantics-Hardening_REPORT.md`
- Result: `ACCEPTED_CODE_TEST_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

## Decision

Accepted at code/test level.

The implementation stays within the assigned scope:

- changed `server/lib/ops-mineru-log-parser.mjs`;
- changed `server/tests/mineru-log-channel-ownership-smoke.mjs`;
- did not change frontend helpers;
- did not run upload, production mutation, Docker commands, MinerU/Ollama/sidecar/supervisor operations, log deletion, cleanup, repair/reparse/re-AI, sample/config/secret/model mutation, or readiness/go-live claims.

## Evidence Accepted

The accepted behavior is:

- explicit configured `MINERU_LOG_PATH` / `MINERU_ERR_LOG_PATH` suppress workspace scratch fallback as current progress;
- stale `uat/scratch/mineru-api.log` content such as old `Predict 99%` cannot be selected as `latest-valid-business-signal`;
- the stale fallback can remain visible as ignored diagnostic metadata;
- fresh configured log business progress still parses as `active-progress`;
- empty configured logs remain diagnostic and do not fabricate phase/page/batch progress;
- `fast-complete-no-business-signal` remains truthful.

Director reran required checks:

- `node --check server/lib/ops-mineru-log-parser.mjs` -> pass
- `node server/tests/mineru-log-channel-ownership-smoke.mjs` -> pass, 8 cases
- `node server/tests/mineru-log-progress-smoke.mjs` -> pass, 144/0
- `node server/tests/mineru-log-observation-transport-smoke.mjs` -> pass
- `node server/tests/mineru-log-source-live-smoke.mjs` -> pass, 21/0
- `git diff --check` -> pass

In the clean sync clone, the first rerun of `mineru-log-channel-ownership-smoke` failed only because `node_modules` was absent and `jszip` could not be resolved; after temporarily symlinking the existing development `node_modules` for verification, the same focused tests passed. The symlink was removed before commit and is not part of the repository.

## Boundary

This is not deployed to production yet.

Because the parser is used by both upload-server surfaces and the running `luceon-sidecar`, production validation will require a scoped upload-server rebuild and sidecar restart/re-attach to load the new code. That is a production runtime operation and must be guarded by preflight stop conditions, especially because the production worktree currently has unrelated dirty files.

No production readiness, L3, pressure PASS, release-readiness, go-live readiness, or production上线 is claimed.

## Next Step

Issue Task 118 to DevelopmentEngineer:

`P1 MinerU Stale Fallback Hygiene Production Deployment And Read-Only Runtime Validation`

The task may deploy only if preflight is clean and dirty production files do not block or materially affect the scoped upload-server/sidecar validation. It must not upload PDFs or mutate MinerU/Ollama/DB/MinIO data.
