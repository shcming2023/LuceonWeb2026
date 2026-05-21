# Luceon Review - Task 225 Final Acceptance

- **Task ID**: `TASK-20260521-081057-P0-Mineru2Table-External-Service-Protocol-Gap-Fixes`
- **Review Time**: `2026-05-21T11:24:49+0800`
- **Decision**: `ACCEPTED_EXTERNAL_SERVICE_CODE_TEST_LEVEL`
- **Accepted External Repository**: `shcming2023/Mineru2Table2026`
- **Accepted External Branch**: `lucode/task-225-mineru2table-protocol-gap-fixes`
- **Accepted External HEAD**: `b43852485d9f0e7d2918578df494afefe6b2f687`
- **Reviewed Luceon Control Commit**: `50959ff84416ba0e981dca01b1b044dff43e7575`
- **Boundary**: code/test acceptance for the external service branch only; no deployment, no service restart, no Luceon runtime wiring.

## 1. Verdict

Task 225 is accepted at external-service code/test level.

The resubmission resolves the narrow return blockers from `2026-05-21T09-32-41+0800`:

1. The external `Mineru2Table2026` branch is now GitHub-visible.
2. The Luceon control-plane report and ledger are now GitHub-visible on `main`.
3. `git diff --check origin/main..HEAD` passes on the accepted external branch.
4. Out-of-scope behavior changes to `llm_client.py` and `src/core/provenance/generator.py` were removed.
5. Hostile/pathlike `job_id` handling and temp cleanup guard coverage were added.

## 2. Verified Scope

Luceon verified the accepted external branch:

```bash
git ls-remote --heads https://github.com/shcming2023/Mineru2Table2026.git 'lucode/task-225-mineru2table-protocol-gap-fixes'
# b43852485d9f0e7d2918578df494afefe6b2f687 refs/heads/lucode/task-225-mineru2table-protocol-gap-fixes
```

Accepted external diff:

```text
M       src/core/jobs/__init__.py
M       src/core/jobs/runner.py
M       src/core/provenance/__init__.py
M       src/core/storage/__init__.py
M       src/core/storage/minio_backend.py
M       src/core/webhook/__init__.py
M       tests/cleanservice/test_deprecated_routes.py
M       tests/cleanservice/test_idempotency.py
M       tests/cleanservice/test_provenance_schema.py
M       tests/cleanservice/test_quota_hard_limit.py
A       tests/cleanservice/test_runner_protocol.py
M       tests/cleanservice/test_storage_allowlist.py
```

The four `src/core/*/__init__.py` changes are accepted as mechanical null-byte cleanup needed for Python compilation. No `llm_client.py`, `src/core/provenance/generator.py`, Docker, Compose, env, dependency, or deployment file change remains in the accepted external branch.

## 3. Technical Acceptance

Accepted implementation behavior:

- `runner.py` emits canonical `metrics.json` and no canonical `token_stats.json`.
- `runner.py` emits `unresolved_anchors.json` and keeps its entries ID-only/source-reference-only: stable node IDs, levels, status, candidate block IDs, page ranges, and bounded reason codes.
- `minio_backend.py` maps endpoint/input/output allowlist violations to `StoragePermissionError`.
- `runner.py` maps `StoragePermissionError` to `forbidden_storage_target`.
- `runner.py` rejects hostile/pathlike `job_id` values before constructing temp paths.
- `runner.py` cleanup only removes guarded `/tmp/mineru2table_{job_id}` directories.

## 4. Luceon Verification

Luceon used a temporary clone and temporary venv under `/tmp`; no project deployment or persistent service state was modified.

```bash
git clone --single-branch --branch lucode/task-225-mineru2table-protocol-gap-fixes https://github.com/shcming2023/Mineru2Table2026.git /tmp/mineru2table-task225-review-1779333813
python3 -m venv /tmp/mineru2table-task225-venv-1779333813
/tmp/mineru2table-task225-venv-1779333813/bin/python -m pip install -r /tmp/mineru2table-task225-review-1779333813/requirements.txt pytest
git -C /tmp/mineru2table-task225-review-1779333813 fetch origin main:refs/remotes/origin/main
```

Verification commands:

```bash
/tmp/mineru2table-task225-venv-1779333813/bin/python -m py_compile \
  /tmp/mineru2table-task225-review-1779333813/api_server.py \
  /tmp/mineru2table-task225-review-1779333813/src/core/jobs/runner.py \
  /tmp/mineru2table-task225-review-1779333813/src/core/storage/minio_backend.py

git -C /tmp/mineru2table-task225-review-1779333813 diff --check origin/main..HEAD

PYTHONPATH=/tmp/mineru2table-task225-review-1779333813 \
API_KEY=test-key \
JOB_STORE_PATH=/tmp/mineru2table_jobs_task225_luceon_review_1779333813.json \
DEEPSEEK_API_KEY=dummy \
MINIO_ACCESS_KEY=dummy \
MINIO_SECRET_KEY=dummy \
/tmp/mineru2table-task225-venv-1779333813/bin/python -m pytest \
  /tmp/mineru2table-task225-review-1779333813/tests/cleanservice -q
```

Result:

```text
13 passed, 11 warnings in 4.24s
```

Warnings are Python deprecation warnings for `datetime.utcnow()` in existing test paths and do not block Task 225 acceptance.

## 5. Acceptance Boundary

This acceptance does not mean:

- the external branch has been merged into Mineru2Table `main`;
- the local `/Users/concm/prod_workspace/Mineru2Tables` deployment has been updated;
- the running `mineru2table-api` container has been rebuilt or restarted;
- Luceon has wired `CleanServiceWorker` to real Mineru2Table dispatch;
- any real MinIO object, DB row, Docker volume, model, sample file, or production data was mutated;
- UAT, L3, pressure PASS, release readiness, production readiness, or go-live is approved.

## 6. Next Mainline Recommendation

The next mainline task should be a separate deployment-readiness step for the external Mineru2Table service:

- decide whether and how to merge `b43852485d9f0e7d2918578df494afefe6b2f687` into the external service mainline;
- rebuild/redeploy the local Mineru2Table container only if explicitly authorized;
- verify `/api/v1/jobs`, `/health`, and the seven-file output contract with mock-safe or tightly scoped non-production inputs before any Luceon orchestrator wiring task.
