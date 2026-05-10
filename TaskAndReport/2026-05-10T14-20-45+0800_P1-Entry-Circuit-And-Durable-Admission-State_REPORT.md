# Lucode Report: P1 Entry Circuit And Durable Admission State

## Basis

- Based on Lucia task brief: `TaskAndReport/2026-05-10T14-20-45+0800_P1-Entry-Circuit-And-Durable-Admission-State_TASK.md`
- Related activation evidence: `TaskAndReport/2026-05-10T15-11-28+0800_P0-Apply-Production-Runtime-Env-Ownership-Contract_LUCIA_REVIEW.md`
- Execution role: Lucode
- Development path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Implementation branch: `lucode/p1-entry-circuit-durable-admission-state`
- Implementation HEAD: `0ceedd3`

## Result Classification

`DURABLE_ADMISSION_CIRCUIT_IMPLEMENTED_READY_FOR_LUCIA_REVIEW`

Lucode implemented a code-level shared MinerU admission circuit. The circuit promotes submit-probe evidence from diagnostics into a durable DB-backed state that can be read by frontend upload UI, `/tasks` intake, worker, dependency health, and ops evidence surfaces.

No production deployment, production validation upload, pressure test, failed-task repair, or release-readiness claim was performed in this task.

## Files Changed

Implementation branch `lucode/p1-entry-circuit-durable-admission-state` changes:

- `server/services/mineru/admission-circuit.mjs`
- `server/db-server.mjs`
- `server/lib/task-actions-routes.mjs`
- `server/services/queue/task-worker.mjs`
- `server/upload-server.mjs`
- `src/app/hooks/useFileUpload.ts`
- `src/app/components/BatchUploadModal.tsx`
- `src/app/components/DependencyHealthBanner.tsx`
- `server/tests/dependency-health-smoke.mjs`
- `server/tests/mineru-submit-circuit-breaker-smoke.mjs`

## Circuit State Model

The durable state is stored through the existing settings path under key `mineruAdmissionCircuit`.

State shape includes:

- `version`: `mineru-admission-circuit.v0.1`
- `state`: `open` or `closed`
- `reason`
- `message`
- `openedAt`
- `closedAt`
- `cooldownUntil`
- `lastSubmitProbe`
- `lastSuccessfulSubmitAt`
- `closeCriteria`
- `counts`
- `updatedAt`

The first-version operator message is:

```text
MinerU 当前不可接收新任务，文件未收取，请稍后重试。
```

## Trigger And Close Rules

Circuit open triggers include:

- MinerU `/tasks` HTTP `5xx`;
- submit timeout;
- `ECONNREFUSED` or equivalent connection failure;
- invalid submit response, including invalid JSON or missing `task_id` / `taskId`.

Circuit close requires all of:

- submit probe succeeds with a task id;
- cooldown has elapsed;
- active-task snapshot is clean enough for new intake;
- dependency-health has no blocking condition.

The implementation explicitly keeps `/health` 200 insufficient for closing the circuit.

## Frontend And Intake Behavior

Frontend upload UI:

- reads the shared admission state through `/__proxy/upload/ops/mineru/admission-circuit`;
- prevents adding new PDF-like MinerU jobs to the local batch queue when the circuit is open;
- shows the exact operator-facing message from the task brief.

Backend `/tasks` intake:

- performs a submit-probe admission check before accepting non-Markdown MinerU-bound uploads;
- returns HTTP `503` before MinIO, Material, or ParseTask creation when the circuit is open or MinerU submit admission is blocked;
- returns `code: MINERU_ADMISSION_CIRCUIT_OPEN` when the durable circuit is open;
- preserves the Markdown bypass behavior because Markdown does not require MinerU parsing.

Worker behavior:

- records submit-path dependency failures into the durable admission circuit;
- reads the durable circuit before processing pending local-MinerU tasks, so a restarted worker still respects the open circuit;
- keeps the existing in-process pause as a fast local guard, not the only source of truth.

## Ops Evidence Path

Added or extended read surfaces:

- `GET /__proxy/upload/ops/mineru/admission-circuit`
- `GET /__proxy/upload/ops/dependency-health`
- `GET /__proxy/upload/ops/dependency-health?mineruSubmitProbe=true`

The dependency-health MinerU section now includes `admissionCircuit` evidence. Default dependency-health remains lightweight unless submit probe is explicitly requested or enabled by existing submit-probe controls.

## Test Evidence

### Syntax checks

- `node --check server/upload-server.mjs` -> exit `0`
- `node --check server/services/queue/task-worker.mjs` -> exit `0`
- `node --check server/services/mineru/admission-circuit.mjs` -> exit `0`

### Diff hygiene

- `git diff --check` -> exit `0`

### Dependency-health smoke

Command:

```bash
node server/tests/dependency-health-smoke.mjs
```

Exit `0`.

Summary:

```text
Results: 48 passed, 0 failed
```

Covered evidence included:

- submit probe failure opens durable admission circuit;
- `/health`-only check still sees MinerU health OK;
- `/health`-only check does not run submit probe;
- `/health` 200 alone does not close the admission circuit;
- successful submit probe closes the circuit after cooldown and clean active diagnostics;
- `POST /tasks` returns `503` when the submit circuit opens;
- `POST /tasks` returns the exact operator message;
- `POST /tasks` succeeds when `/health` and submit probe are both OK;
- Ollama down still does not block parse.

### Submit circuit breaker smoke

Command:

```bash
node server/tests/mineru-submit-circuit-breaker-smoke.mjs
```

Exit `0`.

Summary:

```text
Results: 10 passed, 0 failed
```

Covered evidence included:

- submit-path HTTP `500` opens durable MinerU admission circuit;
- first task remains `pending` / `dependency-blocked`;
- Material state is normalized to blocked, not failed;
- circuit breaker prevents another pending task from being submitted after worker restart.

### TypeScript

Command:

```bash
npx pnpm@10.4.1 exec tsc --noEmit
```

Exit `0`.

### Build

Command:

```bash
npx pnpm@10.4.1 run build
```

Exit `0`.

Summary:

```text
vite v6.3.5 building for production...
✓ 1651 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.32 kB
dist/assets/index-Bhv8R7HJ.css   61.17 kB │ gzip:  11.15 kB
dist/assets/index-CvrHRb9w.js   698.60 kB │ gzip: 190.17 kB
(!) Some chunks are larger than 500 kB after minification...
✓ built in 1.57s
```

The chunk-size warning is existing Vite build output and was not introduced as a task blocker.

## Skipped Checks

- Production deployment: skipped because this task was scoped to implementation and Lucia review, not deployment.
- Production validation upload or pressure test: skipped because the task brief forbids pressure tests and production mutation in this task.
- Failed pressure-task repair: skipped because it was outside the task scope and would require separate Lucia/Director authorization.
- L3, production release readiness, or full-site acceptance: not claimed.

## GitHub Sync

- Started from synchronized `origin/main`.
- Created and pushed implementation branch:
  - branch: `lucode/p1-entry-circuit-durable-admission-state`
  - HEAD: `0ceedd3`
- Report and tracking-list updates are recorded on `main` for Lucia task review.
- Branch is not merged to `main`.

## Remaining Work For P2 Queue-Pressure

The new durable circuit exposes enough state for P2, but P2 still needs separate design and implementation for:

- richer queue-pressure display;
- Director/operator dashboard wording;
- retry/cooldown UI;
- possible explicit admin acknowledge/reset controls if Lucia scopes them.

## Remaining Work For P3 Ollama Stability

Ollama stability was not changed in this task. Remaining P3 concerns include:

- transport retry and keep-alive behavior;
- cold-load readiness;
- clear distinction between real AI metadata and skeleton fallback;
- any model/runtime stability policy Lucia chooses to scope later.

## Risks And Residual Technical Debt

- Circuit closure depends on submit-probe evidence and the active-task snapshot available to the upload-server process. Production deployment must verify those surfaces against the actual runtime after Lucia acceptance.
- First-version frontend blocking prevents newly selected files from entering the batch queue when the circuit is open. Already listed local queue items still depend on server-side admission at submit time.
- The implementation intentionally avoids a durable intake queue. When the circuit is open, the file is not retained for later parsing.

## Review Requirement

Lucia review is required before merge, deployment, manual validation restart, pressure testing, or any readiness promotion.

