# Lucode Task: P1 Ollama Keep-Alive And Cold/Warm Health Semantics

- Task ID: `TASK-20260510-225807-P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics`
- Created At: `2026-05-10T22:58:07+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P1
- Status: 下达待执行
- Basis: Director judgment after Task 76/77 and Lucia read-only runtime recheck.

## Objective

Make Ollama residency and dependency-health semantics explicit enough for the local long-running production line.

The goal is not to make the system faster. The goal is to prevent a MinerU-completed task from falling into AI metadata instability because `qwen3.5:9b` has gone cold or because a cold-start timeout is indistinguishable from a true Ollama failure.

## Current Evidence

Director observed that `/api/ps` can be empty while only `ollama serve` is running, and dependency-health Ollama smoke can time out at 15 seconds.

Lucia's later read-only recheck showed the state is volatile rather than settled:

- `/api/ps` currently showed `qwen3.5:9b` resident.
- `dependency-health?mineruSubmitProbe=true` still returned `ollama.ok=false`, `chatOk=false`, `durationMs=15025`, error `Smoke test failed: The operation was aborted due to timeout`.
- MinerU submit-probe was OK and admission circuit was closed.

This confirms that Ollama residency / cold-warm health semantics remain unresolved even after Task 77.

## Required Scope

Implement the smallest code/config-documentation change needed to make Ollama behavior explicit and testable.

Required analysis and implementation targets:

- Identify the effective source of Ollama keep-alive configuration for:
  - dependency-health smoke;
  - AI metadata worker/provider calls;
  - production upload-server environment.
- Prefer a repo-backed, explicit setting such as `OLLAMA_KEEP_ALIVE=24h` or `OLLAMA_KEEP_ALIVE=-1`, or an explicit `/api/chat` `keep_alive` parameter where that is the established local pattern.
- Ensure `/api/ps` or an equivalent read-only probe can report whether `qwen3.5:9b` is resident before and after dependency-health.
- Separate dependency-health reporting for:
  - Ollama service reachable;
  - model listed/present;
  - model resident/warm;
  - cold-start chat timeout;
  - warm chat success/failure.
- Do not mask JSON/schema/repair failures as transport retries.
- If limited transport retry is needed for cold-start detection, keep it bounded and explicitly classified.
- Update focused tests/smokes so cold/warm semantics and keep-alive propagation are covered.

## Forbidden Scope

- Do not declare production release readiness, L3/full-site acceptance, manual pressure-test readiness, or pressure PASS.
- Do not create uploads or rerun pressure tests.
- Do not repair, retry, delete, close, or mutate Task 75/76 pressure tasks.
- Do not pull, delete, reload, replace, or change the selected model.
- Do not change secrets.
- Do not modify production local `docker-compose.override.yml` unless Director explicitly authorizes a production override mutation.
- Do not mutate DB rows, MinIO objects, Docker volumes, task/artifact data, logs, sample files, or historical artifacts.
- Do not run broad production restart/rebuild/rollback.

## Required Checks

Run relevant checks and report exact output:

```bash
git diff --check
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
node server/tests/dependency-health-smoke.mjs
```

Add or update focused tests if `dependency-health-smoke.mjs` does not already cover the new cold/warm fields.

If runtime checks are performed, keep them read-only unless a separate Director authorization exists. At minimum, report:

```bash
curl -sS --max-time 8 http://localhost:11434/api/ps
curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

## Required Report

Create:

`TaskAndReport/2026-05-10T22-58-07+0800_P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics_REPORT.md`

The report must include:

- branch and HEAD;
- changed files;
- exact keep-alive source and effective behavior;
- before/after dependency-health semantics;
- `/api/ps` evidence and whether `qwen3.5:9b` is resident;
- exact test results;
- clear statement that no model operation, upload, pressure retry, data mutation, production override mutation, broad restart, or release-readiness claim occurred;
- remaining runtime deployment/validation gap if implementation is code-level only.

