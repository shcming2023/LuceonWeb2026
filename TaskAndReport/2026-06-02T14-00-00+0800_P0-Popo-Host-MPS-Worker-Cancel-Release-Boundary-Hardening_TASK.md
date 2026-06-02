# P0 Popo Host MPS Worker Cancel Release Boundary Hardening Task

Issued by: Luceon
Issued at: 2026-06-02T14:00:00+0800
Task ID: TASK-20260602-140000-P0-Popo-Host-MPS-Worker-Cancel-Release-Boundary-Hardening

## Objective

Harden the cancellation/release boundary between the Luceon Popo adapter and the host Mac MPS worker.

Task 318 restored official MinerU-Popo invocation:

```text
label_normalization.py -> run_inference.py -> get_json_tree.py
```

The remaining immediate blocker is not Popo chunk scheduling. It is that, after Luceon cancels a Docker-side Popo job, the host MPS worker can remain stuck with `active_generations=1`, contaminating the next official Popo run.

## Scope

Allowed:

- Luceon adapter outer boundary in `luceon_service/service.py`.
- Luceon Popo adapter tests in `luceon_service/tests/**`.
- Luceon-local host worker overlay in `/Users/concm/prod_workspace/MineruPopo/luceon_service/host_mps_worker.py`.
- Luceon-local host worker launch wrapper in `/Users/concm/prod_workspace/MineruPopo/scripts/**`.
- `TaskAndReport/**`.

Forbidden:

- MinerU-Popo official `post_processing/label_normalization.py`, `post_processing/run_inference.py`, `post_processing/get_json_tree.py`, or inference algorithm changes.
- Reintroducing Luceon-owned chunk scheduling.
- DB/MinIO cleanup, object deletion, source asset rewrite, or image hash rename.
- Claiming full large-PDF completion/readiness/release/L3/go-live without production evidence.

## Requirements

- Add an observable host-worker release path.
- Empty/idle release should clear model/cache state and return `active_generations=0`.
- Busy release should not pretend success; it must clearly report that worker restart is required, or perform a bounded self-termination when explicitly requested.
- Adapter cancel/timeout should call the host worker release endpoint and preserve release evidence in job metadata/progress.
- The production worker should be relaunched through a stable tmux wrapper that can restart after an intentional self-termination.

## Acceptance

Positive:

- Focused tests pass.
- Python compile passes.
- `git diff --check` passes.
- Production `mineru-popo` stays on official `run_inference.py --resume`.
- After cancel/release validation, host worker returns to `active_generations=0`.

Negative:

- No official Popo pipeline modifications.
- No adapter chunk runner revival.
- No broad runtime cleanup.
