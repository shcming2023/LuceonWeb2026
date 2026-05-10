# Lucode Task: P0 Local Production Service Ownership Unification

- Task ID: `TASK-20260510-142045-P0-Local-Production-Service-Ownership-Unification`
- Created At: `2026-05-10T14:20:45+0800`
- Created By: Lucia
- Next Actor: Lucode
- Priority: P0
- Status: 待执行
- Related Lucia Review: `TaskAndReport/2026-05-10T14-20-45+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_LUCIA_REVIEW.md`

## Objective

Unify the local production runtime ownership contract for MinerU, Ollama, MinIO/Docker, upload-server, and supervisor/ops processes.

This task treats the current failure class as a local long-running production-line governance issue, not a single bug. The short PRD mainline is valid and must not be overturned.

## Required Diagnosis Boundary

Lucode must confirm and record one effective runtime truth for:

- MinerU owner:
  - actual running process;
  - tmux session name;
  - expected repo script;
  - LaunchAgent/supervisor involvement if any;
  - recovery command;
  - health endpoint;
  - submit-probe endpoint and expected success status;
- Ollama owner:
  - actual process/listener;
  - launch/ownership source;
  - container-facing endpoint;
  - host-facing endpoint;
  - expected model `qwen3.5:9b`;
  - whether runtime uses keep-alive settings;
- MinIO/Docker owner:
  - compose service ownership;
  - local-only MinIO console binding;
  - data/volume boundaries that must not be touched;
- upload-server owner:
  - compose service ownership;
  - production override settings;
  - dependency endpoint sources;
- supervisor / sidecar status:
  - which process is expected to monitor what;
  - which process is not owner of MinerU/Ollama/MinIO.

Lucode must explicitly verify whether production runtime env/config fixes these values instead of relying on DB settings as production truth:

- `LOCAL_MINERU_ENDPOINT`
- `OLLAMA_API_URL`
- strict AI/model settings.

## Required Output

Implement or document the smallest durable repository-backed contract needed so future agents and operators have one running口径.

Acceptable outputs include a focused docs/ops config update, a small ops status script, or a minimal runtime-owner status endpoint if already consistent with the codebase. Do not invent a large orchestration layer.

The output must answer:

- who starts MinerU;
- who monitors MinerU;
- who recovers MinerU;
- who starts/owns Ollama;
- who owns MinIO/Docker;
- what endpoint upload-server must use;
- where Director/Lucia/Lucode can inspect current runtime ownership;
- what must never be taken from DB settings as production runtime truth.

## Required Checks

- `git status --short --branch` in development and production;
- inspect production-local override without committing it;
- read-only process/listener/status checks for MinerU/Ollama/MinIO/upload-server;
- `curl -fsS http://localhost:8081/__proxy/upload/health`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`;
- `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'`;
- `git diff --check`;
- targeted smoke/test if code changes are made;
- `npx pnpm@10.4.1 exec tsc --noEmit` and `npx pnpm@10.4.1 run build` if TypeScript/server code changes are made.

## Forbidden Scope

- Do not create new validation uploads.
- Do not run 24-PDF pressure tests.
- Do not repair/reprocess failed pressure-test tasks.
- Do not delete or mutate DB rows, MinIO objects, Docker volumes, tasks, materials, artifacts, logs, samples, secrets, model/provider selection, timeout policy, or production override settings.
- Do not broaden architecture into a new orchestrator.
- Do not claim L3, production release readiness, or full-site acceptance.

## Required Report

Create:

`TaskAndReport/2026-05-10T14-20-45+0800_P0-Local-Production-Service-Ownership-Unification_REPORT.md`

Report must include:

- runtime ownership table;
- exact process/listener/status evidence;
- exact endpoint truth for MinerU and Ollama;
- supervisor/sidecar boundary;
- production override summary;
- changed files and HEAD;
- test/check evidence;
- residual gaps before P1 can be activated.

