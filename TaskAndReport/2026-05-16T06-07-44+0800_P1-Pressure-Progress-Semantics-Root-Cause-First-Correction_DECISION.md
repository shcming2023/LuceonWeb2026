# Director Correction: Pressure Progress Semantics Must Be Root-Cause Diagnosed First

- Decision time: 2026-05-16T06:07:44+0800
- Recorded by: Director
- Trigger: User explicitly noted that the semantic-lag problem has appeared for a long time and must be root-caused before implementation.

## Correction

Director accepts the correction.

The previously dispatched Task 191 was too implementation-forward. It is now superseded before execution.

The next step is a read-only, evidence-grounded root-cause diagnosis:

- identify the exact source-of-truth chain for task progress;
- compare UI task semantics, DB `ParseTask` state, active-task endpoint logic, direct MinerU task API, MinerU log parser, dependency-health, worker polling, and material/AI backfill;
- explain why these sources diverge during long-running pressure work;
- identify which divergence is expected latency and which is a real defect;
- propose a small implementation plan after the root cause is known.

## Superseded Task

- `TASK-20260516-060121-P1-Pressure-Progress-Semantics-And-AI-Residual-Visibility-Hardening`

The task is not deleted for traceability, but should not be executed as an implementation task.

## Replacement Task

- `TASK-20260516-060744-P1-Pressure-Progress-Semantics-Root-Cause-Diagnosis`

## Forbidden Until Diagnosis Is Reviewed

- source-code implementation for progress semantics;
- UI wording changes that only mask the issue;
- production deployment;
- runtime mutation;
- upload/pressure rerun;
- task/material mutation;
- retry/reparse/re-AI/repair/reset;
- submit-probe;
- service restart/rebuild/redeploy;
- pressure PASS, L3, release readiness, production readiness, production上线, or go-live claim.

