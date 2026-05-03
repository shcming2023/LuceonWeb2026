# Luceon2026 Task Brief Template

Last updated: 2026-05-03

Use this template when Lucia assigns work to `lucode`, `luceonhmm`, or `luplan`. The task brief is the execution contract. Do not broaden work beyond the signed scope.

Luceon2026 uses Lucia-centered coordination. Autonomous task queues are not active. Execution agents must receive a Lucia task brief, execute only the signed scope, and report back to Lucia using the corresponding report format. They do not automatically write task results into a queue or durable project facts.

Only facts confirmed by Lucia or Director may be promoted by `luplan` into `docs/codex/PROJECT_STATE.md`, `docs/codex/HANDOFF.md`, PRD, changelog, role handoffs, or durable project memory.

## lucode Implementation Task

```text
Task:

Assignee:
lucode

Workspace:
/workspace/ops/Luceon2026

Host/IDE working copy reference:
D:\Users\moonp\OneDrive\Mac\项目开发\Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

Task issued by:
Lucia

Background:

Current known facts:

PRD / contract reference:
docs/prd/Luceon2026-PRD-v0.4.md

Problem to fix:

Goal:

Non-goals:

Allowed files or modules:

Forbidden changes:
- Do not start implementation from vague oral instructions or self-created tasks.
- Do not perform broad rewrites or disaster-prone refactors.
- Do not change unrelated files.
- Do not edit PRD facts, project-state facts, role contracts, or release judgments unless the task explicitly says so.
- Do not commit secrets, tokens, local private credentials, or machine-only artifacts.
- Do not claim UAT, L2, L3, production, or real-environment validation without luceonhmm evidence.
- Do not run destructive data, MinIO, DB, Docker volume, or production cleanup commands.

Suggested repair direction:

Required local checks:

GitHub sync requirements:
- Before starting: cd /workspace/ops/Luceon2026; git status --short --branch; git fetch origin; git pull --ff-only origin main.
- Before reporting: git status --short --branch; git log -1 --oneline.
- Push the branch or commit to GitHub when the task requires remote review.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- branch and HEAD
- files changed
- summary of implementation
- commands run and exit codes
- skipped checks and reasons
- risks or blockers
- whether any remaining validation must be routed to luceonhmm
```

## luceonhmm Validation Task

```text
Task:

Assignee:
luceonhmm

Target path:
/Users/concm/prod_workspace/Luceon2026

Background:

Exact validation target:

Environment prerequisites:

Task issued by:
Lucia

Allowed operations:

Forbidden operations:
- Do not write business implementation code.
- Do not modify PRD or project facts unless explicitly assigned.
- Do not use Lite mock, skeleton fallback, or partial checks as Tier 2 Standard or L3 proof.
- Do not report unjudged evidence as final PASS; report evidence or PASS_CANDIDATE for Lucia judgment.
- Do not echo full secrets or tokens.
- Do not run docker compose down -v, delete Docker volumes, wipe MinIO, wipe DB data, or clean staging/production data without explicit Director approval.

Commands or manual checks:

Required evidence:
- confirmation that work was based on this Lucia task brief
- machine and OS
- cwd, branch, HEAD, dirty state
- deployment mode
- command exit codes and durations
- service health
- original error text if failed
- API/log evidence
- task/material/batch/object identifiers when applicable
- MinIO/object-storage evidence
- DB or consistency-audit evidence
- real MinerU status
- real Ollama status and effective model
- skeleton fallback status
- Director browser verification state when required

Completion report status:
PASS_CANDIDATE | FAIL | BLOCKED | PENDING | INCONCLUSIVE
```

## luplan Documentation Task

```text
Task:

Assignee:
luplan

Background:

Source documents to read:

Task issued by:
Lucia

Facts to promote:

Facts to keep pending:

Files allowed to edit:

Forbidden changes:
- Do not edit business implementation code.
- Do not treat failed or pending validation as passed.
- Do not promote unreviewed reports, pending validation, or compatibility-only results as confirmed project facts.
- Do not create a competing current PRD.
- Do not write secrets or tokens.
- Do not edit .agents/** unless Director explicitly authorizes it.

Required output:
- confirmation that work was based on this Lucia task brief
- files changed
- confirmed requirements promoted
- pending strategies left unpromoted
- evidence source
- impact on lucia, lucode, or luceonhmm
```
