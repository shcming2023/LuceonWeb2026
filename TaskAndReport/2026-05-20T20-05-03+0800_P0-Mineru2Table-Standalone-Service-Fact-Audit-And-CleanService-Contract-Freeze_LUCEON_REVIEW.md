# Luceon Review - Task 224 Final Acceptance

- **Task ID**: `TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Review Time**: `2026-05-20T20:05:03+0800`
- **Decision**: `ACCEPTED_DOCS_LEVEL_WITH_LUCEON_CONTROL_PLANE_CORRECTION`
- **Reviewed Branch**: `lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze`
- **Confirmed Branch HEAD**: `6461830fe049f2976151223d277af0a4aead9fef`
- **Boundary**: docs/control-plane fact audit only; no runtime/source/deployment acceptance.

## 1. Review Verdict

Task 224 is accepted at docs/control-plane level.

The narrow-return blockers that affected the mainline integration decision are resolved:

1. The audit now distinguishes the current local deployed Mineru2Table container from the latest upstream source state.
2. The local deployed state is correctly recorded as legacy multipart-only and not Protocol v1 ready.
3. The upstream source state is correctly recorded as a Protocol v1 candidate with remaining explicit gaps.
4. The storage allowlist exception mismatch is recorded as a non-compliant gap rather than compliant behavior.
5. Option A is recorded as Lucode-recommended / candidate for Luceon approval, not as already approved.

One residual control-plane issue remained: the submitted report and ledger still pointed to stale branch HEAD `441e06d649dbb064c585c54d7d4ecb9feee3c3f3`, while the fetched remote branch HEAD is `6461830fe049f2976151223d277af0a4aead9fef`. Luceon corrected that evidence during integration instead of returning the task again, because the remaining mismatch was bookkeeping and not a mainline technical blocker.

## 2. Luceon Verification Evidence

Luceon verified the submitted branch and scope from `/Users/concm/prod_workspace/Luceon2026`:

```bash
git fetch origin --prune --tags
git rev-parse origin/main
# 4d5d8db6907d6f81038cfd35f5ee9f982153c935

git rev-parse origin/lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze
# 6461830fe049f2976151223d277af0a4aead9fef

git diff --check origin/main..origin/lucode/TASK-20260520-192050-P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze
# exit 0; no output
```

Submitted diff scope before Luceon correction:

```text
A       TaskAndReport/2026-05-20T19-20-50+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_REPORT.md
M       TaskAndReport/TASK_TRACKING_LIST.md
M       docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
A       docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md
```

Luceon independently verified the Mineru2Table split:

```bash
git -C /Users/concm/prod_workspace/Mineru2Tables rev-parse HEAD
# 43754fa0f3d18051b2d9a3ab4b3cf769a0d47239

git -C /Users/concm/prod_workspace/Mineru2Tables rev-parse origin/main
# 7e9e592cac7d062edbff31e0c4ddb06d41577474

docker ps --filter name=mineru2table --format '{{.Names}} {{.Image}} {{.Ports}}'
# mineru2table-api mineru2tables-mineru2table 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

`GET http://127.0.0.1:8000/openapi.json` on the running local container exposes `/health`, `/api/v1/extract`, `/api/v1/tasks`, and `/api/v1/tasks/{task_id}`. It does not expose `/api/v1/jobs`.

The latest upstream source was checked through the Mineru2Table remote ref:

```bash
git ls-remote https://github.com/shcming2023/Mineru2Table2026.git HEAD
# 7e9e592cac7d062edbff31e0c4ddb06d41577474 HEAD
```

Source spot-checks against `/Users/concm/prod_workspace/Mineru2Tables` `origin/main` showed:

- `api_server.py` defines `/api/v1/jobs`, `/api/v1/jobs/{job_id}`, and `/api/v1/jobs:from-storage`.
- `src/core/jobs/store.py` requires `JOB_STORE_PATH`, writes JSON through a temporary file, calls `fsync`, then `os.replace`.
- `src/core/storage/minio_backend.py` raises built-in `PermissionError` for allowlist violations.
- `src/core/jobs/runner.py` catches `StoragePermissionError` to emit `forbidden_storage_target`, so current upstream exception mapping is not compliant until fixed.
- `src/core/jobs/runner.py` still uploads `token_stats.json` rather than `metrics.json`; unresolved anchors and temp directory cleanup remain follow-up gaps.

## 3. Luceon Integration Corrections

During acceptance integration, Luceon made only control-plane/document corrections:

1. Corrected the report's `Final Branch HEAD` from stale `441e06d...` to `6461830fe049f2976151223d277af0a4aead9fef`.
2. Replaced the report's branch/HEAD placeholder with the confirmed branch/HEAD.
3. Updated the Task 224 ledger row to `完成关闭` / `None` and linked this acceptance review.
4. Removed one premature readiness phrase from the adaptation-plan Option A benefits, replacing it with long-term architecture wording.

## 4. Acceptance Boundary

This acceptance means the Task 224 fact audit is usable for the next mainline task.

It does not accept or authorize:

- Luceon runtime wiring to Mineru2Table;
- production dispatch;
- external Mineru2Table source edits;
- Mineru2Table rebuild/redeploy/restart;
- DB/MinIO/Docker/model/sample/data mutation;
- real processing requests, upload, reparse, retry, or re-AI;
- UAT, L3, pressure PASS, release readiness, production readiness, or go-live.

## 5. Next Mainline Recommendation

Proceed with a narrow external-service implementation task for Mineru2Table itself:

- implement `metrics.json` naming;
- generate/upload `unresolved_anchors.json`;
- add temp directory cleanup;
- fix allowlist exception mapping to `StoragePermissionError`;
- keep deployment and Luceon orchestrator wiring out of that task unless explicitly authorized.
