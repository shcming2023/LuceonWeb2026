# Task: P0 AI Metadata JSON Repair And Schema Reliability

Assignee:
DevelopmentEngineer

Issued by:
Director

Issued at:
2026-05-13T19:13:44+0800

Project:
Luceon2026

Development workspace:
/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026

Production deployment path:
/Users/concm/prod_workspace/Luceon2026

GitHub:
https://github.com/shcming2023/Luceon2026

TaskAndReport record:
TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_TASK.md

Expected report:
TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md

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
- TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md
- TaskAndReport/2026-05-13T19-13-44+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_DIRECTOR_REVIEW.md

## Background

Task 95 performed exactly one controlled production upload after the batched Task 91 and Task 93 deployment.

Accepted facts:

- MinerU completed and stored 21 parsed artifacts.
- Ollama `qwen3.5:9b` first pass succeeded after `101519ms`.
- The previous 30s `UND_ERR_HEADERS_TIMEOUT` did not recur.
- JSON Repair failed after `154520ms`.
- Repair output was malformed JSON, `rawLooksTruncated=false`, `responseFormatRequested=true`, `expectJson=true`.
- Strict no-skeleton behavior correctly blocked skeleton fallback.
- The task/material ended failed at AI stage.

The relevant production identifiers are:

- task: `task-1778670208778`;
- material: `validation-batched-fixes-1778670207`;
- AI job: `ai-job-1778670234560-4a6f`;
- repair raw object recorded in event payload:
  `ai-raw/validation-batched-fixes-1778670207/ai-job-1778670234560-4a6f/repair-pass.txt`;
- repair raw content hash:
  `f883d062a67716bf29a175045de3996dd3c5cfe051bb79d96acd4666ea843c90`.

## Objective

Implement a scoped code/test-level remediation so the AI metadata path is materially more reliable for qwen3.5:9b under strict no-skeleton semantics.

The goal is not to hide failure. The goal is to accept only trustworthy non-skeleton metadata when the provider output contains enough valid evidence, and to keep explicit failure when it does not.

## Required Investigation

Perform read-only investigation before coding:

- inspect the current AI metadata worker and provider flow:
  - `server/services/ai/metadata-worker.mjs`;
  - `server/services/ai/providers/base.mjs`;
  - `server/services/ai/providers/ollama.mjs`;
  - `server/services/ai/metadata-standard-v0.2.mjs`;
  - existing AI metadata tests.
- inspect Task 95 report and, if safely accessible without mutation, the raw AI repair output object from production MinIO or existing persisted raw trace.
- determine whether the Task 95 failure is best treated as:
  - prompt/output-shape issue;
  - deterministic normalization gap;
  - JSON extraction/repair robustness gap;
  - schema validation gap;
  - or a combination.

Do not mutate production during this investigation.

## Implementation Guidance

Choose the smallest reliable remediation that matches the evidence. Do not implement a broad redesign.

Reasonable directions to consider:

- keep qwen output constrained to a smaller draft schema and use deterministic v0.2 normalization when enough facets/evidence are present;
- improve deterministic repair for draft-like or canonical-like provider output before asking the model for a second full canonical JSON object;
- improve repair prompt shape so qwen is less likely to emit malformed nested canonical JSON;
- improve robust JSON extraction only if it can be done deterministically and safely;
- preserve raw trace details so future failures identify whether they are parse, schema, truncation, timeout, or strict fallback blocks.

Do not:

- accept skeleton fallback as real AI recognition;
- weaken `DISABLE_AI_SKELETON_FALLBACK=true`;
- convert unparseable or evidence-free output into accepted metadata;
- silently mark failed AI as successful;
- hide JSON repair failures from raw trace or task events;
- make a production deployment or upload.

## Expected Code Areas

Likely files, but inspect before editing:

- `server/services/ai/metadata-worker.mjs`;
- `server/services/ai/metadata-standard-v0.2.mjs`;
- `server/services/ai/providers/base.mjs`;
- `server/services/ai/providers/ollama.mjs`;
- focused tests under `server/tests/`.

Do not change PRD truth, role contracts, release judgment documents, public APIs, production overrides, model selection, secrets, Docker files, DB/MinIO data, or sample files unless the task evidence proves a small test-only/doc-only edit is required and you report it explicitly.

## Required Tests

Add or update focused tests that cover the Task 95 class of failure.

At minimum, include tests for:

- strict no-skeleton remains enforced when provider output cannot be trusted;
- malformed or schema-invalid repair output does not become a false success;
- a valid draft-like provider output can be deterministically normalized to non-skeleton v0.2 metadata without requiring a fragile second canonical-generation pass, if your implementation supports that path;
- raw trace records repair failure details clearly enough for Director/TestAcceptanceEngineer review.

Run, unless impossible:

```bash
git diff --check
node --check server/services/ai/metadata-worker.mjs
node --check server/services/ai/providers/base.mjs
node --check server/services/ai/providers/ollama.mjs
node --check server/services/ai/metadata-standard-v0.2.mjs
node server/tests/ai-metadata-repair-hardening-smoke.mjs
node server/tests/ai-metadata-single-pass-guard-smoke.mjs
node server/tests/ai-metadata-real-sample-smoke.mjs
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If any command is not relevant because the touched files differ, explain exactly why. If any command cannot run because of unrelated local environment state, report the exact blocker and run the closest focused checks.

## Completion Report Requirements

Write:

`TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- status `已回报待 Director 审查` or blocked equivalent;
- `Next Actor=Director`;
- report path;
- branch/HEAD;
- concise implementation summary;
- checks and exit codes;
- explicit production boundary statement.

Report must include:

- based-on task brief path;
- files changed;
- implementation summary;
- the exact Task 95 failure mechanism you confirmed or revised;
- how the remediation preserves strict no-skeleton behavior;
- raw trace / observability changes, if any;
- commands run and exit codes;
- skipped checks and reasons;
- risks, blockers, residual debt;
- whether Director should authorize production deployment and exactly-one-upload validation after review.

## Forbidden Actions

Do not perform:

- production deployment;
- production upload;
- pressure/batch/soak/24-PDF validation;
- failed-task repair, reparse, or re-AI;
- DB, MinIO, Docker volume/data cleanup or mutation;
- Docker `down`, `down -v`, prune, broad restart, rebuild, rollback;
- model pull/delete/replace/restart/reload;
- secret, override, PRD, role-contract, release truth, or public API mutation;
- sample mutation or sample copy into the repository;
- L3, pressure PASS, production-readiness, or release-readiness claim.

## Acceptance Criteria

- Task 95 AI JSON/schema failure is diagnosed from concrete evidence.
- A narrow code/test-level remediation is implemented or a blocked report explains why it cannot be implemented safely.
- Strict no-skeleton semantics remain intact.
- Focused tests cover the new behavior and regression boundaries.
- Standard checks are run or explicitly justified if skipped.
- No production/runtime/data/sample mutation occurs.
