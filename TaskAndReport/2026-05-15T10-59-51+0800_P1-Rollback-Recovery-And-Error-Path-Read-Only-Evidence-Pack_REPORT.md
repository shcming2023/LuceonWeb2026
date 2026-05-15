# TestAcceptanceEngineer Report: P1 Rollback Recovery And Error Path Read-Only Evidence Pack

- Task ID: `TASK-20260515-105951-P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack`
- Based on Director task brief: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Read-Only-Evidence-Pack_TASK.md`
- Based on Architect report: `TaskAndReport/2026-05-15T10-10-39+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T10-59-51+0800_P1-Rollback-Recovery-And-Error-Path-Evidence-Gap-Plan_DIRECTOR_REVIEW.md`
- Role: `TestAcceptanceEngineer`

## Required Reading Completed

Read or re-read the required documents: `AGENTS.md`, `docs/codex/TEAM_CONTRACT.md`, `docs/codex/roles/test-acceptance-engineer.md`, `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, `docs/prd/Luceon2026-PRD-v0.4.md`, `docs/codex/TEST_POLICY.md`, `docs/codex/REPOSITORY_STRUCTURE.md`, `TaskAndReport/README.md`, `TaskAndReport/TASK_TRACKING_LIST.md`, Task 168 report and Director review, and this Task 170 brief.

## Scope And Important Finding

This task collected read-only rollback/recovery and error-path evidence. No rollback, deploy, rebuild, restart, stop, kill, attach, failure injection, upload, cleanup, retry, reparse, re-AI, restore/import, DB/MinIO/Docker volume/data mutation, service/config/secret/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim was performed.

Important finding: `bash ops/runtime-ownership-status.sh` is documented as a read-only helper, but it internally calls dependency-health with `mineruSubmitProbe=true`. During this evidence pass that submit probe returned HTTP `500`, and the MinerU admission circuit opened. I did not attempt to close, repair, restart, or rerun any mutating recovery. The opened circuit is reported as production evidence and a release-boundary blocker.

## Runtime Snapshot

| Check | Exit | Evidence |
| --- | ---: | --- |
| Development `git status --short --branch` and HEAD | 0 | `main...origin/main`, HEAD `36be611 Normalize task ledger file mode`. |
| Production `git status --short --branch` and HEAD | 0 | `main...origin/main`, HEAD `1716add Dispatch dependency health production validation`; known local-boundary dirty files remain. |
| Production dirty files | 0 | `.gitignore`, `docker-compose.override.yml`, `server/db-server.mjs`, `server/tests/worker-smoke.mjs`, `src/app/components/BatchUploadModal.tsx`, `src/app/pages/SourceMaterialsPage.tsx`. |
| `docker compose ps` | 0 | `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server` healthy. |
| Listeners | 0 | `8081` via Docker, `8083` host MinerU, `11434` Ollama, `19001` MinIO console local-only. |
| Upload health | 0 | `{"ok":true,"service":"upload-server"}`. |
| Dependency-health without submit probe | 0 | `ok=true`, `blocking=false`; MinIO OK, MinerU `/health` OK, Ollama resident/chat OK. Admission circuit was already `open` after the submit-probe finding. |
| Dependency-health with submit probe via runtime helper | 0 command / endpoint HTTP 200 | Response body `ok=false`, `blocking=true`; MinerU submit probe `status=500`, `error=HTTP 500: Internal Server Error`; admission circuit opened. |
| Admission circuit after submit probe | 0 | `open=true`, message `MinerU 当前不可接收新任务，文件未收取，请稍后重试。`, last submit probe failed at `2026-05-15T03:08:28.443Z`. |
| Active-task diagnostics | 0 | `activeTask=null`, no queued/current/drift/takeover work; historical AI failure tasks count `6`. |
| Direct MinerU `/health` | 0 | `healthy`, queued `0`, processing `0`, failed `0`. |
| `/cms/` and `/cms/tasks` | 0 | Both HTTP `200`. |
| Runtime ownership helper | 0 | `mineru_api` tmux present, expected `luceon-mineru` absent; `luceon-sidecar` and `luceon-supervisor` absent; upload-server env truth has strict AI/model endpoint values. |

## Rollback / Recovery Evidence Pack

| Area | Evidence | Classification | Risk |
| --- | --- | --- | --- |
| Source rollback | Git HEADs and prior deployment reports show fast-forward deploys; `DEPLOY.md` documents deployment primitives. No reverse rollback rehearsal found. | `requires user-approved rehearsal` | Source rollback remains procedural, not release-rehearsed. |
| Docker/service recovery | Compose services are currently healthy. `PRODUCTION_RUNTIME_OWNERSHIP.md` records owners and recovery/start commands. No restart/recreate rehearsal was run. | `requires user-approved rehearsal` | Service recovery may still be improvised during a release incident. |
| Production-local override preservation | `docker-compose.override.yml` preserves `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, and MinIO console `127.0.0.1:19001:9001`; compose/env defaults include `ALLOW_AI_SKELETON_FALLBACK=false`, `LOCAL_MINERU_ENDPOINT=http://host.docker.internal:8083`, `OLLAMA_API_URL=http://host.docker.internal:11434`. | `closed by read-only evidence` | Remaining risk is housekeeping/automation: future deploy cleanup could still disturb local override unless asserted. |
| DB backup/export | `/__proxy/db/health` OK. `/__proxy/db/backup/export` returned HTTP 200, JSON bytes `4053189`, top-level keys including `materials`, `parseTasks`, `aiMetadataJobs`, `settings`, `secrets`; shape: `materials=74`, `parseTasks=74`, `aiMetadataJobs=74`, `assetDetails=41`, `taskEvents=0`, `settings=4`, `secrets=0`. Code shows import creates a `.bak` before overwrite. | `closed by read-only evidence` for export shape; `requires user-approved rehearsal` for restore | Restore/import is mutating and unproven in current production. |
| MinIO artifact inventory/preservation | MinIO container has buckets `eduassets`, `eduassets-parsed`; filesystem inventory shows `original_material_dirs=205`, `parsed_material_dirs=170`, `ai_raw_material_dirs=190`. Selected object metadata exists for review-pending and failed/AI tasks. | `closed by read-only evidence` for current inventory and selected object presence; `requires user-approved rehearsal` for restore | Object restore and full-backup import are still unrehearsed. |
| Task-state recovery / failed-task handling | Current tasks: total `74`; `68 review-pending/review`, `6 failed/ai`. Recent pressure window: `24`; `21 review-pending/review`, `3 failed/ai`. Active-task diagnostics separate historical AI failures from active work. | `closed by read-only evidence` for visibility; `accepted operational risk candidate` for leaving historical AI residuals unrepaired | User already accepted known `failed/ai` residuals as visible manual retry candidates for this track; actual retry/re-AI path was not rehearsed. |
| MinerU submit-path recovery | Direct `/health` is healthy, but submit probe failed HTTP `500` and opened admission circuit. UI shows `MinerU 当前不可接收新任务`. | `blocked/inconclusive` | This blocks new non-Markdown parse intake until Director/user authorizes recovery or a scoped diagnosis/fix. |

## Error-Path Evidence Pack

| Error path | Evidence | Classification |
| --- | --- | --- |
| Upload dependency failure surfaces | Live UI banner shows `系统诊断: MinerU 当前不可接收新任务`, `MinIO 正常`, `MinerU 暂停接收`, `Ollama 正常`; admission circuit message says files will not be accepted while MinerU cannot receive tasks. | `closed by read-only evidence` for surface; `blocked/inconclusive` for underlying submit failure. |
| MinerU `/health` failure | Direct `/health` is currently healthy. No failure injection performed. | `requires user-approved rehearsal`. |
| MinerU submit failure | Live submit-probe evidence: HTTP `500`, circuit `open=true`, parse/AI active counts `0`. | `closed by read-only evidence` as currently observed error path; release boundary blocked until recovery. |
| MinerU long-running/local-timeout | Existing task `task-1778765417422` records `localTimeoutOccurred=true`, `recoveredFromMisjudgedFailed=true`, final `review-pending/review`, `mineruStatus=completed`, parsed files `114`. | `closed by read-only evidence`. |
| MinIO unavailable/object failure | MinIO is healthy and selected objects are present. No MinIO-down simulation performed. | `requires user-approved rehearsal` for unavailable path. |
| DB unavailable/proxy failure | DB health and export shape passed. No DB-down/proxy-502 simulation performed. | `requires user-approved rehearsal` for unavailable path. |
| Ollama missing/tags/cold/warm/chat failure | Current production naturally observed resident success: `readinessState=resident-chat-succeeded`, `readinessSeverity=info`, `blockingAi=false`, `readinessBlocking=false`, `recommendedClientTimeoutMs=20000`. Task 164 code/test evidence covers missing/timeout/chat-failure semantics. | `closed by read-only evidence` for healthy production and code/test semantics; `requires user-approved rehearsal` for live failure. |
| Strict no-skeleton AI failure/manual retry | Existing failed/AI task `task-1778765415701` remains `failed/ai`, `mineruStatus=completed`, parsed files `8`, AI job present; UI shows `AI 识别失败，需人工查看` in list and `需排查或重试` in detail. | `closed by read-only evidence`; copy polish remains optional. |
| UI partial success / residual semantics | `/cms/tasks` shows `68`待复核, `6`已失败; recent pressure window remains `21 review-pending/review` + `3 failed/ai`, not flattened into whole-run failure. | `closed by read-only evidence`. |

## Representative Existing Task Evidence

| Task | Type | Evidence |
| --- | --- | --- |
| `task-1778765417422` | review-pending, recovered long MinerU/local-timeout residue | DB: `review-pending/review`, `progress=100`, `mineruStatus=completed`, `parsedFilesCount=114`, AI job `ai-job-1778802426675-7006`, `localTimeoutOccurred=true`, `recoveredFromMisjudgedFailed=true`. UI: `当前状态 待复核`, `下一步动作 需人工审核`, `MinerU 已完成，解析产物 114 个`. |
| `task-1778765415701` | failed/AI residual | DB: `failed/ai`, `progress=100`, `mineruStatus=completed`, `parsedFilesCount=8`, AI job `ai-job-1778792291124-94e7`. UI: task list `AI 识别失败，需人工查看`; detail `当前状态 失败`, `当前阶段 ai`, `下一步动作 需排查或重试`. |
| `task-1778765408050` | large review-pending success-like example | DB: `review-pending/review`, `progress=100`, `mineruStatus=completed`, `parsedFilesCount=99`, AI job `ai-job-1778792104596-c38c`. |

Selected MinIO object metadata:

| Object | Size | Evidence |
| --- | ---: | --- |
| `eduassets/originals/2274129919986463/source.pdf` | `10147571` | Original PDF for `task-1778765417422` present. |
| `eduassets-parsed/parsed/2274129919986463/full.md` | `156040` | Parsed Markdown present. |
| `eduassets-parsed/parsed/2274129919986463/artifact-manifest.json` | `52884` | Manifest present. |
| `eduassets-parsed/parsed/1959768726011097/full.md` | `5275` | Parsed Markdown for failed/AI task present. |
| `eduassets-parsed/parsed/1959768726011097/artifact-manifest.json` | `2416` | Manifest for failed/AI task present. |

## Browser / Console Evidence

Read-only Playwright navigation visited `/cms/tasks`, `task-1778765415701`, and `task-1778765417422`.

| Signal | Count |
| --- | ---: |
| Relevant `[db-sync]` warnings/errors | 0 |
| `/settings` requests | 3 |
| `/secrets` requests | 3 |
| `Failed to fetch` console messages | 0 |
| HTTP 5xx responses in browser navigation | 0 |
| Non-stream request failures | 0 |
| Stream/eventsource navigation teardown failures | 2 |

Only informational `[appContext] Hydrated from DB (74 materials, initialized=false)` logs were observed.

## Gap Classification Matrix

| Gap | Classification | Precise risk |
| --- | --- | --- |
| Current MinerU submit-path readiness | `blocked/inconclusive` | `/health` is green but submit probe fails HTTP `500`; new non-Markdown intake is blocked by admission circuit. |
| Source rollback rehearsal | `requires user-approved rehearsal` | No proven rollback-to-prior-HEAD and forward-recovery procedure for current release path. |
| Docker/service recovery rehearsal | `requires user-approved rehearsal` | Restart/recreate behavior for current production services is not release-rehearsed. |
| DB restore/import rehearsal | `requires user-approved rehearsal` | Export shape is proven; restore is mutating and not proven on current data. |
| MinIO restore/full-backup rehearsal | `requires user-approved rehearsal` | Object presence is proven; restore/import is mutating and not proven. |
| Production-local override preservation | `closed by read-only evidence` | Current values are correct; future automation should assert them before/after deploy. |
| DB export shape | `closed by read-only evidence` | Export exists and has expected top-level data shape. |
| MinIO selected object preservation | `closed by read-only evidence` | Representative raw/parsed/manifest objects exist. |
| Failed/AI residual visibility | `closed by read-only evidence` | Residuals are visible as AI-stage failures, not hidden success/systemic failure. |
| Live dependency failure UI surface | `closed by read-only evidence` | Current UI clearly shows MinerU paused while MinIO/Ollama remain OK. |
| Live MinIO/DB/Ollama-down behavior | `requires user-approved rehearsal` | Healthy production cannot prove unavailable paths without failure injection. |
| Known historical `failed/ai` residual disposition | `accepted operational risk candidate` | User has accepted these as visible manual retry candidates for this readiness track; actual retry remains unrehearsed. |

## Recommended Next Decision

Recommendation: `NO_GO_UNTIL_IMPLEMENTATION_FIX`, interpreted for this evidence as **no release-boundary progression until the live MinerU submit-path failure is diagnosed and recovered or fixed**.

Exact Director decision to present:

1. Authorize a scoped MinerU submit-path recovery/diagnosis task first, with explicit permission boundaries for any needed service recovery; or
2. If the user believes current parse intake outage is acceptable, explicitly accept the operational risk and keep the admission circuit open while proceeding only with non-upload/read-only release activities; or
3. Defer release-boundary decisions until a user-approved staging or production rehearsal plan covers rollback/recovery and the current submit-path blocker.

I do not recommend asking the user to accept general rollback/error-path residual risk while the production MinerU submit path is currently failing admission.

## Commands Run

- `git status --short --branch` and `git log -1 --oneline` in development and production -> 0.
- `docker compose ps` -> 0.
- `curl` GET checks for upload health, dependency-health, admission circuit, active-task diagnostics, direct MinerU health, CMS routes, DB health, DB backup export shape, and audit consistency -> 0 where command completed.
- `bash ops/runtime-ownership-status.sh` -> 0; important side effect: it invoked dependency-health with `mineruSubmitProbe=true`, which opened the admission circuit after HTTP `500`.
- `docker exec` read-only MinIO directory/object metadata and upload-server MinIO `statObject` checks -> selected object checks succeeded; full bucket list through MinIO client hit a parser limit and was not used as final evidence.
- Headless Playwright read-only navigation -> 0.

## Forbidden Operations Confirmation

No rollback, fast-forward, deploy, rebuild, restart, stop, kill, attach, failure injection, PDF/Markdown upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue, DB/MinIO restore/import, object deletion/overwrite, Docker prune/down/down-v, DB/MinIO/Docker volume/data mutation, MinerU/Ollama/supervisor mutation, settings/secrets/config/model/sample mutation, PRD/role/project-state/handoff edit, skeleton fallback weakening, silent degradation, pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness declaration was performed.
