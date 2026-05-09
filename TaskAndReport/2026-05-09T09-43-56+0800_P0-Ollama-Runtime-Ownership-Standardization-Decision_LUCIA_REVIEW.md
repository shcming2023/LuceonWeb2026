# Lucia Review: P0 Ollama Runtime Ownership Standardization Decision

- Task ID: `TASK-20260509-092935-P0-Ollama-Runtime-Ownership-Standardization-Decision`
- Review time: 2026-05-09T09:43:56+0800
- Reviewer: Lucia
- Director response: Option A approved; Director clarified "本地只有一个 Ollama server"
- Review decision: `DIRECTOR_APPROVED_OPTION_A`
- Production release readiness: not claimed

## Director Decision Recorded

Director selected Option A and clarified that the intended local operating boundary is a single Ollama server, not an accepted two-server architecture.

Lucia records this as authorization to issue a scoped Lucode runtime-standardization task. The task must reconcile the observed evidence with the Director's intended target state:

- host `localhost:11434` must be the same effective Ollama runtime as container-facing `host.docker.internal:11434` / `192.168.65.254:11434`;
- the required model remains `qwen3.5:9b`;
- container-facing `/api/version`, `/api/tags`, and no-think `/api/chat` must pass after standardization;
- dependency-health with MinerU submit probe must pass after standardization;
- no production release readiness may be declared by this task.

## Boundary

The authorization is limited to local Ollama runtime ownership/listener standardization and verification.

Still forbidden:

- production release-readiness declaration;
- production validation upload or validation pass 3;
- DB, MinIO object, Docker volume, task, artifact, log, or sample deletion;
- secret, model-selection, timeout-policy, or production override changes;
- model pull/delete/reload unless Director separately approves it;
- broad production deploy/rebuild/restart/rollback.

Lucode may perform only the minimum necessary local Ollama runtime service/process action after identifying the exact process/listener/command and rollback condition in the report.

## Next Step

Lucia issued:

`TASK-20260509-094356-P0-Ollama-Runtime-Ownership-Standardization`

Next Actor: Lucode.

