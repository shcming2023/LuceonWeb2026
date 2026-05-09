# Director Decision Required: P0 Ollama Runtime Ownership Standardization

- Task ID: `TASK-20260509-092935-P0-Ollama-Runtime-Ownership-Standardization-Decision`
- Created at: 2026-05-09T09:29:35+0800
- Created by: Lucia
- Status: `挂起`
- Next Actor: Director
- Related review: `TaskAndReport/2026-05-09T09-29-35+0800_P0-Container-To-Host-Ollama-Chat-Timeout-Revision-2_LUCIA_REVIEW.md`
- Production release readiness: not claimed

## Decision Needed

Lucode and Lucia both confirmed that the remaining release-candidate blocker is a local Ollama runtime ownership/listener split:

- host `localhost:11434` reports Ollama `0.23.1` and can complete no-think chat;
- container-facing `host.docker.internal:11434` / `192.168.65.254:11434` reports Ollama `0.22.1`;
- container-facing `/api/tags` works, but container-facing `/api/chat` times out before response headers;
- two host `ollama serve` listeners exist: one on `127.0.0.1:11434`, one on `*:11434`.

This blocks production release-candidate readiness because Phase 1 requires container upload-server access to host Ollama `qwen3.5:9b` for AI metadata recognition.

## Options

### Option A: Authorize scoped local Ollama runtime standardization

Authorize Lucia to issue a Lucode task that may:

- identify the intended single Ollama runtime instance for Luceon;
- stop or disable the duplicate/unintended Ollama listener only if the exact target process is verified;
- preserve required model `qwen3.5:9b`;
- avoid model pull/delete/reload unless separately approved;
- avoid changing Luceon secrets, production override, timeout policy, or DB/MinIO/Docker volumes;
- verify that both host-local and container-facing `/api/version`, `/api/tags`, and no-think `/api/chat` use the same effective runtime and pass;
- rerun only the approved dependency-health route after standardization.

This option still does not authorize production release readiness by itself.

### Option B: Hold release-candidate validation

Do not change local Ollama runtime. Keep release-candidate readiness as `NO_GO` and pause further validation until Director performs or approves manual runtime cleanup.

### Option C: Request more read-only evidence

Ask Lucode for another read-only diagnostic pass. This may inspect runtime state but must not stop/restart/change any service or run validation uploads.

## Lucia Recommendation

Lucia recommends Option A, scoped narrowly, because both validation passes and both revision cycles have already been consumed and the blocker is now clearly outside repo-code repair.

Required boundary if Option A is approved:

- no production release-readiness claim;
- no upload unless separately assigned after runtime standardization passes;
- no DB/MinIO/Docker volume deletion or mutation;
- no sample mutation/sync;
- no secret, model-selection, timeout-policy, or production override change;
- no model pull/delete/reload without separate approval;
- every service/process action must name the exact process, listener, command, and rollback condition in the Lucode report.

## Autonomy Boundary

Decision requested timestamp: 2026-05-09T09:29:35+0800.

Heartbeat wait evidence: none yet for this decision.

Decision boundary: local runtime service ownership/listener changes may require stopping, restarting, disabling, or changing Ollama process ownership. Lucia may not autonomously authorize those operations after two unanswered heartbeat checks.

Autonomy rule: if unanswered after heartbeat checks, Lucia may only issue read-only evidence collection or record `NO_GO/HOLD`; Lucia may not authorize process stop/restart/disable, service ownership change, model operation, production release readiness, or destructive data/Docker/MinIO/DB actions.

