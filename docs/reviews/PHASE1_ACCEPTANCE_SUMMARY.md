# Luceon2026 Phase 1 Acceptance Summary

Last updated: 2026-05-06

Snapshot note: this file is a dated governance snapshot from 2026-05-06. Later task-level changes, technical-debt closures, release-readiness evidence, and active status are tracked in `docs/codex/PROJECT_STATE.md` and `TaskAndReport/TASK_TRACKING_LIST.md`.

## Scope

This summary records the confirmed first-phase state after repository governance. It is not a production release declaration.

The first-phase mainline is:

1. upload through `/cms/tasks`;
2. local MinerU parsing;
3. parsed artifact persistence in MinIO;
4. AI metadata recognition through Ollama `qwen3.5:9b`;
5. operator review using the `待复核` state when AI confidence requires review.

The current runtime baseline is local conda MinerU, Docker MinIO, host Ollama `qwen3.5:9b`, `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, and `STORAGE_BACKEND=minio`.

## Confirmed System Shape

| Layer | Current shape |
| --- | --- |
| Frontend | React/Vite SPA served under `/cms`; `/cms/tasks` is the main task workbench |
| Upload/API | Express upload server behind `/__proxy/upload` |
| Data API | Express JSON DB server behind `/__proxy/db` |
| Storage | MinIO raw and parsed buckets; parsed artifact lists are tracked through `artifact-manifest.json` |
| Parser | Local MinerU FastAPI endpoint submitted through `/tasks` and polled to completion |
| AI metadata | Ollama provider with `qwen3.5:9b`; strict mode rejects skeleton output on provider failure |
| Review state | `review-pending` is shown to the operator as `待复核` |

## Verified During Governance

| Check | Result |
| --- | --- |
| `npx pnpm@10.4.1 install --frozen-lockfile` | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS |
| `npx pnpm@10.4.1 run build` | PASS |
| `node server/tests/worker-smoke.mjs` | PASS |
| `node server/tests/dependency-supervisor-smoke.mjs` | PASS |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` | PASS, 12 passed / 0 failed / 0 skipped |
| `DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts` | PASS, 8 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts` | PASS, 18 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts` | PASS, 2 passed |

## Known Issues And Technical Debts

| ID | Status | Description | Required closure |
| --- | --- | --- | --- |
| TD-001 | Open | MinerU `/health` can be insufficient evidence for `/tasks` submit readiness in a half-failed runtime | Add submit-path probe or stronger dependency-health evidence |
| TD-002 | Open | `upload-server.mjs` remains a large mixed server | Keep unchanged for Phase 1 stability; consider modular refactor later |
| TD-003 | Open | Legacy redirects remain for `/cms/source-materials` and `/cms/workspace` | Keep redirect tests; do not treat legacy routes as main entry points |
| TD-004 | Open | Online MinerU v4 adapter remains for compatibility-only validation | Do not use it as Standard mainline unless explicitly assigned |
| TD-005 | Open | Vite build reports a chunk-size warning | Non-blocking; consider later code splitting |
| TD-006 | Open | Concurrency, large-file soak, permissions/security, rollback, folder upload, and all error paths are not fully validated | Treat as release-readiness or Phase 2 scope |

## Core Asset Index

| Path | Role |
| --- | --- |
| `src/app/` | Operator UI and SPA routing |
| `server/upload-server.mjs` | Upload, MinIO, ParseTask, AI trigger, and operational proxy routes |
| `server/db-server.mjs` | JSON-backed data API |
| `server/services/mineru/` | MinerU adapters |
| `server/services/queue/` | ParseTask worker |
| `server/services/ai/` | AI metadata worker and schema helpers |
| `uat/` | Browser and shell UAT suites |
| `docs/codex/PROJECT_STATE.md` | Current project ledger |
| `docs/codex/REPOSITORY_STRUCTURE.md` | Root directory and folder placement policy |
| `archive/phase1-governance-2026-05-06/` | Historical plan and review archive |

## Governance Boundary

The 2026-05-06 governance pass archived historical plans and review reports, aligned active documents and tests, removed confirmed obsolete code/assets, and preserved the Phase 1 external behavior. It does not claim production release readiness.

Later status note: TD-001 was closed after this snapshot by the MinerU submit-path probe work recorded in `docs/codex/PROJECT_STATE.md` and `TaskAndReport/`.
