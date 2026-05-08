# P0 Adaptive Evidence-Pack Scoped Production Validation

Task:
P0 Adaptive Evidence-Pack Scoped Production Validation

Task ID:
`TASK-20260508-173100-P0-Adaptive-Evidence-Pack-Scoped-Production-Validation`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T17:31:00+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T17-31-00+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T15-11-45+0800_P0-Adaptive-Evidence-Pack-First-Pass-For-Large-AI-Metadata-Inputs_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T15-54-11+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight_REPORT.md`
- `TaskAndReport/2026-05-08T16-02-45+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Runbook-And-Preflight_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T17-31-00+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Adaptive evidence-pack first-pass selection has been accepted at code level on `main`. Task 33 produced a non-destructive production validation runbook and preflight. Director has now authorized scoped production validation.

Production release readiness remains unclaimed.

## Objective

Execute one scoped production validation to verify whether the accepted adaptive evidence-pack code is active in production and whether the accepted large-PDF sample no longer uses the old timeout-prone legacy first-pass payload.

## Authorized Scope

Follow the task 33 runbook unless a safer stop condition is encountered.

Lucode may:

1. Bring `/Users/concm/prod_workspace/Luceon2026` to accepted `origin/main` using a controlled fast-forward path while preserving production-local `docker-compose.override.yml`.
2. Preserve and verify:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - MinIO console mapping `127.0.0.1:19001:9001`
3. Use minimum necessary Docker/Compose action to apply the accepted upload-server code.
4. Run pre-upload readiness checks.
5. Create at most one controlled validation upload using:
   - `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
   - expected size `15157403`
   - expected SHA-256 `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
6. Poll only the created validation task and related AI job until terminal state or timeout.
7. Collect evidence required below.

## Stop Conditions

Stop and write a blocked or inconclusive report if:

- There are active parse tasks or AI metadata jobs before apply.
- Production override cannot be preserved exactly within accepted boundaries.
- `git stash pop` or fast-forward creates a conflict.
- Ollama `qwen3.5:9b` is not ready before upload.
- MinerU, MinIO, DB, CMS, or upload-server readiness fails before upload.
- The accepted sample size/hash does not match.
- More than one controlled validation upload would be required.
- Any step would require a forbidden operation.

## Required Evidence

Collect and report:

- Production HEAD before and after apply.
- `origin/main` HEAD.
- Production override boundary after apply.
- Docker/Compose commands run and exit codes.
- Pre-upload dependency health with `mineruSubmitProbe=true`.
- DB health.
- CMS reachability.
- Sample size and SHA-256.
- Created validation task ID and material ID.
- Task terminal state, stage, message, parsed file count, parsed artifact fields.
- AI job ID, terminal state, provider/model, message/error.
- Adaptive input-selection fields:
  - `aiClassificationSamplingMode`
  - `aiClassificationInputOriginalLength`
  - `aiClassificationInputSampledLength`
  - `aiClassificationInputHash`
  - `aiClassificationInputSelectionReasons`
  - `aiClassificationInputSelectionThresholds`
  - `aiClassificationRawTrace.input.observed`
- Relevant task events:
  - `ai-content-truncated`
  - provider request start/success/failure events
  - repair events, if any
  - final state transition event

## Pass Criteria

The validation may be reported as pass only if:

- Production code is on the accepted adaptive evidence-pack `main`.
- Production override remains within accepted local boundary.
- Pre-upload dependency health is non-blocking and Ollama is ready.
- MinerU completes and parsed artifacts are preserved.
- AI first-pass input uses `evidence-pack-v0.3`.
- Selected input is below `30000` characters before prompt wrapping.
- Trigger reasons and thresholds are present.
- No skeleton fallback is generated or represented as real AI recognition.
- No forbidden operation occurs.

AI metadata completion is preferred. If AI still fails, classify the validation carefully: adaptive input-selection may pass while end-to-end large-PDF AI completion remains failed or inconclusive.

## Forbidden

- Do not claim production release readiness.
- Do not delete DB rows.
- Do not delete MinIO objects.
- Do not delete or prune Docker volumes.
- Do not change secrets.
- Do not change model or timeout policy.
- Do not add skeleton fallback or silent degradation.
- Do not run broad production rollback outside this scoped validation.
- Do not create more than one controlled validation upload.
- Do not alter unrelated production-local override values.

## Required Checks

Run and report exact exit codes for all commands used. At minimum:

- `git status --short --branch` in dev and production workspaces.
- `git fetch origin` in dev and production workspaces.
- Production HEAD and `origin/main` before and after apply.
- Production override boundary inspection after apply.
- `docker compose ps` after apply.
- CMS reachability.
- Dependency health with `mineruSubmitProbe=true`.
- DB health.
- Sample `stat` and `shasum -a 256`.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_REPORT.md`

The report must include:

- Result classification: `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.
- Commands and exit codes.
- Evidence fields listed above.
- Any residual risk or follow-up task recommendation.
- Confirmation that no production release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.
