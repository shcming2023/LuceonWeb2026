# Task Brief: P1 Release Readiness Final Refresh After MinerU Recovery And Helper Sync

- Task ID: `TASK-20260515-121739-P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync`
- Created: 2026-05-15T12:17:39+0800
- Created by: Director
- Assigned role: `Architect`
- Expected report: `TaskAndReport/2026-05-15T12-17-39+0800_P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync_REPORT.md`
- Based on prior Architect consolidation: `TaskAndReport/2026-05-15T08-46-31+0800_P1-Release-Readiness-Consolidation-And-Gap-Refresh_REPORT.md`
- Based on Director review: `TaskAndReport/2026-05-15T12-17-39+0800_P1-No-Submit-Helper-Production-Source-Sync-And-Read-Only-Verification_DIRECTOR_REVIEW.md`

## Context

The previous Architect release-readiness consolidation was not a go decision. It identified specific blockers:

- production source drift / override boundary;
- dependency-health timing semantics;
- known AI residual disposition;
- incomplete rollback/recovery and error-path evidence.

Since then, the project has recorded and accepted additional evidence:

- source-drift and production-local override boundary classified;
- dependency-health timing semantics implemented, deployed, and read-only verified;
- user accepted known `failed/ai` pressure residuals as visible manual retry candidates for this readiness track;
- rollback/error-path evidence pack found a critical MinerU submit-path blocker;
- MinerU submit path was recovered through scoped MinerU-only recovery and exactly one authorized submit-probe;
- runtime ownership helper was hardened so read-only status checks no longer run submit-probe by default;
- production workspace received the no-submit helper/docs sync and read-only verification.

Director needs an updated architecture-level recommendation before asking the user for any release-boundary decision.

## Required Reading

Before acting, read:

1. `AGENTS.md`
2. `docs/codex/TEAM_CONTRACT.md`
3. `docs/codex/roles/architect.md`
4. `docs/codex/PROJECT_STATE.md`
5. `docs/codex/HANDOFF.md`
6. `docs/prd/Luceon2026-PRD-v0.4.md`
7. `docs/codex/TEST_POLICY.md`
8. `docs/codex/REPOSITORY_STRUCTURE.md`
9. `TaskAndReport/README.md`
10. `TaskAndReport/TASK_TRACKING_LIST.md`
11. Task 162 report and Director review
12. Task 163 report and Director review
13. Tasks 164-166 reports/reviews
14. Task 167 decision
15. Tasks 168, 170, 171, 173, 174, and 176 reports/reviews
16. This task brief

If the task row, role file, or required evidence files are missing locally, stop and report `本地任务列表或角色文档未更新/疑似不同步`.

## Objective

Produce a read-only final refresh of release-readiness architecture status after MinerU recovery and no-submit helper sync.

Recommend exactly one of:

- `READY_FOR_USER_RELEASE_DECISION`
- `CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS`
- `NO_GO`

The recommendation must be evidence-grounded and must not declare production readiness, L3, pressure PASS, production上线, release approval, or go-live approval. Only Director and User can make those decisions.

## Required Analysis

Address:

1. Whether the previous Task 162 blockers are now closed, mitigated, or still open.
2. Whether current evidence supports moving to a user release-boundary decision.
3. Which residuals remain:
   - historical `failed/ai` tasks;
   - production-local dirty files;
   - no new PDF upload after MinerU recovery;
   - local single-machine dependency ownership risks;
   - any remaining rollback/recovery or error-path evidence gaps.
4. Whether further read-only TestAcceptanceEngineer evidence is needed before a user decision.
5. What exact scope, limitations, and no-go boundaries should be presented to the user if Architect recommends a user decision.

## Allowed Operations

Allowed:

- read repository docs, task reports, reviews, and source files;
- inspect development git status;
- inspect production git status and read-only runtime health/status if needed;
- run no-submit/read-only helper default only if useful;
- run read-only HTTP GETs for health/status endpoints only.

## Forbidden Operations

Forbidden:

- submit-probe, `mineruSubmitProbe=true`, `--submit-probe`, or `RUN_MINERU_SUBMIT_PROBE=1`;
- upload, pressure/batch/soak/fresh serial validation, validation artifact creation;
- production deployment, source sync, pull/fast-forward, rebuild, rollback, Docker Compose, service restart, MinerU/Ollama/supervisor/sidecar mutation;
- DB/MinIO/Docker volume/data mutation, restore/import, cleanup, cancel, repair, retry, reparse, re-AI, takeover, automatic retry/requeue;
- settings, secrets, config, model, sample-library mutation;
- PRD truth, role contract, project state, or handoff changes;
- skeleton fallback weakening or silent degradation;
- declaring pressure PASS, L3, release-readiness, production-readiness, production上线, or go-live readiness.

## Required Report Structure

The report must include:

1. **Recommendation**
   - exactly one of the three allowed recommendation labels.

2. **Blocker Refresh**
   - each Task 162 blocker and current status.

3. **Evidence Matrix**
   - key accepted tasks and what each proves;
   - what each does not prove.

4. **Residual Risk**
   - list residuals by severity and whether they block a user decision.

5. **Recommended Next Actor**
   - Director with a suggested next action:
     - ask User for release-boundary decision;
     - issue TestAcceptanceEngineer read-only check;
     - issue further DevelopmentEngineer/Architect task;
     - or hold.

6. **Forbidden Operations Confirmation**

## Completion

Write:

`TaskAndReport/2026-05-15T12-17-39+0800_P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync_REPORT.md`

Update row 177 in `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status: `已回报待 Director 审查` or a precise blocked status;
- Next Actor: `Director`;
- Report path populated;
- Notes include recommendation label and key residuals.

## GitHub Sync

Do not fetch, pull, push, merge, or create commits unless Director explicitly instructs you. Work in the current synchronized workspace. Director will review and handle GitHub synchronization.
