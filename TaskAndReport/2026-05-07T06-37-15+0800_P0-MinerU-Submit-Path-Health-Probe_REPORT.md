# Lucode Completion Report: P0 MinerU Submit-Path Health Probe

```text
Task:
P0 MinerU Submit-Path Health Probe

Basis:
Work was executed from Lucia's 2026-05-07 task brief. Lucode did not change PRD truth, PROJECT_STATE, HANDOFF, role contracts, or release judgments.

Branch and HEAD:
Branch: lucode/p0-mineru-submit-path-health-probe
HEAD: d89d16a fix: add mineru submit-path health probe
Remote sync: pushed to origin/lucode/p0-mineru-submit-path-health-probe
PR URL: https://github.com/shcming2023/Luceon2026/pull/new/lucode/p0-mineru-submit-path-health-probe

Files changed:
- server/upload-server.mjs
- scripts/tier2-standard-check.mjs
- server/tests/dependency-health-smoke.mjs
- .env.example

Implementation summary:
- Added opt-in MinerU submit-path probe for /ops/dependency-health.
- Default dependency-health remains lightweight and only checks MinerU /health.
- Submit probe can be enabled by query flag:
  /ops/dependency-health?mineruSubmitProbe=true
- Submit probe can also be enabled by env:
  DEPENDENCY_HEALTH_MINERU_SUBMIT_PROBE=true
- Probe submits a minimal synthetic PDF directly to active local MinerU POST /tasks.
- Probe does not create Luceon Material, ParseTask, MinIO objects, or DB rows.
- MinerU dependency result now includes:
  healthOk
  submitProbe.enabled
  submitProbe.ok
  submitProbe.status
  submitProbe.durationMs
  submitProbe.taskId
  submitProbe.error
- When submit probing is enabled, dependencies.mineru.ok requires both /health success and POST /tasks task-id success.
- Tier 2 Standard check now requests mineruSubmitProbe=true and fails if submitProbe.ok is not true.

Submit-probe evidence:
- Default cheap behavior:
  health OK + submit probe disabled -> mineru.healthOk=true, submitProbe.enabled=false, mineru.ok=true, MinerU /tasks call count=0.
- Failure behavior:
  health OK + submit probe enabled + /tasks returns 503 -> submitProbe.ok=false, submitProbe.status=503, mineru.ok=false, blocking=true.
- Success behavior:
  health OK + submit probe enabled + /tasks returns task_id -> submitProbe.ok=true, submitProbe.taskId present, mineru.ok=true, blocking=false.
- Ollama-down behavior remains non-blocking for parse:
  ollama.ok=false, ollama.blockingParse=false, blocking=false, POST /tasks still returns 200 when MinerU/MinIO are OK.

Commands run and results:
- git status --short --branch: exit 0
- git fetch origin: exit 0
- git pull --ff-only origin main: exit 0
- git switch -c lucode/p0-mineru-submit-path-health-probe origin/main: exit 0
- node server/tests/dependency-health-smoke.mjs: exit 0, 31 passed / 0 failed
- npx pnpm@10.4.1 exec tsc --noEmit: exit 0
- npx pnpm@10.4.1 run build: exit 0; existing Vite chunk-size warning only
- npx pnpm@10.4.1 run tier2:standard:check: exit 1
  Blocker: default BASE_URL http://127.0.0.1:8080 served CMS HTML for /__proxy/upload/ops/dependency-health, causing JSON parse failure: Unexpected token '<'.
- BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check: exit 1
  Blocker: reachable 8081 backend was not rebuilt from this branch; dependency-health returned missing new fields (mineru.healthOk=undefined, mineru.submitProbe.enabled=undefined) and ollama=false, so this cannot be used as branch validation evidence.
- BASE_URL=http://localhost:8081 bash uat/smoke-test.sh: exit 0, 12 passed / 0 failed / 0 skipped
  Note: this validates currently reachable runtime basics, not rebuilt branch submit-probe behavior.
- git diff --check: exit 0
- git commit -m "fix: add mineru submit-path health probe": exit 0
- git push -u origin lucode/p0-mineru-submit-path-health-probe: exit 0
- final git status --short --branch: exit 0, clean working tree

Checks skipped:
- No destructive Docker, MinIO, DB, volume, or production cleanup commands were run.
- Full Tier 2 Standard PASS was not claimed because the reachable local runtime was not rebuilt from this branch and did not expose the new dependency-health fields.

Risks / residual technical debt:
- The submit probe creates a synthetic task inside MinerU itself. It is intentionally outside Luceon DB/MinIO, but MinerU may retain its own internal probe task record.
- Real rebuilt-runtime Tier 2 Standard should be rerun after deploying this branch into the local stack.
- Default BASE_URL behavior in tier2:standard:check can still point at 8080, where /__proxy/upload may return frontend HTML depending on the active local setup.

Review needed:
Lucia review is required before merge. Director decision is only required if Lucia wants to promote this into a release/readiness gate.
```
