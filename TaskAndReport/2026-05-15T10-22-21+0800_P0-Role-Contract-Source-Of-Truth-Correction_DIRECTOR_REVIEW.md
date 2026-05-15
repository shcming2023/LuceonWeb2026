# P0 Role Contract Source-Of-Truth Correction

Issued at: 2026-05-15T10:22:21+0800

Reviewer: Director

## Result

`ACCEPTED_CORRECTION_APPLIED`

## Background

After Task 168 was dispatched to `Architect`, the Architect role thread reported that it did not see an executable task. Director investigated and found a source-of-truth mismatch:

- GitHub `main` contained Task 168 in `TaskAndReport/TASK_TRACKING_LIST.md`.
- GitHub `main` still had the old Lucia/Lucode-oriented collaboration contract and did not contain active role files for `Director`, `ProductManager`, `Architect`, `DevelopmentEngineer`, or `TestAcceptanceEngineer`.
- The updated multi-role contract existed only in the dirty shared development workspace and had not been promoted to GitHub `main`.
- The retired `lucia.md` and `lucode.md` files were still located in the active `docs/codex/roles/` directory on GitHub `main`, which could mislead role threads.

## Correction Applied

Director promoted the active multi-role collaboration baseline to GitHub `main` and removed retired Lucia/Lucode role files from the active role directory:

- Updated `AGENTS.md` to the active Director/ProductManager/Architect/DevelopmentEngineer/TestAcceptanceEngineer model.
- Updated `docs/codex/TEAM_CONTRACT.md` to the active multi-role contract.
- Updated `TaskAndReport/README.md` to the active Director-issued task/report workflow.
- Updated `docs/codex/REPOSITORY_STRUCTURE.md` to describe the active task handoff surface.
- Added active role files under `docs/codex/roles/`.
- Moved retired `docs/codex/roles/lucia.md` and `docs/codex/roles/lucode.md` to `archive/legacy-roles-2026-05-15/`.

## Scope Boundary

This correction changes only collaboration/governance documentation and active role-file placement. It does not change business logic, public API, production deployment, runtime state, sample files, secrets, model configuration, DB, MinIO, Docker volumes, or task-processing behavior.

## Director Finding

The underlying issue was a Director process error: Task 168 was dispatched to an active role before the active role contract had been synchronized to GitHub `main`. This made the task row visible in GitHub but not reliably executable by a compliant role thread.

## Required Next Action

Architect should retry `Architect, check task` from GitHub `main` after this correction is pushed. Task 168 remains the active executable task for `Architect`.

If a role thread is operating from a stale or dirty local checkout and cannot see an expected task, it should report `本地任务列表未更新/疑似不同步` rather than claiming no task exists. Director should then decide whether to sync GitHub, use a clean clone, or explicitly repair the local checkout.

## Release Boundary

No production readiness, L3, pressure PASS, release-readiness, or go-live claim is made by this correction.
