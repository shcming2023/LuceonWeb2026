# User Decision: P0 Production Dirty Source Reconciliation Authorization

- Decision ID: `TASK-20260516-070535-P0-Production-Dirty-Source-Reconciliation-Authorization`
- Created at: `2026-05-16T07:05:35+0800`
- Created by: `Director`
- Current owner: `User`
- Related blocked task: `TASK-20260516-065643-P1-MinerU-Progress-Snapshot-Production-Deployment-And-Read-Only-Validation`
- Development HEAD: `627f69b`
- Production path: `/Users/concm/prod_workspace/Luceon2026`

## Current Facts

The progress-snapshot implementation is accepted on GitHub/main, but production deployment is blocked.

Production source facts:

- production HEAD: `1716add`;
- production `origin/main`: `06d47b6`;
- production is behind by 37 commits;
- production has uncommitted tracked modifications in 9 files:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `docs/codex/TEST_MATRIX.md`
  - `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
  - `ops/runtime-ownership-status.sh`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`

Runtime facts from Task 195:

- active/queued/running/takeover-required work was clear at report time;
- containers were healthy;
- read-only endpoints were healthy;
- Task 193 `progressSnapshot` semantics are not deployed in production yet.

## Why A User Decision Is Needed

Cleaning a dirty production source checkout can overwrite local production adaptations. Even if we create a backup first, a reset/restore/fast-forward is a mutating production-source operation. Director should not silently authorize it as part of a deployment task.

## Options

### Option A: Preserve Dirty Source, Then Reconcile And Continue Deployment (Recommended)

Authorize DevelopmentEngineer to perform a tightly scoped production source recovery:

1. recheck active-work gate immediately before any mutation;
2. create a timestamped backup outside the Git repo, for example under `/Users/concm/prod_workspace/Luceon2026-source-backups/`, containing:
   - `git status --short --branch`;
   - `git diff --stat`;
   - full `git diff` patch;
   - copies of the 9 dirty tracked files;
   - HEAD/origin metadata;
3. verify the backup files exist and are readable;
4. restore/reset only tracked production source files needed to make the worktree clean;
5. fast-forward production source to `origin/main`;
6. rebuild/restart only the minimum required services for Task 193, expected `upload-server` and `cms-frontend`;
7. run only read-only validation endpoints.

Still forbidden:

- upload, pressure test, submit-probe, retry/reparse/re-AI/cancel/repair/reset of tasks;
- DB/MinIO/Docker volume cleanup, `docker compose down -v`, prune, destructive data mutation;
- model pull/delete/replace, secret/config/sample mutation;
- pressure PASS, L3, release readiness, production readiness, go-live declaration.

Director recommendation: choose Option A. It is the fastest safe path because it preserves rollback evidence before cleaning the production source checkout.

### Option B: Backup And Classify Only

Authorize only backup and classification of the production dirty files, with no reset, no fast-forward, no rebuild/restart, and no deployment.

This is safest but will leave the progress-snapshot fix undeployed until another decision.

### Option C: Hold Deployment

Do nothing for now. Production remains on pre-Task-193 code and the known progress-semantics lag remains in live observation.

### Option D: Manual Cleanup By User

User manually handles the production dirty source state, then asks Director to reissue deployment validation.

This keeps production-source cleanup under direct owner control, but may take longer and should still preserve a diff backup before cleanup.

## Pending User Reply

Please choose Option A, B, C, or D.
