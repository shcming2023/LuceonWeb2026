# TASK-20260522-114002-P0-Mineru2Table-DeepSeek-Test-Credential-Injection-And-Minimal-Auth-Probe

## 1. Mainline Objective

Task 242 did not prove the Mineru2Table success path because the real DeepSeek call returned `HTTP 401 Authorization Required`.

The mainline question for this task is narrow:

```text
Is Mineru2Table actually running with the Director-authorized DeepSeek test credential, and can that credential pass a minimal DeepSeek authentication probe?
```

This task must not rerun Mineru2Table processing. It only corrects the runtime credential injection and proves the auth boundary.

## 2. Current Evidence

Luceon performed a read-only host-side diagnosis after Task 242:

- `mineru2table-api` is running and healthy.
- The container has `DEEPSEEK_API_KEY` set, length `35`, with no leading/trailing whitespace and no CR/LF.
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`.
- `LLM_MODEL=deepseek-chat`.
- Mineru2Table initializes `OpenAI(api_key=..., base_url=...)` in `src/core/llm_client.py`.
- The Task 242 request reached `https://api.deepseek.com/chat/completions`.
- DeepSeek returned `HTTP 401 Authorization Required`.
- The provider-masked key fingerprint observed in the runtime error did not match the Director-authorized test key fingerprint observed by Luceon.

Therefore the leading hypothesis is:

```text
Mineru2Table is running with a different or invalid DeepSeek key, not the Director-authorized test key.
```

Do not print, commit, or report the actual key or any raw key suffix.

## 3. Environment And Write Boundary

### Primary Luceon Control Workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed writes in Luceon workspace:

- `TaskAndReport/2026-05-22T11-40-02+0800_P0-Mineru2Table-DeepSeek-Test-Credential-Injection-And-Minimal-Auth-Probe_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden in Luceon workspace:

- `server/**`
- `src/**`
- package manifests or lockfiles
- Docker/Compose files
- `.env*`
- private role files (`AGENTS.md`, `.agents/**`)

### Mineru2Table Deployment Workspace

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed runtime/config write:

- Update only `DEEPSEEK_API_KEY` in `/Users/concm/prod_workspace/Mineru2Tables/.env` to the Director-authorized test key.

The key was authorized by the Director outside Git. It must never be written into any tracked file, report, task note, terminal transcript, debug dump, or Git commit.

Allowed runtime action:

- Recreate only the `mineru2table` Compose service, with no dependency restart and no image build.

Preferred command from `/Users/concm/prod_workspace/Mineru2Tables`:

```bash
docker compose up -d --force-recreate --no-deps mineru2table
```

If this command is unavailable in the local environment, use the equivalent `docker-compose` command. Do not use `docker compose down`, do not rebuild, and do not recreate Docker networks or volumes.

Forbidden in Mineru2Table workspace:

- source code edits
- Git commits or pushes in the Mineru2Table repository
- Docker image build
- broad `docker compose down`
- dependency service restart
- Docker network or volume mutation
- MinIO object writes/deletes/cleanup
- any `/api/v1/jobs` POST or legacy extraction POST
- any rerun into `eduassets-clean/toc-rebuild/1842780526581841/v1/`

## 4. Critical Path Scope

1. Privately update the Mineru2Table `.env` so `DEEPSEEK_API_KEY` equals the Director-authorized test key.
2. Recreate only the `mineru2table` service with no deps and no build.
3. Verify inside `mineru2table-api` that:
   - `DEEPSEEK_API_KEY` is set;
   - length is expected;
   - no leading/trailing whitespace;
   - no CR/LF;
   - an ephemeral local comparison confirms it matches the Director-authorized key, without printing the key or fingerprint.
4. Run exactly one minimal auth-only DeepSeek probe from inside the container.
5. Verify no Mineru2Table job was submitted and no output/data state changed.

## 5. True Preconditions

- Disable shell tracing before handling the key (`set +x` if using shell).
- Do not echo the key.
- Do not store the key in scratch files.
- Do not paste the key into the report.
- Confirm `mineru2table-api` is reachable before and after the service recreate.
- Capture the pre-probe `jobs.json` size, SHA256, and key count.

## 6. Minimal Auth Probe

Use a no-completion auth probe. Prefer DeepSeek balance endpoint from inside `mineru2table-api`:

```bash
python - <<'PY'
import os, requests
key = os.environ["DEEPSEEK_API_KEY"]
resp = requests.get(
    "https://api.deepseek.com/user/balance",
    headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    timeout=10,
)
print("status_code", resp.status_code)
print("content_type", resp.headers.get("content-type", ""))
print("body_kind", "json" if "application/json" in resp.headers.get("content-type", "") else "non-json")
PY
```

The report may record status code, content type, and a redacted body classification. It must not print account balance details if that would expose private account information. Do not call `chat/completions` in this task.

## 7. Fast Validation Target

Positive target:

- `DEEPSEEK_API_KEY` in the running container is confirmed to match the Director-authorized test key without revealing the key.
- The minimal auth probe returns a non-401 authentication result, ideally `200 OK`.
- `/health` still reports `llm=configured`.
- `jobs.json` size/SHA/key-count remain unchanged from pre-probe.
- No `POST /api/v1/jobs` appears in logs during this task window.

## 8. Stop Rules

Stop and report without widening scope if any of these occur:

- Director-authorized key is not available to the executor.
- The service recreate would require `docker compose down`, image build, network recreate, or volume mutation.
- The running container still does not match the Director-authorized key after one careful `.env` correction and no-deps recreate.
- The auth probe still returns `401`; classify as `BLOCKED_DEEPSEEK_KEY_INVALID_OR_REVOKED`.
- The auth probe times out or cannot reach DeepSeek; classify as `BLOCKED_DEEPSEEK_NETWORK_OR_PROVIDER_REACHABILITY`.
- Any command would print the key or raw key suffix.

Do not retry by submitting a Mineru2Table job.

## 9. Deferrable Side Work

Explicitly defer:

- rerunning the Mineru2Table success path;
- using a new `assetVersion` or output prefix;
- cleaning or replacing the contaminated Task 242 `v1` prefix;
- fixing Mineru2Table false-success failure semantics;
- webhook/callback validation;
- Luceon orchestrator wiring or scheduler activation.

## 10. Acceptance Criteria

### Positive Acceptance

- Report proves whether the Director-authorized key is now loaded by the running container.
- Report records one minimal auth probe result without leaking secrets.
- Report proves no job submission and no data/output mutation occurred.
- Ledger row 243 is updated to `Ready for luceon Review`, `Next Actor=luceon`.

### Negative Acceptance

- No raw key, key suffix, provider-masked key suffix, full key hash, balance amount, or account-private detail appears in Git.
- No `/api/v1/jobs` POST.
- No MinIO object write/delete/cleanup.
- No Luceon DB write.
- No LLM `chat/completions` call.
- No source-code edit.
- No Docker image build, broad compose down, dependency restart, network/volume mutation.
- No UAT/L3/release-readiness/production-readiness/pressure PASS/go-live claim.

## 11. Required Report Content

The report must include:

- exact branch and HEAD;
- pre/post `mineru2table-api` container status;
- redacted env matrix;
- key match result as boolean only, with no fingerprint value;
- minimal auth probe status and classification;
- pre/post `jobs.json` size, SHA256, and key count;
- log audit proving no `/api/v1/jobs` POST during this task window;
- explicit statement that Task 242 contaminated output prefix was not cleaned, reused, or overwritten;
- final classification:
  - `AUTH_PROBE_PASSED`, or
  - `BLOCKED_DEEPSEEK_KEY_INVALID_OR_REVOKED`, or
  - `BLOCKED_DEEPSEEK_NETWORK_OR_PROVIDER_REACHABILITY`, or
  - `BLOCKED_RUNTIME_KEY_MISMATCH`.

## 12. Review Boundary

Acceptance of this task means only:

```text
The DeepSeek credential injection/auth boundary is corrected or honestly classified.
```

It does not mean Mineru2Table success path is validated, CleanService is activated, Luceon orchestration is wired, or the system is ready for UAT, L3, pressure testing, release, or go-live.
