# Lucia Review: P0 MinerU Runtime Submit-500 Controlled Recovery

- Review Time: `2026-05-10T14:20:45+0800`
- Reviewer: Lucia
- Task ID: `TASK-20260510-083554-P0-MinerU-Runtime-Submit-500-Controlled-Recovery`
- Task Brief: `TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_TASK.md`
- Lucode Report: `TaskAndReport/2026-05-10T08-35-54+0800_P0-MinerU-Runtime-Submit-500-Controlled-Recovery_REPORT.md`
- Review Decision: `ACCEPTED_LOCAL_RUNTIME_RECOVERED_GOVERNANCE_REQUIRED`

## Judgment

Lucode's scoped MinerU-only recovery is accepted as a local runtime recovery precheck, not as readiness to resume production-candidate pressure testing and not as production release readiness.

The evidence confirms that the immediate MinerU submit-path blocker was cleared by restarting the MinerU API tmux session. It also confirms the deeper project diagnosis: the problem is not a single code bug and should not be reduced to adding another worker lock. The current Luceon mainline is valid, but the local long-running production line lacks a unified runtime contract among intake, worker admission, dependency health, service ownership, and resource pressure.

This issue is therefore classified as:

`LOCAL_LONG_RUNNING_PRODUCTION_LINE_GOVERNANCE_PROBLEM`

## Accepted Facts

- Production HEAD during recovery: `e015cc8`.
- Production-local `docker-compose.override.yml` was preserved.
- Before recovery, upload health was OK, MinerU `/health` was OK, but `dependency-health?mineruSubmitProbe=true` returned MinerU submit probe HTTP 500 and `blocking=true`.
- MinerU reported `max_concurrent_requests=1`.
- Existing Luceon MinerU parse and AI metadata worker behavior is already effectively serial for heavy stages.
- Lucode used a MinerU-only tmux session restart:
  - `tmux kill-session -t mineru_api`
  - `tmux new-session -d -s mineru_api "cd '/Users/concm/prod_workspace/Luceon2026' && bash ops/start-mineru-api.sh"`
- After recovery, upload health was OK.
- After recovery, MinerU `/health` was OK.
- After recovery, `dependency-health?mineruSubmitProbe=true` returned `ok=true`, `blocking=false`, MinerU submit probe HTTP `202`, task `3ef74604-9282-4248-bb8f-e2784573ee14`.
- Active-task diagnostics were clean.
- No new validation upload was created.
- No failed 24-task repair or reprocessing was attempted.
- No DB row, MinIO object, Docker volume, task, material, artifact, log, sample, secret, model/provider, timeout-policy, or production override mutation was reported.
- No broad Docker stack restart/rebuild/rollback was performed.

## Governance Direction

The validated short path remains the PRD mainline:

upload -> MinIO -> local MinerU -> parsed artifacts -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.

The next work must govern long-running local production behavior instead of trying to make the system merely faster. The system must know:

- when it may accept work;
- when it must stop accepting work;
- who owns recovery;
- how Director can judge whether more input is safe.

Lucia is issuing two consecutive governance tasks:

1. Task 69 P0: service ownership unification.
2. Task 70 P1: entry circuit and durable circuit-state design/implementation.

Task 70 is created now but must not be activated for Lucode execution until Task 69 is completed and accepted by Lucia.

## Release Boundary

Manual pressure testing and production release readiness remain blocked. Passing a submit probe after a tmux restart is not enough to resume 24-PDF pressure validation. The next accepted evidence must include a stable runtime contract and intake admission rules.

