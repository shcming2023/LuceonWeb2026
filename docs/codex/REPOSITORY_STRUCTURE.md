# Repository Structure Policy

Last updated: 2026-05-16

## Root Directory Rule

The repository root is reserved for files that are required by common tooling, container orchestration, package management, or cross-agent entrypoints.

Allowed root files:

| Category | Files |
| --- | --- |
| Agent and repo entrypoints | `AGENTS.md`, `README.md`, `CHANGELOG.md` |
| Package and build tools | `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `index.html`, `vite.config.ts`, `tsconfig.json`, `postcss.config.mjs` |
| Docker and environment tools | `Dockerfile`, `docker-compose*.yml`, `.dockerignore`, `.env.example` |
| Git and ignore/editor rules | `.gitignore`, `.editorconfig` |
| Convenience runtime script | `start-uat.sh` |

Directories allowed at root:

| Directory | Role |
| --- | --- |
| `.agents/` | Reserved for future documented agent entrypoints; no active workflow prompt is tracked after 6.9.1 |
| `.codebuddy/` | CodeBuddy metadata; active plan files must not accumulate here |
| `.workbuddy/` | WorkBuddy memory metadata |
| `TaskAndReport/` | Active Luceon/Lucode task briefs, reports, reviews, decisions, and historical task tracking ledger |
| `archive/` | Historical governance archive |
| `docker/` | Docker support files such as Nginx config |
| `docs/` | Project documentation, PRD, codex state, deployment docs, and reviews |
| `ops/` | Local operational tooling |
| `public/` | Static frontend assets |
| `scripts/` | Developer and validation scripts |
| `server/` | Backend services and service tests |
| `src/` | Frontend source code |
| `uat/` | UAT test suites and UAT-specific package metadata |

## Files Moved During Governance

| Previous path | Current path | Reason |
| --- | --- | --- |
| `DEPLOY.md` | `docs/deploy/DEPLOY.md` | Deployment documentation belongs under `docs/deploy/` |
| `说明文档.md` | `docs/codex/PROJECT_HISTORY.md` | Long-form project history belongs under codex documentation |
| `default_shadcn_theme.css` | removed | Unreferenced generated theme artifact |

## Policy

1. Do not add one-off reports, drafts, screenshots, generated outputs, or temporary files to the root directory.
2. Put current project state and handoff material in `docs/codex/`.
3. Put deployment material in `docs/deploy/`.
4. Put historical plans and superseded reviews in `archive/`.
5. Keep Compose files at the root unless the related scripts and documentation are changed together; current scripts depend on root-level compose paths.
6. Keep `start-uat.sh` at the root because package scripts and UAT docs invoke it directly.
7. Keep `TaskAndReport/` at the root because it is the active GitHub-mediated control plane and historical execution record.
8. Current active role docs may live under `docs/codex/roles/`; as of 2026-05-16 the active file is `docs/codex/roles/luceon.md`.
9. Retired role contracts and workflow prompts must stay under `archive/team-model-retired-2026-05-16/`; do not revive archived role files by implication.
