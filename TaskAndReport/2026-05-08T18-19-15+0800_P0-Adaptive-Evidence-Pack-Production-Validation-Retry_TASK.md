# P0 Adaptive Evidence-Pack Production Validation Retry

Task:
P0 Adaptive Evidence-Pack Production Validation Retry

Task ID:
`TASK-20260508-181915-P0-Adaptive-Evidence-Pack-Production-Validation-Retry`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T18:19:15+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

GitHub:
`https://github.com/shcming2023/Luceon2026`

TaskAndReport record:
`TaskAndReport/2026-05-08T18-19-15+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Retry_TASK.md`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `docs/deploy/DEPLOY.md`
- `TaskAndReport/2026-05-08T17-31-00+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_TASK.md`
- `TaskAndReport/2026-05-08T17-41-06+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_REPORT.md`
- `TaskAndReport/2026-05-08T18-09-49+0800_P0-Adaptive-Evidence-Pack-Scoped-Production-Validation_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T18-16-06+0800_P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan_REPORT.md`
- `TaskAndReport/2026-05-08T18-19-15+0800_P0-Ollama-Readiness-Timeout-Diagnosis-And-Recovery-Plan_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Background

Task 34 applied accepted adaptive evidence-pack code to production and rebuilt upload-server, but stopped before upload because Ollama readiness timed out.

Task 35 diagnosed the timeout as transient cold-load/readiness behavior. Without mutation, Ollama `qwen3.5:9b` became ready, direct warm chat completed in about `1.348s`, and warm dependency health completed in `793ms`.

This task re-attempts the scoped production validation. It is not a production deploy task.

## Objective

Verify whether the accepted adaptive evidence-pack first-pass path is active during one controlled production large-PDF validation upload.

## Authorized Scope

Lucode may:

1. Synchronize development workspace metadata with GitHub.
2. In production, run read-only status/fetch/inspection commands.
3. Confirm production code HEAD is still the accepted applied code `8092965`, or at least that `server/services/ai/metadata-worker.mjs` contains:
   - `shouldUseEvidencePack`
   - `evidence-pack-v0.3`
4. Confirm production-local override boundary remains:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - MinIO console mapping `127.0.0.1:19001:9001`
5. Run immediate pre-upload readiness checks, including dependency health with `mineruSubmitProbe=true`.
6. If dependency health is passing and `ollama.ok=true` / `ollama.chatOk=true`, create at most one controlled validation upload using:
   - `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
   - expected size `15157403`
   - expected SHA-256 `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
7. Poll only the created validation task and related AI job until terminal state or a bounded timeout.
8. Collect the evidence fields listed below.

## Stop Conditions

Stop and write a blocked or inconclusive report if:

- Production code markers are absent.
- Production override boundary is not preserved.
- Any Docker, production deploy, production rebuild, service restart, model change, timeout change, config change, or data mutation would be required.
- Active parse tasks or AI jobs exist before upload.
- CMS, DB, MinIO, MinerU submit probe, upload-server, or Ollama warm dependency-health fails before upload.
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
- Pre-upload dependency health with `mineruSubmitProbe=true`, including Ollama duration.
- CMS reachability.
- DB health.
- Active tasks/jobs count before upload.
- Sample size and SHA-256.
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
- Pre-upload dependency health passes and Ollama is ready immediately before upload.
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
- Do not delete DB rows.
- Do not delete MinIO objects.
- Do not delete or prune Docker volumes.
- Do not change secrets.
- Do not change model or timeout policy.
- Do not change production-local override values.
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
- Dependency health with `mineruSubmitProbe=true`.
- DB health.
- Active tasks/jobs count.
- Sample `stat` and `shasum -a 256`.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Adaptive-Evidence-Pack-Production-Validation-Retry_REPORT.md`

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
