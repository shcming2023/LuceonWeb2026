# Environment Matrix

Last updated: 2026-05-06

This matrix records environments that can run Luceon2026. Validation evidence must state the machine, path, commit, compose files, runtime URL, and dependency mode.

## Active Development Workspace

- Role: current repository governance and development workspace
- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `main`
- Remote source: GitHub `origin/main`
- Package manager: `npx pnpm@10.4.1`
- Main validation URL used in this governance pass: `http://localhost:8081/cms/tasks`

Runtime baseline:

- Docker Compose frontend, upload server, DB server, MinIO
- Host local conda MinerU FastAPI, default container endpoint `http://host.docker.internal:8083`
- Host Ollama, default container endpoint `http://host.docker.internal:11434`
- Required model: `qwen3.5:9b`
- Strict AI mode: `DISABLE_AI_SKELETON_FALLBACK=true`, `ALLOW_AI_SKELETON_FALLBACK=false`
- Storage backend: `minio`

Known risks:

- The workspace is OneDrive-backed; GitHub remains the durable sync source.
- Local runtime state can retain prior UAT jobs. Full-chain UAT should either start from a drained AI queue or use the updated pipeline wait windows.

## Staging Workspace

- Role: staging / production-like validation
- Path: `/Users/concm/staging/Luceon2026`
- Runtime URL previously recorded for L3 evidence: `http://127.0.0.1:18081/cms/tasks`
- Compose project previously recorded: `luceon2026-staging`

Boundary:

- Staging PASS evidence is distinct from production release readiness.
- Staging records must include exact HEAD, compose files, task/material IDs, MinIO evidence, AI provider/model, and dependency health.

## Production Workspace

- Role: production deployment and validation target
- Path: `/Users/concm/prod_workspace/Luceon2026`

Boundary:

- Production release readiness is not claimed by the 2026-05-06 repository governance pass.
- Production validation must include backup/rollback procedure evidence before release approval.

## Compatibility-Only Online MinerU

- Online MinerU v4 is retained only for explicitly assigned compatibility validation.
- Missing online MinerU credentials must not block the current local real runtime main gate.
- Strict AI no-skeleton flags must not implicitly switch MinerU from local mode to online mode.

## Reporting Rule

Every L2, L3, or release-readiness report must include:

- machine name or role
- OS
- repository path
- commit hash
- Docker/Compose status
- compose files
- runtime URL
- MinerU endpoint mode
- Ollama endpoint and model
- MinIO bucket/object evidence
- validation command list and exit codes
- scope limits and remaining risks
