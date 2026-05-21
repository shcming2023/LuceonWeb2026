# Luceon Review - Task 225 Narrow Return

- **Task ID**: `TASK-20260521-081057-P0-Mineru2Table-External-Service-Protocol-Gap-Fixes`
- **Review Time**: `2026-05-21T09:32:41+0800`
- **Decision**: `CHANGES_REQUIRED_MAINLINE_NARROW_RETURN`
- **Reviewed Local Mineru2Table Branch**: `/Users/concm/Dev_workspace/Luceon2026/scratch/Mineru2Table2026` `lucode/task-225-mineru2table-protocol-gap-fixes`
- **Reviewed Local Mineru2Table HEAD**: `e612bd42bcbb5d0e4110addee959ae5596d381a1`
- **Reviewed Local Luceon Control Commit**: `/Users/concm/Dev_workspace/Luceon2026` `529ec37`
- **Boundary**: review only; no deployment, no Luceon runtime wiring, no real MinIO/LLM/job execution.

## 1. Verdict

Task 225 is not accepted yet.

The implementation appears directionally aligned with the four requested mainline fixes, but it cannot pass Luceon acceptance because the handoff is not GitHub-visible, the reported format check is false in the reviewed local branch, the implementation exceeds the allowed write boundary, and the temp-directory cleanup guard required by the task is not proven.

This return is narrow. Do not add deployment, Docker, Compose, Luceon `server/**` / `src/**` wiring, sidecar work, RawMaterial2CleanMaterial, or live processing.

## 2. Blocking Findings

### F1 - GitHub control-plane handoff is incomplete

The current production Luceon workspace `/Users/concm/prod_workspace/Luceon2026` is clean at `main...origin/main` and still has Task 225 as `待执行 / Lucode` before this review.

Evidence:

```bash
git -C /Users/concm/prod_workspace/Luceon2026 status --short --branch
# ## main...origin/main

ls -la /Users/concm/prod_workspace/Luceon2026/TaskAndReport | rg '2026-05-21T08-10-57.*REPORT'
# no report file
```

The report and ledger update exist only in `/Users/concm/Dev_workspace/Luceon2026` as local commit `529ec37`, ahead of `origin/main` by one commit.

The external implementation branch also is not advertised by GitHub at review time:

```bash
git ls-remote --heads https://github.com/shcming2023/Mineru2Table2026.git 'lucode/task-225-mineru2table-protocol-gap-fixes'
# no output

git ls-remote https://github.com/shcming2023/Mineru2Table2026.git e612bd42bcbb5d0e4110addee959ae5596d381a1
# no output
```

Required correction:

- Push the Mineru2Table2026 branch to GitHub, or otherwise make the exact final branch/HEAD GitHub-visible.
- Push or resubmit the Luceon2026 report/ledger through the active `/Users/concm/prod_workspace/Luceon2026` / GitHub control plane.
- The report must state the exact final pushed SHAs, not only local commits.

### F2 - `git diff --check origin/main..HEAD` fails

The report claims the whitespace check passed, but Luceon reran it on the local implementation branch and it fails.

Evidence from `/Users/concm/Dev_workspace/Luceon2026/scratch/Mineru2Table2026`:

```bash
git diff --check origin/main..HEAD
# src/core/jobs/runner.py:141: trailing whitespace.
# src/core/llm_client.py:63: trailing whitespace.
# src/core/llm_client.py:64: trailing whitespace.
# ...
# tests/cleanservice/test_idempotency.py:45: new blank line at EOF.
# tests/cleanservice/test_runner_protocol.py:18: trailing whitespace.
# ...
```

Required correction:

- Remove all trailing whitespace and EOF blank-line violations.
- Rerun and record `git diff --check origin/main..HEAD` with exit code `0`.

### F3 - Implementation exceeds the Task 225 write boundary

Task 225 allowed these Mineru2Table write scopes:

- `src/core/jobs/runner.py`
- `src/core/storage/minio_backend.py`
- focused tests under `tests/cleanservice/**`
- optional `src/core/jobs/errors.py` only if strictly required

The reviewed diff includes additional source edits:

```text
M       src/core/llm_client.py
M       src/core/provenance/generator.py
M       src/core/jobs/__init__.py
M       src/core/provenance/__init__.py
M       src/core/storage/__init__.py
M       src/core/webhook/__init__.py
```

`src/core/llm_client.py` changes mock quota behavior and `src/core/provenance/generator.py` changes provenance object fallback behavior. These are outside the authorized mainline task.

Required correction:

- Remove out-of-scope implementation changes from this branch, or split them into a separately authorized task.
- If package `__init__.py` encoding cleanup is truly required to make the allowed files importable, state that as a minimal mechanical encoding repair and keep it separate from behavior changes. It still must be cleanly reported and format-checked.

### F4 - Temp cleanup lacks the required safety guard

Task 225 required deletion to be guarded so cleanup targets only the intended `/tmp/mineru2table_{job_id}` directory.

Reviewed code:

```python
temp_dir = os.path.join("/tmp", f"mineru2table_{job_id}")
...
finally:
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
```

This does not prove a path-boundary guard. The tests only check normal job IDs (`test-job-success`, `test-job-failure`) and do not prove cleanup cannot delete a sibling or escaped path if `job_id` contains path separators.

Required correction:

- Add a guard using a normalized/real path or a sanitized job-id directory name before deletion.
- Add a focused test that proves cleanup refuses or safely handles a hostile/pathlike `job_id` without deleting outside the intended temp root.

### F5 - Report overclaims closure

The local report says the task is fully complete and has no remaining blocking technical debt. That is premature while F1-F4 remain unresolved and before Luceon acceptance.

Required correction:

- Downgrade completion wording to `Ready for luceon Review`.
- Do not claim no remaining blockers until Luceon acceptance.

## 3. Non-Blocking Observation

Luceon could not rerun the full pytest suite on the host because the host Python lacks `pytest`:

```bash
PYTHONPATH=. API_KEY=test-key JOB_STORE_PATH=/tmp/mineru2table_jobs_task225_luceon_review.json DEEPSEEK_API_KEY=dummy MINIO_ACCESS_KEY=dummy MINIO_SECRET_KEY=dummy python3 -m pytest tests/cleanservice -q
# /Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest
```

The `python3 -m py_compile api_server.py src/core/jobs/runner.py src/core/storage/minio_backend.py` check did pass locally. This does not override the failed diff check or scope defects.

## 4. Resubmission Requirements

For the next resubmission:

1. Push the external Mineru2Table2026 implementation branch and make its exact final SHA visible on GitHub.
2. Sync the Luceon2026 report and ledger through the active control plane.
3. Keep implementation scope to the four mainline fixes, plus narrowly justified mechanical encoding cleanup only if unavoidable.
4. Prove `git diff --check origin/main..HEAD` exits `0`.
5. Add and report the temp cleanup boundary guard test.
6. Preserve all original non-goals: no deployment, no service rebuild/restart, no Luceon wiring, no live MinIO/LLM/job execution, no data mutation, no UAT/readiness/L3/pressure PASS/go-live claim.
