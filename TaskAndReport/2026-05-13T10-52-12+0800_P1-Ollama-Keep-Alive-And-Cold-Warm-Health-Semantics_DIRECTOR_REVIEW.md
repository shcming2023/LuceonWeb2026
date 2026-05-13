# Director Review: P1 Ollama Keep-Alive And Cold/Warm Health Semantics

- Task ID: `TASK-20260510-225807-P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics`
- Reviewed At: `2026-05-13T10:52:12+0800`
- Reviewer: Director
- Reviewed Task: `TaskAndReport/2026-05-10T22-58-07+0800_P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics_TASK.md`
- Reviewed Report: `TaskAndReport/2026-05-10T22-58-07+0800_P1-Ollama-Keep-Alive-And-Cold-Warm-Health-Semantics_REPORT.md`
- Implementation HEAD: `f4350e5c4ce1172b6b1892901ea852f61513a7c5`
- Current main contains implementation via: `9db0054`
- Review Result: `ACCEPTED`
- Acceptance Boundary: code-level accepted; production deployment, runtime validation, pressure PASS, L3, and production release readiness remain unclaimed.

## Evidence Reviewed

- Task brief and Lucode report for Task 78.
- Implementation diff for `f4350e5c4ce1172b6b1892901ea852f61513a7c5`.
- Current code in:
  - `.env.example`
  - `server/upload-server.mjs`
  - `server/services/ai/providers/ollama.mjs`
  - `server/services/ai/metadata-worker.mjs`
  - `server/tests/dependency-health-smoke.mjs`
  - `server/tests/ai-metadata-real-sample-smoke.mjs`
- Git containment check: `f4350e5c4ce1172b6b1892901ea852f61513a7c5` is contained by local `main`, `origin/main`, and the legacy Lucode branch.

## Scope Judgment

The Task 78 implementation stayed inside the requested code/config/test scope.

Accepted scoped behavior:

- `OLLAMA_KEEP_ALIVE` is explicit, defaults to `24h`, and is documented in `.env.example`.
- Dependency-health Ollama smoke sends `keep_alive`.
- Native `OllamaProvider` sends `keep_alive` on `/api/chat`.
- `AiMetadataWorker` passes keep-alive to the native Ollama provider.
- Dependency-health separates service reachability, tag listing, required model presence, residency before chat, chat result, cold-start timeout, and warm-chat timeout.
- No retry was added for JSON parse, schema validation, or repair failures.

No evidence was found that Task 78 performed model operations, uploads, pressure retries, Task 75/76 mutation, production override mutation, broad restart, L3 validation, pressure PASS, or release-readiness declaration.

## Validation Judgment

Director reran focused checks on the current workspace:

- `git diff --check`: exit `0`.
- `node --check server/upload-server.mjs && node --check server/services/ai/providers/ollama.mjs && node --check server/services/ai/metadata-worker.mjs`: exit `0`.
- `node server/tests/dependency-health-smoke.mjs`: exit `0`, `65 passed, 0 failed`.
- `npx pnpm@10.4.1 exec tsc --noEmit`: exit `0`.
- `npx pnpm@10.4.1 run build`: exit `0`; Vite produced the existing large-chunk warning only.

Director also reran `node server/tests/ai-metadata-real-sample-smoke.mjs` on current `main`; it failed:

- exit `1`;
- failing assertion: `server/tests/ai-metadata-real-sample-smoke.mjs:830`;
- observed mismatch: `headersTimeoutMs` actual `30000`, expected `12345`.

This failure appears to come from the later `e7c68ba` AI Worker observability change, which intentionally set the Ollama provider first-byte/header timeout to `30000` while leaving body timeout tied to provider timeout. The smoke test still asserts the pre-`e7c68ba` behavior. This is not treated as a Task 78 keep-alive regression, but it is a current-main validation debt and blocks a clean production deployment/runtime-validation authorization.

## Accepted Facts

- Task 78 makes Ollama keep-alive explicit at code level.
- Task 78 improves dependency-health semantics so cold-before-chat and resident-before-chat timeouts can be distinguished.
- The dependency-health focused smoke covers keep-alive propagation and cold/warm timeout classification.
- Task 78 does not deploy the new behavior to production runtime by itself.
- Current production release readiness remains unclaimed.

## Rejected Or Pending Claims

- Not accepted: production deployment of Task 78 behavior.
- Not accepted: production runtime validation of new cold/warm fields.
- Not accepted: pressure PASS, L3, or production release readiness.
- Not accepted: current `main` has a fully clean AI metadata smoke suite, because `ai-metadata-real-sample-smoke` currently fails on timeout semantics drift.

## Required Follow-Up

Director issued `TASK-20260513-105212-P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment` to `DevelopmentEngineer`.

The follow-up must reconcile the current AI metadata smoke with the current Ollama provider timeout contract before Director considers production deployment/runtime validation of Task 77 and Task 78 code.

## Next Actor

`DevelopmentEngineer`

## Next Action

Execute `TASK-20260513-105212-P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment`.

## Required Output

`TaskAndReport/2026-05-13T10-52-12+0800_P0-AI-Metadata-Smoke-Timeout-Semantics-Alignment_REPORT.md`
