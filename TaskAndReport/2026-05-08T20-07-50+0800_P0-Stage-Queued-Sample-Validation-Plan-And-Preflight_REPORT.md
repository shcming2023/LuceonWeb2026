# Lucode Completion Report: P0 Stage-Queued Sample Validation Plan And Preflight

## 1. Result Classification

Result: `PLAN_READY`

This work was based on Lucia task brief:

`TaskAndReport/2026-05-08T19-47-44+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_TASK.md`

Director clarified that the next validation should be stage-queued流水, not simultaneous heavy concurrency. This report proposes a serial/stage-queued validation wave using true sample-directory inputs and records non-destructive preflight evidence only.

No production upload was created. No production release-readiness claim is made.

## 2. Scope Executed

Executed:

- Synchronized the development workspace with GitHub.
- Read task 42 and its related Director correction / Lucia review.
- Ran read-only production git, override, service, CMS, DB, dependency-health, and active work checks.
- Inspected the true sample directory as read-only inventory.
- Calculated SHA-256 hashes for reasonable non-zero sample candidates.
- Produced a stage-queued validation plan that avoids simultaneous heavy MinerU and Ollama jobs.

Not executed:

- No production upload.
- No simultaneous heavy-stage validation.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- No Ollama restart/start/stop/kill/reload.
- No model, timeout, config, secret, or override change.
- No DB row, MinIO object, Docker volume, task, artifact, or log deletion.
- No external sample copy, move, rename, edit, delete, normalization, pollution, or GitHub sync.
- No skeleton fallback or silent degradation.

## 3. Branch And HEAD

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Status after sync: `main...origin/main`
- HEAD before report: `983c27ab13223c0bc6659b73351dd74638b97381`

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Status after read-only fetch: `main...origin/main [behind 13]`, with local `docker-compose.override.yml` modification preserved.
- Production HEAD: `8092965c104cee57ff9cb739106e4320dfc22a7d`
- Production `origin/main` before fetch: `eb127c63d0347032625b8f0f60a1d44152c74bce`
- Production `origin/main` after fetch: `983c27ab13223c0bc6659b73351dd74638b97381`
- No production fast-forward, deploy, rebuild, restart, rollback, or Docker mutation was performed.

## 4. Production Override Boundary

Production override markers present:

- `DISABLE_AI_SKELETON_FALLBACK=true`
- `OLLAMA_TIER2_MODEL=qwen3.5:9b`
- MinIO console mapping `127.0.0.1:19001:9001`

## 5. Read-Only Production Preflight Evidence

`docker compose ps`:

- `cms-db-server`: healthy.
- `cms-frontend`: healthy, `0.0.0.0:8081->80/tcp`.
- `cms-minio`: healthy, `127.0.0.1:19001->9001/tcp`.
- `cms-upload-server`: healthy.

CMS and DB:

- CMS reachability: `CMS_OK`.
- DB health: `{"ok":true,"service":"db-server","dataPath":"/data/db-data.json","secretsPath":"/data/secrets.json"}`.

Dependency-health with MinerU submit probe:

- Exit: `0`
- `ok=true`
- `blocking=false`
- `minio.ok=true`
- `mineru.ok=true`
- `mineru.submitProbe.ok=true`
- `mineru.submitProbe.status=202`
- `mineru.submitProbe.durationMs=37`
- `ollama.ok=true`
- `ollama.chatOk=true`
- `ollama.durationMs=12740`
- `ollama.model=qwen3.5:9b`

Active work:

- Tasks total: `45`
- Active parse/task states: `0`
- AI metadata jobs total: `39`
- Active AI jobs: `0`

Interpretation:

- Preflight was non-blocking at the time of this report.
- Ollama health passed but remained slow at `12740ms`; the actual validation run should still include an explicit bounded warm-up/readiness gate.

## 6. True Sample Directory Inventory

True sample directory:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Inventory found `19` PDF files at max depth 1. The directory was inspected read-only only.

### Recommended First Wave

The first stage-queued wave should use three non-zero samples ordered small -> medium -> large:

1. Small diagnostic sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf`
   - Size: `1041695`
   - SHA-256: `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8`
   - Reason: small non-zero PDF; good first signal before heavier local stages.

2. Medium educational sample:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
   - Size: `3457503`
   - SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`
   - Reason: non-zero English education/exam-style sample; suitable main validation sample from the true directory.

3. Large backup sample, only if samples 1 and 2 pass stage gates:
   - Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`
   - Size: `39063547`
   - SHA-256: `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022`
   - Reason: non-zero large education-material sample; use only after the smaller two prove the stage-queued path is stable.

### Additional Non-Zero Candidate

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/附件三：考务流程培训-纸笔标准考试.pdf`
- Size: `5349060`
- SHA-256: `d2e8e9bcd5b59e88a516d2143ece6a03060bf01276481e09d7577a5f82c5ae5a`
- Inclusion judgment: suitable fallback medium sample if Lucia prefers an operational-document sample instead of the Cambridge large candidate.

### Exclusion Reasons

Excluded for first wave:

- 0-byte files, likely OneDrive placeholders or unavailable local content:
  - `G7_Textbook_ready_to_print.pdf`
  - `一个推销员的诞生弗莱德曼.pdf`
  - `英文学术精读教材_中阶_C本.pdf`
  - `华东师大版一课一练六年级下册数学沪教版.pdf`
  - `G8_Workbook_.pdf`
  - `Pemberton Mathematics for Cambridge Igcse Extended Student Book Third Edition Sue Pemberton Z-Library.pdf`
  - `七上数学校本B.pdf`
  - `我真笨（1_2_3）.pdf`
- Very large files over about `55MB` are excluded from the first wave to avoid mixing a large soak with stage-queue validation.
- Non-education or unsuitable content is excluded even when non-zero.

## 7. Proposed Stage-Queued 流水 Validation Plan

Recommended next task type:

- Controlled production validation artifacts.
- Not production release readiness.
- Max uploads for first stage-queued wave: `3`.
- Upload order:
  1. `期末质量分析及建议（曹云童 ）.pdf`
  2. `走向成功_英语_二模卷16篇.pdf`
  3. `Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`, only if samples 1 and 2 pass gates.

Key stage-queued rule:

- Do not run more than one heavy MinerU parse job at the same time.
- Do not run more than one heavy Ollama metadata job at the same time.
- The next upload may be submitted only after the previous sample has completed upload/storage intake and has entered a trackable queued/running parse stage.
- Before submitting the next sample, confirm the previous sample is not causing an unbounded or ambiguous active state.

Pre-run gates:

1. Confirm production override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - `127.0.0.1:19001:9001`
2. Confirm `docker compose ps` services healthy.
3. Confirm CMS reachable.
4. Confirm DB health OK.
5. Confirm active parse tasks and AI jobs are `0`.
6. Confirm exact sample size and SHA-256 for all selected samples.
7. Perform exactly one bounded non-mutating Ollama warm-up with `qwen3.5:9b`, `num_predict=1`.
8. Run warm dependency-health with `mineruSubmitProbe=true`.
9. Proceed only if MinIO, MinerU submit probe, and Ollama are all OK.

Stage gates per sample:

1. Upload/storage intake:
   - Capture HTTP status, task ID, material ID, objectName, provider, and file name.
   - Do not record signed MinIO URLs.
   - Wait until the task is visible via DB and has entered parse queue/running state.
2. MinerU parse stage:
   - Poll only the current sample's task until MinerU terminal parse evidence appears.
   - Required pass for advancing: parsed artifact fields present, `parsedFilesCount` recorded, `artifactIncomplete=false` or explicitly explained.
   - If MinerU is running for the current sample, do not submit another sample.
3. Ollama AI metadata stage:
   - Poll the related AI job only after it is created.
   - Required pass for advancing: AI job reaches `review-pending`, `completed`, or a terminal explicit failure with raw trace; no skeleton fallback.
   - If Ollama AI metadata is running for the current sample, do not submit another sample.
4. Advance condition:
   - Submit the next sample only after the current sample has reached a terminal state, or after Lucia explicitly accepts a narrower handoff boundary in a separate task.

This plan intentionally chooses full per-sample stage completion before the next upload for the first corrected validation wave. It is more conservative than theoretical stage-overlap, but it matches Director's local-runtime caution and avoids simultaneous heavy MinerU/Ollama work.

Polling strategy:

- Poll current task every `10s` during upload/parse stage.
- Poll related AI job every `15s` to `30s` during AI stage.
- Suggested per-sample bound:
  - small sample: `15` minutes.
  - medium sample: `25` minutes.
  - large sample: `45` minutes.
- Stop the wave if any sample reaches terminal failure unless Lucia's next task explicitly authorizes continuing after failed evidence.

Evidence fields:

- Per sample: path, size, SHA-256, upload HTTP code, task ID, material ID, objectName, provider.
- Per task: terminal `state`, `stage`, `message`, MinerU task ID, parsed artifact fields, `parsedFilesCount`, `artifactIncomplete`.
- Per material: provider/model/sampling mode, original length, selected length, input hash, trigger reasons, thresholds, observed values when AI metadata exists.
- Per AI job: state, provider/model, message/error, first-pass and repair-pass trace, whether repair succeeded.
- Events: `worker-completed`, `ai-content-truncated` if applicable, provider request start/success/failure, repair events, final state transition.
- Queue behavior: confirm no simultaneous heavy MinerU parse jobs and no simultaneous heavy Ollama jobs.

Stop conditions:

- Any pre-run gate fails.
- Active parse tasks or AI jobs exist before the first upload.
- Sample size or hash mismatches.
- More than three uploads would be required.
- Any simultaneous heavy MinerU/Ollama job would be created.
- Any service/Docker/Ollama/model/config/secret/override mutation would be required.
- Any DB/MinIO/Docker volume/task/artifact/log deletion would be required.
- Skeleton fallback or silent degradation appears.
- Signed URLs or secrets would need to be committed.

No-cleanup boundary:

- Do not delete created tasks, DB rows, MinIO objects, AI raw traces, parsed artifacts, or logs after validation.
- Record created IDs and artifacts as validation evidence.

## 8. Proposed Next Lucode Task

Suggested next task name:

`P0 Stage-Queued Sample Validation Run`

Suggested authorization:

- Allow up to three controlled production uploads in the exact order listed above.
- Require the warm-up/readiness gates above.
- Require per-sample terminal state before the next sample upload.
- Preserve all forbidden-operation boundaries.
- Report `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.

## 9. Commands Run

| Workspace | Command | Exit | Notes |
| --- | --- | ---: | --- |
| dev | `git status --short --branch` | 0 | `main...origin/main` |
| dev | `git fetch origin` | 0 | succeeded |
| dev | `git pull --ff-only origin main` | 0 | already up to date |
| dev | `rg -n "\\| Lucode \\||Next Actor" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | found task 42 assigned to Lucode |
| dev | `tail -n 15 TaskAndReport/TASK_TRACKING_LIST.md` | 0 | task 42 confirmed |
| dev | `git log -1 --oneline && git status --short --branch` | 0 | HEAD `983c27a`; clean |
| dev | task/context `sed -n ...` reads | 0 | task brief and related decision/review read |
| prod | `git status --short --branch && git rev-parse HEAD && git rev-parse origin/main` | 0 | production behind origin; local override present |
| prod | `git fetch origin` | 0 | updated origin/main to `983c27a` |
| prod | override marker `rg` | 0 | strict AI/model and local-only MinIO console present |
| prod | `docker compose ps` | 0 | read-only service state; services healthy |
| prod | `curl -fsS http://localhost:8081/cms/ >/dev/null && echo CMS_OK` | 0 | CMS reachable |
| prod | `curl -fsS http://localhost:8081/__proxy/db/health` | 0 | DB healthy |
| prod | dependency-health with `mineruSubmitProbe=true` | 0 | passed; Ollama duration `12740ms` |
| prod | active tasks query via `/__proxy/db/tasks` | 0 | active tasks `0` |
| prod | active AI jobs query via `/__proxy/db/ai-metadata-jobs` | 0 | active AI jobs `0` |
| dev | external sample size inventory `find ... -exec stat ...` | 0 | read-only size inventory |
| dev | `find ... -iname '*.pdf' | wc -l` | 0 | `19` PDFs |
| dev | `shasum -a 256` on selected candidates | 0 | hashes collected |
| dev | `date '+%Y-%m-%dT%H-%M-%S%z'` | 0 | report timestamp |

## 10. Skipped Checks And Reasons

Skipped by task design:

- Production uploads: forbidden in task 42.
- Task/AI polling: no uploads were created.
- Bounded Ollama warm-up: not needed because dependency-health with submit probe passed during this preflight. The next validation run should still include it as a gate because Ollama duration remained high.
- Docker/service mutation: forbidden.
- Production fast-forward/deploy/rebuild/restart/rollback: forbidden.
- Sample copying or normalization: forbidden.
- Cleanup of existing validation artifacts: forbidden.

## 11. Risks And Residual Debt

- Ollama health passed but was slow at `12740ms`; the actual run should still include a warm-up gate before upload.
- Several true sample-directory files are 0-byte placeholders. They must not be selected unless local content becomes available and hash/size are reconfirmed.
- A three-sample first wave may be too long if the large Cambridge file reaches AI timeout behavior; the plan therefore makes sample 3 conditional on samples 1 and 2 passing.
- Production workspace remains behind latest docs-only `origin/main`, and task 42 did not authorize production fast-forward or deploy.
- Stage-queued validation will create durable production validation artifacts; Lucia/Director should explicitly authorize the exact sample order before running it.

## 12. Guardrail Confirmation

Confirmed:

- No production upload was created.
- No simultaneous heavy-stage validation was planned or executed.
- No production release-readiness claim occurred.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation was run.
- No Ollama restart/start/stop/kill/reload was run.
- No model, timeout, config, secret, or override value was changed.
- No DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs were deleted.
- No external sample was copied, moved, renamed, edited, deleted, normalized, or synchronized to GitHub.
- No skeleton fallback or silent degradation was added.

Lucia review is required.
