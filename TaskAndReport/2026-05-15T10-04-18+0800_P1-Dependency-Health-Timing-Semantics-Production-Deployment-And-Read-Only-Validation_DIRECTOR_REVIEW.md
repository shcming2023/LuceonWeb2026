# Director Review: P1 Dependency Health Timing Semantics Production Deployment And Read-Only Validation

- Review ID: `TASK-20260515-100418-P1-Dependency-Health-Timing-Semantics-Production-Deployment-Director-Review`
- Reviewed task: `TASK-20260515-093631-P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation`
- Task brief: `TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_TASK.md`
- Report: `TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_REPORT.md`
- Reviewer: Director
- Review time: `2026-05-15T10:04:18+0800`

## Decision

`ACCEPTED_SCOPED_DEPLOYMENT_AND_READ_ONLY_VALIDATION_PASS`

Task 166 is accepted within its scoped production deployment and read-only validation boundary.

This review accepts that production now contains the Task 164 dependency-health timing semantics and that `/ops/dependency-health` exposes the new Ollama readiness/timing fields in the running production upload-server.

This review does not declare pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Evidence Reviewed

Director reviewed the DevelopmentEngineer report and independently spot-checked production.

Report evidence:

- Production fast-forwarded from `91c1352` to `1716add`.
- Commit `d3c9952` is an ancestor of the production HEAD.
- Deployment command was limited to `docker compose up -d --build upload-server`.
- Compose rebuilt/recreated `cms-upload-server` and waited on `cms-minio`; no `down`, volume cleanup, prune, upload, repair, retry, reparse, or re-AI occurred.
- Production read-only checks reported `/cms/` and `/cms/tasks` HTTP 200, upload health OK, dependency-health `ok=true` and `blocking=false`, MinerU admission closed, active task idle, and direct MinerU healthy.
- Production dependency-health exposed the new Ollama fields with `readinessState=resident-chat-succeeded`, `readinessSeverity=info`, `probeTimeoutMs=15000`, `recommendedClientTimeoutMs=20000`, `blockingAi=false`, `readinessBlocking=false`, `blockingParse=false`, `warmState=resident-before-chat`, and `failureKind=null`.

Director spot-check evidence:

```text
production git status --short --branch:
## main...origin/main
 M .gitignore
 M docker-compose.override.yml
 M server/db-server.mjs
 M server/tests/worker-smoke.mjs
 M src/app/components/BatchUploadModal.tsx
 M src/app/pages/SourceMaterialsPage.tsx

production git log -1 --oneline:
1716add Dispatch dependency health production validation

git merge-base --is-ancestor d3c9952 HEAD:
exit 0
```

Docker spot-check:

```text
cms-db-server       Up (healthy)
cms-frontend        Up (healthy)
cms-minio           Up (healthy)
cms-upload-server   Up (healthy)
```

Source markers found in production `server/upload-server.mjs`:

- `recommendedDependencyHealthClientTimeoutMs`
- `annotateOllamaReadiness`
- `readinessState`
- `recommendedClientTimeoutMs`
- `coldStartChatSucceeded`

Director read-only runtime spot-check:

```json
{
  "cmsStatus": 200,
  "tasksStatus": 200,
  "uploadHealth": { "ok": true, "service": "upload-server" },
  "dependencyHealth": {
    "ok": true,
    "blocking": false,
    "ollama": {
      "ok": true,
      "blockingParse": false,
      "blockingAi": false,
      "readinessBlocking": false,
      "readinessState": "resident-chat-succeeded",
      "readinessSeverity": "info",
      "probeTimeoutMs": 15000,
      "recommendedClientTimeoutMs": 20000,
      "warmState": "resident-before-chat",
      "failureKind": null,
      "modelResident": true,
      "chatOk": true
    }
  },
  "mineruAdmissionOpen": false,
  "activeTask": null,
  "queuedTasks": 0,
  "directMineru": {
    "status": "healthy",
    "queued_tasks": 0,
    "processing_tasks": 0
  }
}
```

## Boundaries

Accepted within scope only:

- production contains `1716add`, including accepted commit `d3c9952`;
- upload-server deployment/read-only dependency-health validation passed;
- production local-boundary dirty files remain the known Task 163 boundary and were not cleaned or normalized.

Not performed or authorized:

- PDF upload or fresh validation;
- pressure/batch/soak/broader serial validation;
- cleanup, cancel, repair, retry, reparse, or re-AI for existing tasks;
- destructive DB/MinIO/Docker volume/data mutation;
- Docker down, volume cleanup, or prune;
- MinerU/Ollama/supervisor start/stop/restart/kill/attach/mutation;
- settings, secrets, config, model, or sample-library mutation;
- automatic retry/requeue;
- skeleton fallback weakening;
- pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live claim.

## Residual Risk

- The observed production Ollama path was resident success. The cold-before-chat successful path is code/test-covered but was not naturally observed in this production read-only validation because `qwen3.5:9b` was resident.
- Known production-local dirty files remain as recorded by Task 163.
- AI residual disposition remains an owner-level release boundary: known `failed/ai` residuals can be accepted as manual retry candidates only if the user explicitly accepts that product/release boundary.
- Release-grade rollback/recovery and full error-path matrix evidence remain incomplete.

## Next Step

Director records a User decision row for the AI residual release-boundary policy before moving to rollback/error-path evidence. This is an owner decision because it determines whether known `failed/ai` residuals may remain as manual retry candidates for a release-readiness decision, or whether they must be repaired/retried before any release decision.
