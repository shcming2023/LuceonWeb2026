# Task Brief: P1 No-Submit Helper Production Source Sync And Read-Only Verification

- Task ID: `TASK-20260515-120307-P1-No-Submit-Helper-Production-Source-Sync-And-Read-Only-Verification`
- Created: 2026-05-15T12:03:07+0800
- Created by: Director
- Assigned role: `DevelopmentEngineer`
- Expected report: `TaskAndReport/2026-05-15T12-03-07+0800_P1-No-Submit-Helper-Production-Source-Sync-And-Read-Only-Verification_REPORT.md`
- Based on user decision: `TaskAndReport/2026-05-15T12-00-20+0800_P1-No-Submit-Helper-Production-Sync-Decision_DECISION.md`
- Accepted source commit: `6bd00f7`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production workspace: `/Users/concm/prod_workspace/Luceon2026`

## Context

Task 174 was accepted at code/docs level. It makes `ops/runtime-ownership-status.sh` read-only/no-submit by default and requires explicit opt-in for MinerU submit-probe.

The user approved Option A: apply this accepted helper/docs change to the production workspace with read-only verification only.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/development-engineer.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 174 report and Director review
12. Task 175 decision
13. This task brief

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Apply only the accepted no-submit helper/docs source change to the production workspace and verify that production's default helper behavior is no-submit/read-only.

## Allowed Target Files In Production

Only these production files may be changed:

- `/Users/concm/prod_workspace/Luceon2026/ops/runtime-ownership-status.sh`
- `/Users/concm/prod_workspace/Luceon2026/docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
- `/Users/concm/prod_workspace/Luceon2026/docs/codex/TEST_MATRIX.md`

No other production source, config, data, task, material, artifact, log, sample, model, secret, DB, MinIO, or Docker-volume file may be changed.

## Allowed Operations

Allowed:

- inspect dev and production git status and HEAD;
- fetch GitHub metadata if needed to confirm `6bd00f7`;
- sync the three allowed files from accepted `origin/main`/`6bd00f7` into the production workspace;
- if any of the three target production files already has local uncommitted changes before sync, stop and write a blocked report instead of overwriting it;
- run `bash -n /Users/concm/prod_workspace/Luceon2026/ops/runtime-ownership-status.sh`;
- run production helper `--help`;
- run production helper default mode only, against production path, and verify it prints:
  - `dependency health without MinerU submit probe`;
  - `MinerU submit probe skipped`;
  - `RUN_MINERU_SUBMIT_PROBE=0`;
- inspect output only enough to confirm no `mineruSubmitProbe=true` request was made by default;
- write the report and update this task row.

## Forbidden Operations

Forbidden:

- `RUN_MINERU_SUBMIT_PROBE=1`;
- `--submit-probe`;
- any direct `mineruSubmitProbe=true` call;
- upload, pressure/batch/soak/fresh serial validation, or any validation artifact creation;
- Docker Compose, rebuild, restart, broad pull that changes unrelated files, service restart, MinerU/Ollama/supervisor/sidecar mutation;
- DB/MinIO/Docker volume/data mutation, restore/import, cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report Structure

The report must include:

1. **Pre-Sync State**
   - dev HEAD;
   - production HEAD;
   - production `git status --short --branch`;
   - whether the three target files were clean before sync.

2. **Sync Method**
   - exact commands used;
   - confirmation that only the three allowed files changed in production.

3. **Read-Only Verification**
   - `bash -n` result;
   - helper `--help` result summary;
   - default helper output evidence showing submit-probe skipped;
   - explicit confirmation no `mineruSubmitProbe=true`, `--submit-probe`, or `RUN_MINERU_SUBMIT_PROBE=1` was run.

4. **Outcome**
   - one of:
     - `PRODUCTION_HELPER_SYNCED_NO_SUBMIT_DEFAULT_VERIFIED`;
     - `BLOCKED_TARGET_FILES_DIRTY`;
     - `BLOCKED_SYNC_WOULD_TOUCH_UNRELATED_FILES`;
     - `BLOCKED_VERIFICATION_FAILED`.

5. **Forbidden Operations Confirmation**

## Completion

Write:

`TaskAndReport/2026-05-15T12-03-07+0800_P1-No-Submit-Helper-Production-Source-Sync-And-Read-Only-Verification_REPORT.md`

Update row 176 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include outcome, production file-change list, and checks.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits in the development workspace unless Director explicitly instructs you. Director will review and handle GitHub synchronization.
