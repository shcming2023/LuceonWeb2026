# Lucia Decision Review: P0 MinerU Runtime Submit-500 Recovery Authorization

- Review Time: `2026-05-10T08:35:54+0800`
- Reviewer: Lucia
- Decision ID: `TASK-20260510-083141-P0-MinerU-Runtime-Submit-500-Recovery-Authorization`
- Decision Record: `TaskAndReport/2026-05-10T08-31-41+0800_P0-MinerU-Runtime-Submit-500-Recovery-Authorization_DECISION.md`
- Director Decision: `受控 MinerU runtime 恢复`
- Outcome: `DIRECTOR_APPROVED_SCOPED_MINERU_RUNTIME_RECOVERY`

## Decision Interpretation

Director approved Option 1: authorize a scoped MinerU runtime recovery task.

This authorization is limited to recovering the current production MinerU submit path from the observed state where MinerU `/health` is OK but `POST /tasks` returns HTTP 500 through `dependency-health?mineruSubmitProbe=true`.

This is not authorization to restart normal manual PDF validation, create a new validation upload, repair/reprocess the failed 24 pressure-test tasks, mutate production data, or declare production release readiness.

## Authorized Boundary For Lucode

Lucia is issuing Task 68 to Lucode with these constraints:

- inspect current production runtime state first with read-only checks;
- use the minimum necessary MinerU runtime recovery action to clear submit-path HTTP 500;
- prefer the narrowest service-level action over broad stack operations;
- run post-recovery `dependency-health?mineruSubmitProbe=true`;
- run post-recovery upload health and active-task diagnostics;
- preserve production-local `docker-compose.override.yml`;
- report exact commands, evidence, and whether manual testing may safely restart.

## Explicitly Forbidden Without Separate Director Approval

- DB row mutation or deletion;
- MinIO object mutation or deletion;
- Docker volume deletion, pruning, or recreation;
- failed 24 pressure-test task repair or reprocessing;
- new validation upload;
- source code changes;
- secret, model/provider, timeout-policy, or production override changes;
- broad Docker stack restart/rebuild/rollback;
- production release-readiness declaration.

## Next Step

Task 68 is assigned to Lucode.

