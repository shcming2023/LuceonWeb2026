# DevelopmentEngineer Report: P1 Production MinerU Submit-Path 500 Read-Only Diagnosis And Recovery Plan

- Task ID: `TASK-20260515-111251-P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan`
- Based on Director task brief: `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_TASK.md`
- Based on prior evidence:
  - `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_REPORT.md`
  - `TaskAndReport/2026-05-15T11-12-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_DIRECTOR_REVIEW.md`
- Report time: 2026-05-15T11:31:00+0800
- Role: `DevelopmentEngineer`

## Current Live State

Development workspace:

- Branch/status before report edit: `## main...origin/main`
- Development HEAD: `724de0b`
- `origin/main`: `724de0b`
- Task brief and row 171 were present locally after the user-authorized read-only origin check.

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Branch/status: `## main...origin/main`
- Production HEAD: `1716add Dispatch dependency health production validation`
- Production worktree has known local-boundary dirty files: `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`.

Container/process/listener state:

- `docker compose ps` reports `cms-db-server`, `cms-frontend`, `cms-minio`, and `cms-upload-server` as healthy.
- `tmux ls` reports `mineru_api` session present.
- `ps -ef` shows `conda run -n mineru mineru-api --port 8083 --host 0.0.0.0` and child `mineru-api` Python process alive.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` shows the MinerU Python process listening on `*:8083`.
- `lsof -nP -iTCP:8081 -sTCP:LISTEN` shows Docker exposing upload-server through port `8081`.

Admission circuit and dependency health:

- `GET /__proxy/upload/ops/dependency-health` was run without `mineruSubmitProbe=true`.
- Overall dependency health returned `ok=true`, `blocking=false`.
- MinerU `/health` portion returned `ok=true`, `healthOk=true`, `submitProbe.enabled=false`.
- Durable MinerU admission circuit remains `state=open`.
- Admission circuit reason: `mineru-submit-probe-HTTP 500`.
- Circuit opened at `2026-05-15T03:08:28.444Z`.
- Last submit probe:
  - `ok=false`
  - `status=500`
  - `durationMs=196`
  - `taskId=null`
  - `error="HTTP 500: Internal Server Error"`
  - `observedAt="2026-05-15T03:08:28.443Z"`
- Last successful submit: `2026-05-14T21:54:13.400Z`.
- Current counts in circuit: `parsePending=0`, `parseRunning=0`, `aiPending=0`, `aiRunning=0`.
- Close criteria still show `submitProbeOk=false`, `cooldownElapsed=false`, `activeTaskClean=true`, `dependencyBlockingClear=false`.
  - Code inspection shows these close criteria are persisted from the last probe write. Without an authorized successful submit probe, the circuit is not expected to self-close from read-only health alone.

Active task diagnostics:

- `GET /__proxy/upload/ops/mineru/active-task` returned:
  - `activeTask=null`
  - `currentProcessingTask=null`
  - `queuedTasks=[]`
  - `completedButNotIngestedTasks=[]`
  - `driftTasks=[]`
  - `submitRetryableTasks=[]`
  - `takeoverRequiredTasks=[]`
  - `historicalAiFailureTasks` count: `6`
- This provides no evidence of a current stuck MinerU parse queue.

Direct MinerU `/health`:

- `GET http://127.0.0.1:8083/health` returned:
  - `status="healthy"`
  - `version="3.1.0"`
  - `queued_tasks=0`
  - `processing_tasks=0`
  - `completed_tasks=0`
  - `failed_tasks=0`
  - `max_concurrent_requests=1`
  - `processing_window_size=64`

Ollama state, for boundary only:

- Dependency health reports Ollama `ok=true`.
- `readinessState="resident-chat-succeeded"`.
- `modelResident=true`.
- Latest smoke response time observed in this run: `406ms`.
- This is not the current blocker.

## Evidence From Logs

Upload-server logs:

- Read-only `docker compose logs` around the failed submit-probe window did not show a submit-probe stack trace, admission-circuit write trace, or upload-server internal exception.
- A targeted grep for `mineru|submit|dependency|admission|500|health|probe|error|circuit` around the relevant time window produced no matching upload-server lines.
- Therefore the upload-server log stream does not currently explain the HTTP 500.

MinerU host logs:

- Known host logs inspected:
  - `/Users/concm/ops/logs/mineru-api.log`
  - `/Users/concm/ops/logs/mineru-api.err.log`
- `mineru-api.log` contains many older `GET /health HTTP/1.1" 200 OK` lines.
- `mineru-api.err.log` contains older business/progress signals, but no current error signal for the failed submit probe.
- Targeted search for `POST /tasks`, `500`, `Internal`, `ERROR`, `Traceback`, `Exception`, and `/tasks` in those files showed older successful task result reads, but no current `POST /tasks` HTTP 500 line explaining the `2026-05-15T03:08:28Z` failure.

Log-channel ownership endpoint:

- `GET /__proxy/upload/ops/mineru/log-channel-ownership` returned `summaryState="stale"`.
- Selected source was `MINERU_ERR_LOG_PATH:mineru-api.err.log`, state `stale`.
- `mineru-api.err.log` mtime: `2026-05-14T23:47:05.839Z`.
- `mineru-api.log` mtime: `2026-05-15T00:23:48.968Z`.
- Endpoint says sidecar expected but `runningState="not-observed"`.

Interpretation:

- The MinerU process is alive and `/health` is green, but the configured Luceon log channel is stale.
- Current read-only evidence cannot recover the internal Python exception or stack trace for the HTTP 500.
- This is itself an observability issue: production can detect submit-path failure through admission circuit state, but current MinerU logs are not sufficient to diagnose the exact internal cause.

## Code/Config Path Analysis

Dependency-health submit-probe path:

- `server/upload-server.mjs` implements `probeMineruSubmitPath(localEndpoint)`.
- The probe posts a synthetic one-page PDF to `${localEndpoint}/tasks`.
- Probe fields include:
  - `backend=pipeline` by default
  - `lang_list=ch`
  - `parse_method=auto`
  - `formula_enable=0`
  - `table_enable=0`
  - `response_format_zip=false`
  - `end_page_id=0`
  - `endpageid=0`
- On non-2xx response, the upload-server records the response status and body detail as probe error.
- The observed last probe was `HTTP 500: Internal Server Error` in `196ms`, with no `taskId`.

Network/routing path:

- Upload-server container config includes `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`.
- Direct host MinerU `/health` is healthy on `127.0.0.1:8083`.
- Dependency health without submit probe reaches MinerU `/health` through the configured route.
- This makes a pure network/listener/routing failure unlikely. Routing is sufficient for `/health`; the failing surface is specifically submit to `/tasks`.

Admission circuit:

- `server/services/mineru/admission-circuit.mjs` opens the circuit when submit probe returns status `>=500`, timeout, connection refusal, missing task id, or invalid JSON.
- It can close only when a later authorized submit probe succeeds and all close criteria are true:
  - submit probe OK;
  - cooldown elapsed;
  - active task snapshot clean;
  - dependency blocking clear.
- Read-only dependency health does not close the circuit, even if `/health` is green.
- Therefore this is not an `ADMISSION_CIRCUIT_STALE_ONLY` case. The open circuit is a faithful persisted guardrail from the last failed submit probe. It remains open because no authorized successful submit has been observed.

Runtime ownership helper side effect:

- `ops/runtime-ownership-status.sh` is documented and used as a read-only status helper, but currently calls:
  - `curl "$UPLOAD_BASE/ops/dependency-health?mineruSubmitProbe=true"`
- That call is not read-only. It creates a bounded synthetic submit attempt and can mutate admission-circuit state.
- This helper needs a no-submit/read-only mode before it can be safely used in future evidence collection without Director/user authorization.

## Likely Root Cause Classification

Primary classification: `MINERU_SUBMIT_API_BROKEN`.

Confidence: medium.

Rationale:

- MinerU `/health` is healthy and reachable.
- Docker/upload-server route to MinerU is sufficient for `/health`.
- Active-task diagnostics and direct MinerU `/health` show no queued or processing task.
- The last submit probe reached a submit surface and received HTTP 500 quickly (`196ms`), which is consistent with an internal `/tasks` handler failure or runtime state defect rather than network timeout.
- The admission circuit is not merely stale: it is intentionally open from a concrete submit-path failure.

Secondary risk/classification: `SERVICE_OWNERSHIP_OR_CONFIG_MISMATCH`.

- The currently configured MinerU log channel is stale and sidecar is not observed.
- Because no current MinerU log line explains the failed `/tasks` HTTP 500, there may also be a process/log ownership mismatch or log capture defect.
- This secondary issue limits root-cause precision but does not by itself explain the submit-path 500.

Rejected classifications:

- `UPLOAD_SERVER_PROBE_OR_ROUTING_BUG`: unlikely from current evidence. The probe uses `backend=pipeline`, reaches a healthy endpoint, and records a real HTTP 500 from the submit path.
- `ADMISSION_CIRCUIT_STALE_ONLY`: unlikely. Circuit state maps to the last failed submit probe, and code requires a later successful submit probe to close.
- `MINERU_RUNTIME_STALE_OR_RECOVERING`: possible but not supported by current queue/state evidence. Health reports zero queue/processing/failed tasks.
- `INCONCLUSIVE_NEEDS_AUTHORIZED_PROBE_OR_RECOVERY`: not the primary classification, but exact internal stack/root cause remains inconclusive until an authorized probe/recovery operation or current logs become available.

## Recovery Options

1. Keep production blocked and perform no mutation.
   - Status: read-only / already current.
   - Effect: preserves evidence and avoids further side effects.
   - Limitation: non-Markdown parse intake remains blocked by open admission circuit.
   - Proposed commands: none.

2. User-approved single submit-path verification only.
   - Status: requires explicit user approval.
   - Effect: tests whether the submit path has self-recovered and, if successful, can update/close admission state according to code criteria.
   - Risk: posts a synthetic MinerU task and mutates admission-circuit state.
   - Proposed command, not executed:
     ```bash
     curl -sS --max-time 15 "http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true"
     ```

3. User-approved MinerU-only runtime restart/relaunch, followed by health and one authorized submit-path verification.
   - Status: requires explicit user approval.
   - Effect: likely resolves a stale/broken in-memory MinerU submit handler if the issue is operational.
   - Risk: mutates live runtime process state. Must be done only after confirming no active parse/AI work.
   - Proposed commands, not executed:
     ```bash
     curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task
     tmux kill-session -t mineru_api
     cd /Users/concm/prod_workspace/Luceon2026
     bash ops/start-mineru-api.sh
     curl -sS --max-time 10 http://127.0.0.1:8083/health
     curl -sS --max-time 15 "http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true"
     ```

4. DevelopmentEngineer code hardening for observability and helper safety.
   - Status: requires Director task; may not require user approval if confined to repository code/docs and not deployed.
   - Recommended changes:
     - Add `NO_SUBMIT_PROBE` or equivalent to `ops/runtime-ownership-status.sh`.
     - Make the helper default to no submit probe, or clearly split read-only and mutation sections.
     - Add clearer logging around submit-probe failures and admission-circuit writes.
     - Improve log-channel diagnostics or sidecar supervision so current MinerU business/error logs are visible.
   - Effect: prevents future "read-only" checks from opening admission circuit and improves diagnosis.
   - Limitation: does not by itself recover current production submit path unless deployed and paired with operational recovery.

5. Production deploy/rebuild/rollback or DB/MinIO/task repair.
   - Status: forbidden before explicit task/user authorization.
   - Current evidence does not justify this as the first recovery route.
   - Proposed commands: none.

## Recommended Next Actor

Recommended next actor: `Director`.

Recommended Director decision:

- Create a user-decision or scoped runtime-recovery task asking whether to authorize option 3:
  - confirm active task snapshot is clean;
  - perform MinerU-only restart/relaunch;
  - run direct `/health`;
  - run exactly one authorized submit-path verification;
  - do not upload PDFs and do not perform DB/MinIO/Docker volume cleanup.

Recommended follow-up DevelopmentEngineer task:

- Add a no-submit/read-only mode to `ops/runtime-ownership-status.sh` and improve submit-probe/admission/log-channel evidence so future status reports cannot accidentally mutate admission state.

Recommended follow-up TestAcceptanceEngineer task after recovery:

- Re-run read-only dependency health and, if Director/user separately authorizes, one small controlled parse validation. Do not declare production readiness from health alone.

## Files Changed

- Added this report:
  - `TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_REPORT.md`
- Updated task ledger row 171:
  - `TaskAndReport/TASK_TRACKING_LIST.md`

## Commands Run And Exit Codes

Development workspace:

- `git status --short --branch` -> exit 0.
- `git ls-remote origin refs/heads/main` -> exit 0.
- `git fetch origin` -> exit 0. Run only after user explicitly requested read-only sync confirmation because local ledger was suspected stale.
- `git show origin/main:TaskAndReport/TASK_TRACKING_LIST.md | rg "TASK-20260515-093631|\\| 166 \\|"` -> exit 0 in the earlier user-directed stale-ledger check.
- `git show origin/main:TaskAndReport/2026-05-15T09-36-31+0800_P1-Dependency-Health-Timing-Semantics-Production-Deployment-And-Read-Only-Validation_TASK.md` -> exit 0 in the earlier user-directed stale-ledger check.
- `git show origin/main:TaskAndReport/TASK_TRACKING_LIST.md | rg "TASK-20260515-111251|\\| 171 \\|"` -> exit 0.
- `sed -n '1,260p' TaskAndReport/2026-05-15T11-12-51+0800_P1-Production-MinerU-Submit-Path-500-Read-Only-Diagnosis-And-Recovery-Plan_TASK.md` -> exit 0.

Production workspace/read-only runtime:

- `git status --short --branch && git log -1 --oneline && docker compose ps` -> exit 0.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/dependency-health` -> exit 0.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit` -> exit 0.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task` -> exit 0.
- `curl -sS --max-time 10 http://127.0.0.1:8083/health` -> exit 0.
- `ps -ef | rg -i "mineru|uvicorn|fastapi|python"` -> exit 0.
- `tmux ls` -> exit 0.
- `lsof -nP -iTCP:8083 -sTCP:LISTEN` -> exit 0.
- `lsof -nP -iTCP:8081 -sTCP:LISTEN` -> exit 0.
- `docker compose logs --since '2026-05-15T11:00:00+08:00' --until '2026-05-15T11:15:00+08:00' upload-server` -> exit 0.
- `docker compose logs ... | rg -i "mineru|submit|dependency|admission|500|health|probe|error|circuit"` -> no matching relevant submit/circuit lines observed.
- `ls -l /Users/concm/ops/logs` -> exit 0.
- `tail -n 120 /Users/concm/ops/logs/mineru-api.log` -> exit 0.
- `tail -n 120 /Users/concm/ops/logs/mineru-api.err.log` -> exit 0.
- `rg -n "POST /tasks|500|Internal|ERROR|Traceback|Exception|/tasks" /Users/concm/ops/logs/mineru-api.log /Users/concm/ops/logs/mineru-api.err.log` -> exit 0 with older task-result matches but no current submit 500 evidence.
- `tmux capture-pane -pt mineru_api -S -200` -> exit 0, no useful current diagnostic content.
- `rg -n "mineruSubmitProbe|submitProbe|dependency-health|admissionCircuit|mineru-admission|lastSubmitProbe|openAdmission|closeCriteria|runtime-ownership-status" server/upload-server.mjs ops server/lib scripts docs -g '*.mjs' -g '*.sh' -g '*.md'` -> exit 0.
- `sed -n '250,420p' server/upload-server.mjs` -> exit 0.
- `sed -n '430,880p' server/upload-server.mjs` -> exit 0.
- `sed -n '1,280p' server/services/mineru/admission-circuit.mjs` -> exit 0.
- `sed -n '1,100p' ops/runtime-ownership-status.sh` -> exit 0.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/log-channel-ownership` -> exit 0.
- `docker inspect cms-upload-server --format '{{range .Config.Env}}{{println .}}{{end}}' | rg '^(LOCAL_MINERU_ENDPOINT|OLLAMA_API_URL|OLLAMA_TIER2_MODEL|DISABLE_AI_SKELETON_FALLBACK|ALLOW_AI_SKELETON_FALLBACK|MINERU_LOG_PATH|MINERU_ERR_LOG_PATH|MINERU_ADMISSION_CIRCUIT_COOLDOWN_MS)='` -> exit 0.

## Skipped Checks And Reasons

- Did not run `dependency-health?mineruSubmitProbe=true`: explicitly forbidden by Task 171.
- Did not run any direct `POST /tasks`: explicitly forbidden by Task 171.
- Did not upload PDF/Markdown or create validation artifacts: explicitly forbidden by Task 171.
- Did not close/reset the admission circuit: explicitly forbidden by Task 171.
- Did not restart/stop/kill/attach/start MinerU, upload-server, Docker, Ollama, MinIO, DB, supervisor, or sidecar: explicitly forbidden by Task 171.
- Did not deploy/rebuild/rollback/pull production code: explicitly forbidden by Task 171.
- Did not clean, cancel, repair, retry, reparse, re-AI, takeover, requeue, mutate DB/MinIO/Docker volumes/data, restore/import, delete/overwrite objects, prune/down/down-v, or mutate settings/secrets/config/models/samples: explicitly forbidden by Task 171.
- Did not declare pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness: explicitly forbidden and not supported by evidence.

## Evidence

- Admission circuit records a concrete failed submit probe: `HTTP 500: Internal Server Error`, `durationMs=196`, `taskId=null`, observed `2026-05-15T03:08:28.443Z`.
- MinerU `/health` is healthy with zero queued/processing/completed/failed tasks.
- Upload active-task diagnostics show no current active, queued, drift, submit-retryable, completed-but-not-ingested, or takeover-required task.
- Upload-server can reach MinerU `/health` through configured route; routing is therefore not the primary suspect.
- Log-channel ownership endpoint reports stale MinerU log channels, so current MinerU business/error logs do not explain the submit 500.
- Source code confirms the runtime ownership helper currently performs a submit-probe side effect.

## Risks / Blockers / Residual Debt

- Production non-Markdown parse intake remains blocked by the open MinerU admission circuit.
- Exact Python-side stack trace for the submit 500 is unavailable because current MinerU log channels are stale.
- A submit-path recovery probe is required to prove recovery and potentially close the circuit, but that probe mutates runtime/circuit state and needs explicit approval.
- Runtime ownership helper has a design hazard: a tool presented as status/evidence collection can open the circuit by running a submit probe.
- Current evidence supports operational recovery first, then code hardening for helper/logging safety.

## Director Review Needed

Yes.

Director should review this diagnosis and decide whether to request explicit user approval for MinerU-only runtime recovery plus one authorized submit-path verification, and whether to dispatch a separate DevelopmentEngineer code-hardening task for read-only helper semantics and log-channel observability.

## Need For Production Validation Or User Decision

Yes.

- User approval is required before any MinerU restart/relaunch or submit-probe retry.
- After recovery, TestAcceptanceEngineer should validate the restored path under a separately authorized validation boundary.
