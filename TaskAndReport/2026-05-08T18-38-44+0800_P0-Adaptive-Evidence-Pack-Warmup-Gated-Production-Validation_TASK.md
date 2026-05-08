# P0 Adaptive Evidence-Pack Warmup-Gated Production Validation

Task:
P0 Adaptive Evidence-Pack Warmup-Gated Production Validation

Task ID:
`TASK-20260508-183844-P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T18:38:44+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T18-38-44+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T18-31-29+0800_P0-Ollama-Warmup-Before-Validation-Authorization_DECISION.md`
- `TaskAndReport/2026-05-08T18-38-44+0800_P0-Ollama-Warmup-Before-Validation-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T18-31-29+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Retry_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T18-27-32+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Retry_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Task 34 and task 36 both stopped before upload because upload-server dependency-health timed out on Ollama `qwen3.5:9b` readiness. Task 35 diagnosed the issue as cold-load/model-residency readiness instability rather than model absence.

Director approved a narrow validation procedure: one bounded non-mutating Ollama warm-up/readiness step may be performed before the single controlled upload. Warm dependency-health must then pass before upload.

## Objective

Verify whether the accepted adaptive evidence-pack first-pass path is active during one controlled production large-PDF validation upload, using the Director-approved warm-up gate.

## Authorized Scope

Lucode may:

1. Synchronize development workspace metadata with GitHub.
2. In production, run read-only status/fetch/inspection commands.
3. Confirm production adaptive evidence-pack code markers:
   - `shouldUseEvidencePack`
   - `evidence-pack-v0.3`
4. Confirm production-local override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - MinIO console mapping `127.0.0.1:19001:9001`
5. Confirm no active parse tasks or AI metadata jobs exist before validation.
6. Perform exactly one bounded non-mutating Ollama warm-up/readiness step using the existing model `qwen3.5:9b`.
   - The warm-up must be a minimal direct local Ollama request such as `num_predict=1`.
   - It must not change model, timeout, config, secrets, override, services, Docker, DB, MinIO, or artifacts.
   - Record command, duration, result, and any load duration if available.
7. Immediately after warm-up, run dependency health with `mineruSubmitProbe=true`.
8. Only if warm dependency-health passes with `ollama.ok=true` and `ollama.chatOk=true`, create at most one controlled validation upload using:
   - `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
   - expected size `15157403`
   - expected SHA-256 `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
9. Poll only the created validation task and related AI job until terminal state or a bounded timeout.
10. Collect the evidence fields listed below.

## Stop Conditions

Stop and write a blocked or inconclusive report if:

- Production code markers are absent.
- Production override boundary is not preserved.
- Any Docker, production deploy, production fast-forward, rebuild, service restart, model change, timeout change, config change, secret change, override change, or data mutation would be required.
- Active parse tasks or AI jobs exist before upload.
- The bounded warm-up fails.
- Warm dependency-health after warm-up fails.
- CMS, DB, MinIO, MinerU submit probe, upload-server, or Ollama readiness fails before upload.
- Sample size/hash does not match.
- More than one controlled validation upload would be required.
- Any step would require a forbidden operation.

## Required Evidence

Collect and report:

- Development and production git status.
- Production HEAD and `origin/main` HEAD.
- Production code marker confirmation.
- Production override boundary confirmation.
- `docker compose ps` read-only service state.
- Pre-warm CMS, DB, active tasks/jobs, and sample hash/size.
- Warm-up command, exit code, result, total duration, and load duration if available.
- Warm dependency-health with `mineruSubmitProbe=true`, including Ollama duration.
- Created validation task ID and material ID.
- Task terminal state, stage, message, parsed file count, and parsed artifact fields.
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

- Production code includes the accepted adaptive evidence-pack implementation.
- Production override remains within accepted local boundary.
- The bounded warm-up succeeds without mutation.
- Warm dependency-health passes immediately before upload.
- MinerU completes and parsed artifacts are preserved.
- AI first-pass input uses `evidence-pack-v0.3`.
- Selected input is below `30000` characters before prompt wrapping.
- Trigger reasons and thresholds are present.
- No skeleton fallback is generated or represented as real AI recognition.
- No forbidden operation occurs.

AI metadata completion is preferred. If AI still fails, classify carefully: adaptive input-selection may pass while end-to-end large-PDF AI completion remains failed or inconclusive.

## Forbidden

- Do not claim production release readiness.
- Do not run production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- Do not restart, start, stop, kill, or reload Ollama or any production service.
- Do not delete DB rows.
- Do not delete MinIO objects.
- Do not delete or prune Docker volumes.
- Do not change secrets.
- Do not change model or timeout policy.
- Do not change config or production-local override values.
- Do not add skeleton fallback or silent degradation.
- Do not create more than one controlled validation upload.
- Do not alter unrelated files or task artifacts.

## Required Checks

Run and report exact exit codes for all commands used. At minimum:

- `git status --short --branch` in dev and production workspaces.
- `git fetch origin` in dev and production workspaces.
- Production HEAD and `origin/main` before validation.
- Production code marker inspection.
- Production override boundary inspection.
- `docker compose ps`.
- CMS reachability.
- DB health.
- Active tasks/jobs count.
- Sample `stat` and `shasum -a 256`.
- Bounded direct Ollama warm-up.
- Warm dependency health with `mineruSubmitProbe=true`.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Adaptive-Evidence-Pack-Warmup-Gated-Production-Validation_REPORT.md`

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
