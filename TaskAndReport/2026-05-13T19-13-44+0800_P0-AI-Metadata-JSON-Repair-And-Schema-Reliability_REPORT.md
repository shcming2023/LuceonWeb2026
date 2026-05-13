# DevelopmentEngineer Report: P0 AI Metadata JSON Repair And Schema Reliability

## Based On

- Director task brief: `TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_TASK.md`
- Accepted failed-validation evidence: `TaskAndReport/2026-05-13T18-31-48+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_REPORT.md`
- Director review: `TaskAndReport/2026-05-13T19-13-44+0800_P0-Exactly-One-Controlled-Upload-Validation-After-Batched-Fixes_DIRECTOR_REVIEW.md`

## Branch / HEAD / Workspace State

- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `development-engineer/p0-post-validation-ollama-mineru-blockers`
- HEAD before this report: `996dbdf Review upload validation and dispatch AI repair task`
- Worktree had pre-existing unrelated modified/untracked files. This task touched only the files listed below.
- GitHub fetch/pull/push was not run because the current DevelopmentEngineer thread rule forbids synchronization unless explicitly authorized by Director/task brief.

## Files Changed

- `server/services/ai/providers/base.mjs`
- `server/services/ai/metadata-worker.mjs`
- `server/tests/ai-metadata-repair-hardening-smoke.mjs`
- `TaskAndReport/2026-05-13T19-13-44+0800_P0-AI-Metadata-JSON-Repair-And-Schema-Reliability_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Confirmed Failure Mechanism

Task 95's repair raw object was safely read through the existing read-only proxy path:

`http://localhost:8081/__proxy/upload/proxy-file?objectName=ai-raw%2Fvalidation-batched-fixes-1778670207%2Fai-job-1778670234560-4a6f%2Frepair-pass.txt&bucket=parsed`

The object existed in the parsed bucket, had length `2687`, and matched the reported class of failure. It looked structurally valid and evidence-bearing, but `JSON.parse` failed with:

`Bad escaped character in JSON at position 2140 (line 97 column 37)`

The concrete bad fragment was inside an evidence quote containing LaTeX-style content:

`$\sqcap ...$`, `$\angle ...$`, `$\circ ...$`

Those single backslashes are invalid JSON string escapes even though they are valid domain text. The failure is therefore best classified as a deterministic JSON extraction/repair robustness gap for evidence text containing LaTeX backslashes, not as a prompt-only issue, not as a trustworthy schema failure, and not as a reason to weaken strict no-skeleton semantics.

## Implementation Summary

Implemented a narrow deterministic JSON-string escape repair:

- Added `repairInvalidJsonStringEscapes(candidate)` in `server/services/ai/providers/base.mjs`.
- The repair scans only JSON string literals and doubles invalid backslashes that are not valid JSON escapes.
- Valid JSON escapes such as `\"`, `\\`, `\/`, `\n`, `\t`, and valid `\uXXXX` are preserved.
- `BaseProvider.parseJsonRobust()` now attempts normal parse first, then the deterministic invalid-escape repair for direct JSON, fenced JSON, and first-brace/last-brace extraction.
- `AiMetadataWorker.extractJson()` uses the same repair for worker-side parsing and nested `content` parsing.
- The existing strict no-skeleton path remains unchanged. Unparseable output, non-object output, schema-invalid repair output, and evidence-free output still fail or degrade to skeleton; strict mode still blocks skeleton.

This lets a valid repair object like Task 95's output become parseable only when the issue is JSON escaping inside strings. It does not synthesize metadata, does not bypass v0.2 validation, and does not accept skeleton fallback as real AI recognition.

## Raw Trace / Observability

No raw-trace schema was changed. Existing raw trace recording remains intact:

- parse errors still record raw content length/head/tail, `rawLooksTruncated`, `expectJson`, `responseFormatRequested`, and raw object/hash when persisted;
- successful parse after deterministic escape repair proceeds as a normal provider success and still feeds v0.2 normalization/taxonomy validation.

Residual observability improvement could later add a dedicated flag such as `invalidJsonEscapesRepaired=true`, but this task kept the remediation minimal and did not change event schema.

## Commands Run And Exit Codes

- `git status --short --branch` -> exit 0
- Read `TaskAndReport/TASK_TRACKING_LIST.md` and Task 96 brief -> exit 0
- Read required role/test/project docs and Task 95 report/review -> exit 0
- Inspect AI worker/provider/standard/test files -> exit 0
- `curl -fsS 'http://localhost:8081/__proxy/upload/proxy-file?objectName=ai-raw%2Fvalidation-batched-fixes-1778670207%2Fai-job-1778670234560-4a6f%2Frepair-pass.txt'` -> exit 22 / HTTP 500 because the object is not in the raw bucket
- `curl -fsS 'http://localhost:8081/__proxy/upload/proxy-file?objectName=ai-raw%2Fvalidation-batched-fixes-1778670207%2Fai-job-1778670234560-4a6f%2Frepair-pass.txt&bucket=parsed'` -> exit 0
- `curl ...bucket=parsed | node -e '<JSON.parse check>'` -> exit 1, reproduced `Bad escaped character in JSON at position 2140`
- `curl ...bucket=parsed | nl -ba | sed -n '90,102p'` -> exit 0, confirmed invalid LaTeX escapes in evidence text
- `git diff --check` -> exit 0
- `node --check server/services/ai/metadata-worker.mjs` -> exit 0
- `node --check server/services/ai/providers/base.mjs` -> exit 0
- `node --check server/services/ai/providers/ollama.mjs` -> exit 0
- `node --check server/services/ai/metadata-standard-v0.2.mjs` -> exit 0
- `node server/tests/ai-metadata-repair-hardening-smoke.mjs` -> exit 0
- `node server/tests/ai-metadata-single-pass-guard-smoke.mjs` -> exit 0
- `node server/tests/ai-metadata-real-sample-smoke.mjs` -> exit 0
- `node server/tests/dependency-health-smoke.mjs` -> exit 0, `65 passed, 0 failed`
- `npx pnpm@10.4.1 exec tsc --noEmit` -> exit 0
- `npx pnpm@10.4.1 run build` -> exit 0, Vite build passed with existing large-chunk warning
- `git log -1 --oneline` -> exit 0, `996dbdf Review upload validation and dispatch AI repair task`

## Skipped Checks And Reasons

- Production deployment: forbidden by task.
- Production upload / exactly-one-upload validation: forbidden by task; should only happen after Director review/authorization.
- Pressure, batch, soak, or 24-PDF validation: forbidden by task.
- Failed-task repair, reparse, re-AI, cleanup: forbidden by task.
- DB, MinIO, Docker volume/data cleanup or mutation: forbidden by task.
- Docker restart/rebuild/rollback/down/prune: forbidden by task.
- Model pull/delete/replace/restart/reload: forbidden by task.
- GitHub fetch/pull/push: skipped because this DevelopmentEngineer thread's current standing instruction forbids sync unless task and Director explicitly authorize it.

## Risks / Blockers / Residual Debt

- This is code/test-level evidence only. No production deployment or runtime upload validation was performed.
- The remediation handles invalid JSON string escapes deterministically. It does not solve genuinely malformed object structure, missing fields, missing evidence, taxonomy mismatch, timeout, or schema-invalid repair output.
- Task 95 also exposed P1 MinerU observability debt: stale task metadata retained `log-observation-unreadable`, and transient false failed events still self-corrected. This report does not address that P1 track.
- If Director accepts this code-level fix, a separate deployment/runtime validation task is needed before any new exactly-one-upload validation.

## Review / Next Step

Director review is required.

Recommended next step if accepted:

1. Director authorizes scoped production deployment/runtime validation of this code path.
2. Only after that deployment report is reviewed, Director may authorize exactly one controlled upload validation to determine whether the Task 95 sample now reaches `review-pending` or a trustworthy non-skeleton terminal result.

No production readiness, L3, pressure PASS, or release-readiness claim is made.
