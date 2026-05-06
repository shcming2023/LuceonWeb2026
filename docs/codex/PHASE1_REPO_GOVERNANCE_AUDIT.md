# Luceon2026 Phase 1 Repository Governance Audit

Last updated: 2026-05-06

## Scope

This audit covers `.codebuddy/plans/`, `docs/reviews/`, `docs/prd/`, `docs/codex/`, `src/`, `server/`, `ops/`, `scripts/`, `uat/`, `server/tests/`, `docker-compose*.yml`, `.env.example`, and package metadata.

Baseline before governance changes: `origin/main` / `main` at `22857e9d83f7598e508f4b2827480c2ec166b96d`.

## Governance Rules Applied

1. No framework-level rewrite was performed.
2. Runtime behavior of the Phase 1 mainline was preserved.
3. Historical documents were archived, not deleted.
4. Active documents now point to verified facts and current runtime boundaries.
5. `Full-Text Reasoning` remains the required direction for any chapter preprocessing work; heuristic chapter preprocessing files such as `chapterPreprocessV2.ts` are not present in the active repository.
6. Current Standard runtime forbids AI skeleton fallback through explicit strict configuration.
7. Unsupported parse engines fail fast in the active worker path.

## Documentation Governance

| Area | Result |
| --- | --- |
| `.codebuddy/plans/` | 27 historical plan files archived under `archive/phase1-governance-2026-05-06/codebuddy-plans/` |
| `docs/reviews/` | 15 historical reports archived under `archive/phase1-governance-2026-05-06/docs-reviews/` |
| Archive manifest | Added `archive/phase1-governance-2026-05-06/MANIFEST.md` |
| Active review directory | Reduced to `README.md` and `PHASE1_ACCEPTANCE_SUMMARY.md` |
| PRD / Codex state | Updated to local MinerU + MinIO + Ollama `qwen3.5:9b` Standard baseline |
| Legacy online MinerU | Retained only as explicit compatibility-only context |
| Root directory policy | Added `docs/codex/REPOSITORY_STRUCTURE.md` and moved non-tooling root documents into `docs/` |

## Code And Configuration Governance

| Area | Result |
| --- | --- |
| Obsolete scripts | Removed `scripts/test-mineru-v4-batch-parsing.mjs` |
| Mock naming | Renamed `src/store/mockData.ts` to `src/store/seedData.ts` |
| Worker skeleton path | Removed non-`local-mineru` simulated success path; unsupported engines now fail |
| AI strict mode | Provider failure in strict mode now fails without skeleton output |
| Dependency supervisor | Removed the test-only environment-driven execution branch from runtime code |
| Package metadata | Removed unused exploration-era dependencies; pnpm workspace now includes `uat` |
| Lockfiles | Root `package-lock.json` removed; UAT-local lockfile removed from the active project layout |
| Docker Standard overlay | `docker-compose.tier2-standard.yml` now points to local MinerU and host Ollama |
| Env example | `.env.example` now documents local real runtime defaults and explicit online mode only |
| Root generated artifact | Removed unreferenced `default_shadcn_theme.css` |

## Test And UAT Governance

| Area | Result |
| --- | --- |
| Shell smoke | `/cms/tasks` is the primary route; `/cms/source-materials` is legacy compatibility |
| Playwright pages smoke | `/cms/workspace` is treated as a legacy redirect |
| Playwright CMS UAT | Removed skip usage; MinIO URL tests use raw upload instead of creating unnecessary AI jobs |
| Pipeline consistency | Waits for real AI terminal state and avoids retry-created duplicate long-chain tasks |
| Server worker smoke | Verifies strict AI mode fails fast without skeleton fallback |

## Validation Evidence

| Check | Result |
| --- | --- |
| `npx pnpm@10.4.1 install --frozen-lockfile` | PASS |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS |
| `npx pnpm@10.4.1 run build` | PASS |
| `node server/tests/worker-smoke.mjs` | PASS |
| `node server/tests/dependency-supervisor-smoke.mjs` | PASS |
| `npx pnpm@10.4.1 run tier2:standard:check` with local endpoints | PASS |
| `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` | PASS |
| `DB_BASE_URL=http://localhost:8081/__proxy/db node server/tests/mineru-deep-check.mjs` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pages-smoke.spec.ts` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/cms-uat.spec.ts` | PASS |
| `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 --dir uat exec playwright test tests/pipeline-consistency.spec.ts` | PASS |

## Residual Boundaries

The following items remain outside this governance pass:

1. Production release readiness.
2. Large-PDF soak testing and concurrent upload stress testing.
3. Permissions and security hardening validation.
4. Rollback rehearsal and backup restore validation.
5. Modular decomposition of `upload-server.mjs`.
6. Online MinerU v4 compatibility run.
