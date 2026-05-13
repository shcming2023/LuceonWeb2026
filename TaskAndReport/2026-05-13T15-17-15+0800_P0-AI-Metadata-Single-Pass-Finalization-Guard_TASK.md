# Task: P0 AI Metadata Single Pass Finalization Guard

Assignee:
DevelopmentEngineer

Issued by:
Director

Issued at:
2026-05-13T15:17:15+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_TASK.md

Expected report:
TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_REPORT.md

## Required Reading Before Execution

- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/development-engineer.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/prd/Luceon2026-PRD-v0.4.md
- docs/codex/TEST_POLICY.md
- docs/codex/TEST_MATRIX.md
- docs/codex/REPOSITORY_STRUCTURE.md
- TaskAndReport/README.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_TASK.md
- TaskAndReport/2026-05-13T14-46-20+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_REPORT.md
- TaskAndReport/2026-05-13T15-17-15+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Task-87-Deployment_DIRECTOR_REVIEW.md

## Background

Task 90 executed exactly one controlled upload after Task 87 deployment.

Observed facts:

- task `task-1778655375028`;
- material `validation-postfix-1778655374`;
- AI job `ai-job-1778655391785-6d94`;
- MinerU completed and stored 21 parsed artifacts;
- previous 30-second `UND_ERR_HEADERS_TIMEOUT` did not recur;
- events show one Ollama response success and one JSON repair success;
- task metadata contains `aiClassificationProvider=ollama`, `aiClassificationRepairSucceeded=true`, `aiClassificationV02`, and review metadata;
- the same AI job later started another Ollama pass and ended in JSON repair failure;
- final task/material/AI job state is failed.

Director quick code inspection found a plausible duplicate-processing path in `server/services/ai/metadata-worker.mjs`: `scanAndProcess()` can process a pending job from `postRecoveryJobs`, then continue to process pending jobs from the stale pre-recovery `jobs` snapshot. This may allow the same job to be processed twice in one scan cycle after the first pass reaches a terminal state. You must verify the root cause independently before implementing.

## Objective

Fix the AI metadata worker so a single AI metadata job cannot be processed twice after it reaches a terminal state, and so successful AI finalization cannot be overwritten by a later duplicate run failure.

## Scope

Allowed code areas:

- `server/services/ai/metadata-worker.mjs`
- focused tests under `server/tests/`
- minimal supporting test fixtures/helpers if needed
- task report and tracking list

You may touch another file only if strictly necessary and must explain why in the report.

## Expected Technical Direction

Independently inspect and implement the smallest robust fix. Candidate changes include:

- make `scanAndProcess()` process at most one job per tick and return immediately after processing a recovered/pending job;
- avoid using a stale `jobs` snapshot after processing `postRecoveryJobs`;
- add a start-of-`processJob()` guard that re-reads the latest job state and skips terminal or non-pending jobs;
- ensure terminal states such as `confirmed`, `review-pending`, `failed`, and `skipped-canceled` cannot be reprocessed by a later scan;
- preserve strict no-skeleton behavior and do not convert real AI failures into successful skeleton results.

Do not blindly implement all candidates if a narrower fix is enough. Explain the chosen boundary.

## Required Tests / Checks

Add or update focused regression coverage proving that a pending AI job is not processed twice in a single scan cycle, especially when `postRecoveryJobs` and the original pre-recovery `jobs` snapshot both contain the same pending job.

Run at minimum:

```bash
git diff --check
node --check server/services/ai/metadata-worker.mjs
node <focused regression test>
node server/tests/ai-metadata-real-sample-smoke.mjs
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If any check is skipped, report the exact reason.

## Non-Goals And Hard Limits

- Do not perform production deployment.
- Do not run a validation upload.
- Do not repair, retry, reparse, re-AI, delete, or clean up `task-1778655375028`, `task-1778651226016`, or any historical task.
- Do not mutate DB rows, MinIO objects, Docker volumes, model files, secrets, production overrides, or sample files.
- Do not change prompts, taxonomy, PRD truth, role contracts, release judgments, or public API unless absolutely necessary for the focused bug and explicitly justified.
- Do not weaken strict no-skeleton behavior.
- Do not claim production readiness, L3, pressure PASS, or release-readiness.

## Required Report

Write:

`TaskAndReport/2026-05-13T15-17-15+0800_P0-AI-Metadata-Single-Pass-Finalization-Guard_REPORT.md`

The report must include:

- root cause found;
- files changed;
- implementation summary;
- why strict no-skeleton is preserved;
- commands run and exit codes;
- skipped checks and reasons;
- residual risk;
- whether Director should authorize production deployment/runtime validation after review.

Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch/HEAD, status, next actor `Director`, and required output.

Commit and push only this scoped implementation/report if possible.

## Acceptance Criteria

- The duplicate-processing or terminal-overwrite path is fixed at code level.
- A focused regression test would fail before the fix and pass after the fix, or the report explains the closest achievable focused evidence.
- Existing AI metadata and dependency-health smoke checks still pass.
- No production/data/sample/model mutation or validation upload occurs.
