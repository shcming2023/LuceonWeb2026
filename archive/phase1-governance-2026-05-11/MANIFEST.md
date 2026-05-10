# Phase 1 Medium-Risk Governance Archive Manifest

Archive date: 2026-05-11

## Scope

This archive stores historical `.agents/workflows/` prompts that were removed from active agent-rule locations during medium-risk repository governance.

No file was deleted in this archival pass.

## Source And Target

| Source file | Target file | Reason |
| --- | --- | --- |
| `.agents/workflows/team-roles.md` | `archive/phase1-governance-2026-05-11/agents-workflows/team-roles.md` | Retired four-agent role model conflicts with the current Director/Lucia/Lucode contract. |
| `.agents/workflows/luceon2026rules.md` | `archive/phase1-governance-2026-05-11/agents-workflows/luceon2026rules.md` | Old workspace paths and lucode-only rules are superseded by `AGENTS.md` and `docs/codex/roles/lucode.md`. |
| `.agents/workflows/luceonhmm-rules.md` | `archive/phase1-governance-2026-05-11/agents-workflows/luceonhmm-rules.md` | Production-ops authority model is historical and must not override current task/authorization boundaries. |

## Retention Rule

Archived workflow prompts are retained for audit trail only. Current facts and executable role instructions must be promoted into `AGENTS.md`, `docs/codex/TEAM_CONTRACT.md`, the active role files, or `TaskAndReport/` before use.
