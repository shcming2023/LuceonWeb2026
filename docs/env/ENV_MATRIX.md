# Environment Matrix

Last updated: 2026-05-03

This matrix records the environments that can run Luceon2026. Keep it updated whenever validation evidence is reported.

## Windows Work Computer

- Role: current transition development and Tier 2 validation environment
- Path: `D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026`
- Branch: `main`
- Notes:
  - This is an active OneDrive-backed working copy.
  - GitHub should be treated as the durable sync source.
  - Codex thread state is local to `C:\Users\moonp\.codex`.
  - Tier 2 Standard has been tested here with real MinerU v4 online and Docker Ollama.

Known services:

- Docker available
- MinIO through compose
- Ollama through compose as `cms-ollama-local`
- MinerU v4 online through external API

Known risks:

- OneDrive can create file-locking and sync-timing issues for active development.
- Windows Docker behavior may differ from the Home Mac mini.
- Local Codex threads do not automatically move with the repository.

## Home Mac Mini

- Role: target primary Codex host, staging validator, production host
- Path targets:
  - `~/dev/Luceon2026`
  - `~/staging/Luceon2026`
  - `/opt/luceon2026`
- Status: planned migration target

Required setup:

- Git
- Docker or Docker Desktop equivalent
- Node.js
- npm
- Codex
- Ollama, either compose-managed or host-managed with documented routing
- production secrets stored outside Git

First validation goal:

- clone from GitHub
- run L1
- run Tier 2 Standard
- create `luceonhmm` thread for staging, production validation, deployment, rollback, and evidence capture

## Reporting Rule

Every L2 or L3 report must include:

- machine name or role
- OS
- commit hash
- Docker/compose status
- env presence with secrets redacted
- validation level: L1, L2, or L3
