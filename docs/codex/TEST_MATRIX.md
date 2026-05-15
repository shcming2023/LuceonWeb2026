# Luceon2026 Test Matrix

Last updated: 2026-05-11

This matrix maps common validation commands to the risk they cover. It is a coordination aid, not a release-readiness claim.

## Fast Static Gate

| Command | Covers | Notes |
| --- | --- | --- |
| `git diff --check` | Whitespace and patch hygiene | Run before commit when files changed. |
| `node --check server/upload-server.mjs` | Syntax check for the monolithic upload server | Add other touched `.mjs` files explicitly when changed. |
| `bash -n uat/smoke-test.sh` | UAT smoke script syntax | Does not validate runtime reachability. |
| `npx pnpm@10.4.1 exec tsc --noEmit` | Frontend TypeScript contract | Current `tsconfig.json` covers `src`; server `.mjs` files are not type-checked. |
| `npx pnpm@10.4.1 run build` | Production frontend bundle | A chunk-size warning is not a failure by itself. |

## Local Server Smoke

| Command | Covers | Notes |
| --- | --- | --- |
| `node server/tests/worker-smoke.mjs` | Worker strict no-skeleton behavior and parse-worker failure writeback | Uses smoke fakes; does not prove real MinerU/Ollama reachability. |
| `node server/tests/dependency-health-smoke.mjs` | MinerU submit-probe, admission circuit, Ollama cold/warm health semantics | Does not mutate production data. |
| `node server/tests/mineru-submit-circuit-breaker-smoke.mjs` | Durable MinerU admission circuit behavior | Use when touching admission or intake code. |
| `node server/tests/mineru-log-progress-smoke.mjs` | MinerU log progress semantics | Use when touching sidecar/log-progress parsing. |

## Runtime And UAT Gates

| Command | Covers | Notes |
| --- | --- | --- |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run test:smoke` | Current local UAT proxy, frontend routes, upload/db health, MinIO proxy and console | Requires a running local stack. Failure is runtime evidence, not automatically a code regression. |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts` | Browser-visible route rendering | Requires Chromium installed in `uat`. |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts` | Browser/API pipeline consistency | Requires a healthy local real-runtime stack. |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check` | Tier 2 Standard local MinerU + MinIO + Ollama gate | Do not report as L3 or production release readiness. |

## Production-Line Read-Only Checks

| Command | Covers | Notes |
| --- | --- | --- |
| `curl -fsS http://localhost:8081/__proxy/upload/health` | Upload-server proxy surface | Read-only. |
| `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health'` | MinIO, MinerU `/health`, Ollama dependency semantics, and current admission-circuit evidence | Read-only; does not prove MinerU `/tasks` submit readiness by itself. |
| `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'` | MinerU submit path, MinIO, Ollama dependency semantics | Side-effecting: creates a bounded synthetic MinerU task and may update the durable admission circuit; use only where explicitly authorized by validation policy/task brief. |
| `curl -sS --max-time 15 'http://localhost:8081/__proxy/upload/ops/mineru/admission-circuit'` | Durable MinerU admission circuit state | Read-only. |
| `docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'` | Runtime container status | Read-only; does not imply authorization to restart. |

## Reporting Rules

- Report exact command, exit code, and key counts such as `65 passed / 0 failed`.
- Keep local UAT, L2, L3, production deployment, and production release readiness as separate labels.
- If a runtime command fails because a dependency is down, report it as runtime evidence and do not silently replace it with a static check.
- Do not run destructive cleanup, DB edits, MinIO object deletion, Docker volume operations, model changes, or production restarts unless a task explicitly authorizes them.
