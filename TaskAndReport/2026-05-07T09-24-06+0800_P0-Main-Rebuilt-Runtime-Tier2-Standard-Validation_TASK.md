# Task: P0 Main Rebuilt-Runtime Tier2 Standard Validation

```text
Task:
P0 Main Rebuilt-Runtime Tier2 Standard Validation

Assignee:
Lucode

Issued by:
Lucia

Project:
Luceon2026

Date:
2026-05-07

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-07T09-24-06+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/codex/TEST_POLICY.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md

Background:
P0 MinerU Submit-Path Health Probe has been accepted by Lucia and merged into GitHub `main`.
The project ledger now marks TD-001 as closed at the code and documentation level.
Before any release-readiness or Standard-readiness statement is made from this change, the merged `main` must be validated in a rebuilt local runtime.

Current known facts:
- Current `main` HEAD at task issue time: `9a4f1e99dd1dc5af8d8779dd6e02ceec0f09d112`.
- MinerU submit-path implementation commit: `5b21ae3392a4f334b02e0ac2d75f616d4286fdfb`.
- Merge commit: `8201d2e903d5fa524490c17d16258f1764ce98fe`.
- Project ledger closure commit: `cc9dde211da79a017ccb23806cf4238b5cd54698`.
- Task ledger finalization commit: `9a4f1e99dd1dc5af8d8779dd6e02ceec0f09d112`.
- Standard dependency-health must verify both `dependencies.mineru.healthOk=true` and `dependencies.mineru.submitProbe.ok=true`.

Objective:
Validate the merged `main` in a rebuilt runtime and prove that Tier 2 Standard now exercises the MinerU submit path, not only MinerU `/health`.

Non-goals:
- Do not implement new code.
- Do not change PRD truth, PROJECT_STATE, HANDOFF, role contracts, or release judgments.
- Do not claim production release readiness.
- Do not perform destructive data, DB, MinIO, Docker volume, or production cleanup.

Required steps:
1. Sync the development workspace to GitHub `main`.
2. Confirm `HEAD` equals or is fast-forwarded to `9a4f1e99dd1dc5af8d8779dd6e02ceec0f09d112` or a newer Director/Lucia-approved `origin/main`.
3. Rebuild or restart the local runtime sufficiently for the merged `upload-server` code to be active.
4. Confirm dependency-health exposes:
   - `dependencies.mineru.healthOk`
   - `dependencies.mineru.submitProbe.enabled`
   - `dependencies.mineru.submitProbe.ok`
   - `dependencies.mineru.submitProbe.taskId` when successful
5. Run Tier 2 Standard with the merged runtime.
6. Run core smoke validation if the local runtime is reachable.
7. Write a completion report into `TaskAndReport/`.
8. Update `TaskAndReport/TASK_TRACKING_LIST.md` with status, report path, HEAD, and evidence summary.

Required commands:
- `git status --short --branch`
- `git fetch origin`
- `git pull --ff-only origin main`
- `node server/tests/dependency-health-smoke.mjs`
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `npx pnpm@10.4.1 run tier2:standard:check`
- `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh`, if the rebuilt local runtime is reachable at `localhost:8081`

Required evidence:
- Exact `main` HEAD validated.
- Runtime URL used.
- Whether runtime was rebuilt or restarted, with command and exit code.
- Dependency-health MinerU fields, including `healthOk` and `submitProbe`.
- Tier 2 Standard exit code and relevant output summary.
- UAT smoke result or exact reason it was skipped.
- Any blocker must include exact error text and whether it is code, environment, or configuration.

Forbidden operations:
- Do not run `docker compose down -v`.
- Do not remove MinIO buckets, DB files, volumes, or production data.
- Do not force-push `main`.
- Do not modify implementation files unless Lucia issues a separate repair task.
- Do not silently pass if `mineru.submitProbe.ok` is missing or false.

Completion report storage requirements:
- Write the completion report into TaskAndReport/ using this naming rule:
  YYYY-MM-DDTHH-MM-SS+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_REPORT.md
- Update TaskAndReport/TASK_TRACKING_LIST.md with report path, branch, HEAD, and current status.

Completion report must include:
- confirmation that work was based on this Lucia task brief
- branch and HEAD
- commands run and exit codes
- dependency-health MinerU submit-probe evidence
- Tier 2 Standard result
- smoke/UAT result or skipped reason
- blockers, risks, or residual technical debt
- whether Lucia review is required

Acceptance criteria:
- Validated `main` contains the MinerU submit-path probe implementation.
- `node server/tests/dependency-health-smoke.mjs`, TypeScript check, and build pass.
- Tier 2 Standard either passes with `mineru.submitProbe.ok=true`, or fails with a precise blocker that Lucia can route.
- No release-readiness claim is made without explicit Lucia acceptance.
```
