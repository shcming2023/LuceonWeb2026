# Lucia Review: P1 Entry Circuit And Durable Admission State

- Review Time: `2026-05-10T15:31:54+0800`
- Reviewed By: Lucia
- Task ID: `TASK-20260510-142045-P1-Entry-Circuit-And-Durable-Admission-State`
- Task Brief: `TaskAndReport/2026-05-10T14-20-45+0800_P1-Entry-Circuit-And-Durable-Admission-State_TASK.md`
- Lucode Report: `TaskAndReport/2026-05-10T14-20-45+0800_P1-Entry-Circuit-And-Durable-Admission-State_REPORT.md`
- Implementation Branch: `lucode/p1-entry-circuit-durable-admission-state`
- Implementation Branch HEAD: `0ceedd324992c1bcb2991cb1a7f4012477f9749f`
- Integrated Main HEAD: `98339b6`

## Review Decision

`ACCEPTED_CODE_LEVEL_PRODUCTION_DEPLOYMENT_REQUIRED`

Lucia accepts the implementation at code level and integrated the implementation into `main`.

This is not production deployment evidence, not production release readiness, and not L3/full-site acceptance.

## Accepted Facts

- A shared MinerU admission circuit now exists in `server/services/mineru/admission-circuit.mjs`.
- The circuit state is persisted through the existing settings path under key `mineruAdmissionCircuit`.
- `POST /tasks` runs MinerU submit-probe admission for non-Markdown MinerU-bound uploads before MinIO, Material, or ParseTask creation.
- When admission is open or blocked, intake returns HTTP `503`, `code=MINERU_ADMISSION_CIRCUIT_OPEN`, and the operator-facing message: `MinerU 当前不可接收新任务，文件未收取，请稍后重试。`
- `/health` HTTP 200 alone does not close the circuit; close requires submit-probe success, cooldown elapsed, active-task clean, and dependency blocking clear.
- The worker reads durable admission state before pending local-MinerU submissions, so a restart does not erase the stop condition.
- Frontend upload UI and dependency banner read the shared admission/circuit state and surface the paused-intake condition.

## Independent Verification

Lucia independently ran these checks after integrating the implementation into local `main`:

```bash
git diff --check HEAD~1..HEAD
node --check server/upload-server.mjs
node --check server/services/queue/task-worker.mjs
node --check server/services/mineru/admission-circuit.mjs
node server/tests/dependency-health-smoke.mjs
node server/tests/mineru-submit-circuit-breaker-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

Results:

- `dependency-health-smoke`: `48 passed, 0 failed`
- `mineru-submit-circuit-breaker-smoke`: `10 passed, 0 failed`
- TypeScript: passed
- Build: passed, with the existing Vite chunk-size warning only
- Diff hygiene and syntax checks: passed

## Residual Boundaries

- The accepted implementation has not been deployed to `/Users/concm/prod_workspace/Luceon2026`.
- No production validation upload, pressure test, failed-task repair, DB/MinIO/Docker volume mutation, secret change, model change, override change, or production release-readiness decision occurred in this review.
- P2 queue-pressure and P3 Ollama stability work remain separate follow-up layers.
- Production runtime validation must record GitHub HEAD, production override summary, dependency-health submit-probe, admission-circuit state, queue/active-task state, Ollama `/api/ps`, and exact pass/fail boundary.

## Next Step

Lucia recorded Director decision task `TASK-20260510-153154-P0-Entry-Circuit-Production-Deployment-Validation-Authorization` to decide whether the accepted P1 circuit may be deployed to production and validated with non-destructive runtime evidence.
