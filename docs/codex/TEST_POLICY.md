# Luceon2026 Validation Policy

Last updated: 2026-05-03

## Validation Levels

### L1: Fast Code Gate

Owner in the target model: `lucia`

Purpose: determine whether the code is obviously broken before deeper environment validation.

Typical commands:

```bash
npx tsc --noEmit
npm run build
npm run local:check
npm run test:smoke
```

L1 must not be reported as Tier 2 Standard or production validation.

### L2: Tier 2 Near-Production Validation

Current owner: `lutest`

Target owner after Mac mini migration: `luceonhmm`

Purpose: validate real integration behavior in a near-production local or staging environment.

Current Standard target:

- real MinerU v4 online API
- local Docker Ollama
- model `qwen3.5:0.8b`
- `aiClassificationProvider` must not be `skeleton`
- parsed artifact evidence must be non-empty

Standard command set:

```powershell
$env:MINERU_ONLINE_API_BASE_URL="https://mineru.net/api/v4"
$env:MINERU_ONLINE_API_TOKEN="<real token, redacted in reports>"
$env:MINERU_ONLINE_MODEL_VERSION="vlm"
docker compose -f docker-compose.yml -f docker-compose.tier2-standard.yml -f docker-compose.override.yml up -d --build --force-recreate
npm.cmd run tier2:standard:check
node server/tests/tier2-standard-smoke.mjs
```

Required report fields:

- machine and OS
- commit hash
- command list and exit codes
- Docker/compose status
- dependency-health result
- MinerU `batch_id`
- MinerU `full_zip_url`
- parsed artifact evidence, including `full.md` or content-list evidence
- AI job id
- AI provider and model
- AI duration
- `aiClassificationProvider`
- whether skeleton fallback was used
- consistency audit result
- Director browser verification state

### L3: Home Mac Mini Production Truth

Target owner: `luceonhmm`

Purpose: validate the actual staging or production environment on the Home Mac mini.

Only L3 can be treated as production truth. L1 and L2 can support a release decision, but they do not replace L3.

## Result Vocabulary

Use these words exactly in reports:

- `PASS`: command or validation target completed and met the stated criteria.
- `FAIL`: command or validation target ran and violated the criteria.
- `BLOCKED`: required environment, credential, service, or input was missing.
- `SKIPPED`: intentionally not run, with reason.
- `PENDING`: started but not completed by the handoff point.

Do not use "passed" for a check that did not return a green exit code.

## Secret Handling

MinerU tokens and other secrets must only be injected through local process environment or local uncommitted secret management.

Reports may say:

```text
MINERU_ONLINE_API_TOKEN=<present, redacted>
```

Reports must not include the full token.

## Destructive Operations

These require explicit Director approval:

- `docker compose down -v`
- deleting Docker volumes
- clearing MinIO buckets
- clearing DB data
- deleting production or staging deployment data
- changing production secrets

Rebuilding containers with `up -d --build --force-recreate` is allowed for L2 when the task explicitly asks for it, as long as volumes are not wiped.
