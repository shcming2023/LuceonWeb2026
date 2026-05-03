# Luceon2026 Codex Operating Rules

Last updated: 2026-05-03

This repository is the durable project memory for Luceon2026. Codex thread history is useful working context, but it is not the source of truth. Any Codex thread that joins this project must read this file first, then read the relevant role handoff in `docs/codex/roles/`.

## Project Direction

Luceon2026 is moving toward a single primary development and validation host:

- Home Mac mini will host the long-lived Codex working environment.
- Work laptops will access the Mac mini through remote desktop.
- GitHub remains the code and documentation source of truth.
- OneDrive may hold a working copy, but it must not be treated as the version-control source.

The intended Mac mini layout is:

- `~/dev/Luceon2026` for Codex development work.
- `~/staging/Luceon2026` for staging and production-like validation.
- `/opt/luceon2026` for production deployment.

Keep dev, staging, and production data, containers, and compose project names isolated.

## Active Roles

Read the role files before acting:

- `docs/codex/roles/lucia.md`: architecture control, task writing, review, and final judgment.
- `docs/codex/roles/luplan.md`: PRD and documentation source-of-truth maintenance.
- `docs/codex/roles/lutest.md`: Tier 2 local validation handoff and retirement path.

Target role model after the Mac mini migration:

- `lucia`: code-facing architecture, task control, L1 gate review, and release judgment.
- `luplan`: PRD, decisions, project state, and changelog maintenance.
- `luceonhmm`: Home Mac mini staging, production validation, deployment, rollback, and evidence capture.
- `lutest`: archive or temporary support role only after its Tier 2 knowledge is transferred.

## Role Boundaries

Lucia must not write business implementation code. Lucia writes tasks, review findings, validation criteria, and final judgments.

luplan must not write business implementation code or perform deployment. luplan updates PRD, decisions, changelog, project-state documents, and handoff docs only when asked.

lutest must not write business implementation code or PRD facts. lutest runs current-environment validation and reports evidence.

No role may claim Lite mock, skeleton fallback, or partial local checks as Tier 2 Standard or production validation.

## Validation Gates

L1 is the fast code gate. It should be runnable on any development host and may include:

```bash
npx tsc --noEmit
npm run build
npm run local:check
npm run test:smoke
```

L2 is Tier 2 near-production validation. Current Standard target is real MinerU v4 online plus local Ollama `qwen3.5:0.8b`, with skeleton fallback disabled.

```powershell
$env:MINERU_ONLINE_API_BASE_URL="https://mineru.net/api/v4"
$env:MINERU_ONLINE_API_TOKEN="<real token, never commit>"
$env:MINERU_ONLINE_MODEL_VERSION="vlm"
docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml up -d --build --force-recreate
npm.cmd run tier2:standard:check
node server/tests/tier2-standard-smoke.mjs
```

L3 is the Home Mac mini staging or production validation. Only L3 can be treated as production truth.

## Safety Rules

- Do not commit secrets or tokens.
- Do not echo full API tokens in reports.
- Do not run `docker compose down -v`, wipe MinIO, wipe DB data, delete Docker volumes, or clean production data without explicit Director approval.
- Do not edit `.agents/**` unless Director explicitly authorizes it.
- Do not broaden a task beyond the signed scope.
- Do not hide skipped or unavailable checks.
- Report environment identity with every L2/L3 validation result.

## Handoff Discipline

Before changing machines or retiring a thread, update:

- `docs/codex/PROJECT_STATE.md`
- the relevant file in `docs/codex/roles/`
- `docs/codex/HANDOFF.md`

Each handoff must include current HEAD, test status, blockers, next action, and whether the result is L1, L2, or L3.
