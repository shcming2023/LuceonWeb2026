# Lucode Task Brief: P0 Ollama Runtime Ownership Standardization

- Task ID: `TASK-20260509-094356-P0-Ollama-Runtime-Ownership-Standardization`
- Issued at: 2026-05-09T09:43:56+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `f917099188fc47169c75a91cfe0fd683fc1e85f1`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Director Authorization

Director selected Option A for `TASK-20260509-092935-P0-Ollama-Runtime-Ownership-Standardization-Decision` and clarified:

> 本地只有一个 Ollama server.

Lucia interprets this as approval to standardize Luceon's local runtime boundary so the host-local and container-facing Ollama endpoints resolve to the same intended single effective Ollama runtime.

## Objective

Resolve the release-candidate blocker where upload-server containers can reach Ollama `/api/tags` but container-facing `/api/chat` times out.

The target state is:

- host `localhost:11434` and container-facing `host.docker.internal:11434` / `192.168.65.254:11434` report the same effective Ollama runtime/version;
- required model `qwen3.5:9b` remains available;
- host-local and container-facing no-think `/api/chat` both succeed;
- `/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true` passes after standardization.

This task is runtime standardization only. It is not validation pass 3 and cannot declare production release readiness.

## Accepted Background

Task 55 reported:

- host `localhost:11434` returned Ollama `0.23.1` and no-think chat succeeded;
- container-facing `host.docker.internal:11434` and `192.168.65.254:11434` returned Ollama `0.22.1`;
- container-facing `/api/tags` saw `qwen3.5:9b`;
- container-facing `/api/chat` timed out before headers;
- read-only listener inspection showed listeners on both `127.0.0.1:11434` and `*:11434`.

Director clarified the intended local state is one Ollama server. Treat the observed split as a runtime/listener ownership inconsistency to reconcile, not as a product design choice.

## Authorized Scope

You may:

- inspect host Ollama processes/listeners/binaries/versions;
- inspect Docker container DNS and endpoint reachability;
- identify which Ollama runtime/listener is the intended Luceon endpoint;
- perform the minimum necessary local Ollama runtime/service/process action to standardize the endpoint, only after recording:
  - exact process/listener targeted;
  - exact command or UI-equivalent operation;
  - why it is the minimum necessary action;
  - rollback condition;
- verify that `qwen3.5:9b` remains present;
- verify host-local and container-facing `/api/version`, `/api/tags`, and no-think `/api/chat`;
- run dependency-health with MinerU submit probe after standardization;
- inspect logs without deleting/truncating them.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness;
- run validation pass 3;
- create production validation uploads;
- change model selection, timeout policy, secrets, or production `docker-compose.override.yml`;
- pull, delete, reload, replace, or retag Ollama models without separate Director approval;
- delete or mutate DB rows, MinIO objects, Docker volumes, logs, tasks, artifacts, or sample files;
- run broad production deploy/rebuild/restart/rollback;
- enable skeleton fallback or silent degradation;
- mask Ollama chat failure as healthy.

If the fix requires model operation, production override change, timeout-policy change, Docker Desktop setting change, DB/MinIO/Docker-volume mutation, or broader production deploy/rebuild/restart/rollback, stop and write a blocked report for Lucia.

## Required Verification

Run and report exact concise evidence for:

```bash
git status --short --branch
git diff --check
```

Runtime evidence:

1. Host listener/process/version evidence after standardization.
2. Host-local `/api/version`, `/api/tags`, and no-think `/api/chat`.
3. Container-facing `/api/version`, `/api/tags`, and no-think `/api/chat`.
4. `curl -fsS --max-time 35 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`.
5. Confirmation that no upload was created and no validation pass 3 was run.

If source code is changed unexpectedly, also run:

```bash
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

## Required Report

Create:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Ollama-Runtime-Ownership-Standardization_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 57 with:

- status;
- report path;
- branch / HEAD if any repository commit is made;
- exact runtime operations performed;
- exact verification results;
- Next Actor `Lucia`.

Expected outcomes:

- `STANDARDIZED_READY_FOR_VALIDATION_DECISION`: runtime endpoint standardized and dependency-health passes; Lucia must decide the next validation route separately.
- `BLOCKED_RUNTIME_OPERATION_REQUIRED`: cannot safely standardize within scope.
- `NO_GO_FINAL`: standardization attempted within scope but container-facing chat still fails.

