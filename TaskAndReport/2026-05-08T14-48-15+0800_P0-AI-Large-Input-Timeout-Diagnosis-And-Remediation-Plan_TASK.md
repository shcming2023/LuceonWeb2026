# P0 AI Large-Input Timeout Diagnosis And Remediation Plan

Task:
P0 AI Large-Input Timeout Diagnosis And Remediation Plan

Task ID:
`TASK-20260508-144815-P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T14:48:15+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T14-48-15+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `TaskAndReport/2026-05-08T14-44-54+0800_P0-Large-PDF-Soak-Validation_REPORT.md`
- `TaskAndReport/2026-05-08T14-48-15+0800_P0-Large-PDF-Soak-Validation_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Large-PDF soak task `task-1778222027064` failed in the AI metadata stage. MinerU completed and MinIO artifacts were produced, but Ollama `qwen3.5:9b` timed out after about `300000ms` for a large parsed Markdown input. Strict no-skeleton fallback behaved correctly.

This blocks production release readiness under the current Phase 1 boundary.

## Objective

Produce a non-destructive diagnosis and remediation plan for large-input AI metadata timeout handling.

The plan must answer:

- Where the current AI metadata input is selected, sampled, truncated, sent, timed out, retried, and failed.
- Why the current truncation/sampling strategy still produces an input that times out for the large-PDF sample.
- Whether the issue is more likely prompt/input size, model capacity, timeout policy, retry policy, schema/repair behavior, or worker orchestration.
- What remediation options exist, with tradeoffs, risks, implementation scope, and validation plan.
- Which remediation Lucia should assign first.

## Required Code Areas To Inspect

- `server/services/ai/metadata-worker.mjs`
- AI provider modules under `server/services/ai/`
- AI metadata job/task event handling in `server/upload-server.mjs` and related services.
- Any timeout, truncation, sampling, deterministic repair, strict fallback, or schema validation helpers.
- Relevant tests under `server/tests/`.
- Relevant PRD/test-policy sections.

## Non-goals

- Do not modify production runtime.
- Do not delete validation artifacts.
- Do not change DB rows, MinIO objects, Docker volumes, tasks, artifacts, or secrets.
- Do not loosen strict no-skeleton semantics.
- Do not configure silent fallback.
- Do not implement code changes unless Lucia later issues a separate implementation task.
- Do not claim production release readiness.

## Required Checks

- `git status --short --branch`
- `git fetch origin`
- If local `main` is behind `origin/main` and clean, `git pull --ff-only origin main`
- Read task 29 report and Lucia review.
- Inspect relevant AI metadata code and tests.
- Run only non-destructive code/read-only checks needed for diagnosis.

Runtime checks are optional and must be read-only unless the report explains why a controlled runtime probe is necessary and within already authorized validation boundaries.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-AI-Large-Input-Timeout-Diagnosis-And-Remediation-Plan_REPORT.md`

The report must include:

- Root-cause hypothesis with evidence.
- Exact current timeout and truncation/sampling behavior.
- Whether existing tests cover this class of failure.
- Remediation options, at minimum:
  - tighter or structured large-input selection/sampling;
  - multi-pass/chunked metadata extraction;
  - timeout/retry policy changes;
  - model/runtime capacity options;
  - UI/operator-state wording if large documents remain bounded.
- Recommended first implementation task with scope and acceptance criteria.
- Required tests for the recommended implementation.
- Residual product/release-boundary decisions.
- Confirmation that no production mutation or release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.

## Acceptance Criteria

- The plan is specific enough for Lucia to issue an implementation task without additional discovery.
- Strict no-skeleton semantics remain preserved.
- Silent fallback is not proposed.
- Production release readiness remains unclaimed.
