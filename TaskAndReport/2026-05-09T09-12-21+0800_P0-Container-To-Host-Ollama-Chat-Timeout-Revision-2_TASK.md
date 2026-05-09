# Lucode Task Brief: P0 Container-To-Host Ollama Chat Timeout Revision 2

- Task ID: `TASK-20260509-091221-P0-Container-To-Host-Ollama-Chat-Timeout-Revision-2`
- Issued at: 2026-05-09T09:12:21+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `fc74d66`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Objective

Use revision cycle 2 of 2 to diagnose and, if safely possible, fix the remaining release-candidate blocker:

> upload-server container-to-host Ollama `/api/chat` to `host.docker.internal:11434` times out, while container `/api/tags` sees `qwen3.5:9b` and host direct no-think chat can succeed.

This task is not validation pass 3. It is the final bounded revision opportunity in the Director timebox.

## Accepted Background

Task 54 pass 2 reported `BLOCKED_AFTER_PASS_2`:

- validation pass count used: 2 of 2
- revision cycle count used so far: 1 of 2
- production and development synced to `f720685`
- production override boundary preserved
- CMS/DB/MinIO/MinerU submit path passed
- diagnostics classification passed
- host direct no-think warm-up succeeded in `8938ms`
- container `/api/tags` to `host.docker.internal:11434` returned HTTP `200` and saw `qwen3.5:9b`
- upload-server dependency-health and container-side no-think `/api/chat` still timed out

Lucia independently confirmed dependency-health with MinerU submit probe still fails on Ollama chat timeout while MinIO/MinerU pass.

## Required Diagnosis

Produce exact evidence for the container-to-host Ollama chat timeout path. At minimum inspect or test, using non-destructive commands:

1. Host-side Ollama reachability and no-think chat behavior.
2. Container-side DNS/endpoint resolution for `host.docker.internal`.
3. Container-side `/api/tags` versus `/api/chat` behavior using the same no-think request shape.
4. Whether timeout occurs before headers, during body read, or during generation.
5. Whether the upload-server request path differs materially from a minimal container `curl`/Node request.
6. Whether Docker networking, Ollama binding, proxy/env, or container runtime constraints are the likely cause.

## Authorized Scope

You may:

- run read-only host and container diagnostics
- use `docker exec` read-only commands against existing containers
- inspect logs without deleting or truncating them
- implement a minimal repository code fix if the cause is in repository code
- add focused tests for any repository code fix
- run local code checks

If a production runtime apply is needed only to verify a repository code fix, stop and report first unless the action is already covered by a non-destructive code-apply boundary. Do not create uploads in this task.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness
- run production-candidate validation pass 3
- create production validation uploads
- change model selection, timeout policy, secrets, or production `docker-compose.override.yml`
- restart, kill, reload, pull, delete, or change Ollama models
- delete or mutate DB rows, MinIO objects, Docker volumes, logs, tasks, artifacts, or sample files
- run broad production deploy/rebuild/restart/rollback
- enable skeleton fallback or silent degradation
- mask Ollama failure as healthy when chat generation is unavailable

If the safe fix requires a production override change, Docker Desktop/network setting change, service restart, model operation, timeout policy change, or other hard-stop action, write a blocked report and propose a Director decision record. Do not apply it.

## Acceptance Criteria

One of these outcomes is required:

1. `FIX_READY_FOR_LUCIA_REVIEW`: a minimal repository code fix is implemented with focused tests and evidence showing it addresses the container-to-host chat timeout without weakening strict AI readiness.
2. `NO_CODE_RUNTIME_DECISION_REQUIRED`: no safe repo fix is appropriate; the report identifies the exact runtime/ops decision needed from Director.
3. `NO_GO_FINAL`: the issue remains unresolved within revision cycle 2 and release readiness should be held.

In all outcomes, preserve:

- strict no-skeleton behavior
- required model `qwen3.5:9b`
- dependency-health honesty
- sample directory read-only boundary
- no production release-readiness claim

## Required Checks

If code changes are made:

```bash
git status --short --branch
git diff --check
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If no code changes are made, still run:

```bash
git status --short --branch
git diff --check
```

Runtime evidence must be exact, but keep outputs concise and redact any secret-like values if encountered.

## Required Report

Create:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Container-To-Host-Ollama-Chat-Timeout-Revision-2_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 55 with:

- status
- report path
- branch / HEAD
- outcome classification
- revision cycle count used
- validation pass count already used
- exact next actor and next action

Expected next actor: `Lucia`.

Do not run another production-candidate validation pass without a new Lucia or Director decision.
