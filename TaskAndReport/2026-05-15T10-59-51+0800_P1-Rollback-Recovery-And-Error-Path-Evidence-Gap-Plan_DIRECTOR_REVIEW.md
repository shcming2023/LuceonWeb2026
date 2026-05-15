# Director Review: P1 Rollback Recovery And Error Path Evidence Gap Plan

- Task ID: `TASK-20260515-101039-P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan`
- Reviewed at: 2026-05-15T10:59:51+0800
- Reviewer: Director
- Reviewed report: `TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_REPORT.md`
- Result: `ACCEPTED_READ_ONLY_EVIDENCE_FIRST`

## Summary

Director accepts the Architect report. The report satisfies the task brief, keeps the analysis read-only, separates accepted evidence from missing evidence, and correctly frames the remaining release-readiness blocker as an evidence-quality gap rather than a known implementation failure.

The accepted recommendation is `READ_ONLY_EVIDENCE_FIRST`: collect a final read-only rollback/recovery and error-path evidence pack before asking the user to approve any controlled rollback/failure-injection rehearsal or to accept residual operational risk.

## Director Spot Check

Director performed a non-mutating spot check after the report:

- Development workspace: `main...origin/main` with Task 168 report and tracking-row updates pending commit.
- Production path: `/Users/concm/prod_workspace/Luceon2026`.
- Production HEAD: `1716add Dispatch dependency health production validation`.
- Production dirty files match the previously classified local-boundary set.
- Docker services are healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
- `/cms/` and `/cms/tasks` returned HTTP 200 through the production frontend.
- `GET /__proxy/upload/health` returned HTTP 200 and `ok=true`.
- `GET /__proxy/upload/ops/dependency-health` returned HTTP 200, `ok=true`, `blocking=false`, and Ollama readiness fields including `readinessState=resident-chat-succeeded`, `readinessSeverity=info`, `probeTimeoutMs=15000`, `recommendedClientTimeoutMs=20000`, `blockingAi=false`, and `readinessBlocking=false`.
- `GET /__proxy/upload/ops/mineru/admission-circuit` returned HTTP 200 and `open=false`.
- `GET /__proxy/upload/ops/mineru/active-task` returned HTTP 200 with no active task and `historicalAiFailureTasks=6`.
- Direct MinerU `/health` returned HTTP 200 and `status=healthy`.

## Accepted Findings

- Source rollback and Docker/service rollback primitives exist, but release-grade rollback rehearsal evidence is missing.
- Production-local override preservation is classified and has survived recent scoped deploys, but exact pre/post assertion evidence is still thin.
- DB backup and import/export mechanisms exist in code/UI, but current production export-shape and restore rehearsal evidence remain incomplete.
- MinIO artifact preservation relies on Docker volume and object manifests; read-only inventory evidence can still improve confidence, while restore rehearsal is mutating.
- Error-path coverage is strong at code/smoke level for Ollama and strict AI failure semantics, but production has naturally observed only the healthy/resident path.
- Known `failed/ai` residuals are accepted as visible manual retry candidates for this readiness track, not systemic pressure failure and not hidden success.

## Next Action

Director issues Task 170 to `TestAcceptanceEngineer`:

`P1 Rollback Recovery And Error Path Read-Only Evidence Pack`

The task must collect the maximum remaining read-only evidence without upload, restart, rollback, failure injection, cleanup, retry, reparse, re-AI, restore, import, destructive mutation, or readiness/go-live declaration.

## Boundaries

This review does not declare pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

No rollback, fast-forward, deploy, rebuild, restart, failure injection, upload, pressure/batch/soak/fresh serial validation, cleanup/cancel/repair/retry/reparse/re-AI, destructive mutation, service/config/secret/model/sample mutation, automatic retry/requeue, or skeleton fallback weakening was performed.
