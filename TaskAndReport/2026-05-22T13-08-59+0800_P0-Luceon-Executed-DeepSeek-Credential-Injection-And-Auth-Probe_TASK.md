# TASK-20260522-130859-P0-Luceon-Executed-DeepSeek-Credential-Injection-And-Auth-Probe

## 1. Mainline Objective

Task 242 failed because the real DeepSeek request returned `HTTP 401 Authorization Required`.

Task 243 then proved that the Director-authorized DeepSeek test key did not reach Lucode's execution context.

This task moves the credential boundary back to Luceon, the host-side validation owner, and answers the next mainline question:

```text
Can the Director-authorized DeepSeek test credential be injected into the running Mineru2Table deployment and pass a minimal auth-only probe?
```

This task must not rerun Mineru2Table processing.

## 2. Director Authorization

The Director explicitly approved:

```text
Task 244: Luceon-Executed DeepSeek Credential Injection And Auth Probe
```

The DeepSeek test key was provided in the private conversation context. It must never be written to Git, reports, task files, terminal output, shell traces, logs, or copied into Lucode-facing artifacts.

## 3. Environment And Write Boundary

### Luceon Control Workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed writes:

- this task brief;
- the Task 244 report;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden:

- `server/**`
- `src/**`
- package manifests / lockfiles
- Docker/Compose files
- `.env*`
- private role files (`AGENTS.md`, `.agents/**`)

### Mineru2Table Deployment Workspace

```text
/Users/concm/prod_workspace/Mineru2Tables
```

Allowed runtime config write:

- update only `DEEPSEEK_API_KEY` in `/Users/concm/prod_workspace/Mineru2Tables/.env`.

Allowed runtime action:

- recreate only Compose service `mineru2table`, no deps, no build.

Allowed probe:

- exactly one auth-only DeepSeek probe against `GET https://api.deepseek.com/user/balance`.

Forbidden:

- `/api/v1/jobs` POST;
- `chat/completions`;
- Task 242 rerun;
- MinIO object write/delete/cleanup;
- Luceon DB write;
- source-code edits;
- Docker image build;
- broad `docker compose down`;
- dependency restart;
- Docker network/volume mutation;
- UAT/L3/release-readiness/production-readiness/pressure PASS/go-live claim.

## 4. Fast Validation Target

Positive target:

- running `mineru2table-api` container has `DEEPSEEK_API_KEY=[SET] redacted`;
- env value has no leading/trailing whitespace and no CR/LF;
- `/health` remains reachable and reports `llm=configured`;
- one auth-only `/user/balance` probe returns non-401, ideally HTTP 200;
- `jobs.json` size, SHA256, and key count remain unchanged;
- logs show no `/api/v1/jobs` POST during the task window.

Blocked outcomes:

- `BLOCKED_DEEPSEEK_KEY_INVALID_OR_REVOKED` if the Director-authorized key is loaded and the auth-only probe still returns 401.
- `BLOCKED_DEEPSEEK_NETWORK_OR_PROVIDER_REACHABILITY` if the auth-only probe cannot reach the provider.
- `BLOCKED_RUNTIME_KEY_INJECTION_FAILED` if the key cannot be loaded into the running container with the authorized no-deps/no-build operation.

## 5. Review Boundary

Acceptance of this task means only:

```text
The DeepSeek credential injection/auth boundary is proven or honestly blocked.
```

It does not mean Mineru2Table success path is validated, CleanService is activated, Luceon orchestration is wired, or the system is ready for UAT, L3, release, pressure testing, production readiness, or go-live.
