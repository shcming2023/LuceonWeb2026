# Lucode Task Brief: P0 Post-Ollama-Standardization Production Candidate Validation

- Task ID: `TASK-20260509-101633-P0-Post-Ollama-Standardization-Production-Candidate-Validation`
- Issued at: 2026-05-09T10:16:33+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `c9a24a459fb6d5445174f4103ce0c2dc468b7e71`
- Production path: `/Users/concm/prod_workspace/Luceon2026`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`

## Director Authorization

Director authorized one post-standardization production-candidate validation pass after Lucia accepted Ollama runtime standardization.

This task is a new bounded validation route. It is not a production release-readiness declaration, and Lucode must not claim production release readiness.

## Objective

Verify whether the production candidate can now pass the critical Phase 1 runtime path after local Ollama endpoint standardization:

upload -> MinIO intake -> local MinerU -> parsed artifacts -> Ollama `qwen3.5:9b` AI metadata -> operator review state.

## Required Preflight Gates

Before any controlled upload:

1. Confirm production workspace and Git state:
   - production HEAD;
   - production `git status --short --branch`;
   - current repo main HEAD;
   - production-local override boundary preserved.
2. Confirm strict runtime settings:
   - `DISABLE_AI_SKELETON_FALLBACK=true`;
   - `ALLOW_AI_SKELETON_FALLBACK=false` or unset equivalent that does not enable fallback;
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`;
   - MinIO console remains local-only bound if present.
3. Confirm no active heavy work before upload:
   - no active parse-running MinerU task;
   - no active Ollama metadata-running task;
   - no takeover-required active MinerU ingestion issue.
4. Run warm dependency-health with MinerU submit probe:

```bash
curl -fsS --max-time 35 'http://localhost:8081/__proxy/upload/ops/dependency-health?mineruSubmitProbe=true'
```

Required pre-upload result:

- overall `ok=true`;
- `mineru.ok=true`;
- `mineru.submitProbe.ok=true`;
- `ollama.ok=true`;
- `ollama.chatOk=true`;
- model `qwen3.5:9b`.

If this gate fails, stop before upload and report `BLOCKED_PRE_UPLOAD_GATE`.

## Controlled Upload Scope

If all gates pass, create at most one controlled validation upload.

Use one sample from the approved true sample boundary:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Prefer a sample already used in the prior approved validation set if it is available and unchanged. Treat the sample directory as read-only:

- do not copy samples into the repository;
- do not rename, move, delete, normalize, or modify samples;
- reports may record path, size, hash, and validation observations only.

## Required Runtime Evidence

For the controlled upload, record:

- sample path, size, and hash;
- task ID, material ID, objectName, and provider;
- upload/MinIO intake durability evidence;
- MinerU task ID and stage transitions;
- parsed artifact evidence, including parsed object prefix and manifest/full.md presence where available;
- AI metadata job ID and final state;
- final task state and material state;
- whether AI reached `review-pending` or `completed`;
- whether strict no-skeleton fallback was preserved;
- active heavy-stage counts showing MinerU and Ollama did not run concurrent heavy work outside the approved single-sample validation.

## Required Checks

Run:

```bash
git status --short --branch
git diff --check
```

If source code unexpectedly changes, stop and report; this validation task is not a code-change task unless Lucia separately authorizes it.

Run relevant read-only health checks:

- dependency-health with MinerU submit probe before upload;
- post-upload dependency-health or diagnostics as needed;
- `/__proxy/upload/ops/mineru/diagnostics` or equivalent read-only diagnostics after completion/failure.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness;
- create more than one validation upload;
- change source code;
- change production `docker-compose.override.yml`;
- change model selection, timeout policy, or secrets;
- pull, delete, reload, replace, or retag Ollama models;
- restart, rebuild, redeploy, or rollback production services unless explicitly required by Lucia and already bounded here;
- delete or mutate DB rows, MinIO objects, Docker volumes, logs, existing tasks, artifacts, or sample files;
- enable skeleton fallback or silent degradation;
- mask AI/Ollama failure as healthy.

If the validation fails, preserve evidence and report the exact blocker.

## Expected Outcomes

Return exactly one outcome:

- `VALIDATION_PASS_READY_FOR_LUCIA_RELEASE_REVIEW`: all required runtime gates and controlled upload path pass; Lucia still must decide release readiness separately.
- `BLOCKED_PRE_UPLOAD_GATE`: pre-upload gate fails, and no upload was created.
- `VALIDATION_FAILED_WITH_EVIDENCE`: upload was authorized and created, but the runtime path failed or ended below required state.
- `BLOCKED_SCOPE_BOUNDARY`: safe progress requires an operation outside this task's authorization.

## Required Report

Create:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Post-Ollama-Standardization-Production-Candidate-Validation_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 59 with:

- status;
- report path;
- branch / HEAD if any repository report commit is made;
- sample evidence;
- final outcome;
- Next Actor `Lucia`.

