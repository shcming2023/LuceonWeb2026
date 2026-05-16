# DevelopmentEngineer Report: P1 CleanService Mock Protocol Foundation Disabled By Default

- Task: `TASK-20260516-080216-P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default`
- Based on Director task brief: `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_TASK.md`
- Source implementation commit: `942420c` (`Add disabled CleanService mock foundation`)
- Outcome: `IMPLEMENTED_MOCK_FOUNDATION_DISABLED_BY_DEFAULT`
- Requires Director review: yes
- Requires follow-up production validation or user decision: no production validation was run; future real Mineru2Table dispatch still requires separate Director/User decision and external protocol evidence.

## Branch / HEAD

- Branch: `main`
- Initial task execution HEAD: `c5a051f`
- Implementation HEAD: `942420c`
- GitHub sync: implementation and this report/ledger update are intended for GitHub `main` per task brief after checks pass.

## Files Changed

- `server/services/cleanservice/config.mjs`
- `server/services/cleanservice/states.mjs`
- `server/services/cleanservice/output-verifier.mjs`
- `server/services/cleanservice/metadata-summary.mjs`
- `server/services/cleanservice/protocol.mjs`
- `server/tests/cleanservice-foundation-smoke.mjs`
- `TaskAndReport/2026-05-16T08-02-16+0800_P1-CleanService-Mock-Protocol-Foundation-Disabled-By-Default_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

No UI, PRD truth, role contract, `PROJECT_STATE`, `HANDOFF`, production, Docker, DB, MinIO, MinerU, Ollama, model, secret, sample, or external repository file was changed.

## Implementation Summary

Implemented a standalone Luceon-side CleanService mock/protocol foundation under `server/services/cleanservice/`. It is not wired into `server/upload-server.mjs`, `ParseTaskWorker`, `AiMetadataWorker`, frontend UI, production, or any runtime worker startup path.

The foundation includes:

- disabled-by-default config loader, where missing endpoint/API key/callback secret does not break startup and disabled state is represented as `not-enabled` / `未启用`;
- stable CleanService state/product label/task-intent helpers for `未启用`, `不适用`, `等待目录重建`, `目录重建中`, `部分完成待复核`, `目录结构已完成`, `目录重建已跳过`, `成本待决策`, timeout, protocol failure, and hard-limit failure;
- cost policy helper where `¥5` soft limit maps to `cost-decision` requiring Director/User decision and `¥8` hard limit maps to explicit `hard-limit-failed`;
- protocol normalization for submit/query response shapes and transport timeout/protocol failure cases;
- client factory that never performs a real HTTP request by itself and only calls a test-injected `transport`;
- bounded task/material metadata summary helpers for `task.metadata.cleanServiceJobs` and `material.metadata.cleanMaterials`, storing ObjectRefs and small stats only;
- mock output/provenance verifier requiring all expected ObjectRefs plus provenance shape before representing clean success;
- no-silent-fallback checks so raw MinerU output, placeholder output, or skeleton-only output is not labeled as clean success.

## Feature Default / External Service Boundary

CleanService is disabled by default. `loadCleanServiceConfig({})` returns `enabled=false`, `status=not-enabled`, and the focused test verifies that even with an injected transport present, disabled config results in zero transport calls.

No real Mineru2Table dispatch was implemented. No `fetch` call is made by the CleanService client. Real transport must be explicitly injected by a focused test or future separately authorized implementation task.

## Product State / Cost / Error Mapping

| Condition | Clean state | Product label | Task intent |
| --- | --- | --- | --- |
| Disabled default | `not-enabled` | `未启用` | `none` |
| Not applicable | `not-applicable` | `不适用` | `none` |
| Queued | `pending` | `等待目录重建` | `pending` |
| Processing | `running` | `目录重建中` | `running` |
| Completed with unresolved anchors | `review-pending-partial` | `部分完成待复核` | `review-pending` with `cleanReview=partial-unresolved-anchors` |
| Verified completed output | `completed` | `目录结构已完成` | `completed` |
| Skipped/canceled | `skipped` | `目录重建已跳过` | `skipped` |
| Cost at or above `¥5` and below `¥8` | `cost-decision` | `成本待决策` | `review-pending` with `cleanReview=cost-decision-required` |
| Cost at or above `¥8` | `hard-limit-failed` | `目录重建失败` | `failed` |
| Transport timeout | `timeout` | `目录重建失败` | `failed` |
| Protocol/output/provenance failure | `protocol-failure` | `目录重建失败` | `failed` |

## Phase 1 Runtime Path Evidence

The current Phase 1 runtime path remains untouched:

```text
upload -> local MinerU -> MinIO -> Ollama qwen3.5:9b -> AI metadata -> operator review
```

Evidence:

- No existing `server/upload-server.mjs`, `server/services/queue/task-worker.mjs`, `server/services/ai/metadata-worker.mjs`, frontend source, runtime config, or Docker file changed.
- New files are isolated to `server/services/cleanservice/**` and a focused server test.
- No production command, upload, pressure validation, submit-probe, retry/reparse/re-AI/cancel/repair/reset, DB/MinIO/Docker volume cleanup, model/secret/config/sample mutation, or external repository command was run.

## Commands Run and Exit Codes

| Command | Exit | Purpose / Evidence |
| --- | ---: | --- |
| `git status --short --branch` | 0 | Required initial state check; branch `main...origin/main` |
| `rg -n "\\| DevelopmentEngineer \\|" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | Located Task 200 |
| `sed -n ...` on Task 200 brief and required role/project/PRD/CleanService docs/reports/reviews | 0 | Required reading before implementation |
| `find server/services -maxdepth 3 -type f` | 0 | Confirmed no existing `server/services/cleanservice` implementation |
| `mkdir -p server/services/cleanservice` | 0 | Created allowed implementation directory |
| `node --check server/services/cleanservice/*.mjs server/tests/cleanservice-foundation-smoke.mjs` | 0 | Syntax check for every changed `.mjs` server file |
| `git diff --check` | 0 | No whitespace errors |
| `node server/tests/cleanservice-foundation-smoke.mjs` | 1 then 0 | First run caught snake_case cost-field bug; after fix, passed with `PASS cleanservice foundation smoke` |
| `npx pnpm@10.4.1 exec tsc --noEmit` | 0 | Required TypeScript check passed |
| `git fetch origin && git status --short --branch` | 0 | Read-only remote status confirmation; branch still `main...origin/main` before commit |
| `git add server/services/cleanservice server/tests/cleanservice-foundation-smoke.mjs && git commit -m "Add disabled CleanService mock foundation"` | 0 | Implementation commit `942420c` |

## Focused Test Coverage

`server/tests/cleanservice-foundation-smoke.mjs` covers:

- disabled-by-default config and `未启用` state;
- disabled state does not call injected transport;
- successful mock protocol response becomes verified clean completion;
- bounded metadata summaries store ObjectRefs and small stats, not large content;
- partial unresolved anchors map to `review-pending-partial` and task intent `review-pending`;
- `¥5` soft limit maps to `cost-decision`;
- `¥8` hard limit maps to `hard-limit-failed`;
- timeout maps to `timeout`;
- missing provenance maps to `protocol-failure`;
- raw MinerU output cannot be represented as clean success.

## Skipped Checks and Reasons

- `npx pnpm@10.4.1 run build`: skipped because this task touched only server `.mjs` modules, one server `.mjs` focused test, and TaskAndReport files; no frontend, TypeScript app, shared type, or build-sensitive file was changed.
- Production checks: skipped because the task explicitly says not to run production checks.
- Upload, pressure/batch/soak validation, submit-probe, retry, reparse, re-AI, cleanup, repair, reset, task-state reconciliation, and real Mineru2Table dispatch: skipped because forbidden by the task brief.
- External Mineru2Table2026 repository checks: skipped because external repository work was outside scope.

## Risks / Blockers / Residual Debt

- This is a mock/protocol foundation only. It is not real Mineru2Table E2E evidence.
- No worker, callback route, persistence, UI surface, or production runtime dispatch is implemented in this task.
- Cross-repo byte-identical protocol sync remains a Director-owned paired-task process.
- Future real integration still needs accepted Mineru2Table evidence for ObjectRef jobs, persistent job state, idempotency, MinIO outputs, provenance, webhook/polling behavior, and cost-limit behavior.
- Future UI/product work should expose clean-stage summaries without conflating mock success with real clean output.

## Director Review

Director review is required. Recommended next action: review the mock foundation and focused test evidence. If accepted, dispatch the next scoped task separately for one of: disabled worker shell, callback/polling contract, UI read surface, or external Mineru2Table protocol evidence. Real dispatch and production validation remain explicitly unclaimed.
