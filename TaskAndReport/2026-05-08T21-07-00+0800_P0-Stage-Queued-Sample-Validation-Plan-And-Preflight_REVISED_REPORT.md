# Lucode Revised Report: P0 Stage-Queued Sample Validation Plan And Preflight

## 1. Result Classification

Result: `PLAN_READY`

This revised report responds to Lucia review:

`TaskAndReport/2026-05-08T20-39-35+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_LUCIA_REVIEW.md`

The original report's preflight facts were accepted, but its plan incorrectly required each sample to reach terminal state before the next upload. This revision corrects the plan to Director's intended stage-queued流水 model:

- after a sample's upload/storage intake is durable, the next upload may start;
- MinerU parse work must remain queued/effectively single-worker;
- Ollama metadata work must remain queued/effectively single-worker;
- no production upload is authorized by this correction report.

No production upload was created. No production release-readiness claim is made.

## 2. Accepted Preflight Evidence Reused

The following preflight evidence from the original report remains unchanged and was accepted by Lucia:

- No production upload was created.
- No production release-readiness claim was made.
- Production override boundary was present:
  - `DISABLE_AI_SKELETON_FALLBACK=true`
  - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
  - MinIO console mapping `127.0.0.1:19001:9001`
- CMS and DB were healthy.
- Dependency-health with MinerU submit probe passed.
- Ollama health passed but was slow at `12740ms`.
- Active parse/task states were `0`.
- Active AI jobs were `0`.
- True sample directory inventory was read-only.
- No production deploy, fast-forward, rebuild, restart, rollback, Docker mutation, service mutation, model/timeout/config/secret/override change, data deletion, sample mutation, GitHub sample sync, skeleton fallback, or silent degradation occurred.

## 3. Branch And HEAD

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- HEAD before revised report: `c073393`

Production workspace evidence from original preflight:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Production HEAD: `8092965c104cee57ff9cb739106e4320dfc22a7d`
- Production `origin/main` after read-only fetch: `983c27ab13223c0bc6659b73351dd74638b97381`
- Production local `docker-compose.override.yml` modification was preserved.
- No production fast-forward, deploy, rebuild, restart, rollback, or Docker mutation was performed.

## 4. True Sample Directory Inventory

True sample directory:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Accepted inventory facts:

- `19` PDF files were observed at max depth 1.
- Multiple `0-byte` files were excluded as likely placeholders or unavailable local content.
- The sample directory was treated as read-only. No file was copied, moved, renamed, edited, deleted, normalized, or synchronized to GitHub.

Recommended first validation wave:

1. Small diagnostic sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf`
   - Size: `1041695`
   - SHA-256: `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8`

2. Medium educational sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
   - Size: `3457503`
   - SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`

3. Conditional large education sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
   - Size: `39063547`
   - SHA-256: `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022`
   - Use only if samples 1 and 2 pass the stage-queued gates.

Fallback medium candidate:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/附件三：考务流程培训-纸笔标准考试.pdf`
- Size: `5349060`
- SHA-256: `d2e8e9bcd5b59e88a516d2143ece6a03060bf01276481e09d7577a5f82c5ae5a`

## 5. Corrected Stage-Queued 流水 Plan

Recommended next task type:

- Controlled production validation artifact run.
- Not production release readiness.
- Max uploads for first stage-queued wave: `3`.
- Use the exact sample order listed above.

### 5.1 Pre-Run Gates

Before any upload in the future validation-run task:

1. Confirm production override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - `127.0.0.1:19001:9001`
2. Confirm `docker compose ps` services healthy.
3. Confirm CMS reachable.
4. Confirm DB health OK.
5. Confirm active parse/task states and AI jobs are `0` before the first upload.
6. Confirm exact sample size and SHA-256 for all selected samples.
7. Perform exactly one bounded non-mutating Ollama warm-up with `qwen3.5:9b`, `num_predict=1`.
8. Run warm dependency-health with `mineruSubmitProbe=true`.
9. Proceed only if MinIO, MinerU submit probe, and Ollama are all OK.

### 5.2 Upload Intake Handoff

The next sample may be uploaded after the previous sample's upload/storage intake is durable.

The handoff condition is satisfied only when all of these are true for the previous sample:

- upload HTTP response returned success;
- `taskId` is recorded;
- `materialId` is recorded;
- original objectName is recorded;
- provider is recorded as `minio`;
- the API response did not need to expose or persist a signed MinIO URL in the report;
- DB task record is visible by `taskId`;
- DB material record is visible by `materialId`;
- task state/stage is trackable, such as queued, running, mineru-processing, ai-pending, ai-running, review-pending, completed, or explicit failed;
- the task has not disappeared and is not in an ambiguous unbounded state.

Once this durable upload/storage intake handoff is met, the next sample may enter upload intake even if the prior sample has not reached terminal state.

This corrects the previous report. Per-sample terminal state is not required before the next upload.

### 5.3 MinerU Single-Worker Proof

The validation run should prove MinerU remains effectively single-worker or stage-queued by collecting evidence at each poll:

- list active tasks in MinerU parse states, for example `queued`, `running`, `mineru-processing`, or equivalent local-MinerU states;
- record each active task ID, stage, state, MinerU task ID, and message;
- verify no more than one task is in an active MinerU parse-running state at the same time;
- if multiple tasks exist, verify later samples remain queued or waiting rather than simultaneously parsing;
- record transition timestamps from upload intake to parse queued/running to parse complete;
- include MinerU submit/task IDs and parsed artifact fields when parse completes.

If evidence shows two or more tasks actively parsing in MinerU at the same time, stop and report `FAILED_ACCEPTED_EVIDENCE` or `INCONCLUSIVE` according to the exact state.

### 5.4 Ollama Single-Worker Proof

The validation run should prove Ollama metadata recognition remains effectively single-worker or stage-queued by collecting evidence at each poll:

- list active AI metadata jobs in states such as `queued`, `running`, `ai-running`, `repair-pass-running`, or equivalent;
- record each active AI job ID, material ID, model, state, current phase, message, and timestamps;
- verify no more than one AI job is actively calling Ollama or running JSON repair at the same time;
- if multiple AI jobs exist, verify later jobs remain queued or pending rather than simultaneously using Ollama;
- record provider request start/success/failure events and repair events per job;
- collect raw trace fields for first pass and repair pass when available.

If evidence shows two or more AI jobs simultaneously using Ollama heavy inference or repair, stop and report `FAILED_ACCEPTED_EVIDENCE` or `INCONCLUSIVE` according to the exact state.

### 5.5 Corrected Stage Flow

Future validation run should follow this flow:

1. Run all pre-run gates.
2. Upload sample 1.
3. Wait only for sample 1 upload/storage intake durability.
4. Upload sample 2.
5. Wait only for sample 2 upload/storage intake durability.
6. Continue polling sample 1 and sample 2 stage states.
7. Confirm MinerU has no simultaneous heavy parse work.
8. Confirm Ollama has no simultaneous heavy AI metadata work.
9. If samples 1 and 2 both remain trackable and do not violate heavy-stage single-worker rules, decide whether to upload sample 3 under the same intake-durable handoff rule.
10. Continue polling all created task IDs and related AI jobs until terminal states or bounded timeout.

Sample 3 is conditional. It should be skipped if samples 1 and 2 already expose queueing defects, slow Ollama instability, MinerU ambiguity, or any forbidden state.

### 5.6 Polling Strategy

Poll all created task IDs, but interpret them by stage:

- Upload/storage intake:
  - poll every `5s` until DB task and material records are visible.
  - max suggested wait per upload intake: `2` minutes.
- MinerU parse stage:
  - poll every `10s`.
  - record active parse set on every poll.
  - verify active parse-running count is at most `1`.
- AI metadata stage:
  - poll every `15s` to `30s`.
  - record active AI job set on every poll.
  - verify active Ollama-running count is at most `1`.
- Overall first-wave bound:
  - samples 1 and 2: up to `45` minutes total.
  - sample 3, if authorized and started: add up to `45` minutes.

### 5.7 Evidence Fields

Per sample:

- path, size, SHA-256;
- upload HTTP code;
- task ID;
- material ID;
- original objectName;
- provider;
- upload intake completion timestamp;
- DB task/material visibility timestamp.

Per task:

- state, stage, message;
- MinerU task ID;
- MinerU active/queued/running evidence;
- parsed artifact fields;
- `parsedFilesCount`;
- `artifactIncomplete`;
- terminal state and timestamp.

Per AI job:

- job ID, material ID;
- state, model, provider;
- queued/running/repair/completed timestamps where available;
- provider request start/success/failure events;
- first-pass and repair-pass raw trace;
- whether repair succeeded;
- terminal state and timestamp.

Queue proof:

- active MinerU parse set per poll;
- active Ollama job set per poll;
- evidence that heavy-stage active count stayed at `0` or `1`;
- explicit violation evidence if active count exceeded `1`.

### 5.8 Stop Conditions

Stop the validation wave if:

- any pre-run gate fails;
- sample size or hash mismatches;
- upload intake durability is not reached for a sample;
- any task disappears or becomes untrackable;
- active MinerU parse-running count exceeds `1`;
- active Ollama-running count exceeds `1`;
- any service/Docker/Ollama/model/config/secret/override mutation would be required;
- any DB/MinIO/Docker volume/task/artifact/log deletion would be required;
- skeleton fallback or silent degradation appears;
- signed URLs or secrets would need to be committed;
- more than the authorized upload count would be needed.

### 5.9 No-Cleanup Boundary

Do not delete created tasks, DB rows, MinIO objects, AI raw traces, parsed artifacts, or logs after validation.

Record created IDs and artifacts as validation evidence.

## 6. Proposed Next Lucode Task

Suggested next task name:

`P0 Stage-Queued Sample Validation Run`

Suggested authorization:

- Allow up to three controlled production uploads in the exact order listed in this revised report.
- Allow upload of the next sample after prior sample upload/storage intake is durable, not after prior terminal completion.
- Require evidence that MinerU active parse-running count remains at most `1`.
- Require evidence that Ollama active metadata-running count remains at most `1`.
- Require the warm-up/readiness gates above.
- Preserve all forbidden-operation boundaries.
- Report `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.

## 7. Commands Run For Correction

| Workspace | Command | Exit | Notes |
| --- | --- | ---: | --- |
| dev | `git status --short --branch` | 0 | `main...origin/main` |
| dev | `git fetch origin` | 0 | succeeded |
| dev | `git pull --ff-only origin main` | 0 | already up to date |
| dev | `rg -n "\\| Lucode \\||Next Actor" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | found task 42 returned to Lucode |
| dev | `tail -n 18 TaskAndReport/TASK_TRACKING_LIST.md` | 0 | correction routing confirmed |
| dev | `sed -n ... LUCIA_REVIEW.md` | 0 | correction requirements read |
| dev | `sed -n ... REPORT.md` | 0 | original report reviewed |
| dev | `date '+%Y-%m-%dT%H-%M-%S%z'` | 0 | revised report timestamp |

No production checks were rerun for this correction because Lucia accepted the original non-destructive preflight facts and requested plan correction only.

## 8. Skipped Checks And Reasons

Skipped by correction scope:

- Production uploads: not authorized.
- Production runtime checks: not rerun because the correction is a planning/report correction and preflight facts were accepted.
- Task/AI polling: no uploads were created.
- Docker/service mutation: forbidden.
- Production fast-forward/deploy/rebuild/restart/rollback: forbidden.
- Sample copying or normalization: forbidden.
- Cleanup of existing validation artifacts: forbidden.

## 9. Guardrail Confirmation

Confirmed:

- No production upload was created by this correction.
- No simultaneous heavy-stage validation was executed.
- No production release-readiness claim occurred.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation was run.
- No Ollama restart/start/stop/kill/reload was run.
- No model, timeout, config, secret, or override value was changed.
- No DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs were deleted.
- No external sample was copied, moved, renamed, edited, deleted, normalized, or synchronized to GitHub.
- No skeleton fallback or silent degradation was added.

Lucia review is required.
