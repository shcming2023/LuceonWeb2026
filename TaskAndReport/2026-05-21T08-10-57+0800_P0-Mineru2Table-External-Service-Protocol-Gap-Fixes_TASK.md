# P0 Mineru2Table External Service Protocol Gap Fixes

- **Task ID**: `TASK-20260521-081057-P0-Mineru2Table-External-Service-Protocol-Gap-Fixes`
- **Issued at**: `2026-05-21T08:10:57+0800`
- **Issuer**: `Luceon`
- **Next Actor**: `Lucode`
- **Status**: `待执行`
- **Priority**: `P0`
- **Scope type**: external Mineru2Table service code/test implementation only; no Luceon runtime wiring or deployment

## 1. Mainline Goal

Fix the four concrete Mineru2Table2026 Protocol v1 blockers discovered and accepted in Task 224:

1. emit `metrics.json` instead of `token_stats.json`;
2. emit `unresolved_anchors.json`;
3. guarantee cleanup of `/tmp/mineru2table_{job_id}` after success and failure;
4. map storage allowlist violations to `StoragePermissionError` so the runner returns `forbidden_storage_target`.

This is a mainline-first task. Do not spend time on deployment, Luceon orchestration, UI, RawMaterial2CleanMaterial, or compatibility sidecars. Those are later tasks after this external service has a testable Protocol v1 output surface.

## 2. Current Evidence

Luceon verified the following from the physical host:

- Luceon workspace: `/Users/concm/prod_workspace/Luceon2026`
- Mineru2Table workspace: `/Users/concm/prod_workspace/Mineru2Tables`
- External repository: `https://github.com/shcming2023/Mineru2Table2026`
- Current local deployed worktree HEAD: `43754fa0f3d18051b2d9a3ab4b3cf769a0d47239`
- Current external upstream `origin/main`: `7e9e592cac7d062edbff31e0c4ddb06d41577474`
- Current running local container remains old/legacy: it exposes `/health`, `/api/v1/extract`, `/api/v1/tasks`, and `/api/v1/tasks/{task_id}`, but does not expose `/api/v1/jobs`.

Source evidence from upstream `7e9e592`:

- `src/core/jobs/runner.py` uploads `token_stats.json` at the metrics step.
- `src/core/jobs/runner.py` does not upload `unresolved_anchors.json`.
- `src/core/jobs/runner.py` creates `temp_dir = /tmp/mineru2table_{job_id}` but has no `finally` cleanup.
- `src/core/storage/minio_backend.py` raises built-in `PermissionError` for endpoint/input/output allowlist failures.
- `src/core/jobs/runner.py` catches `StoragePermissionError` to produce `forbidden_storage_target`, so the current mismatch falls through to `processing_failed_permanent`.

Accepted Task 224 review:

- [Acceptance Review](./2026-05-20T20-05-03+0800_P0-Mineru2Table-Standalone-Service-Fact-Audit-And-CleanService-Contract-Freeze_LUCEON_REVIEW.md)
- [Fact Audit](../docs/contracts/Mineru2Table-Standalone-Service-Fact-Audit.md)
- [Adaptation Plan](../docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md)

## 3. Repositories And Branches

Primary implementation repository:

- repo: `shcming2023/Mineru2Table2026`
- base: latest `origin/main` at or after `7e9e592cac7d062edbff31e0c4ddb06d41577474`
- branch: `lucode/task-225-mineru2table-protocol-gap-fixes`

Luceon control-plane repository:

- repo: `shcming2023/Luceon2026`
- allowed control-plane files only:
  - `TaskAndReport/2026-05-21T08-10-57+0800_P0-Mineru2Table-External-Service-Protocol-Gap-Fixes_REPORT.md`
  - `TaskAndReport/TASK_TRACKING_LIST.md`

The final report must name both repository states:

- Mineru2Table2026 implementation branch and full commit SHA;
- Luceon2026 report/ledger branch and full commit SHA, if a report branch is pushed.

## 4. Write Boundary

Allowed write scope in `shcming2023/Mineru2Table2026`:

- `src/core/jobs/runner.py`
- `src/core/storage/minio_backend.py`
- focused tests under `tests/cleanservice/**`

Optional only if strictly required by the above tests:

- `src/core/jobs/errors.py`

Forbidden in `shcming2023/Mineru2Table2026`:

- no Dockerfile, Compose, `.env*`, secrets, deployment scripts, requirements, package/dependency edits;
- no broad API redesign in `api_server.py`;
- no legacy multipart adapter work;
- no sidecar/proxy code;
- no RawMaterial2CleanMaterial code;
- no deployment, service restart, container rebuild, MinIO write, real LLM call, or real job execution.

Forbidden in `shcming2023/Luceon2026`:

- no edits to `server/**`, `src/**`, Docker, Compose, `.env*`, lockfiles, package files, PRD/body docs, or architecture docs;
- no `AGENTS.md` or `.agents/**` tracking/sync changes;
- no production/runtime/data/sample/model/DB/MinIO/Docker mutation.

## 5. Required Implementation

### 5.1 `metrics.json`

In `src/core/jobs/runner.py`:

- replace the uploaded `token_stats.json` artifact with `metrics.json`;
- make the artifact role/key `metrics`, not `token_stats`;
- keep the job `stats` field if it is already useful for polling;
- ensure `provenance.json` output references the `metrics` artifact role.

Do not emit a second compatibility `token_stats.json` alias unless an existing test proves it is still required. If an alias is added, `metrics.json` must remain the canonical Protocol v1 artifact and the report must justify the alias.

### 5.2 `unresolved_anchors.json`

In `src/core/jobs/runner.py`:

- generate and upload `unresolved_anchors.json` under the same output prefix;
- make the artifact role/key `unresolved_anchors`;
- include it in `provenance.json` outputs;
- when there are no unresolved anchors, upload an empty JSON array `[]`.

The expected minimum schema for each unresolved anchor entry is:

```json
{
  "node_id": "string",
  "level": 1,
  "status": "pending_anchor",
  "candidate_block_uids": ["block-id"],
  "candidate_page_range": [1, 2],
  "reason_codes": ["pending_anchor"]
}
```

Derive this deterministically from the rebuilt tree, especially nodes with `status == "pending_anchor"` and their `anchor_candidates`.

Governance rule: this file is ID-only/source-reference-only. Do not generate or copy free-text source truth into it. Avoid `title`, paragraph text, model explanations, or invented summaries. Use stable IDs, page ranges, and bounded reason codes only.

### 5.3 Temp Directory Cleanup

In `src/core/jobs/runner.py`:

- initialize `temp_dir` safely before the `try` block;
- wrap the job body with `finally`;
- call `shutil.rmtree(temp_dir, ignore_errors=True)` after both success and failure;
- guard deletion so it only targets the intended `/tmp/mineru2table_{job_id}` directory.

Do not add broad cleanup, sweeps, cron jobs, or deletion outside the current job temp directory.

### 5.4 Allowlist Exception Mapping

In `src/core/storage/minio_backend.py`:

- make `_validate_input_bucket`, `_validate_output_bucket`, and `_validate_endpoint` raise `StoragePermissionError`;
- preserve the current error messages enough for diagnostics;
- update focused tests so allowlist violations assert `StoragePermissionError`, not built-in `PermissionError`.

Do not weaken the allowlist checks.

## 6. Required Tests

Run from the Mineru2Table2026 repository.

Required static checks:

```bash
python -m py_compile api_server.py src/core/jobs/runner.py src/core/storage/minio_backend.py
git diff --check origin/main..HEAD
```

Required focused tests:

```bash
PYTHONPATH=. API_KEY=test-key JOB_STORE_PATH=/tmp/mineru2table_jobs_task225.json DEEPSEEK_API_KEY=dummy MINIO_ACCESS_KEY=dummy MINIO_SECRET_KEY=dummy pytest tests/cleanservice -q
```

Add or update tests so the suite proves:

1. allowlist validators raise `StoragePermissionError`;
2. runner upload order includes `metrics.json` and `unresolved_anchors.json`;
3. runner artifact keys include `metrics` and `unresolved_anchors`;
4. runner no longer uploads `token_stats.json` as the canonical metrics artifact;
5. `unresolved_anchors.json` is ID-only and does not include source text/title fields;
6. temp directory cleanup runs on the successful path;
7. temp directory cleanup runs on at least one failure path without deleting outside `/tmp/mineru2table_{job_id}`.

Tests may use monkeypatch/mocks for MinIO, LLM, adapter, tree builder, flooder, job store, and webhook. Tests must not call real MinIO, real LLM, or the currently deployed local container.

## 7. Report Requirements

Create:

`TaskAndReport/2026-05-21T08-10-57+0800_P0-Mineru2Table-External-Service-Protocol-Gap-Fixes_REPORT.md`

The report must include:

- Mineru2Table2026 branch name and full final commit SHA;
- Luceon2026 report branch name and full final commit SHA, if used;
- exact changed-file list from Mineru2Table2026:

```bash
git diff --name-status origin/main..HEAD
```

- exact validation commands and exit codes;
- a short note that no deployment/rebuild/restart was performed;
- a short note that Luceon runtime wiring remains pending;
- any remaining gap that should block deployment or Luceon orchestrator wiring.

Update this ledger row to:

- `Status`: `Ready for luceon Review`
- `Next Actor`: `luceon`
- `Branch / HEAD`: include the Mineru2Table2026 implementation branch and exact commit SHA.

## 8. Acceptance Criteria

Positive acceptance:

- `metrics.json` is the canonical metrics artifact;
- `unresolved_anchors.json` is always emitted and is ID-only/source-reference-only;
- `provenance.json` includes both new/renamed artifact roles;
- allowlist violations map to `forbidden_storage_target` through `StoragePermissionError`;
- temp job directory cleanup is proven by tests;
- focused CleanService tests pass;
- report and ledger provide exact branch/head evidence.

Negative acceptance:

- no Luceon runtime wiring;
- no local service deployment/rebuild/restart;
- no Docker/Compose/env/secret/dependency edits;
- no real MinIO, DB, model, sample, or production data mutation;
- no real LLM call or live job execution;
- no sidecar/proxy or legacy multipart integration work;
- no RawMaterial2CleanMaterial work;
- no free-text hallucination or source-text invention in `unresolved_anchors.json`;
- no UAT, L3, pressure PASS, production readiness, release readiness, or go-live claim.

## 9. Stop Rules

Stop and report instead of widening scope if:

- the upstream source has drifted so the named files no longer contain the gaps;
- tests require real credentials or real MinIO/LLM to verify these changes;
- changing `api_server.py`, Docker/Compose, dependencies, or deployment config appears necessary;
- unresolved anchor extraction cannot be made ID-only without broader tree-builder redesign.
