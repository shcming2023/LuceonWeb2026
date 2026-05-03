# lutest Handoff

Last updated: 2026-05-03

## Identity

lutest is the archived Luceon2026 legacy Tier 2 validation analyst role.

lutest is not an implementation role and not a PRD role. It is retained only as a historical evidence and knowledge-transfer file.

## Current Lifecycle Status

lutest is retired.

The original purpose of lutest was to handle the differences between work computers, local Docker setups, MinIO, MinerU, and Ollama. The project has moved to a Home Mac mini centered workflow. Active UAT, L2, L3, real-environment validation, and dependency debugging duties now belong to `luceonhmm`.

Do not route new validation work to lutest unless Director explicitly asks to inspect historical Tier 2 evidence.

## Boundaries

lutest must not:

- write implementation code
- edit PRD or changelog
- make final release judgments
- use mock MinerU as Standard evidence
- use skeleton fallback as Standard evidence
- hide failed command exit codes
- write or echo full tokens
- wipe volumes, MinIO, DB, or production data

lutest history can be used to:

- understand prior Tier 2 failures and partial evidence
- compare old Windows/local validation behavior with current `luceonhmm` evidence
- preserve command, artifact, and report expectations for the Tier 2 Standard chain

## Historical Tier 2 Standard Target

Environment:

- MinerU online API base: `https://mineru.net/api/v4`
- MinerU token: injected as `MINERU_ONLINE_API_TOKEN`, redacted in reports
- model version: `vlm`
- Ollama container: `cms-ollama-local`
- Ollama model: `qwen3.5:0.8b`
- skeleton fallback: disabled

Commands:

```powershell
$env:MINERU_ONLINE_API_BASE_URL="https://mineru.net/api/v4"
$env:MINERU_ONLINE_API_TOKEN="<real token, redacted in reports>"
$env:MINERU_ONLINE_MODEL_VERSION="vlm"
docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml up -d --build --force-recreate
npm.cmd run tier2:standard:check
node server/tests/tier2-standard-smoke.mjs
```

## Last Captured Timeline

1. Earlier attempts were blocked because the MinerU online env values were missing.
2. MinerU v4 adapter work landed through commits `3e3064f` and following fixes.
3. `4ada517` fixed Ollama container network and test PDF suitability.
4. `ee932a4` showed the real chain could complete, but automation windows and pre-check behavior were not yet green.
5. `bcf3de2` fixed the pre-check hang and expanded smoke wait time. lutest then reported:
   - pre-check green
   - real MinerU artifacts present
   - AI completed with `ollama/qwen3.5:0.8b`
   - smoke still exit `1` because it relied on missing `metadata.artifactQuality`
6. `d8ef152` added fallback evidence checking for real parsed artifacts such as `full.md`.
7. The final captured lutest state for `d8ef152` was `PENDING`: stack rebuilt, pre-check green in about `1.74s`, smoke running.

## Historical Final Report Shape

Historical task name:

```text
P1-tier2-standard-smoke-green-final-uat
```

Required report fields:

- commit hash
- machine and OS
- Docker status
- env presence, with token redacted
- `tier2:standard:check` exit code and duration
- `tier2-standard-smoke` exit code and duration
- MinerU `batch_id`
- MinerU `full_zip_url`
- parsed artifact evidence, especially `full.md` size
- `artifact-manifest.json` summary if available
- AI job id
- AI provider
- AI model
- AI duration
- `aiClassificationProvider`
- skeleton status
- consistency audit status
- Director browser manual verification state

## Retirement Checklist

Retirement status:

1. Tier 2 knowledge has been copied into `docs/codex/roles/luceonhmm.md`.
2. `docs/codex/TEST_POLICY.md` names `luceonhmm` as the current L2 owner.
3. `docs/codex/PROJECT_STATE.md` marks lutest as retired legacy history.
4. Keep this file as archived historical context; do not delete it.
