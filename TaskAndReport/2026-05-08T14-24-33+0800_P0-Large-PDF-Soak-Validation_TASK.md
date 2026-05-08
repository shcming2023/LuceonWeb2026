# P0 Large-PDF Soak Validation

Task:
P0 Large-PDF Soak Validation

Task ID:
`TASK-20260508-142433-P0-Large-PDF-Soak-Validation`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T14:24:33+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T14-24-33+0800_P0-Large-PDF-Soak-Validation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T14-05-45+0800_P0-Release-Readiness-Runtime-Validation-Authorization_DECISION.md`
- `TaskAndReport/2026-05-08T14-24-33+0800_P0-Release-Readiness-Runtime-Validation-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Director authorized a staged release-readiness runtime-validation wave. Production release readiness is not claimed. The first authorized validation task is a controlled large-PDF soak against the current production runtime.

Current accepted runtime boundary includes:

- Phase 1 mainline: upload -> local MinerU -> MinIO -> Ollama `qwen3.5:9b` -> AI metadata -> operator review.
- Strict AI/model settings remain required.
- MinIO console is bound to `127.0.0.1:19001`.

## Objective

Run one controlled large-PDF soak validation through the production manual-review runtime and report exact evidence.

The validation should prove whether a large PDF can complete the Phase 1 chain to `review-pending` or fail explicitly with actionable evidence.

## Authorized Runtime Effects

This task may create controlled validation artifacts:

- One upload task.
- One parse task.
- MinIO source object and parsed artifacts for that task.
- AI metadata output or explicit AI failure record.
- Logs and status evidence.

These artifacts must be reported and preserved unless Director separately approves cleanup.

## Test File Selection

Lucode must identify a suitable large PDF before upload.

Preferred candidate:

- A previously used large sample such as `G7_Workbook_ready_to_print.pdf`, if locally available.

If the preferred candidate is not available, Lucode may use another locally available large PDF that is representative of Phase 1 educational-material ingestion.

The report must include:

- Absolute file path.
- File size.
- SHA-256 hash.
- Reason the file qualifies as large-PDF soak input.

If no suitable large PDF is available, do not substitute a small file. Write a blocked report.

## Required Pre-Checks

Development workspace:

- `git status --short --branch`
- `git fetch origin`
- If local `main` is behind `origin/main` and clean, `git pull --ff-only origin main`

Production runtime:

- Record production workspace `git status --short --branch`.
- Record production workspace `git log -1 --oneline`.
- Read production `docker-compose.override.yml` relevant lines and confirm:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- Confirm no active parse/AI work before starting.
- Confirm dependency health with `mineruSubmitProbe=true` is non-blocking.
- Confirm CMS manual-review URL is reachable.

## Execution Requirements

Use the production manual-review runtime at:

`http://localhost:8081/cms/`

Lucode may use the UI path if reliable. If browser automation is blocked, Lucode may use the production upload API only if the report clearly labels the path used and explains why UI validation was not possible.

Required monitoring:

- Record task ID.
- Poll task state and stage until terminal state.
- Capture MinerU status, parsed file count, MinIO object names/prefixes, AI metadata stage/result, and final material/review state if available.
- Capture relevant upload-server and MinerU-sidecar/observation evidence.
- Record wall-clock duration from upload start to terminal state.

Stop conditions:

- PASS if the task reaches `review-pending` with MinerU completed and AI metadata produced or deterministically repaired according to current strict semantics.
- FAIL if task reaches explicit failed state; report exact stage, error, logs, and whether failure is product, dependency, input, or timeout related.
- TIMEOUT if no terminal state after 45 minutes; report last stage, logs, and dependency health.
- ABORT if dependency health becomes blocking before upload starts.

## Required Validation After Terminal State

- Dependency health with MinerU submit probe.
- CMS reachability.
- DB/task state read-only evidence.
- MinIO artifact presence read-only evidence.
- Confirmation that strict AI skeleton fallback was not used as real AI recognition.
- Confirmation that no DB row deletion, MinIO object deletion, Docker volume deletion/pruning, secret change, broad deploy/rollback, or production release-readiness claim occurred.

## Forbidden Operations

- Do not delete DB rows.
- Do not delete MinIO objects.
- Do not delete or prune Docker volumes.
- Do not mutate secrets.
- Do not run broad production deploy, rollback, rebuild, or sync.
- Do not change production configuration.
- Do not claim production release readiness.
- Do not clean up validation artifacts unless separately approved.

## Allowed Repository Files

- One `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Do not edit application code or docs unless blocked and the report explains why. The expected repository output is a report and task-list update.

## Completion Report Requirements

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Large-PDF-Soak-Validation_REPORT.md`

The report must include:

- Test file path, size, SHA-256, and selection reason.
- Upload path used: UI or API.
- Task ID and all relevant state transitions.
- Final state and decision: PASS, FAIL, TIMEOUT, or BLOCKED.
- Commands run with exit codes.
- Runtime health evidence before and after.
- Artifact evidence and cleanup/non-cleanup decision.
- Exact failure evidence if failed.
- Residual risks.
- Confirmation production release readiness remains unclaimed.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.

## Acceptance Criteria

- Large-PDF soak evidence is complete and reproducible.
- Terminal state is objectively classified.
- Created validation artifacts are identified.
- No forbidden cleanup, data mutation, secret mutation, volume mutation, broad deploy/rollback, or release-readiness claim occurred.
