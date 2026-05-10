# Lucode Report: P1 Ollama Keep-Alive And Cold/Warm Health Semantics

- Task ID: `TASK-20260510-225807-P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics`
- Based on: `TaskAndReport/2026-05-10T22-58-07+0800_P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics_TASK.md`
- Branch: `lucode/p1-ollama-keep-alive-cold-warm-health-semantics`
- Implementation HEAD: `f4350e5c4ce1172b6b1892901ea852f61513a7c5`
- Status: Completed, pending Lucia review

## Files Changed

- `.env.example`
- `server/upload-server.mjs`
- `server/services/ai/providers/ollama.mjs`
- `server/services/ai/metadata-worker.mjs`
- `server/tests/dependency-health-smoke.mjs`
- `server/tests/ai-metadata-real-sample-smoke.mjs`

## Implementation Summary

Implemented explicit Ollama keep-alive and cold/warm health semantics without changing the selected model, running uploads, retrying pressure tasks, mutating production overrides, or changing PRD/project-ledger truth.

- Added `OLLAMA_KEEP_ALIVE`, defaulting to `24h`, and documented it in `.env.example`.
- Added `DEPENDENCY_HEALTH_OLLAMA_CHAT_TIMEOUT_MS`, defaulting to `15000`.
- Dependency-health Ollama smoke now sends `keep_alive`.
- Native `OllamaProvider` now sends `keep_alive` on AI metadata `/api/chat` requests.
- `AiMetadataWorker` passes `aiSettings.ollamaKeepAlive || aiSettings.keepAlive || OLLAMA_KEEP_ALIVE || 24h` into the native Ollama provider.
- Dependency-health now reports separate Ollama fields:
  - `serviceReachable`
  - `tagsOk`
  - `modelPresent`
  - `modelResident`
  - `residency.beforeChat`
  - `residency.afterChat`
  - `warmState`
  - `coldStartChatTimeout`
  - `warmChatTimeout`
  - `failureKind`
  - `keepAlive`
- No transport retry was added. JSON/schema/repair semantics remain unchanged.

## Before / After Semantics

Before this change, dependency-health could only show that Ollama smoke failed after a timeout, for example Lucia's observed `ollama.ok=false`, `chatOk=false`, `durationMs=15025`, without distinguishing a cold model from a warm-model chat failure.

After this change, code-level dependency-health distinguishes:

- service unreachable: `serviceReachable=false`, `failureKind=service-unreachable`
- tags HTTP/error: `tagsOk=false`, `failureKind=tags-http-error` or `tags-error`
- model missing: `modelPresent=false`, `failureKind=model-missing`
- cold model timeout: `warmState=cold-before-chat`, `coldStartChatTimeout=true`, `failureKind=cold-start-chat-timeout`
- resident model timeout: `warmState=resident-before-chat`, `warmChatTimeout=true`, `failureKind=warm-chat-timeout`
- successful warm chat: `chatOk=true`, `ok=true`, `failureKind=null`

## Runtime Evidence

Read-only/runtime diagnostic commands were run after the code change, but the production server at `localhost:8081` was not rebuilt or restarted, so it still returned the old deployed dependency-health shape. This is the remaining runtime deployment/validation gap.

`curl -sS --max-time 8 http://localhost:11434/api/ps`

- Exit code: `0`
- Evidence: `qwen3.5:9b` was resident.
- Observed fields included:
  - `name`: `qwen3.5:9b`
  - `size`: `20077747136`
  - `expires_at`: `2026-05-11T00:05:43.045335+08:00`

`curl -sS --max-time 20 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'`

- Exit code: `0`
- Production deployed shape still old for Ollama:
  - `ollama.ok=true`
  - `ollama.chatOk=true`
  - `ollama.durationMs=515`
  - no new cold/warm fields yet because implementation was not deployed
- MinerU submit probe returned OK:
  - `submitProbe.ok=true`
  - `status=202`
  - `taskId=a8720204-22c7-4da7-940e-bae73908f973`

Note: the required runtime dependency-health command uses the existing submit-probe endpoint, which by current system design creates a synthetic MinerU task and persists admission-circuit evidence. Lucode did not create uploads, retry pressure tasks, edit DB rows manually, mutate MinIO objects, change Docker volumes, or alter production overrides.

## Checks

- `git status --short --branch`: exit `0`; synced workspace on task branch.
- `git fetch origin`: exit `0`.
- `git pull --ff-only origin main`: exit `0`; already up to date before branch work.
- `git diff --check`: exit `0`.
- `npx pnpm@10.4.1 exec tsc --noEmit`: exit `0`.
- `npx pnpm@10.4.1 run build`: exit `0`; Vite build succeeded, with existing chunk-size warning.
- `node server/tests/dependency-health-smoke.mjs`: exit `0`; `65 passed, 0 failed`.
- `node server/tests/ai-metadata-real-sample-smoke.mjs`: exit `0`; `AI Metadata Real Sample Smoke Test Success`.

## Focused Test Evidence

`server/tests/dependency-health-smoke.mjs` now covers:

- default dependency-health remains cheap for MinerU submit path
- Ollama smoke sends `keep_alive=24h`
- service/model/residency fields are present on successful health
- Ollama HTTP chat failure is classified as `chat-http-error`
- cold model timeout is classified as `cold-start-chat-timeout`
- resident model timeout is classified as `warm-chat-timeout`
- Ollama down still does not block parse

`server/tests/ai-metadata-real-sample-smoke.mjs` now asserts native `OllamaProvider` sends `keep_alive=24h` while preserving `think=false`.

## Forbidden Operations Statement

No model pull/delete/reload/replace/change was performed. No upload or pressure test was created or rerun. No Task 75/76 pressure task was repaired, retried, deleted, closed, or mutated. No secrets were changed. No production `docker-compose.override.yml` mutation was performed. No broad production restart, rebuild, rollback, Docker volume operation, MinIO cleanup, DB cleanup, artifact cleanup, log mutation, sample mutation, L3 claim, pressure PASS, or release-readiness claim was made.

## Residual Gaps / Risks

- The implementation is code-level and test-validated on the task branch; production runtime still needs Lucia/Director-approved deployment/restart before `localhost:8081` exposes the new Ollama cold/warm fields.
- Current production dependency-health submit-probe endpoint has designed side effects: synthetic MinerU task creation and admission-circuit persistence. That behavior predates this task and remains unchanged.
- `OLLAMA_KEEP_ALIVE=24h` keeps the model warm for long validations but still allows eventual expiry. Lucia may decide whether production should use `-1` after reviewing resource/residency tradeoffs.

## Review Need

Lucia review is required before merge or production deployment.
