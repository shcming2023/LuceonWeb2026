# P0 Stage-Queued Sample Validation Run

Task:
P0 Stage-Queued Sample Validation Run

Task ID:
`TASK-20260508-215138-P0-Stage-Queued-Sample-Validation-Run`

Assignee:
Lucode

Issued by:
Lucia

Issued at:
2026-05-08T21:51:38+0800

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
- `TaskAndReport/2026-05-08T21-43-25+0800_P0-Stage-Queued-Sample-Validation-Run-Authorization_DECISION.md`
- `TaskAndReport/2026-05-08T21-51-38+0800_P0-Stage-Queued-Sample-Validation-Run-Authorization_LUCIA_REVIEW.md`
- `TaskAndReport/2026-05-08T21-07-00+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_REVISED_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Director Authorization

Director approved Option A: up to three true-directory samples for a controlled stage-queued production validation run.

This task authorizes controlled validation artifact creation only. It does not authorize production release readiness.

## Objective

Execute the stage-queued validation run and collect evidence that:

- upload/storage intake can accept the next sample after the prior sample is durable;
- MinerU active parse-running count remains `<=1`;
- Ollama active metadata/Ollama-running count remains `<=1`;
- all selected samples use the true sample directory without modifying it.

## Authorized Samples And Order

1. Small diagnostic sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf`
   - Expected size: `1041695`
   - Expected SHA-256: `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8`
2. Medium educational sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
   - Expected size: `3457503`
   - Expected SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`
3. Conditional large education sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
   - Expected size: `39063547`
   - Expected SHA-256: `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022`
   - Start only if samples 1 and 2 pass stage-queued gates and no new risk appears.

Do not use other samples without Lucia/Director approval.

## Pre-Run Gates

Before any upload:

1. Confirm production override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - MinIO console mapping `127.0.0.1:19001:9001`
2. Confirm production services are healthy with read-only `docker compose ps`.
3. Confirm CMS reachable.
4. Confirm DB health OK.
5. Confirm active parse/task states and AI jobs are `0`.
6. Confirm exact sample size and SHA-256 for all selected samples.
7. Perform exactly one bounded non-mutating Ollama warm-up:
   - model `qwen3.5:9b`
   - `num_predict=1`
8. Run warm dependency-health with `mineruSubmitProbe=true`.
9. Proceed only if MinIO, MinerU submit probe, and Ollama are all OK.

If any gate fails, do not upload; write a `BLOCKED` report.

## Stage-Queued Run Rules

### Upload/Storage Intake Handoff

The next sample may be uploaded after the previous sample's upload/storage intake is durable.

Durable intake requires all of:

- upload HTTP response success;
- task ID recorded;
- material ID recorded;
- original objectName recorded;
- provider recorded as `minio`;
- no signed MinIO URL persisted in the report;
- DB task visible by task ID;
- DB material visible by material ID;
- task state/stage trackable, such as queued, running, mineru-processing, ai-pending, ai-running, review-pending, completed, or explicit failed;
- no ambiguous unbounded state.

Per-sample terminal completion is not required before the next upload.

### MinerU Stage Gate

At each poll, record:

- active MinerU parse-running task count;
- active parse task IDs, state, stage, MinerU task ID, message;
- queued/waiting tasks separately from running tasks.

Requirement:

- active MinerU parse-running count must remain `<=1`.

If active MinerU parse-running count exceeds `1`, stop the wave and report accepted failure evidence.

### Ollama Stage Gate

At each AI poll, record:

- active Ollama metadata-running job count;
- active AI job IDs, material IDs, model, state, current phase, message;
- queued/pending jobs separately from active running jobs.

Requirement:

- active Ollama metadata/Ollama-running count must remain `<=1`.

If active Ollama metadata-running count exceeds `1`, stop the wave and report accepted failure evidence.

## Polling Strategy

- Upload/storage intake: poll every `5s` until DB task/material records are visible; max `2` minutes per upload intake.
- MinerU parse stage: poll every `10s`; record active parse set every poll.
- AI metadata stage: poll every `15s` to `30s`; record active AI job set every poll.
- First-wave bound:
  - samples 1 and 2: up to `45` minutes total.
  - sample 3, if started: add up to `45` minutes.

## Stop Conditions

Stop and report if:

- any pre-run gate fails;
- sample size or hash mismatches;
- upload intake durability is not reached;
- any task disappears or becomes untrackable;
- active MinerU parse-running count exceeds `1`;
- active Ollama metadata-running count exceeds `1`;
- sample 1 or 2 exposes queueing defects, slow Ollama instability, MinerU ambiguity, or forbidden state before sample 3;
- more than three uploads would be required;
- any service/Docker/Ollama/model/config/secret/override mutation would be required;
- any DB/MinIO/Docker volume/task/artifact/log deletion would be required;
- skeleton fallback or silent degradation appears;
- signed URLs or secrets would need to be committed.

## Forbidden

- Do not claim production release readiness.
- Do not create more than three uploads.
- Do not use samples outside the authorized list.
- Do not run production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- Do not restart, start, stop, kill, or reload Ollama or any production service.
- Do not change model, timeout, config, secret, or production-local override values.
- Do not delete DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs.
- Do not copy, move, rename, edit, delete, normalize, pollute, or GitHub-sync external samples.
- Do not add skeleton fallback or silent degradation.

## Required Evidence

Report:

- pre-run gate commands and exit codes;
- sample size/SHA-256 reconfirmation;
- upload command/status per sample;
- task ID, material ID, objectName, provider per sample;
- durable intake evidence per sample;
- active MinerU parse set per poll;
- active Ollama metadata job set per poll;
- per task terminal or bounded-timeout state;
- per AI job terminal or bounded-timeout state;
- parsed artifact fields, `parsedFilesCount`, `artifactIncomplete`;
- AI provider/model, input mode, selected length, original length, input hash, trigger reasons where available;
- all stop-condition decisions;
- confirmation of no cleanup/deletion/mutation/sample modification/GitHub sample sync/release-readiness claim.

## Required Output

Write report to:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Stage-Queued-Sample-Validation-Run_REPORT.md`

Report classification must be one of:

- `PASS`
- `FAILED_ACCEPTED_EVIDENCE`
- `BLOCKED`
- `INCONCLUSIVE`

Update `TaskAndReport/TASK_TRACKING_LIST.md`:

- Status `已回报待审`
- `Next Actor=Lucia`
- Report path
- Branch/HEAD
- Summary notes

Commit and push report/task-list changes to GitHub `main`.
