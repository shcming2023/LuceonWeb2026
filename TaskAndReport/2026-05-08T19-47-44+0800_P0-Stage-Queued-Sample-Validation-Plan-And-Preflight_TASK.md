# P0 Stage-Queued Sample Validation Plan And Preflight

Task:
P0 Stage-Queued Sample Validation Plan And Preflight

Task ID:
`TASK-20260508-194744-P0-Stage-Queued-Sample-Validation-Plan-And-Preflight`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T19:47:44+0800

Project:
Luceon2026

Development workspace:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

Production deployment path:
`/Users/concm/prod_workspace/Luceon2026`

True sample directory:
`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

## Required Reading Before Execution

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/lucode.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/codex/TEST_POLICY.md`
- `TaskAndReport/2026-05-08T19-47-44+0800_P0-Controlled-Concurrency-Validation-Run-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Director Clarification

Director rejected concurrency validation as simultaneous heavy processing.

The local deployment must use a stage-queued流水 validation model because MinerU, MinIO, and Ollama are local runtime dependencies.

The corrected accepted validation shape is:

1. The upload-to-MinIO intake may accept the next sample after the previous sample has completed upload/storage intake.
2. MinerU parsing is queued as a stage; do not run multiple heavy MinerU parse jobs simultaneously in this local deployment validation.
3. Ollama metadata recognition is queued as a stage; do not run multiple heavy Ollama metadata jobs simultaneously in this local deployment validation.
4. Multiple samples may be in different stages only if the plan proves the stage handoff is safe and each heavy local dependency remains effectively single-worker.
5. Evidence must track each sample's stage transition separately.

The real validation samples are under:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

## Objective

Prepare a corrected stage-queued流水 validation plan and collect non-destructive preflight evidence from the true sample directory.

This task must not create production uploads.

## Authorized Scope

Lucode may:

1. Synchronize development workspace metadata with GitHub.
2. In production, run read-only status/fetch/inspection commands.
3. Inspect production service state with read-only commands such as `docker compose ps`.
4. Run CMS, DB, dependency-health with `mineruSubmitProbe=true`, and active task/job checks.
5. Perform at most one bounded non-mutating Ollama warm-up/readiness check if needed for preflight.
6. Inspect the true sample directory as read-only inventory only.
7. Produce a serial validation plan with:
   - proposed first validation wave;
   - explicit reason for sample choice and ordering;
   - exact sample paths, sizes, and SHA-256 values;
   - stage-queue stop conditions;
   - warm-up/readiness gates;
   - polling strategy for each sample's upload, MinerU parse, and Ollama metadata stages;
   - evidence fields to collect;
   - no-cleanup boundary;
   - risk assessment and recommended next task.

## Hard Limits

- Planning/preflight only.
- Do not create production uploads.
- Do not plan simultaneous heavy MinerU parse jobs.
- Do not plan simultaneous heavy Ollama metadata jobs.
- Do not represent this as unconstrained concurrency validation.
- Do not mutate production services, Docker, DB, MinIO, Ollama, config, secrets, overrides, samples, artifacts, or logs.
- Do not copy, move, rename, edit, delete, normalize, or pollute sample files.
- Do not synchronize external sample files to GitHub.
- Do not claim production release readiness.

## Required Preflight Evidence

Collect and report:

- Development and production git status.
- Production HEAD and `origin/main`.
- Production override boundary:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- `docker compose ps` read-only service state.
- CMS reachability.
- DB health.
- Dependency health with `mineruSubmitProbe=true`.
- Active parse/task states and active AI metadata jobs.
- True sample directory inventory:
  - exact paths;
  - size;
  - SHA-256 for reasonable non-zero candidates;
  - exclusion reasons for 0-byte placeholders or unsuitable files.
- Recommended first stage-queued validation wave and exact sample order.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_REPORT.md`

The report must include:

- Result classification: `PLAN_READY`, `BLOCKED`, or `INCONCLUSIVE`.
- Exact commands and exit codes.
- Preflight evidence listed above.
- Proposed stage-queued流水 validation plan.
- Proposed next Lucode task if Lucia accepts the plan.
- Confirmation that no production upload, simultaneous heavy-stage concurrency plan, mutation, cleanup, sample modification, GitHub sample sync, or production release-readiness claim occurred.

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.
