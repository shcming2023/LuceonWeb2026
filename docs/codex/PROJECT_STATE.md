# Luceon2026 Project State

Last updated: 2026-05-06

## 1. Current Repository Baseline

- Active workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- Remote sync baseline before this governance pass: `origin/main` at `22857e9d83f7598e508f4b2827480c2ec166b96d`
- Package manager: `npx pnpm@10.4.1`
- Root lockfile: `pnpm-lock.yaml`
- Removed lockfile class: root `package-lock.json` and UAT-local `package-lock.json`
- Production release readiness: not claimed by this record.

## 2. Phase 1 Mainline Architecture Snapshot

The current first-phase mainline is the local real runtime path:

1. Operator uploads a document through `/cms/tasks`.
2. `server/upload-server.mjs` stores the raw object in MinIO and creates a `Material` plus a `ParseTask`.
3. `server/services/queue/task-worker.mjs` processes `local-mineru` tasks.
4. Local conda MinerU FastAPI parses PDF inputs; Markdown inputs bypass MinerU and write canonical `full.md`.
5. Parsed artifacts are stored in MinIO under `parsed/{materialId}/`, with `artifact-manifest.json` as the durable large-artifact index.
6. `server/services/ai/metadata-worker.mjs` creates and processes AI metadata jobs through host Ollama `qwen3.5:9b`.
7. High-confidence or accepted results reach `completed`; low-confidence AI results reach `review-pending` and are shown to the operator as `待复核`.

Current runtime dependencies:

| Dependency | Current mainline |
| --- | --- |
| Frontend | React/Vite SPA under `/cms`; `/cms/tasks` is the main workbench |
| Upload/API | Express upload server behind `/__proxy/upload` |
| Data API | Express JSON DB server behind `/__proxy/db` |
| Storage | Docker MinIO with raw and parsed buckets |
| Parser | Local conda MinerU FastAPI, default `http://host.docker.internal:8083` in containers |
| AI | Host Ollama, required model `qwen3.5:9b` |
| Strict AI mode | `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false` |
| Online MinerU | Compatibility-only; not part of the current main gate unless explicitly assigned |

## 3. Governance Closure Summary

Completed on 2026-05-06:

- Archived 27 historical `.codebuddy/plans/` files to `archive/phase1-governance-2026-05-06/codebuddy-plans/`.
- Archived 15 historical `docs/reviews/` files to `archive/phase1-governance-2026-05-06/docs-reviews/`.
- Added archive manifest: `archive/phase1-governance-2026-05-06/MANIFEST.md`.
- Replaced active review sprawl with `docs/reviews/README.md` and `docs/reviews/PHASE1_ACCEPTANCE_SUMMARY.md`.
- Removed obsolete online MinerU v4 batch parsing script: `scripts/test-mineru-v4-batch-parsing.mjs`.
- Renamed `src/store/mockData.ts` to `src/store/seedData.ts`.
- Removed dependency-supervisor test-only mock execution path.
- Removed non-`local-mineru` simulated worker-success path from the runtime worker; unsupported parse engines now fail fast.
- Decoupled strict AI skeleton fallback flags from MinerU online mode selection.
- Rewrote Tier 2 Standard configuration toward local MinerU + MinIO + host Ollama `qwen3.5:9b`.
- Removed unused npm dependency groups from `package.json` and regenerated `pnpm-lock.yaml`.
- Added `uat` to the pnpm workspace and removed local lockfile drift.
- Moved deployment documentation to `docs/deploy/DEPLOY.md`.
- Moved long-form historical project notes to `docs/codex/PROJECT_HISTORY.md`.
- Removed unreferenced root theme artifact `default_shadcn_theme.css`.
- Added root-directory policy: `docs/codex/REPOSITORY_STRUCTURE.md`.
- Aligned UAT route semantics: `/cms/tasks` is the main route; `/cms/source-materials` and `/cms/workspace` are legacy redirects.
- Removed explicit skip markers from active UAT suites.
- Repaired stale comments, mojibake text, and misleading pending-comment wording found during governance scans.

## 4. Validation Ledger

Commands run in this governance pass:

| Check | Result |
| --- | --- |
| `npx pnpm@10.4.1 install --frozen-lockfile` | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS |
| `npx pnpm@10.4.1 run build` | PASS; Vite reported only the existing chunk-size warning |
| `node server/tests/worker-smoke.mjs` | PASS; strict AI mode fails fast without skeleton fallback |
| `node server/tests/dependency-supervisor-smoke.mjs` | PASS |
| `BASE_URL=http://localhost:8081 LOCAL_MINERU_ENDPOINT=http://127.0.0.1:8083 OLLAMA_API_URL=http://127.0.0.1:11434 OLLAMA_TIER2_MODEL=qwen3.5:9b npx pnpm@10.4.1 run tier2:standard:check` | PASS |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` | PASS, 12 passed / 0 failed / 0 skipped |
| `DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts` | PASS, 8 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts` | PASS, 18 passed |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts` | PASS, 2 passed |

Runtime evidence from the final pipeline run:

- PDF chain reached `review-pending`.
- Markdown chain reached an accepted AI-after-parse terminal state.
- Parsed artifacts included `full.md`, `artifact-manifest.json`, and MinerU result carriers.
- Parsed ZIP export included the manifest and canonical Markdown.
- Strict AI worker smoke proved provider failure does not produce skeleton output in current strict mode.

## 5. Known Technical Debts

| ID | Status | Description | Boundary |
| --- | --- | --- | --- |
| TD-001 | Open | MinerU `/health` can report healthy while `/tasks` submit path is unavailable in a half-failed MinerU runtime. | Add a submit-path dependency probe before production release readiness is claimed. |
| TD-002 | Open | `server/upload-server.mjs` remains a large mixed server containing upload, storage, parser, AI, and ops routes. | Keep unchanged for Phase 1 stability; modular refactor belongs to a later phase. |
| TD-003 | Open | Legacy compatibility routes remain for `/cms/source-materials` and `/cms/workspace`. | Keep redirect tests; do not use them as the main operator entry point. |
| TD-004 | Open | Online MinerU v4 adapter remains in the codebase for explicit compatibility-only validation. | It must not be selected by no-skeleton flags or treated as the current Standard gate. |
| TD-005 | Open | Vite production build emits a chunk-size warning for the main bundle. | Non-blocking for Phase 1; consider route-level code splitting later. |
| TD-006 | Open | Full concurrency, large-PDF soak, permissions/security, rollback rehearsal, folder upload, and all error-path coverage are not closed by this governance run. | These are Phase 2 or release-readiness validation items. |

## 6. Core Asset Directory Index

| Path | Role |
| --- | --- |
| `src/app/` | React SPA routes, pages, and reusable UI components |
| `src/store/` | Frontend application state and seed data |
| `server/upload-server.mjs` | Upload, MinIO, parse task, AI trigger, operational proxy entrypoints |
| `server/db-server.mjs` | JSON-backed data API for materials, tasks, settings, secrets, and AI metadata jobs |
| `server/services/mineru/` | Local and compatibility MinerU adapters |
| `server/services/queue/` | Parse task worker and task processing orchestration |
| `server/services/ai/` | AI metadata worker, provider adapters, taxonomy, and v0.2 schema helpers |
| `server/tests/` | Service-level smoke and regression checks |
| `ops/` | Local dependency supervisor and operator tooling |
| `scripts/` | Local checks, test runner wrappers, and Tier 2 pre-check scripts |
| `uat/` | Playwright UAT suites and shell smoke test |
| `docs/prd/` | Active PRD source |
| `docs/codex/` | Project state, handoff, role, validation policy, repository structure, and historical project records |
| `docs/deploy/` | Deployment documentation and environment migration notes |
| `docs/reviews/` | Current review index and phase acceptance summary only |
| `archive/phase1-governance-2026-05-06/` | Historical plan and review archive for traceability |

## 7. Boundary For Future Work

- GitHub `main`, this local workspace, and the PRD remain the three project truth sources.
- Current Phase 1 status is local real-runtime PASS for the upload -> MinerU -> MinIO -> Ollama metadata -> review path.
- This record does not promote staging readiness, production release readiness, or full-site acceptance.
- Future changes must preserve full-text reasoning as the chapter-preprocessing direction if chapter preprocessing is reintroduced or extended; heuristic chapter preprocessing such as `chapterPreprocessV2.ts` must not be restored as a main path.
