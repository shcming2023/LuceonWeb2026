# Task: P0 AI Metadata Repair Prompt And Timeout Hardening

```text
Task:
P0 AI Metadata Repair Prompt And Timeout Hardening

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
TaskAndReport/2026-05-07T10-56-16+0800_P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening_TASK.md

Required reading before execution:
- AGENTS.md
- docs/codex/TEAM_CONTRACT.md
- docs/codex/roles/lucode.md
- docs/codex/PROJECT_STATE.md
- docs/codex/HANDOFF.md
- docs/codex/TEST_POLICY.md
- docs/prd/Luceon2026-PRD-v0.4.md
- TaskAndReport/TASK_TRACKING_LIST.md
- TaskAndReport/2026-05-07T10-51-34+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_REPORT.md
- TaskAndReport/2026-05-07T10-56-16+0800_P0-Production-AI-JSON-Repair-Ollama-Timeout-Diagnosis_LUCIA_REVIEW.md

Background:
Production manual review exposed repeated AI metadata failures after MinerU completed successfully. Current evidence shows:

- First pass can consume large prompt context and run for minutes.
- JSON Repair can embed large first-pass output and schema guidance, then time out at the same 300s provider timeout.
- Lightweight Ollama health can recover while production-sized metadata prompts still fail.
- Strict no-skeleton mode correctly blocks fallback, so failed AI recognition stays visible.

Objective:
Reduce avoidable AI JSON Repair timeouts and improve observability of first-pass/repair size and duration, while preserving strict no-skeleton semantics.

Non-goals:
- Do not change the required model from `qwen3.5:9b`.
- Do not enable skeleton fallback.
- Do not increase the provider timeout as the primary fix.
- Do not retry, mutate, or repair existing production tasks or AI jobs.
- Do not change MinerU parsing behavior.
- Do not claim production release readiness.

Allowed files:
- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/metadata-standard-v0.2.mjs`
- `server/services/ai/providers/ollama.mjs`, only if needed for structured timing/size metadata already consumed by the worker
- `server/tests/ai-metadata-real-sample-smoke.mjs` or a new focused AI metadata smoke test under `server/tests/`
- `.env.example`, only if a clearly bounded repair-specific environment variable is introduced
- `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden changes:
- Do not edit production-only config.
- Do not edit PRD truth, project ledger, handoff, role contracts, or release judgments.
- Do not restart services as part of this implementation task.
- Do not mutate existing production task or AI job records.
- Do not introduce silent degradation or make skeleton output look like real AI metadata.

Required implementation direction:
1. Add or improve instrumentation for AI first-pass and repair-pass:
   - prompt/input length
   - generated output length
   - phase duration
   - timeout kind
   - repair pass input size
2. Make the repair pass smaller and more deterministic where safe:
   - avoid sending full original Markdown to the repair pass when the first-pass draft already contains the information needed for repair;
   - pass the first-pass draft, validation/parse error summary, and compact schema instructions rather than repeating large source context;
   - preserve enough source/object identity to keep provenance fields stable.
3. If first-pass output contains extractable JSON-like content, attempt deterministic extraction/normalization before invoking a full LLM repair pass.
4. Keep strict failure explicit:
   - if repair still times out or fails, job/task must fail clearly under strict no-skeleton mode.
5. Do not mask provider slowness as success.
6. Add tests proving the behavior.

Required tests:
- Existing AI metadata smoke coverage remains passing.
- Add focused coverage for:
  - repair pass receives a bounded prompt/input compared with first pass;
  - deterministic extraction can avoid LLM repair for recoverable JSON-wrapped output;
  - repair timeout still fails explicitly in strict mode;
  - no skeleton fallback is treated as successful AI recognition;
  - raw trace/phase metadata records first-pass and repair-pass boundaries.

Required checks:
- `git status --short --branch`
- `node server/tests/ai-metadata-real-sample-smoke.mjs`
- any new focused smoke test added by this task
- `npx pnpm@10.4.1 exec tsc --noEmit`
- `npx pnpm@10.4.1 run build`
- `git diff --check`

GitHub sync requirements:
- Start from GitHub `main`.
- Use a scoped branch, suggested:
  `lucode/p0-ai-metadata-repair-hardening`
- Commit and push the branch to GitHub.
- Do not merge to `main` before Lucia review.

Completion report storage requirements:
- Write the report into TaskAndReport/:
  `YYYY-MM-DDTHH-MM-SS+0800_P0-AI-Metadata-Repair-Prompt-And-Timeout-Hardening_REPORT.md`
- Update `TaskAndReport/TASK_TRACKING_LIST.md` with report path, branch, HEAD, status, next actor, and evidence summary.

Completion report must include:
- implementation summary
- files changed
- exact commands and exit codes
- test evidence
- before/after explanation of repair prompt/input behavior
- strict no-skeleton preservation evidence
- skipped checks and reasons
- risks and residual technical debt
- whether Lucia review is required

Acceptance criteria:
- Repair pass no longer repeats unnecessary large source context when first-pass draft is available.
- Recoverable JSON-wrapped output can be normalized without a full LLM repair call.
- Strict no-skeleton semantics remain unchanged.
- Timeout/failure remains explicit and observable.
- Tests, TypeScript, build, and diff check pass.
```
