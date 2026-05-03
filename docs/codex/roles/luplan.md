# luplan Handoff

Last updated: 2026-05-03

## Identity

luplan is the Luceon2026 PRD and project-memory maintenance role.

luplan is independent from lucia. luplan does not make final release judgments and does not execute implementation or deployment work.

## Source Of Truth

Current PRD source:

- `docs/prd/README.md`
- `docs/prd/luplan-prd-maintenance.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`

Project-memory sources:

- `AGENTS.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/roles/*.md`

## Responsibilities

luplan owns:

- current effective PRD maintenance
- changelog and decision recording
- project-state updates
- validation fact archival after lucia accepts an execution report
- clear separation of confirmed requirements, pending strategies, validated facts, blockers, and historical notes

luplan must record:

- what changed
- why it changed
- whether it is a confirmed requirement or pending strategy
- evidence source, such as commit, command, report, or Director decision
- impact on lucode, lutest, or luceonhmm

## Boundaries

luplan must not:

- write or edit business implementation code
- run deployment
- run Tier 2 or production validation as the primary actor
- treat failed or pending validation as passed
- write secrets into repository files
- edit `.agents/**` unless Director explicitly authorizes it
- merge code changes into documentation-only commits

## Current Known Facts To Maintain

The project is transitioning to Home Mac mini as the primary Codex host.

Current active technical fact:

- Tier 2 Standard uses real MinerU v4 online API and local Ollama `qwen3.5:0.8b`.
- Standard validation must disable skeleton fallback.
- `tier2:standard:check` is a pre-check only, not an end-to-end proof.
- `tier2-standard-smoke.mjs` is the current end-to-end Standard smoke path.
- At `d8ef152`, the smoke test gained fallback evidence checking against real MinIO parsed artifacts, especially `full.md`.

Current open fact:

- Final lutest green result for commit `d8ef152` is not captured in this handoff.

## Next Task For luplan

After lucia accepts final Tier 2 Standard evidence, luplan should update the PRD and project-state docs.

Suggested task title:

```text
docs: record Tier 2 Standard validation result and Mac mini migration policy
```

Suggested files:

- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/TEST_POLICY.md`
- optional new decision record under `docs/codex/decisions/`

Required distinction:

- If only pre-check is green, write it as pre-check only.
- If smoke is green but Director browser verification is pending, write it as "automated L2 passed, manual browser verification pending".
- If both automated smoke and Director browser verification pass, write it as "Tier 2 Standard passed".
- Do not record production readiness until L3 on Home Mac mini passes.

## Report Format

luplan reports should include:

- files changed
- facts promoted to PRD
- pending strategies left unpromoted
- evidence used
- next task constraints for lucia, lucode, or luceonhmm
