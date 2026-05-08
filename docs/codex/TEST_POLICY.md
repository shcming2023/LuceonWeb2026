# Luceon2026 Validation Policy

Last updated: 2026-05-08

## Local Test Sample Library

Local validation tasks may use sample files from:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Rules:

- Treat the directory as a read-only sample source.
- The directory is outside this repository and must not be synchronized to GitHub.
- Do not delete, move, rename, modify, normalize, or otherwise pollute original sample files.
- Do not copy sample files into the repository for commit.
- Validation reports may record absolute paths, file sizes, hashes, task IDs, produced artifacts, and observed results.
- If a task needs to create derived files, temporary copies, or transformed samples, the task brief must specify a separate output location and cleanup/preservation rule.

## Validation Levels

### L1: Fast Code Gate

Execution owner: `Lucode`; review owner: `Lucia`

Purpose: determine whether the code is obviously broken before deeper environment validation.

Typical commands:

```bash
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
npx pnpm@10.4.1 run local:check
npx pnpm@10.4.1 run test:smoke
```

L1 must not be reported as L2, UAT, or production validation.

### L2: Tier 2 Near-Production Validation

Execution owner: `Lucode` when assigned by Lucia; review owner: `Lucia`.

Purpose: validate real integration behavior in a near-production local or staging environment.

Current main L2/UAT target:

- task name: `P1-real-runtime-uat-local-mineru-minio-ollama9b`
- local Conda-deployed MinerU
- Docker-deployed MinIO
- Ollama-deployed project-required 9B model
- real Luceon upload, parse, object-storage, AI metadata, task-state, and result-library behavior
- `aiClassificationProvider` must not be `skeleton`
- parsed artifact evidence must be non-empty

Current accepted result:

- `P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: `TaskAndReport/2026-05-07T09-31-59+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_REPORT.md`, accepted by `TaskAndReport/2026-05-07T09-35-39+0800_P0-Main-Rebuilt-Runtime-Tier2-Standard-Validation_LUCIA_REVIEW.md`.
- Validated report HEAD: `1da8ce1a55c8b4115fbd30c4fc707f21355ccfb8`.
- Scope: local rebuilt runtime at `http://localhost:8081`, Tier 2 Standard dependency-health and smoke validation after MinerU submit-path probe merge.
- Confirmed behavior:
  - `mineru.healthOk=true`.
  - `mineru.submitProbe.enabled=true`.
  - `mineru.submitProbe.ok=true`.
  - `mineru.submitProbe.status=202`.
  - `BASE_URL=http://localhost:8081 npx pnpm@10.4.1 run tier2:standard:check` passed.
  - `BASE_URL=http://localhost:8081 bash uat/smoke-test.sh` passed, 12 passed / 0 failed / 0 skipped.
- Pending scope: no production release readiness, no L3 validation, no large-PDF soak, no concurrency validation, no rollback rehearsal, and no all-error-path coverage.

- `P2-upload-entry-testability-enhancement`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated branch HEAD: `042c6508e8357fa07c6a0bb12ec48fc09129e8cc`
- Main merged HEAD: `042c6508e8357fa07c6a0bb12ec48fc09129e8cc`
- Scope: local real runtime UAT, `/cms/tasks` upload file input testability.
- Confirmed behavior:
  - `data-testid` upload contract present.
  - Playwright `setInputFiles` works on `task-upload-file-input`.
  - real PDF creates task/material through the frontend input path.
  - task appears in task list.
  - task detail opens.
  - local MinerU completed.
  - MinIO parsed artifacts available.
  - Ollama provider/model: `ollama` / `qwen3.5:9b`.
  - final state: `review-pending`.
  - browser console clean.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
- Pending scope: no folder input validation, no error-path validation, no concurrent upload validation, no large-file upload validation, and no L3/production-readiness claim. The raw object list API `rawTotal=0` observation remains non-blocking and unpromoted unless separately assigned.

- `P3-task-list-pending-sync-tooltip-polish`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated branch HEAD: `3962fb1d7834a4b13683503d740fb9ea7edb28c1`
- Main merged HEAD: `3962fb1d7834a4b13683503d740fb9ea7edb28c1`
- Scope: local real runtime UAT, task list `待同步` tooltip polish.
- Confirmed behavior:
  - Tooltip text: `状态映射待同步：任务、资料、AI 任务或产物状态暂未完全对齐；不代表审核失败。`
  - `状态一致` title did not regress.
  - Page did not show `需审计`.
  - browser console clean.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no full badge state matrix validation, and no upload modal / file picker validation.

- `P2-operator-main-workflow-polish-bundle`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated implementation HEAD: `c60152d72fe8dae545a2c18c3f425b6f0620ecf4`
- Scope: local real runtime UAT, task `task-1777849339744`, material `mat-1777849339732`, focused Operator polish checks for MetadataTab tags, completed actions, completed list wording, and overview next-action label.
- Confirmed behavior:
  - MetadataTab tag save immediate sync passed.
  - read-only chip updates immediately after save without refresh.
  - re-entering edit mode preserves the saved draft tags.
  - delete tag -> save -> read-only chip disappears immediately without refresh.
  - refresh UI matches API `Material.tags`.
  - `metadata.tags` was not polluted.
  - completed task detail no longer shows misleading `审核通过` main button.
  - completed task list row no longer shows review action.
  - completed list row no longer shows `需审计`; it shows `待同步` where relevant.
  - overview label now shows `下一步动作`.
  - browser console error/warn empty.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no all-task-state validation, no all-error-path validation, and no upload file-picker / upload modal validation.
- Follow-up polish status: `待同步` tooltip clarity was later resolved by `P3-task-list-pending-sync-tooltip-polish`.

- `P1-operator-main-workflow-usability-review`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `1849beacef6d755859c45e7704ddd467dc3b03aa`
- Scope: local real runtime UAT, task `task-1777849339744`, material `mat-1777849339732`, Operator main workflow: upload real PDF, task list, task detail, MetadataTab, tag save, review approval, ZIP download, and event log.
- Confirmed behavior:
  - real PDF upload created the task successfully.
  - local MinerU completed.
  - MinIO raw and parsed artifacts were available.
  - Ollama provider/model: `ollama` / `qwen3.5:9b`.
  - `review-pending` -> `completed` / `done` can complete.
  - `Material.tags` saved successfully.
  - `metadata.tags` was not polluted.
  - ZIP download succeeded.
  - event log explains MinerU, MinIO, AI, and review stages.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
  - browser console error/warn empty.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no complete browser file-picker / upload modal validation, no all-task-state validation, and no all-error-path validation.
- Follow-up polish status: MetadataTab tag save immediate chip/draft sync, completed `审核通过` action visibility, completed-list `需审计` wording, and completed overview next-action label were later resolved by `P2-operator-main-workflow-polish-bundle`.

- `P1-metadatatab-expanded-tag-interaction-validation`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `8601eab2dd784f7d808f4bc9257b3b5c47909f9a`
- Scope: real local runtime stack, task `task-1777788279069`, material `mat-1777788279055`, MetadataTab current-tags expanded interaction.
- Confirmed behavior:
  - multi-tag add passed.
  - tag deletion passed.
  - duplicate tag handling passed.
  - refresh persistence passed.
  - toast success was observed.
  - `Material.tags` remains the Operator current tags fact source.
  - `metadata.tags` remains the AI/parse tag source and was not polluted.
  - internal diagnostics title includes `AI 任务`.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
  - browser console error/warn empty.
- Final `Material.tags`: `["uat-tag-persistence","uat-tag-multi-a","uat-tag-multi-b"]`
- `metadata.tags` remained: `["PDF","OCR","Pipeline","表格识别","公式识别","含解析产物"]`
- Pending scope: no L3/production-readiness claim, no full-site UI review, no validation for other task states, concurrent editing, or failure-toast/error-path behavior.
- Non-blocking polish: after save success, current-page chips may not immediately sync to the final state, but refresh stabilizes the state. Potential follow-up: `P2-metadatatab-tags-immediate-chip-sync-polish`.

- `P1-ui-clarity-polish-after-review-pass`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Validated HEAD: `87543399673308f2b8ff2febf145c85b3e342f75`
- Scope: `/cms/tasks`, review-pending task detail overview, internal diagnostics folded area, task `task-1777788279069`, material `mat-1777788279055`.
- Validated behavior:
  - task list main status remains `待复核`.
  - same-row diagnostics badge now shows `状态一致`, with no duplicate second `待复核`.
  - overview shows current state, current stage, generated artifact, and next action.
  - AI Job / model technical info no longer appears in the main summary by default.
  - AI metadata job/model remains available after expanding internal diagnostics.
  - dependency-health `blocking=false`.
  - consistency audit `ok=true`, `findingsCount=0`.
  - browser console error/warn empty.
- Pending scope: no MetadataTab full revalidation claim, no products/library/settings review claim, no multi-task-state UI validation claim, and no L3/production-readiness claim.
- Follow-up polish status: internal diagnostics title clarity was later resolved by `P1-metadatatab-expanded-tag-interaction-validation`; the title now includes `AI 任务`.

- `P1-latest-ui-metadata-task-detail-interaction-review`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Scope: latest UI/code baseline `origin/main@cb6f2376b5146e53c7c83cba62d36bac2236e7e3`, real local runtime stack, review-pending task `task-1777788279069`, material `mat-1777788279055`, `/cms/tasks`, task detail overview, MetadataTab, classification/tag display, and current tag persistence state.
- Validated facts:
  - task list and detail use `待复核` consistently.
  - overview answers state, stage, artifact, and next action.
  - MetadataTab four-layer structure is visible: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) default folded.
  - provider/model displayed as `ollama` / `qwen3.5:9b`.
  - `[object Object]` regression not present.
  - `Material.tags=["uat-tag-persistence"]`.
  - `metadata.tags` remains the AI/parse tag source.
  - dependency-health `blocking=false`.
  - consistency audit `ok=true`, `findingsCount=0`.
  - browser console error/warn empty.
- Pending scope: no L3/production-readiness claim, no full-site UI review, no validation for other task states, concurrent editing, or failure-toast/error-path behavior. Tag deletion, multi-tag editing, duplicate-tag handling, refresh persistence, and success toast observation were later covered by `P1-metadatatab-expanded-tag-interaction-validation`.
- Follow-up polish status: duplicate `待复核` in the task-list row and default main-summary AI job/model exposure were later resolved by `P1-ui-clarity-polish-after-review-pass`.

- `P0-metadata-tab-review-architecture-first-pass`: `PASS`
- Scope: MetadataTab information architecture first-pass closure, covering only a real `review-pending` sample.
- Validated HEAD: `372f060450a387da7122064520ecc6a682198dda`
- Later tag persistence HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`
- Validated structure: 审核摘要; 当前保存值; AI 建议与证据; 技术详情 (`Technical Details`) 默认折叠.
- Actual provider/model displayed from result facts: `ollama` / `qwen3.5:9b`
- `[object Object]` controlled-classification leak fixed and rerun passed.

- `P1-fix-metadata-current-tags-persistence-contract`: `PASS`
- Scope: `review-pending` task single-tag add + refresh persistence path.
- Validated HEAD: `cb6f2376b5146e53c7c83cba62d36bac2236e7e3`
- Task: `task-1777788279069`
- Material: `mat-1777788279055`
- Test tag: `uat-tag-persistence`
- Backend fact: `Material.tags=["uat-tag-persistence"]`
- `metadata.tags` remains the AI/parse tag source and is not the Operator current-tags fact source.
- Consistency audit: `ok=true`, `findingsCount=0`
- Dependency-health: `blocking=false`
- Pending scope: other task states, concurrent editing, and failure-toast/error-path behavior are not validated.

- `P1-uat-verify-disable-ai-skeleton-local9b-after-decouple`: `PASS`
- Lucia final judgment: `PASS`
- Scope: strict no-skeleton local real runtime UAT with local `qwen3.5:9b`; this does not prove the retired online MinerU v4 Standard path.
- HEAD: `3714590bb2fe351bfc018cd369a08c5491c98628`
- Required local runtime env:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- Must not require:
  - `MINERU_ONLINE_API_BASE_URL`
  - `MINERU_ONLINE_API_TOKEN`
- UAT taskId: `task-1777788279069`
- materialId: `mat-1777788279055`
- MinerU taskId: `ebfbd78e-5304-4748-a6e6-c527f3b9b7c6`
- AI job: `ai-job-1777788288960-12c7`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: pending for this specific run
- Baseline meaning: current valid configuration baseline is strict no-skeleton + local `qwen3.5:9b` for the local real runtime stack.

- `P1-real-runtime-uat-local-mineru-minio-ollama9b`: `PASS`
- Lucia final judgment: `PASS`
- Scope: local real runtime UAT only; this does not prove the retired online MinerU v4 Standard path.
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.

The previous online MinerU v4 Standard target is retired from the current main validation path and is retained only as legacy / compatibility-only context:

- retired target: MinerU online v4 + `MINERU_ONLINE_API_TOKEN` + `MINERU_ONLINE_MODEL_VERSION=vlm` + local Docker Ollama `qwen3.5:0.8b`
- missing `MINERU_ONLINE_API_TOKEN` no longer blocks the current main UAT.
- do not report the retired online target as passed unless a future compatibility task explicitly requires and proves it.

Current UAT command set is task-specific. Lucode must start from the real runtime path assigned by Lucia, confirm the effective dependency chain, then run the assigned checks without destructive cleanup.

Required report fields:

- machine and OS
- commit hash
- command list and exit codes
- Docker/compose status
- dependency-health result; for Tier 2 Standard, MinerU evidence must include `dependencies.mineru.healthOk=true` and `dependencies.mineru.submitProbe.ok=true`
- local Conda MinerU process/reachability/effective runtime evidence
- Docker MinIO health and object-storage evidence
- Ollama health and effective 9B model evidence
- parsed artifact evidence, including Markdown, JSON, ZIP, or content-list evidence when applicable
- AI job id
- AI provider and model
- AI duration
- `aiClassificationProvider`
- whether skeleton fallback was used
- consistency audit result
- Director browser verification state

Accepted local real runtime UAT evidence for the 2026-05-03 PASS:

- Machine: `concmdeMac-mini.local`
- HEAD: `d0af4837b6d13605cf5245d275031e0a6a13f895`
- Runtime URL: `http://127.0.0.1:8081/cms/`
- Compose files: `docker-compose.yml` + `docker-compose.override.yml`
- Upload task: `task-1777784999485`
- Material: `mat-1777784999468`
- Local MinerU task: `8c8216c8-6f92-45ea-b76a-c719fcb9e326`, completed
- Raw object: `originals/mat-1777784999468/source.pdf`
- Parsed prefix: `parsed/mat-1777784999468/`
- MinIO artifacts: `artifact-manifest.json`, `full.md`, `mineru-result.zip`
- `full.md`: 211 bytes, HTTP 200 via presigned URL
- AI job: `ai-job-1777785048072-dfc0`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Final state: task `review-pending`; material `reviewing` / `completed` / `analyzed`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: completed; task details usable

Accepted strict no-skeleton local9b evidence for the 2026-05-03 PASS:

- HEAD: `3714590bb2fe351bfc018cd369a08c5491c98628`
- Required local runtime env: `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- Online MinerU env not required: `MINERU_ONLINE_API_BASE_URL`, `MINERU_ONLINE_API_TOKEN`
- UAT taskId: `task-1777788279069`
- materialId: `mat-1777788279055`
- MinerU taskId: `ebfbd78e-5304-4748-a6e6-c527f3b9b7c6`
- AI job: `ai-job-1777788288960-12c7`
- AI provider/model: `ollama` / `qwen3.5:9b`
- Consistency audit: `ok=true`, `findingsCount=0`
- Director browser verification: pending for this specific run

### L3: Home Mac Mini Production Truth

Execution owner: `Lucode` when assigned by Lucia; acceptance owner: `Lucia` and Director

Purpose: validate the actual staging or production environment on the Home Mac mini.

Only L3 can be treated as production truth. L1 and L2 can support a release decision, but they do not replace L3.

Current accepted L3 result:

- `P0-l3-home-mac-mini-staging-real-runtime-e2e-validation`: `PASS`
- Lucia final judgment: `PASS`
- Evidence source: historical validation report recorded `PASS_CANDIDATE`, then Lucia accepted it as `PASS`.
- Scope: Home Mac mini staging / production-like independent environment.
- Staging path: `/Users/concm/staging/Luceon2026`
- Staging URL: `http://127.0.0.1:18081/cms/tasks`
- Evidence directory: `/Users/concm/ops/evidence/luceon2026/l3-20260505-064229/`
- HEAD: `d522fdad98eaec4c149a719df335b02595121741`
- compose project: `luceon2026-staging`
- compose files used: `docker-compose.yml`, `docker-compose.staging.local.yml`
- Explicitly not used: `docker-compose.override.yml`, `docker-compose.tier2-standard.yml`
- Runtime: local conda MinerU, Docker MinIO, host Ollama `qwen3.5:9b`, `DISABLE_AI_SKELETON_FALLBACK=true`, `OLLAMA_TIER2_MODEL=qwen3.5:9b`, `STORAGE_BACKEND=minio`.
- Key IDs: task `task-1777934728573`, material `3969562638063124`, AI job `ai-job-1777934731633-3e49`, MinerU task `6276827e-8b3e-4d2f-bad0-b8a8cbccf4ad`, uploaded file `l3-staging-e2e-1777934728043.pdf`.
- ZIP sha256: `d7e6e51a55d058d5b368ff7435dfc7aa6bf5681ddb7de1f3bf7a41ad03fe7cfb`
- Confirmed L3 E2E behavior:
  - frontend upload input via Playwright `setInputFiles`.
  - task/material created.
  - local MinerU task completed.
  - MinIO raw/parsed/AI raw artifacts available.
  - AI provider/model: `ollama` / `qwen3.5:9b`.
  - provider/model was not `skeleton`.
  - task reached `review-pending`.
  - MetadataTab four-layer structure validated.
  - `Material.tags` updated.
  - `metadata.tags` unchanged.
  - review approval completed.
  - task reached `completed` / `done`.
  - ZIP downloaded with size/hash evidence.
  - browser console had no business error/warn.
  - dependency-health `blocking=false`.
  - consistency audit `findingsCount=0`, `blockingFindings=0`.
- Pending scope: no production release readiness, no full-site completion, no all-error-path coverage, no concurrent upload coverage, no large PDF / long-run stability coverage, no permissions/security coverage, no online MinerU v4 compatibility, no folder upload coverage, no settings/products/library full coverage, and no rollback/backup rehearsal completion.
- Non-blocking follow-ups:
  - `P3-task-detail-toast-overlay-toolbar-polish`: toast can overlay the task detail toolbar and block a normal Playwright click on `下载 ZIP`.
  - `P2-completed-material-status-consistency-review`: after review approval, task is `completed/done` but `Material.status` remains `reviewing`; consistency audit currently does not flag it.

## Result Vocabulary

Use these words exactly in reports:

- `PASS`: command or validation target completed and met the stated criteria.
- `FAIL`: command or validation target ran and violated the criteria.
- `BLOCKED`: required environment, credential, service, or input was missing.
- `SKIPPED`: intentionally not run, with reason.
- `PENDING`: started but not completed by the handoff point.

Do not use "passed" for a check that did not return a green exit code.

## Secret Handling

MinerU, AI provider, and other secrets must only be injected through local process environment or local uncommitted secret management.

Reports may say:

```text
MINERU_OR_AI_TOKEN=<present, redacted>
```

Reports must not include any full token or secret value.

## Destructive Operations

These require explicit Director approval:

- `docker compose down -v`
- deleting Docker volumes
- clearing MinIO buckets
- clearing DB data
- deleting production or staging deployment data
- changing production secrets

Rebuilding containers with `up -d --build --force-recreate` is allowed for L2 when the task explicitly asks for it, as long as volumes are not wiped.
