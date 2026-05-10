# Lucode Report: P0 Entry Circuit Production Deployment And Non-Destructive Runtime Validation

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T15-42-54+0800_P0-Entry-Circuit-Production-Deployment-And-Non-Destructive-Runtime-Validation_TASK.md`
- Director authorization: `TaskAndReport/2026-05-10T15-31-54+0800_P0-Entry-Circuit-Production-Deployment-Validation-Authorization_DECISION.md`
- Accepted code task: `TASK-20260510-142045-P1-Entry-Circuit-And-Durable-Admission-State`
- Execution role: Lucode
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`

## Result Classification

`PRODUCTION_ENTRY_CIRCUIT_DEPLOYED_NON_DESTRUCTIVE_VALIDATION_PASSED`

The accepted durable MinerU admission-circuit code is deployed to production at GitHub `main` HEAD `cf0466a6ff483745b34376039985eabf291ced3a`. Non-destructive runtime validation confirmed:

- CMS and upload-server reachable;
- MinIO remained healthy with local-only console binding;
- dependency-health with `mineruSubmitProbe=true` returned `blocking=false`;
- MinerU submit probe returned HTTP `202` and task id;
- `/ops/mineru/admission-circuit` returned `state=closed`;
- active parse/AI counts were `0`;
- Ollama `/api/ps` showed `qwen3.5:9b` resident.

This is not a production release-readiness, L3, pressure-test, or manual validation restart claim.

## Development And Production HEAD

- Development `main` HEAD before/after execution: `cf0466a6ff483745b34376039985eabf291ced3a`
- Production HEAD before apply: `098120286dcb95a759be3d960dc498649f622aa9`
- Production deployed HEAD after apply: `cf0466a6ff483745b34376039985eabf291ced3a`
- Production fast-forward range: `0981202..cf0466a`

## Production Apply Summary

Production was fast-forwarded from GitHub `origin/main`, preserving the local `docker-compose.override.yml` modification.

Minimum necessary services rebuilt/recreated:

- `upload-server`
- `db-server`
- `cms-frontend`

Reason: accepted P1 code touched upload-server admission logic, db-server allowed settings keys, and frontend upload/intake UI. MinIO data service was not rebuilt. No DB rows, MinIO objects, Docker volumes, logs, samples, artifacts, secrets, model, timeout, or override values were mutated.

## Production Override Boundary

Production local override remained dirty and preserved as local runtime configuration:

```diff
services:
  upload-server:
    environment:
      - DISABLE_AI_SKELETON_FALLBACK=true
      - OLLAMA_TIER2_MODEL=qwen3.5:9b

  minio:
    ports:
      - "127.0.0.1:19001:9001"
```

Rendered compose evidence included:

```text
ALLOW_AI_SKELETON_FALLBACK: "false"
DISABLE_AI_SKELETON_FALLBACK: "true"
LOCAL_MINERU_ENDPOINT: http://host.docker.internal:8083
OLLAMA_API_URL: http://host.docker.internal:11434
OLLAMA_TIER2_MODEL: qwen3.5:9b
```

MinIO console listener remained local-only:

```text
127.0.0.1:19001->9001/tcp
```

## Commands And Evidence

### Development workspace sync

```bash
git status --short --branch
```

Exit `0`:

```text
## main...origin/main
```

```bash
git fetch origin
git pull --ff-only origin main
```

Exit `0`; result: already up to date.

```bash
git rev-parse HEAD origin/main
git log -1 --oneline
```

Exit `0`:

```text
cf0466a6ff483745b34376039985eabf291ced3a
cf0466a6ff483745b34376039985eabf291ced3a
cf0466a Authorize narrow entry circuit production validation
```

### Production pre-apply status

```bash
git status --short --branch
git rev-parse HEAD
git log -1 --oneline
```

Exit `0`:

```text
## main...origin/main
 M docker-compose.override.yml
098120286dcb95a759be3d960dc498649f622aa9
0981202 Record task 71 ledger head
```

After production `git fetch origin`:

```text
## main...origin/main [behind 10]
 M docker-compose.override.yml
```

### Production fast-forward

```bash
git pull --ff-only origin main
```

Exit `0`; production updated:

```text
Updating 0981202..cf0466a
Fast-forward
```

Post-apply:

```bash
git status --short --branch
git rev-parse HEAD
git log -1 --oneline
```

Exit `0`:

```text
## main...origin/main
 M docker-compose.override.yml
cf0466a6ff483745b34376039985eabf291ced3a
cf0466a Authorize narrow entry circuit production validation
```

### Minimum service apply

```bash
docker compose up -d --build upload-server db-server cms-frontend
```

Exit `0`.

Build output included:

```text
Image luceon2026-upload-server Built
Image luceon2026-db-server Built
Image luceon2026-cms-frontend Built
Container cms-db-server Healthy
Container cms-upload-server Healthy
Container cms-frontend Started
```

Vite emitted the existing chunk-size warning during frontend build:

```text
(!) Some chunks are larger than 500 kB after minification.
```

This warning did not block build or deployment.

### Compose status

```bash
docker compose ps
```

Exit `0`:

```text
cms-db-server       Up ... (healthy)
cms-frontend        Up ... (healthy)   0.0.0.0:8081->80/tcp
cms-minio           Up ... (healthy)   127.0.0.1:19001->9001/tcp
cms-upload-server   Up ... (healthy)
```

### CMS and upload-server reachability

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 http://localhost:8081/__proxy/upload/health
```

Exit `0`:

```json
{"ok":true,"service":"upload-server"}
```

HTTP status: `200`.

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 http://localhost:8081/cms/
```

Exit `0`; HTTP status: `200`; returned the CMS HTML shell.

### DB health

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 http://localhost:8081/__proxy/db/health
```

Exit `0`:

```json
{"ok":true,"service":"db-server","dataPath":"/data/db-data.json","secretsPath":"/data/secrets.json"}
```

HTTP status: `200`.

### Dependency health with submit probe

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Exit `0`; HTTP status `200`.

Key response fields:

```json
{
  "ok": true,
  "blocking": false,
  "dependencies": {
    "minio": { "ok": true },
    "mineru": {
      "ok": true,
      "endpoint": "http://host.docker.internal:8083",
      "healthOk": true,
      "submitProbe": {
        "enabled": true,
        "ok": true,
        "status": 202,
        "durationMs": 91,
        "taskId": "aba8af21-914b-46da-bf21-0ddc46ae8ef5",
        "error": null
      },
      "admissionCircuit": {
        "state": "closed",
        "lastSuccessfulSubmitAt": "2026-05-10T07:47:06.142Z",
        "closeCriteria": {
          "submitProbeOk": true,
          "cooldownElapsed": true,
          "activeTaskClean": true,
          "dependencyBlockingClear": true
        },
        "counts": {
          "parsePending": 0,
          "parseRunning": 0,
          "aiPending": 0,
          "aiRunning": 0
        },
        "persisted": true
      }
    },
    "ollama": {
      "ok": true,
      "model": "qwen3.5:9b",
      "chatOk": true
    }
  }
}
```

### Admission circuit endpoint

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'
```

Exit `0`; HTTP status `200`.

After submit-probe validation:

```json
{
  "ok": true,
  "open": false,
  "message": null,
  "circuit": {
    "version": "mineru-admission-circuit.v0.1",
    "state": "closed",
    "lastSubmitProbe": {
      "enabled": true,
      "ok": true,
      "status": 202,
      "durationMs": 91,
      "taskId": "aba8af21-914b-46da-bf21-0ddc46ae8ef5",
      "error": null
    },
    "lastSuccessfulSubmitAt": "2026-05-10T07:47:06.142Z",
    "closeCriteria": {
      "submitProbeOk": true,
      "cooldownElapsed": true,
      "activeTaskClean": true,
      "dependencyBlockingClear": true
    },
    "counts": {
      "parsePending": 0,
      "parseRunning": 0,
      "aiPending": 0,
      "aiRunning": 0
    },
    "activeTaskClean": true
  }
}
```

### Active-task and queue state

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 'http://localhost:8081/__proxy/upload/ops/mineru/active-task'
```

Exit `0`; HTTP status `200`.

Key response fields:

```json
{
  "activeTask": null,
  "currentProcessingTask": null,
  "queuedTasks": [],
  "completedButNotIngestedTasks": [],
  "driftTasks": [],
  "submitRetryableTasks": [
    { "id": "task-1778394134538", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 },
    { "id": "task-1778394122533", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 },
    { "id": "task-1778394120487", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 },
    { "id": "task-1778393923645", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 },
    { "id": "task-1778393912016", "state": "failed", "stage": "submit-failed-retryable", "retries": 6 }
  ],
  "takeoverRequiredTasks": [],
  "historicalAiFailureTasks": [
    { "id": "task-1778388197543", "state": "failed", "stage": "ai" },
    { "id": "task-1778388196668", "state": "failed", "stage": "ai" }
  ]
}
```

Interpretation: no active or queued work blocked intake-state validation. Historical failed tasks remain present and were not repaired, retried, deleted, or mutated.

### Ollama residency

```bash
curl -sS -w '\nHTTP_STATUS:%{http_code}\n' --max-time 10 'http://localhost:11434/api/ps'
```

Exit `0`; HTTP status `200`.

Key response fields:

```json
{
  "models": [
    {
      "name": "qwen3.5:9b",
      "model": "qwen3.5:9b",
      "parameter_size": "9.7B",
      "quantization_level": "Q4_K_M",
      "context_length": 262144
    }
  ]
}
```

### Repository diff check

```bash
git diff --check
```

Exit `0`.

### Development final status

```bash
git status --short --branch
```

Exit `0` before report commit:

```text
## main...origin/main
```

## Runtime Readiness For Next Decision

The deployed runtime is ready for Lucia and Director to make the next decision about whether to authorize a separate validation upload or pressure-test restart.

The evidence supports only this narrower statement:

`ENTRY_CIRCUIT_DEPLOYED_AND_NON_DESTRUCTIVE_RUNTIME_SURFACES_PASS`

It does not establish production release readiness.

## Explicitly Skipped / Forbidden Items

- No validation upload was created.
- No pressure test was run.
- No failed production task was repaired, retried, closed, deleted, or mutated.
- No DB rows, MinIO objects, Docker volumes, logs, samples, or artifacts were deleted or cleaned.
- No secret, model, timeout, strict AI flag, MinIO console binding, or production override value was changed.
- No broad stack restart, rollback, unrelated recovery, or MinerU/Ollama restart was performed.
- No L3, full-site acceptance, manual pressure-test readiness, or production release-readiness claim is made.

## Risks And Residuals

- Historical failed tasks remain visible in active-task diagnostics as `submitRetryableTasks` and `historicalAiFailureTasks`; this task did not authorize repair or cleanup.
- The admission circuit is now closed and persisted after submit-probe success. Future validation upload or pressure testing still requires separate Lucia/Director authorization.
- Ollama was resident during this validation. Prior cold-load instability remains a separate known operational risk unless Lucia scopes further hardening.

## Review Requirement

Lucia review is required. Director decision is required before any validation upload, pressure-test restart, or production release-readiness promotion.

