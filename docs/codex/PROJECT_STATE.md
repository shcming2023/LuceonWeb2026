# Luceon2026 Project State

Last updated: 2026-05-03

## Current Migration Decision

The project is moving from multi-computer local Codex development to a single primary Codex environment on the Home Mac mini.

Current Windows working copy:

- Path: `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`
- Branch: `main`
- Current local HEAD before this documentation handoff: `d8ef152 fix(uat): add minio fallback evidence check for artifact quality in standard smoke`
- Local branch status before this documentation handoff: ahead of `origin/main` by 10 commits

Target Mac mini mode:

- Codex threads live on the Mac mini.
- Work computers connect by remote desktop.
- GitHub remains the durable source for code and project memory.
- Dev, staging, and production directories are separated on the Mac mini.

## Current Engineering Focus

The current active engineering focus is Tier 2 Standard validation:

- MinerU: real MinerU v4 online API through `MINERU_ONLINE_API_BASE_URL=https://mineru.net/api/v4`
- Token: `MINERU_ONLINE_API_TOKEN`, process env only, never committed
- Model version: `MINERU_ONLINE_MODEL_VERSION=vlm`
- Ollama: local Docker container reachable as `http://cms-ollama-local:11434`
- Ollama model: `qwen3.5:0.8b`
- Skeleton fallback: must remain disabled for Standard validation

Recent commits leading to current state:

```text
d8ef152 fix(uat): add minio fallback evidence check for artifact quality in standard smoke
bcf3de2 fix(uat): increase smoke poll window to 12m and fix pre-check hang
ee932a4 fix(uat): increase ollama timeout and provide text-rich pdf fixture
4ada517 fix(uat): resolve ollama container network and provide valid pdf for standard smoke test
3e3064f feat(mineru): implement v4 online API adapter for Tier 2 Standard
20d0c90 feat(uat): implement tier 2 standard with real MinerU & Ollama configuration
13610d1 docs(prd): record tier2 standard online mineru decision
76fca4b test(uat): add markdown upload regression smoke test
aa2667d docs(prd): record local tier2 uat baseline
328c975 fix(uat): auto-init minio buckets, fix mineru mock health, and allow primitive JSON payloads
```

## Last Known Tier 2 Evidence

At commit `bcf3de2`, lutest reported:

- `npm.cmd run tier2:standard:check`: green exit, exit `0`, about `2.7s`
- `node server/tests/tier2-standard-smoke.mjs`: exit `1`, about `576.69s`
- MinerU v4 returned a real `batch_id`
- `full_zip_url` existed
- MinIO contained `full.md`, `mineru-result.json`, `mineru-result.zip`, `artifact-manifest.json`, and content-list artifacts
- AI completed with provider `ollama`, model `qwen3.5:0.8b`
- `aiClassificationProvider=ollama`, not `skeleton`
- Consistency audit was `ok=true` with one existing orphan-object warning

At commit `d8ef152`, Lucia approved code review for a smoke fallback fix that accepts real parsed artifact evidence from `full.md` when `metadata.artifactQuality` is missing. The final lutest smoke result for `d8ef152` was still pending in the captured handoff.

## Current Blocker

Tier 2 Standard is close to green, but the latest captured state does not yet contain a completed final lutest report for `d8ef152`.

The next validation step is:

```powershell
$env:MINERU_ONLINE_API_BASE_URL="https://mineru.net/api/v4"
$env:MINERU_ONLINE_API_TOKEN="<real token, redacted in reports>"
$env:MINERU_ONLINE_MODEL_VERSION="vlm"
docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml up -d --build --force-recreate
npm.cmd run tier2:standard:check
node server/tests/tier2-standard-smoke.mjs
```

Required evidence:

- both commands exit `0`
- smoke total duration
- MinerU `batch_id`
- MinerU `full_zip_url`
- `full.md` size
- AI provider, model, and duration
- `aiClassificationProvider` is real and not `skeleton`
- consistency audit status
- Director manual browser verification status

## Immediate Mac Mini Migration Tasks

1. Push the current branch to GitHub after review.
2. Clone the repository on the Home Mac mini into `~/dev/Luceon2026`.
3. Install and sign in to Codex on the Mac mini.
4. Create or reopen `lucia`, `luplan`, and `luceonhmm` threads on the Mac mini.
5. Read `AGENTS.md` and `docs/codex/roles/*.md` in each thread.
6. Re-run L1 on Mac mini.
7. Re-run Tier 2 Standard on Mac mini or staging.
8. Archive `lutest` after its Tier 2 knowledge is transferred into `luceonhmm`.
