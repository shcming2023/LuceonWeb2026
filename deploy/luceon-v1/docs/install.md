# LuceonWeb2026 v1 arm64 install

This package deploys LuceonWeb without MinerU, Popo, or a GPU wrapper container. The wrapper URL is retained only for a later GPU task.

1. Copy this public package and the private state package to the target Apple Silicon Mac.
2. Verify `checksums.sha256` and restore `private/skills`, `state/backend/mineru.db`, `state/backend/runtime_config.json`, and `.env.production` with mode `0600`.
3. Run `./scripts/preflight`, `./scripts/pull-or-load`, `./scripts/migrate`, `./scripts/start`, and `./scripts/verify` in that order.
4. Start only one Workflow V2 worker against the production database. Stop the staging worker first if both environments share Workflow MySQL or MinIO.

The production Compose file contains only immutable `repository@sha256` image references and must never be rebuilt on the target host.
