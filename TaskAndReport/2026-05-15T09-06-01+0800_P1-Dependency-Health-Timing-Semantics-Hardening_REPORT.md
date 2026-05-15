# DevelopmentEngineer Report: P1 Dependency Health Timing Semantics Hardening

- Task ID: `TASK-20260515-090601-P1-Dependency-Health-Timing-Semantics-Hardening`
- Task brief: `TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_TASK.md`
- Role: `DevelopmentEngineer`
- Report time: `2026-05-15T09:33+0800`

## Scope

This work was based on the Director task brief above, issued after Task 162 and Task 163 Director reviews.

The task was repository code/test hardening only. I did not perform production deployment, production fast-forward, rebuild, restart, rollback, config mutation, upload, pressure/batch/soak/fresh serial validation, cleanup, cancel, repair, retry, reparse, re-AI, destructive DB/MinIO/Docker volume/data mutation, production service mutation, settings/secrets/config/model/sample mutation, automatic retry/requeue, skeleton fallback weakening, or readiness/go-live claim.

## Files Changed

- `server/upload-server.mjs`
- `server/tests/dependency-health-smoke.mjs`
- `TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Note: the shared development workspace was already dirty before this task, and `server/upload-server.mjs` already contained unrelated local modifications from prior role-thread work. This task only added the dependency-health Ollama readiness semantics and focused smoke assertions described below.

## Branch / HEAD

- Development branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- Development HEAD: `005ca96 Hold Task 108 auto progress on GitHub sync`
- GitHub sync: not performed; this task brief did not authorize fetch, pull, commit, or push.

## Implementation Summary

Before this task, dependency-health already separated parse/upload blocking from Ollama health by keeping `blocking=false` when only Ollama failed, and it already exposed `warmState`, `durationMs`, and `failureKind`. The remaining ambiguity was that an external short client timeout could make a slow but successful Ollama cold-start look like a service failure.

After this task, Ollama dependency-health responses now carry explicit timing/readiness semantics:

- `probeTimeoutMs`: configured Ollama chat probe timeout.
- `recommendedClientTimeoutMs`: minimum recommended external client window for dependency-health clients that include Ollama chat probing.
- `readinessState`: explicit state such as `resident-chat-succeeded`, `cold-start-chat-succeeded`, `cold-start-chat-timeout`, `warm-chat-timeout`, `chat-http-error`, `model-missing`, `tags-http-error`, or `service-unreachable`.
- `readinessSeverity`: `info`, `notice`, `warning`, or `error`.
- `timingNote`: human-readable explanation of whether the result is cold-start slow success, timeout, or hard failure.
- `blockingAi` / `readinessBlocking`: true for AI readiness failures, false for successful resident or cold-start chat.
- `blockingParse`: remains false for Ollama/AI issues so parse/upload readiness is not blocked solely by AI slowness or outage.
- `coldStartChatSucceeded`: set when the model was not resident before chat but the chat probe succeeded.

Strict no-skeleton behavior was not weakened. Missing model and chat failures remain AI readiness failures; they are only made more explicit.

## Evidence

Focused smoke coverage added/updated in `server/tests/dependency-health-smoke.mjs`:

- resident-before-chat success reports `readinessState=resident-chat-succeeded`;
- cold-before-chat success remains `ollama.ok=true`, `blocking=false`, `blockingParse=false`, and reports `readinessState=cold-start-chat-succeeded`;
- Ollama down reports AI readiness blocking while parse/upload blocking remains false;
- HTTP chat failure reports `readinessState=chat-http-error`;
- cold chat timeout reports `readinessState=cold-start-chat-timeout`, `readinessBlocking=true`, and `blockingParse=false`;
- warm chat timeout reports `readinessState=warm-chat-timeout`;
- missing required model reports `readinessState=model-missing` and `blockingAi=true`, while parse/upload blocking remains false.

`node server/tests/dependency-health-smoke.mjs` result:

```text
Results: 89 passed, 0 failed
```

## Commands Run

| Command | Exit | Notes |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required DevelopmentEngineer check-task preflight. |
| `sed -n '150,190p' TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Read current task ledger rows. |
| `sed -n '1,280p' TaskAndReport/2026-05-15T09-06-01+0800_P1-Dependency-Health-Timing-Semantics-Hardening_TASK.md` | 0 | Read assigned task brief. |
| `sed -n ...` required role/docs/Task 163 review files | 0 | Required reading and context refresh. |
| `rg -n "dependency-health\|ollamaChatProbe\|warmState\|resident-before-chat\|cold-before-chat\|Ollama" server/upload-server.mjs server/tests -g '*.mjs'` | 0 | Locate relevant implementation/tests. |
| `node --check server/upload-server.mjs` | 0 | Syntax check. |
| `node --check server/tests/dependency-health-smoke.mjs` | 0 | Syntax check. |
| `node server/tests/dependency-health-smoke.mjs` | 0 | Focused smoke; 89 passed, 0 failed. |
| `git diff --check -- server/upload-server.mjs server/tests/dependency-health-smoke.mjs` | 0 | Whitespace/diff check for changed code files. |
| `node server/tests/ai-metadata-repair-hardening-smoke.mjs` | 0 | AI metadata strict/no-skeleton adjacent regression smoke passed. |
| `node server/tests/mineru-runtime-progress-truth-smoke.mjs` | 0 | MinerU progress semantics adjacent regression smoke passed. |
| `node server/tests/pressure-result-semantics-smoke.mjs` | 0 | Pressure-result semantics adjacent regression smoke passed. |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | TypeScript check passed. |

## Skipped Checks

- `npx pnpm@10.4.1 run build` was skipped because this task only changed server `.mjs` code and a Node smoke test; no frontend or TypeScript source was touched.
- Production runtime/browser validation was skipped because the task explicitly forbids production deployment/rebuild/restart/config mutation and does not authorize runtime validation.
- Upload, pressure/batch/soak/fresh serial validation, retry/reparse/re-AI, cleanup, and destructive operations were skipped because they are explicitly forbidden.

## Risks / Residual Debt

- This is code/test-level hardening only. Production runtime evidence requires a later Director-approved deployment/read-only validation task.
- `recommendedClientTimeoutMs` is a server-reported expectation; clients or scripts that hard-code shorter timeouts may still abort before receiving a successful cold-start response until they adopt this field or policy.
- The response now carries richer readiness fields, but UI/operator copy may still need a separate task if Director wants visible wording changes.

## Director Review Needed

Yes. Director should review whether the code/test-level semantics are accepted and decide whether to issue a scoped production deployment/read-only validation task or route to the next release-readiness blocker.
