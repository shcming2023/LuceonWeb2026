# lutest Handoff

Last updated: 2026-05-06

## Identity

`lutest` is retired. It is retained only as a historical role name for earlier Tier 2 validation evidence.

## Current Routing

Do not route new validation work to `lutest`.

Current validation ownership:

- L1/L2/UAT and local real runtime validation: `luceonhmm`
- Project ledger and PRD fact promotion: `luplan`
- Validation criteria and final judgment: `lucia`

## Historical Boundary

Older `lutest` reports may mention the retired online MinerU Standard line. That material is historical context only. It must not override the current Phase 1 mainline recorded in `docs/codex/PROJECT_STATE.md`.

Current mainline:

- local conda MinerU
- Docker MinIO
- host Ollama `qwen3.5:9b`
- strict AI no-skeleton configuration

## Use Rule

If historical `lutest` evidence is inspected, promote only confirmed and currently relevant facts into `docs/codex/PROJECT_STATE.md` or `docs/codex/TEST_POLICY.md`. Do not promote partial historical evidence into PASS.
