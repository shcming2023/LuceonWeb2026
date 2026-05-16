# P0 Lucode External Workflow Detail Expansion Decision

- Timestamp: 2026-05-16T15:16:46+0800
- Decision owner: User
- Recorded by: Luceon

## Decision

The user requested a more detailed Lucode project rule set for the external IDE workspace.

Lucode works outside this Codex environment, usually at:

`/Users/caoming/Documents/Luceon2026`

Lucode responsibilities and strengths:

- product/requirement refinement;
- implementation;
- developer checks;
- product documentation maintenance;
- technical documentation maintenance;
- scoped branch creation;
- completion report writing;
- GitHub synchronization back to Luceon.

Lucode collaborates asynchronously with Luceon. Luceon works in a different workspace and owns architecture review, acceptance, production validation/deployment coordination, and readiness wording. Therefore Lucode reports must be written for cross-workspace review: clear diffs, scoped branch, exact evidence, and explicit risks.

## Repository Update

Add `docs/codex/LUCODE_EXTERNAL_WORKFLOW.md` as a copyable project-rule handoff for Lucode.

The document clarifies:

- GitHub-first sync;
- task-list-first `check task`;
- scoped branch naming;
- implementation boundaries;
- product/requirement refinement boundaries;
- developer checks;
- required completion report fields;
- task ledger update rules;
- final chat reply format.
- collaboration context with Luceon;
- how Lucode can write branches/reports/docs so Luceon can review efficiently.

## Boundary

This is a documentation/workflow update only. It does not authorize production mutation, deployment, validation upload, pressure test, submit-probe, DB/MinIO/Docker volume operation, model change, secret/config change, or readiness/go-live claim.
