# Lucode Completion Report: P0 Adaptive Evidence-Pack Warmup-Gated Production Validation

## 1. Result Classification

Result: `PASS`

This work was based on Lucia task brief:

`TaskAndReport/2026-05-08T18-38-44+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_TASK.md`

The Director-approved warm-up gate succeeded, warm dependency-health passed, exactly one controlled validation upload was created, MinerU completed, and AI metadata reached `review-pending` using adaptive evidence-pack input selection.

No production release-readiness claim is made.

## 2. Scope Executed

Executed:

- Synchronized the development workspace with GitHub.
- Read task 38 and its related Director authorization / Lucia review materials.
- Confirmed production adaptive evidence-pack source markers.
- Confirmed production-local override boundary.
- Confirmed CMS, DB, service, sample, active task, and active AI job preconditions.
- Performed exactly one bounded non-mutating direct Ollama warm-up using `qwen3.5:9b`.
- Ran warm dependency-health with `mineruSubmitProbe=true`.
- Created exactly one controlled upload from the authorized sample PDF.
- Polled only the created validation task and related AI job until terminal state.
- Collected task, material, AI job, and task-event evidence.

Not executed:

- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- No Ollama restart/start/stop/kill/reload.
- No model, timeout, config, secret, or override change.
- No DB row, MinIO object, Docker volume, task, artifact, or log deletion.
- No skeleton fallback or silent degradation.

## 3. Branch And HEAD

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Status before report: `main...origin/main`
- HEAD before report: `a3fe7c80e3a0d36f6c700e9097bc83a2be350d2a`

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Status before validation: `main...origin/main [behind 4]`, with local `docker-compose.override.yml` modification preserved.
- Production HEAD: `8092965`
- Production `origin/main` before fetch: `8ebd8c8`
- Production `origin/main` after fetch: `a3fe7c8`
- No production fast-forward, deploy, rebuild, restart, rollback, or Docker mutation was performed.

## 4. Production Code And Override Evidence

Production code markers present:

- `shouldUseEvidencePack`
- `evidence-pack-v0.3`

Production override boundary present:

- `DISABLE_AI_SKELETON_FALLBACK=true`
- `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- MinIO console mapping `127.0.0.1:19001:9001`

## 5. Pre-Warm Preconditions

`docker compose ps` in production:

- `cms-db-server`: healthy.
- `cms-frontend`: healthy, `0.0.0.0:8081->80/tcp`.
- `cms-minio`: healthy, `127.0.0.1:19001->9001/tcp`.
- `cms-upload-server`: healthy.

CMS and DB:

- CMS reachability: `CMS_OK`.
- DB health: `{"ok":true,"service":"db-server","dataPath":"/data/db-data.json","secretsPath":"/data/secrets.json"}`.

Active work before upload:

- Tasks total: `44`
- Active parse/task states: `0`
- AI metadata jobs total: `38`
- Active AI jobs: `0`

Sample check:

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- Size: `15157403`
- SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`

## 6. Warm-Up And Warm Dependency Health

Bounded non-mutating Ollama warm-up:

- Command: direct local `/api/chat` to `http://127.0.0.1:11434/api/chat`
- Model: `qwen3.5:9b`
- `num_predict=1`
- Exit: `0`
- Result:
  - `done=true`
  - `done_reason=length`
  - `total_duration=29663343542ns`
  - `load_duration=29185837417ns`
  - `prompt_eval_count=11`
  - `eval_count=1`

Interpretation:

- Warm-up succeeded without mutation.
- Cold load was still long: total about `29.66s`, load about `29.19s`.

Warm dependency-health immediately after warm-up:

- Command: `curl -sS --max-time 25 "http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true"`
- Exit: `0`
- Result:
  - `ok=true`
  - `blocking=false`
  - `minio.ok=true`
  - `mineru.ok=true`
  - `mineru.healthOk=true`
  - `mineru.submitProbe.enabled=true`
  - `mineru.submitProbe.ok=true`
  - `mineru.submitProbe.status=202`
  - `mineru.submitProbe.durationMs=33`
  - `mineru.submitProbe.taskId=d7422baa-2f9c-4c48-ae78-4b39bfd0a90e`
  - `ollama.ok=true`
  - `ollama.chatOk=true`
  - `ollama.model=qwen3.5:9b`
  - `ollama.durationMs=1015`

Warm dependency-health passed, so the controlled upload was allowed.

## 7. Controlled Upload Evidence

Controlled upload:

- Command: multipart upload to `http://localhost:8081/__proxy/upload/tasks`
- Exit: `0`
- HTTP code: `200`
- Created task ID: `task-1778237744029`
- Created material ID: `mat-1778237743496`
- Original object: `originals/mat-1778237743496/source.pdf`
- Provider: `minio`
- File name: `G7_Workbook_ready_to_print.pdf`
- Signed MinIO URL returned by the API is intentionally not reproduced in this report.

## 8. Task Terminal Evidence

Created validation task:

- `taskId=task-1778237744029`
- `state=review-pending`
- `stage=review`
- `message=AI 识别完成: review-pending (待人工复核)`
- `materialId=mat-1778237743496`
- `aiJobId=ai-job-1778237936591-e515`
- `mineruTaskId=fd91393d-d200-4a00-860a-525f13f4a7c6`
- `mineruStatus=completed`
- `mineruSubmittedAt=2026-05-08T10:55:51.698Z`
- `mineruStartedAt=2026-05-08T10:55:51.698677+00:00`
- `mineruLastStatusAt=2026-05-08T10:58:53.536Z`
- `parsedAt=2026-05-08T10:58:56.586Z`
- `aiCompletedAt=2026-05-08T11:03:05.458Z`
- `parsedFilesCount=99`
- `markdownObjectName=parsed/mat-1778237743496/full.md`
- `parsedPrefix=parsed/mat-1778237743496/`
- `artifactManifestObjectName=parsed/mat-1778237743496/artifact-manifest.json`
- `zipObjectName=parsed/mat-1778237743496/mineru-result.zip`
- `artifactStorageMode=zip-source`
- `artifactExportModes=["user","mineru-raw","diagnostic"]`
- `artifactIncomplete=false`

Poll timeline:

- `18:55:52`: task running, `mineru-processing`, MinerU task `fd91393d-d200-4a00-860a-525f13f4a7c6`.
- `18:59:03`: `ai-pending`, MinerU complete, `parsedFilesCount=99`.
- `18:59:13`: `ai-running`, Ollama `qwen3.5:9b`.
- `19:01:14`: `ai-running`, JSON Repair.
- `19:03:05`: terminal `review-pending`.

MinerU log observation:

- Last observed phase: `Processing pages`
- Percent: `100`
- Current/total: `90/90`
- Attribution mode: `completed-window-backfill`
- Log source: `/Users/concm/ops/logs/mineru-api.err.log`
- `observationStale=true`

The stale observation is residual observability debt, not a parse failure.

## 9. Material And Adaptive Input Evidence

Material:

- `id=mat-1778237743496`
- `fileName=G7_Workbook_ready_to_print.pdf`
- `fileSize=15157403`
- `status=reviewing`
- `metadata.objectName=originals/mat-1778237743496/source.pdf`
- `metadata.parsedPrefix=parsed/mat-1778237743496/`
- `metadata.aiClassificationProvider=ollama`
- `metadata.aiClassificationModel=qwen3.5:9b`
- `metadata.aiClassificationSamplingMode=evidence-pack-v0.3`
- `metadata.aiClassificationInputOriginalLength=104823`
- `metadata.aiClassificationInputSampledLength=16261`
- `metadata.aiClassificationInputHash=sha256:021a3d990b63704c2474cbfde855ab2d515fb958dca17939907eb2ad67ae901f`
- `metadata.aiClassificationInputSelectionReasons=["markdown-length","source-file-size","parsed-files-count"]`

Selection thresholds:

- `markdownLength=50000`
- `fileSize=10000000`
- `parsedFilesCount=50`

Raw trace observed inputs:

- `markdownLength=104823`
- `fileSize=15157403`
- `parsedFilesCount=99`

Raw trace selected sections were present for `sourceFacts`, `filenameSignals`, `documentShape`, `frontMatter`, `toc`, `headingOutline`, `representativeBody`, `tailSignals`, and `evidenceCandidates`.

## 10. AI Job Evidence

AI job:

- `id=ai-job-1778237936591-e515`
- `materialId=mat-1778237743496`
- `state=review-pending`
- `model=qwen3.5:9b`
- `message=AI 识别完成 (240690ms)`
- `result.aiClassificationProvider=ollama`
- `result.aiClassificationModel=qwen3.5:9b`
- `result.aiClassificationSamplingMode=evidence-pack-v0.3`
- `result.aiClassificationInputOriginalLength=104823`
- `result.aiClassificationInputSampledLength=16261`
- `result.aiClassificationInputHash=sha256:021a3d990b63704c2474cbfde855ab2d515fb958dca17939907eb2ad67ae901f`
- `result.aiClassificationInputSelectionReasons=["markdown-length","source-file-size","parsed-files-count"]`
- `aiClassificationTwoPassAttempted=true`
- `aiClassificationRepairSucceeded=true`
- `updatedAt=2026-05-08T11:03:05.453Z`
- `completedAt=2026-05-08T11:03:05.453Z`

First pass:

- `objectName=ai-raw/mat-1778237743496/ai-job-1778237936591-e515/first-pass.txt`
- `contentHash=256265f6de0ccc1e7e4897dfc2d9540287e18aa7ea7c9c5ebb8ba0c06d2121e7`
- `contentLength=1471`
- `containsThinkTag=false`
- `looksTruncated=true`
- `parseErrorMessage=Expected ',' or '}' after property value in JSON at position 678`
- `durationMs=121366`
- `promptLength=5343`
- `inputLength=16261`
- `numPredict=512`
- `phase=first-pass`
- `failureKind=json_parse_failed`
- `schemaInvalid=false`
- `jsonParseFailed=true`

Repair pass:

- `objectName=ai-raw/mat-1778237743496/ai-job-1778237936591-e515/repair-pass.txt`
- `contentHash=17aa9c355b3fb9218f47f33a325a520cc327802515d85fddf704ee2e0e787ed2`
- `contentLength=2362`
- `containsThinkTag=false`
- `looksTruncated=false`
- `durationMs=119256`
- `promptLength=8781`
- `inputLength=353`
- `numPredict=3072`
- `phase=repair-pass`

AI metadata result:

- `title=G7 ENGLISH`
- `subject=英语`
- `grade=G7`
- `materialType=练习册`
- `language=English`
- `summary=英语 · G7 · 练习册`
- `confidence=90`
- `needsReview=true`

The first pass selected adaptive evidence-pack input under `30000` characters. JSON repair was still required and succeeded. No skeleton fallback was generated or represented as real AI recognition.

## 11. Task Event Evidence

Task event query:

- Correct endpoint: `/__proxy/db/task-events?taskId=task-1778237744029`
- Exit: `0`
- Total events: `102`
- Relevant filtered events: `97`

Key events:

- `worker-completed` at `2026-05-08T10:58:56.587Z`: MinerU complete, `state=ai-pending`, `parsedFilesCount=99`, parsed artifact fields present.
- `ai-job-created`: `ai-job-1778237936591-e515`.
- `ai-content-truncated` at `2026-05-08T10:59:04.777Z`:
  - `samplingMode=evidence-pack-v0.3`
  - `originalLength=104823`
  - `selectedLength=16261`
  - `triggerReasons=["markdown-length","source-file-size","parsed-files-count"]`
  - `inputHash=sha256:021a3d990b63704c2474cbfde855ab2d515fb958dca17939907eb2ad67ae901f`
  - thresholds `{markdownLength:50000,fileSize:10000000,parsedFilesCount:50}`
  - observed `{markdownLength:104823,fileSize:15157403,parsedFilesCount:99}`
- `ai-provider-request-started` at `2026-05-08T10:59:04.779Z`:
  - provider `ollama`
  - model `qwen3.5:9b`
  - timeoutMs `300000`
  - inputLength `16261`
- `ai-provider-request-succeeded` at `2026-05-08T11:01:06.171Z`:
  - durationMs `121366`
  - completion tokens `512`
- `ai-provider-repair-succeeded` at `2026-05-08T11:03:05.450Z`.
- `ai-provider-success` at `2026-05-08T11:03:05.455Z`:
  - state `review-pending`
  - progress `100`
  - message `AI 识别完成 (240690ms)`

Note: one read-only attempt against `/__proxy/db/taskEvents?taskId=...` returned `404`; this was corrected to `/__proxy/db/task-events?taskId=...`.

## 12. Commands Run

| Workspace | Command | Exit | Notes |
| --- | --- | ---: | --- |
| dev | `git status --short --branch` | 0 | `main...origin/main` |
| dev | `git fetch origin` | 0 | succeeded |
| dev | `git pull --ff-only origin main` | 0 | already up to date |
| dev | `sed -n ... TASK_TRACKING_LIST.md` | 0 | task 38 assigned to Lucode |
| dev | `sed -n ... TASK.md` | 0 | task brief read |
| prod | `git status --short --branch` | 0 | `main...origin/main [behind 4]`, local override preserved |
| prod | `git fetch origin` | 0 | updated `origin/main` to `a3fe7c8` |
| prod | `git rev-parse HEAD` / `git rev-parse origin/main` | 0 | production HEAD `8092965`, origin `a3fe7c8` |
| prod | source marker inspection with `rg` | 0 | adaptive markers present |
| prod | override boundary inspection with `rg` | 0 | strict AI/model and local-only MinIO console present |
| prod | `docker compose ps` | 0 | read-only service state; services healthy |
| prod | `curl -fsS http://localhost:8081/cms/ >/dev/null && echo CMS_OK` | 0 | CMS reachable |
| prod | `curl -fsS http://localhost:8081/__proxy/db/health` | 0 | DB healthy |
| prod | active task query via `/__proxy/db/tasks` | 0 | active tasks `0` |
| prod | active AI job query via `/__proxy/db/ai-metadata-jobs` | 0 | active AI jobs `0` |
| prod | `stat -f 'size=%z path=%N' ...G7_Workbook_ready_to_print.pdf` | 0 | sample size matched |
| prod | `shasum -a 256 ...G7_Workbook_ready_to_print.pdf` | 0 | sample hash matched |
| prod | bounded direct Ollama warm-up | 0 | succeeded; cold load about `29.19s` |
| prod | dependency-health with `mineruSubmitProbe=true` | 0 | passed; Ollama duration `1015ms` |
| prod | controlled upload to `/__proxy/upload/tasks` | 0 | HTTP `200`; task `task-1778237744029` |
| prod | bounded task poll loop | 0 | terminal `review-pending` |
| prod | task record query | 0 | terminal evidence collected |
| prod | material record query | 0 | adaptive metadata fields collected |
| prod | AI job record query | 0 | repair success and result collected |
| prod | `/__proxy/db/taskEvents?taskId=...` | 22 | read-only wrong endpoint returned `404`; corrected |
| prod | `/__proxy/db/task-events?taskId=...` | 0 | event evidence collected |

## 13. Skipped Checks And Reasons

No required task-38 checks were skipped.

Runtime checks intentionally not run because they were outside task scope or forbidden:

- No production deploy/rebuild/restart/rollback.
- No Docker mutation.
- No Ollama restart/start/stop/kill/reload.
- No model/timeout/config/secret/override change.
- No cleanup of generated validation task/material/artifacts/logs.

## 14. Pass Criteria Review

Pass criteria met:

- Production code includes adaptive evidence-pack implementation.
- Production override remains within accepted local boundary.
- Bounded warm-up succeeded without mutation.
- Warm dependency-health passed immediately before upload.
- MinerU completed and parsed artifacts were preserved.
- AI first-pass input used `evidence-pack-v0.3`.
- Selected input was `16261`, below `30000`.
- Trigger reasons, thresholds, and observed values were present.
- No skeleton fallback was generated or represented as real AI recognition.
- No forbidden operation occurred.

AI metadata completion was achieved as `review-pending`, with deterministic repair success after first-pass JSON parse failure.

## 15. Risks And Residual Technical Debt

Residual risks:

- Ollama cold load remains slow: this run's warm-up spent about `29.19s` in load time. Without an authorized warm-up gate, dependency-health can still timeout under cold-load/model-residency instability.
- First-pass output was still truncated / JSON-parse-invalid at `numPredict=512`; repair succeeded, but final AI metadata depended on the repair pass.
- MinerU observation for this completed task was attributed through completed-window backfill and marked stale. Parse succeeded, but live log freshness remains an observability limitation.
- Production workspace remained at `8092965` while `origin/main` advanced to `a3fe7c8`; task 38 forbade production fast-forward/deploy/rebuild/restart, so this was preserved intentionally.

Recommended Lucia follow-up:

- Treat adaptive evidence-pack production validation as passed for this controlled sample.
- Keep release-readiness judgment separate.
- Consider a future Lucia/Director decision on Ollama warm-up/readiness strategy before any broader release-candidate validation wave.

## 16. Guardrail Confirmation

Confirmed:

- No production release-readiness claim occurred.
- Exactly one controlled validation upload was created.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation was run.
- No Ollama restart/start/stop/kill/reload was run.
- No model, timeout, config, secret, or override value was changed.
- No DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs were deleted.
- No skeleton fallback or silent degradation was added.

Lucia review is required.
