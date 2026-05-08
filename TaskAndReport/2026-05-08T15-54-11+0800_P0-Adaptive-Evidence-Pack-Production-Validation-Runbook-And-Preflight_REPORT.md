# Lucode Completion Report: P0 Adaptive Evidence-Pack Production Validation Runbook And Preflight

## 1. Task Brief

- Based on Lucia task brief: `TaskAndReport/2026-05-08T15-41-15+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight_TASK.md`
- Assignee: Lucode
- Report time: 2026-05-08T15:54:11+0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path inspected read-only: `/Users/concm/prod_workspace/Luceon2026`
- Scope performed: non-destructive runbook and read-only preflight only.

## 2. Current Heads

Development workspace:

- Branch/status: `main...origin/main`
- HEAD: `c882e2b docs: assign validation preflight runbook`
- `origin/main`: `c882e2b`

Production workspace:

- Branch/status after read-only fetch: `main...origin/main [behind 45]`
- Dirty file: `docker-compose.override.yml`
- Production HEAD: `4cc6d3e docs: accept observation semantics and assign deployment validation`
- Production `origin/main`: `c882e2b`

Preflight conclusion:

- The accepted adaptive evidence-pack code is not active in the production workspace yet.
- Read-only source inspection in production still shows the old evidence-pack trigger: `originalLength > 150000 || parsedFilesCount > 1000`.
- Development `main` contains the accepted adaptive selection helper and metadata fields.

## 3. Production Override Boundary Confirmation

Read-only inspection of `/Users/concm/prod_workspace/Luceon2026/docker-compose.override.yml` confirmed:

- `DISABLE_AI_SKELETON_FALLBACK=true`
- `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- MinIO console mapping: `127.0.0.1:19001:9001`

This matches the accepted production-local boundary:

- strict AI no-skeleton semantics are preserved;
- model remains `qwen3.5:9b`;
- MinIO console is local-only on `127.0.0.1:19001`.

No secret values are reproduced in this report.

## 4. Read-Only Runtime Preflight Facts

Read-only health checks against the already-running local production URL:

- DB health: `ok=true`, `service=db-server`.
- Dependency health without MinerU submit probe:
  - `ok=false`
  - `blocking=false`
  - `minio=true`
  - `mineru=true`
  - `mineru.submitProbe.enabled=false`
  - `ollama=false`
  - `ollama.blockingParse=false`

Read-only active-work inspection:

- Tasks total: `44`
- Active parse/task states: `0`
- AI metadata jobs total: `38`
- Active AI jobs: `0`

Important boundary:

- Ollama is currently reported not ready by cheap dependency-health. This task does not authorize starting, restarting, or repairing Ollama.
- Later production validation should not begin until authorized and until the validation preflight confirms Ollama `qwen3.5:9b` is ready.

## 5. Large-PDF Sample Boundary

Preferred large-PDF validation sample already recorded by task 29:

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- Size: `15157403` bytes
- SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
- Prior task ID: `task-1778222027064`
- Prior material ID: `mat-lucode-large-soak-20260508143346`

Read-only file check in this task confirmed the same size and SHA-256.

## 6. Production Validation Runbook After Director Authorization

This runbook is not authorized for execution by this task. It is the proposed sequence after Director approves task 32 or an equivalent Lucia task brief.

### 6.1 Pre-Apply Stop Conditions

Before touching production runtime:

1. Confirm a Director-approved Lucia task exists.
2. Confirm no active parse task states:
   - `pending`
   - `running`
   - `result-store`
   - `ai-pending`
   - `ai-running`
   - `queued`
   - `processing`
3. Confirm no active AI metadata jobs:
   - `pending`
   - `running`
4. Confirm `docker-compose.override.yml` contains only accepted local runtime boundary changes.
5. Confirm Ollama `qwen3.5:9b`, MinerU, MinIO, CMS, upload-server, and DB are ready.
6. If any condition fails, stop and write a blocked report.

### 6.2 Apply Accepted Code

After authorization, use the minimum required production apply path:

```bash
cd /Users/concm/prod_workspace/Luceon2026
git status --short --branch
git fetch origin
git log -1 --oneline
git rev-parse --short HEAD
git rev-parse --short refs/remotes/origin/main
```

If the only local modification is the accepted production-local `docker-compose.override.yml`, preserve it explicitly before fast-forwarding. Recommended controlled sequence:

```bash
git diff -- docker-compose.override.yml
git stash push -m preserve-production-local-override -- docker-compose.override.yml
git merge --ff-only origin/main
git stash pop
git status --short --branch
rg -n "DISABLE_AI_SKELETON_FALLBACK|OLLAMA_TIER2_MODEL|19001|127\\.0\\.0\\.1" docker-compose.override.yml
```

If `git stash pop` conflicts or the override no longer matches the accepted boundary, stop and write a blocked report. Do not improvise override edits.

Then rebuild/recreate only the service needed to apply the accepted worker code, unless the eventual Lucia task says otherwise:

```bash
docker compose up -d --build upload-server
docker compose ps
```

Do not run `docker compose down`, `docker compose down -v`, `docker compose restart`, `docker compose pull`, `docker compose rm`, `docker compose prune`, or volume-affecting commands unless a later Director-approved task explicitly requires them.

### 6.3 Pre-Upload Validation Checks

Run non-destructive checks after apply:

```bash
curl -fsS http://localhost:8081/cms/ >/dev/null
curl -fsS "http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true"
curl -fsS http://localhost:8081/__proxy/db/health
```

Expected dependency-health readiness before large-PDF upload:

- `blocking=false`
- `minio.ok=true`
- `mineru.healthOk=true`
- `mineru.submitProbe.enabled=true`
- `mineru.submitProbe.ok=true`
- `ollama.ok=true`

If Ollama is still not ready, do not create a new validation upload. Record blocked or inconclusive status.

### 6.4 Controlled Large-PDF Validation

Use the previously approved sample:

```bash
stat -f 'size=%z path=%N' /Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf
shasum -a 256 /Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf
```

Expected:

- size `15157403`
- SHA-256 `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`

Then create one controlled validation upload only if authorized:

```bash
curl -sS -w '\nHTTP_CODE=%{http_code}\n' \
  -F "file=@/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf" \
  http://localhost:8081/__proxy/upload/tasks
```

Record:

- upload start ISO timestamp;
- HTTP status;
- task ID;
- material ID;
- raw object name;
- provider;
- file size and hash.

Poll only the created task and its AI job until terminal state or timeout.

## 7. Evidence Fields To Collect

For the new validation task, collect these fields from DB task, material, AI job, and task event records:

- `task.id`
- `task.state`
- `task.stage`
- `task.message`
- `task.materialId`
- `task.metadata.parsedFilesCount`
- `task.metadata.markdownObjectName`
- `task.metadata.artifactManifestObjectName`
- `material.id`
- `material.fileName`
- `material.fileSize`
- `material.metadata.objectName`
- `material.metadata.parsedPrefix`
- AI job ID and terminal `state`
- AI job `message` and `errorMessage`
- AI metadata result fields:
  - `aiClassificationSamplingMode`
  - `aiClassificationInputOriginalLength`
  - `aiClassificationInputSampledLength`
  - `aiClassificationInputHash`
  - `aiClassificationInputSelectionReasons`
  - `aiClassificationInputSelectionThresholds`
  - `aiClassificationRawTrace.input.observed`
  - `aiClassificationProvider`
  - `aiClassificationModel`
  - `aiClassificationDegraded`
  - `aiClassificationErrorSource`

Expected adaptive evidence-pack signal for a task-29-like large PDF:

- `aiClassificationSamplingMode=evidence-pack-v0.3`
- `aiClassificationInputOriginalLength` around the parsed Markdown size, previously about `104823`
- `aiClassificationInputSampledLength < 30000`
- `aiClassificationInputSelectionReasons` includes:
  - `markdown-length`
  - `source-file-size`
  - `parsed-files-count`
- `aiClassificationInputSelectionThresholds.markdownLength=50000`
- `aiClassificationInputSelectionThresholds.fileSize=10000000`
- `aiClassificationInputSelectionThresholds.parsedFilesCount=50`
- `aiClassificationRawTrace.input.observed.fileSize=15157403`
- `aiClassificationRawTrace.input.observed.parsedFilesCount=99` or the actual parsed count from the new run.

Also collect task events:

- `ai-content-truncated`
- `ai-provider-request-started`
- `ai-provider-request-succeeded` or `ai-provider-request-failed`
- any `ai-provider-repair-*` event
- final task state transition event

## 8. Pass / Fail / Inconclusive Criteria

Pass:

- Production workspace is on the accepted adaptive evidence-pack code.
- Production override still preserves strict AI/model and local-only MinIO console boundary.
- Large PDF creates exactly one controlled validation task.
- MinerU completes and parsed artifacts are preserved.
- AI first-pass input uses `evidence-pack-v0.3`.
- Selected input is below `30000` chars before prompt wrapping.
- Selection reasons and thresholds are present.
- AI metadata completes without skeleton, or if it fails, failure is explicit and preserves parse artifacts.
- No forbidden operation occurs.

Fail:

- Large PDF still uses `legacy-sampler-v0.2` or old roughly `83k` first-pass payload.
- Adaptive selection metadata is missing.
- Skeleton fallback is generated or represented as real AI recognition.
- Model/timeout/strict settings are changed without authorization.
- DB rows, MinIO objects, Docker volumes, tasks, artifacts, secrets, or override files are mutated outside the authorized validation action.
- Production release readiness is claimed from this validation alone.

Inconclusive:

- Production code cannot be applied cleanly while preserving the accepted local override.
- Ollama remains unavailable before upload.
- MinerU or MinIO is unavailable before upload.
- The upload cannot be created.
- Polling cannot conclusively find the AI job/result fields.
- Browser/API/network access fails before evidence collection.

## 9. Rollback And Forbidden Boundaries

This task does not authorize rollback.

If a later authorized apply fails:

- Prefer stopping the validation and writing a blocked report.
- Do not delete DB rows or MinIO objects.
- Do not run volume cleanup.
- Do not run broad rollback unless explicitly authorized.
- Do not change model, timeout, fallback, or strict AI settings as a workaround.

Always forbidden without separate Director approval:

- production release-readiness declaration;
- DB row deletion or mutation outside the controlled upload;
- MinIO object deletion;
- Docker volume deletion or pruning;
- secret changes;
- model or timeout policy changes;
- skeleton fallback or silent degradation;
- broad deploy or rollback outside the scoped validation;
- external or multi-user release boundary acceptance.

## 10. Commands Run

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` in dev | 0 | Clean, `main...origin/main`. |
| `git fetch origin` in dev | 0 | Succeeded. |
| `git pull --ff-only origin main` in dev | 128 | Returned `fatal: Cannot fast-forward to multiple branches.` After fetch, `HEAD` and `origin/main` were both `c882e2b`; no local sync mutation was needed. |
| `git rev-parse --short HEAD` in dev | 0 | `c882e2b`. |
| `git rev-parse --short refs/remotes/origin/main` in dev | 0 | `c882e2b`. |
| `sed` / `rg` required reading commands | 0 | Read task brief, role docs, state docs, PRD references, deploy docs, review/decision docs, and task list. |
| `git status --short --branch` in production | 0 | `main...origin/main [behind 45]`, local `docker-compose.override.yml` modified. |
| `git fetch origin` in production | 0 | Read-only remote sync; production `origin/main` advanced to `c882e2b`. |
| `git log -1 --oneline` in production | 0 | Production HEAD `4cc6d3e`. |
| `rg` production override boundary | 0 | Confirmed strict AI/model and MinIO local-only mapping lines. |
| `rg` production adaptive code markers | 0 | Confirmed production code still uses old `150000` / `1000` trigger. |
| `stat` and `shasum -a 256` on large sample | 0 | Size/hash matched accepted evidence. |
| `curl http://localhost:8081/__proxy/db/health` | 0 | DB `ok=true`. |
| `curl http://localhost:8081/__proxy/upload/ops/dependency-health` | 0 | Non-blocking, MinIO/MinerU true, Ollama false, submit probe disabled. |
| `curl http://localhost:8081/__proxy/db/tasks` active-state summary | 0 | Total `44`, active task count `0`. |
| `curl http://localhost:8081/__proxy/db/ai-metadata-jobs` active-state summary | 0 | Total `38`, active AI job count `0`. |
| `docker compose config --services` in production | 0 | Rendered service names only; no service mutation. |

## 11. Confirmation Of Non-Mutation

Confirmed not performed:

- no production deploy;
- no production restart/rebuild/recreate/rollback;
- no `docker compose up`, `down`, `restart`, `rm`, `pull`, `build`, `prune`, or volume operation;
- no new upload or validation task;
- no DB row mutation;
- no MinIO object mutation;
- no Docker volume mutation;
- no task/artifact/log/secret mutation;
- no model, timeout, fallback, or strict AI setting change;
- no production release-readiness claim.

## 12. Review Requirement

Lucia review is required. Director task 32 remains the authority for whether actual production validation may proceed.

