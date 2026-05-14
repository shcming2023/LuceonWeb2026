# Architect Report: P1 Pressure Test AI Timeout Failure Architecture Diagnosis

- Task ID: `TASK-20260515-053816-P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis`
- Task brief: `TaskAndReport/2026-05-15T05-38-16+0800_P1-Pressure-Test-AI-Timeout-Failure-Architecture-Diagnosis_TASK.md`
- Role: `Architect`
- Report time: `2026-05-15T05:45+0800`
- Result: `AI_TIMEOUT_ROUTE_REMEDIATION_REQUIRED_STRICT_FALLBACK_CORRECT`

## Scope And Boundaries

This report is based on a Director task brief. Required reading was completed:

- `AGENTS.md`
- `docs/codex/TEAM_CONTRACT.md`
- `docs/codex/roles/architect.md`
- `docs/codex/PROJECT_STATE.md`
- `docs/codex/HANDOFF.md`
- `docs/prd/Luceon2026-PRD-v0.4.md`
- `docs/codex/TEST_POLICY.md`
- `docs/codex/REPOSITORY_STRUCTURE.md`
- `TaskAndReport/README.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`
- Task 152 brief
- Task 151 report, notes, and Director review

No code change, failed-task repair, retry, reparse, re-AI, DB/MinIO/Docker volume/data mutation, Docker/service restart/rebuild/down, MinerU/Ollama/supervisor mutation, model/config/secret/sample mutation, production deployment, readiness/L3/pressure PASS/release/go-live action was performed.

## Read-Only Commands And Endpoints

Development workspace:

- `git status --short --branch`: exit `0`; branch `development-engineer/p0-post-validation-ollama-mineru-blockers`, dirty shared workspace.
- `rg`/`sed` reads of task ledger, task brief, role docs, project docs, Task 151 report/notes/review, and source files: exit `0` unless the search intentionally returned no matches.

Production workspace:

- `git status --short --branch && git log -1 --oneline`: exit `0`; branch `main...origin/main`, HEAD `89271a1 Dispatch db-sync hardening production deployment`, local modifications present.
- Read-only HTTP checks:
  - `GET /__proxy/upload/health`: HTTP `200`, `ok=true`.
  - `GET /__proxy/upload/ops/mineru/active-task`: HTTP `200`, active task still `task-1778765417422`.
  - `GET /__proxy/upload/ops/mineru/admission-circuit`: HTTP `200`, circuit `closed`, `parseRunning=1`.
  - `GET /__proxy/upload/ops/dependency-health`: HTTP `200`, current `ok=true`, `blocking=false`; Ollama `chatOk=true`, `modelResident=true`.
  - `GET /__proxy/db/tasks`: HTTP `200`.
  - `GET /__proxy/db/ai-metadata-jobs`: HTTP `200`.
  - `GET /__proxy/db/task-events?taskId=...`: HTTP `200` for the three failed AI tasks and the still-running MinerU task.
  - Direct `GET http://127.0.0.1:11434/api/version`: HTTP `200`, Ollama `0.23.2`.
  - Direct `GET http://127.0.0.1:11434/api/ps`: HTTP `200`, `qwen3.5:9b` resident.
  - Direct `GET http://127.0.0.1:8083/health`: HTTP `200`, MinerU healthy, `processing_tasks=1`, `failed_tasks=0`.

## Current Pressure-Run State

At analysis time, the pressure-test aggregate remains:

| State / Stage | Count |
| --- | ---: |
| `review-pending/review` | 20 |
| `failed/ai` | 3 |
| `running/mineru-processing` | 1 |

Failed AI tasks:

| Task | AI job | Evidence |
| --- | --- | --- |
| `task-1778765409131` | `ai-job-1778792166467-9699` | First pass Ollama timeout, duration about `179956ms`, timeout `180000ms`; strict no-skeleton fallback blocked fallback. |
| `task-1778765412523` | `ai-job-1778792264103-56b5` | First pass Ollama timeout, duration about `180005ms`, timeout `180000ms`; strict no-skeleton fallback blocked fallback. |
| `task-1778765415701` | `ai-job-1778792291124-94e7` | First pass succeeded in about `111987ms`, then JSON repair pass timed out at about `180004ms`; strict no-skeleton fallback blocked fallback. |

Remaining active task:

- `task-1778765417422`, file `06第六章 长期股权投资与合营安排.pdf`, state `running`, stage `mineru-processing`.
- Direct MinerU health still shows `processing_tasks=1`, `failed_tasks=0`.
- Active-task shows live task attribution to `task-1778765417422`, but current message still labels observation as lagging/stale in parts of the diagnostic payload.

## Failure Timeline And Owning Subsystems

The pressure test did not fail at upload intake, MinIO storage, Docker service availability, or global UI availability. It failed because terminal AI-stage task failures occurred.

Signal ownership:

| Signal | Owner | Assessment |
| --- | --- | --- |
| 24 pressure tasks created after baseline | Upload server / DB task model | Intake worked. |
| Sequential MinerU parse progression | ParseTaskWorker + MinerU | Mostly worked; 20 tasks reached review and 1 remained active. |
| Three terminal `failed/ai` tasks | AiMetadataWorker | Direct pressure failure criterion. |
| Ollama timeout at `180000ms` | OllamaProvider + local Ollama runtime capacity | Provider deadline expired despite service/model being reachable. |
| Strict skeleton fallback block | AiMetadataWorker strict mode | Correct guardrail behavior. |
| Repeated dependency-health timeout during monitoring | dependency-health endpoint + Ollama lightweight probes | Health semantics became noisy under active load; not the same as provider SLA. |
| Direct `/api/version` and `/api/ps` reachable, model resident | Ollama service surface | Shows process/model residency, not proof of generation completion within business deadline. |
| Remaining active MinerU task | MinerU + ParseTaskWorker | Not an AI failure; still active and must not be repaired casually. |

## Why Residency And Business Timeout Can Coexist

`/api/ps` only proves that the model is loaded/resident in Ollama. It does not prove that a specific `/api/chat` generation can complete within the AI worker's business deadline.

Current code facts:

- In strict mode, `server/services/ai/metadata-worker.mjs` sets provider timeout to `180000ms`.
- `server/services/ai/providers/ollama.mjs` applies the same deadline to `AbortSignal.timeout`, `headersTimeout`, and `bodyTimeout`.
- The first pass defaults to `num_predict=512`; repair pass uses `num_predict=3072`, and repair retry can use `4096`.
- The AI worker is process-serial through `processingMap`, but Ollama is also sharing the same single machine with MinerU, Docker, DB, MinIO, frontend, and ongoing pressure work.
- dependency-health uses tiny `/api/chat` probes with `num_predict=1`; those checks can time out during load or return OK later without representing the heavier metadata prompts.

Therefore, the observed pattern is internally consistent: Ollama can be reachable and resident while larger metadata calls or repair calls exceed `180000ms`.

## Root-Cause Hypothesis

Primary hypothesis, high confidence:

The current strict-mode AI deadline and prompt/repair workload are not robust enough for long-run mixed-size pressure execution on this single machine. The three failed tasks reached valid parsed-artifact states, then failed in AI metadata generation or repair because Ollama generation exceeded the configured `180000ms` per-pass boundary.

Evidence:

- Failed task events show `ai-provider-request-started` with `timeoutMs=180000`.
- Two tasks failed first pass at about the timeout boundary.
- One task succeeded first pass but failed repair at the timeout boundary.
- Direct MinerU health reported no MinerU task failures.
- Direct Ollama `/api/version` and `/api/ps` were reachable, so this was not a simple process-down or missing-model failure.
- Strict fallback blocked skeleton output, preserving the no-silent-degradation contract.

Secondary hypothesis, medium confidence:

dependency-health currently adds observation noise during pressure work because it mixes entry-gate dependency checks with live Ollama generation probes. Its 10s monitoring timeout and internal 1-token chat probe are useful for idle readiness but are not reliable as pressure-run health truth.

Weaker or still-open alternatives:

- MinerU caused the three AI failures: weak. The failed tasks had completed parsed artifacts and AI jobs; direct MinerU failed count stayed `0`.
- Model was unloaded/cold: weak for the observed final state and repeated `/api/ps` checks, though transient load can still cause slow generation.
- Evidence-pack/sampling alone is wrong: open. One failed task had only `33870 -> 12209` selected chars, so timeout is not only giant input length. The repair pass token budget and output schema pressure matter too.
- Hardware resource saturation: plausible but not proven by this task; prior notes show elevated load, but this report did not run intrusive profiling.

## Architecture Judgment

The current AI timeout boundary is appropriate as a strict fail-fast guardrail for normal one-off work, but not sufficient as the only policy for pressure execution.

Do not solve this by allowing skeleton fallback. Strict no-skeleton behavior is correct: AI failures must remain explicit failed tasks or explicit retry candidates, not pretend-reviewable AI output.

The correct route is to separate:

1. business AI execution policy;
2. health/readiness observation policy;
3. manual or controlled retry policy;
4. active-work safety policy.

## Remediation Route

Recommended order:

1. DevelopmentEngineer: AI timeout/error classification and operator-safe retry contract.
2. DevelopmentEngineer: dependency-health pressure-mode semantics.
3. TestAcceptanceEngineer: non-mutating validation of classification/health behavior.
4. User/Director decision: whether to authorize controlled re-AI for the three failed tasks after code and deployment are accepted.
5. TestAcceptanceEngineer: bounded re-AI or pressure rerun only if explicitly authorized.

### Proposed Task A: AI Timeout Classification And Retry Contract

Assignee: `DevelopmentEngineer`

Scope:

- `server/services/ai/metadata-worker.mjs`
- `server/services/ai/providers/ollama.mjs`
- related tests under `server/tests/`
- UI copy/status mapping only if needed to expose explicit retry eligibility without declaring success

Required behavior:

- Preserve strict no-skeleton fallback.
- Classify first-pass timeout, repair timeout, parse/schema failure, and provider unreachable separately.
- Record retry eligibility metadata for `failed/ai` tasks, without automatically retrying them.
- Make timeout policy explicit by phase: first pass and repair pass may need different deadlines or smaller output budgets.
- Avoid infinite retry loops; failed AI tasks must not be auto-recovered by generic failed-task recovery.

Acceptance criteria:

- Focused tests prove strict mode still fails instead of skeleton fallback.
- Tests prove timeout metadata includes phase, timeout kind, duration, timeoutMs, provider, model, and retry eligibility.
- Tests prove failed AI tasks are not automatically requeued.
- `git diff --check` and relevant static checks pass.

### Proposed Task B: Pressure-Aware Dependency Health

Assignee: `DevelopmentEngineer`

Scope:

- `server/upload-server.mjs` dependency-health route and tests.

Required behavior:

- Keep MinIO/MinerU parse blocking semantics for upload admission.
- Keep Ollama health visible, but do not let a pressure-period 1-token smoke timeout masquerade as parse-blocking failure.
- Add or expose a lighter pressure-mode health response that separates:
  - service reachability;
  - model presence;
  - model residency;
  - generation smoke result;
  - active pressure/load caveat.
- Avoid extra load during active pressure monitoring unless explicitly requested.

Acceptance criteria:

- Existing dependency-health smoke tests still pass.
- New tests cover resident model + chat timeout classification.
- Monitoring documentation/report language distinguishes readiness signal from business AI SLA.

### Proposed Task C: Failed AI Task Disposition Decision

Assignee: `Director` then `User`

Decision needed:

- Leave the three failed AI tasks as failed evidence; or
- after Task A/B are accepted and deployed, authorize exactly one controlled re-AI wave for only the three failed tasks; or
- discard current pressure-run recovery and schedule a fresh pressure rerun after remediation.

Constraints:

- No repair/retry/reparse/re-AI before explicit authorization.
- Do not touch the remaining active MinerU task while it is still running unless a separate user decision authorizes stop/cleanup.

## Handling Current Failed And Active Tasks

Current failed AI tasks should remain `failed/ai` until Director/User authorizes a controlled follow-up. They are valuable failure evidence and should not be silently repaired.

The remaining active MinerU task should be observed, not mutated, until it reaches terminal state or crosses a separately defined stale threshold. If it later completes, it may create another AI job; if it later fails or times out, that is a separate parse/MinerU disposition event, not part of the three AI-timeout failures.

## Risks And Residual Debt

- A longer timeout alone may hide slow failures and extend pressure runs indefinitely.
- Smaller prompts alone may reduce quality if evidence-pack constraints become too aggressive.
- Retrying failed AI jobs without phase classification can repeat the same 180s failure and waste hours.
- dependency-health can become a load amplifier if monitoring keeps triggering generation probes during pressure tests.
- The current report does not establish pressure PASS, L3, production readiness, or release readiness.

## Recommended Next Actor

`Director`

Recommended Director action:

1. Review this architecture report.
2. If accepted, dispatch Task A to `DevelopmentEngineer`.
3. Keep current failed AI tasks and the active MinerU task untouched unless/until a user decision authorizes retry/re-AI/cleanup.

