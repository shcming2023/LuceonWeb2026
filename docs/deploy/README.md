# Deployment Documentation Index

Last updated: 2026-05-16

## Current Truth

- `PRODUCTION_RUNTIME_OWNERSHIP.md` is the current local production-line ownership and endpoint contract.
- `DEPLOY.md` is the Docker deployment guide. Its current sections describe the Phase 1 local MinerU + MinIO + Ollama path; older online-MinerU notes inside it are compatibility or historical notes only.

## Historical Or Proposed Notes

- `HOME_MAC_MINI.md` records Home Mac mini staging/prod layout notes and should not override `AGENTS.md` workspace anchors unless a newer task explicitly promotes it.
- Archived workflow prompts and historical governance files live under `archive/`.

## Safety Boundary

Deployment documentation does not authorize production sync, rebuild, restart, rollback, Docker volume mutation, DB edits, MinIO object deletion, secret changes, model/provider changes, validation uploads, or release-readiness claims. Those actions require explicit user authorization or a future documented governance process.
