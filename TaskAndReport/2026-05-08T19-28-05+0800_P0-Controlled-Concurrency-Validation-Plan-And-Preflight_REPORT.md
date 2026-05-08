# Lucode Completion Report: P0 Controlled Concurrency Validation Plan And Preflight

## 1. Result Classification

Result: `PLAN_READY`

This work was based on Lucia task brief:

`TaskAndReport/2026-05-08T19-17-09+0800_P0-Controlled-Concurrency-Validation-Plan-And-Preflight_TASK.md`

The task was planning and non-destructive preflight only. No production upload was created.

No production release-readiness claim is made.

## 2. Scope Executed

Executed:

- Synchronized the development workspace with GitHub.
- Read task 40 and required project/task context.
- Ran read-only production git, override, service, CMS, DB, dependency-health, and active work checks.
- Performed one bounded non-mutating direct Ollama warm-up because initial dependency-health failed Ollama readiness.
- Re-ran warm dependency-health with `mineruSubmitProbe=true`.
- Inspected the external sample directory as read-only inventory.
- Calculated size/hash for the proven large sample and selected candidate samples.
- Produced a capped concurrency validation plan.

Not executed:

- No production upload.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- No Ollama restart/start/stop/kill/reload.
- No model, timeout, config, secret, or override change.
- No DB row, MinIO object, Docker volume, task, artifact, or log deletion.
- No external sample copy, move, rename, edit, delete, normalization, or GitHub sync.
- No skeleton fallback or silent degradation.

## 3. Branch And HEAD

Development workspace:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Status before execution: `main...origin/main`
- HEAD after sync / before report: `eb127c63d0347032625b8f0f60a1d44152c74bce`

Production workspace:

- Path: `/Users/concm/prod_workspace/Luceon2026`
- Status after read-only fetch: `main...origin/main [behind 10]`, with local `docker-compose.override.yml` modification preserved.
- Production HEAD: `8092965c104cee57ff9cb739106e4320dfc22a7d`
- Production `origin/main` before fetch: `a3fe7c80e3a0d36f6c700e9097bc83a2be350d2a`
- Production `origin/main` after fetch: `eb127c63d0347032625b8f0f60a1d44152c74bce`
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

Active work:

- Tasks total: `45`
- Active parse/task states: `0`
- AI metadata jobs total: `39`
- Active AI jobs: `0`

Initial dependency-health with MinerU submit probe:

- Exit: `0`
- `ok=false`
- `blocking=false`
- `minio.ok=true`
- `mineru.ok=true`
- `mineru.submitProbe.ok=true`
- `mineru.submitProbe.status=202`
- `mineru.submitProbe.durationMs=116`
- `ollama.ok=false`
- `ollama.chatOk=false`
- `ollama.durationMs=14999`
- `ollama.error="Smoke test failed: The operation was aborted due to timeout"`

One bounded non-mutating Ollama warm-up:

- Model: `qwen3.5:9b`
- `num_predict=1`
- Exit: `0`
- `done=true`
- `done_reason=length`
- `total_duration=7296841875ns`
- `load_duration=6764806542ns`
- `prompt_eval_count=11`
- `eval_count=1`

Warm dependency-health with MinerU submit probe:

- Exit: `0`
- `ok=true`
- `blocking=false`
- `minio.ok=true`
- `mineru.ok=true`
- `mineru.submitProbe.ok=true`
- `mineru.submitProbe.status=202`
- `mineru.submitProbe.durationMs=44`
- `ollama.ok=true`
- `ollama.chatOk=true`
- `ollama.durationMs=699`
- `ollama.model=qwen3.5:9b`

Interpretation:

- The concurrency run must include an explicit bounded warm-up gate before any uploads.
- Warm dependency-health can pass after the non-mutating warm-up.

## 6. Candidate Sample Inventory

External sample directory:

`/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample`

Inventory command found `19` PDF files at max depth 1. The directory was inspected read-only only.

Recommended sample A, previously proven large PDF:

- Path: `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
- Size: `15157403`
- SHA-256: `672c96f6125ab3afcf0dcd63b858a2584fa4cdd427000df40870f52aa477435b`
- Reason for inclusion: already controlled-validated in task 38; large enough to exercise adaptive evidence-pack path; known MinerU parse count `99` and AI `review-pending` behavior.

Recommended sample B, medium/smaller PDF:

- Path: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
- Size: `3457503`
- SHA-256: `b3e00ad1c7f7afff4bdae1b484abad941af618fd80b9b5f9f22d69848968eaac`
- Reason for inclusion: non-zero external sample; smaller than sample A; educational English exam-style material; suitable for conservative first concurrency mix.

Additional non-zero candidates inspected:

| Path | Size | SHA-256 | Inclusion judgment |
| --- | ---: | --- | --- |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf` | `1041695` | `c2b15ff6cfdd13e7c7cad7ea898bcd0ad98d33b6afde7c3d3e55773916b256e8` | Good small backup candidate, but not selected for first concurrency run because sample B is more similar to Luceon education-material flow. |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/附件三：考务流程培训-纸笔标准考试.pdf` | `5349060` | `d2e8e9bcd5b59e88a516d2143ece6a03060bf01276481e09d7577a5f82c5ae5a` | Backup candidate; operational document, less preferred than education-material sample. |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/时间总是不够用？其实是你不会用！.pdf` | `254360` | `6e9291b9bf5c41f6402e368a5d6b4a1d6d6ab6565b89d216289706864e298026` | Too small for first concurrency signal; backup for tiny-file smoke only. |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf` | `39063547` | `a74d612fd10ec0d6f13c06e2ed1cc386d356af2ed81242bc14fa33d9a4bd7022` | Valid non-zero large candidate, but not selected for first concurrency because it would combine two heavier documents. |
| `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Hodder Education).pdf` | `39891635` | `1d2a6bac4ec39f83f8d815c68354ec13dfda9c0327cd7ea3fef81c6b843e4fd4` | Valid non-zero large candidate, but not selected for first concurrency because it would combine two heavier documents. |

Excluded candidate classes:

- 0-byte files: excluded as likely OneDrive placeholder or unavailable local content. Examples include `G7_Textbook_ready_to_print.pdf`, `G8_Workbook_.pdf`, `七上数学校本B.pdf`, and several others.
- Very large `55MB+` to `102MB` files: excluded from first concurrency run to avoid mixing large-PDF soak with concurrency in the same first pass.
- Non-education or potentially inappropriate content: excluded from validation candidate selection even if non-zero.

## 7. Proposed Concurrency Validation Plan

Recommended next task result target:

- Result type: controlled production validation evidence, not production release readiness.
- Concurrency level: `2`.
- Max controlled uploads: `2`.
- Samples:
  1. `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
  2. `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`

Pre-upload gates:

1. Confirm production override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - `127.0.0.1:19001:9001`
2. Confirm `docker compose ps` services healthy.
3. Confirm CMS reachable.
4. Confirm DB health OK.
5. Confirm active parse tasks and AI jobs are `0`.
6. Confirm exact sample size and SHA-256 for both samples.
7. Perform exactly one bounded non-mutating Ollama warm-up with `qwen3.5:9b`, `num_predict=1`.
8. Run warm dependency-health with `mineruSubmitProbe=true`.
9. Proceed only if:
   - `ok=true`
   - `blocking=false`
   - `minio.ok=true`
   - `mineru.ok=true`
   - `mineru.submitProbe.ok=true`
   - `ollama.ok=true`
   - `ollama.chatOk=true`

Upload execution:

- Start exactly two uploads close together, one per sample.
- Capture HTTP status, task ID, material ID, objectName, provider, and file name.
- Do not create a third upload. If either upload command fails before returning a task ID, stop and report the exact failure.
- Do not print or store signed MinIO URLs in reports.

Polling strategy:

- Poll only the two created task IDs and their related AI jobs.
- Suggested bound: up to `45` minutes total for first concurrency validation, with `10s` task polling during parse and `15s` to `30s` AI job polling after AI starts.
- Stop early when both tasks reach terminal states.
- If one task reaches terminal failed state, continue polling the other only if it is already created and active; do not start replacements.

Evidence fields:

- For each task: terminal `state`, `stage`, `message`, material ID, MinerU task ID, parsed artifact fields, `parsedFilesCount`, `artifactIncomplete`.
- For each material: provider/model/sampling mode, original length, selected length, input hash, trigger reasons, thresholds, observed values.
- For each AI job: state, provider/model, message/error, first-pass and repair-pass trace, whether repair succeeded.
- Task events: `worker-completed`, `ai-content-truncated`, provider request start/success/failure, repair events, final state transition.
- Queue behavior: whether both tasks were active concurrently, whether one blocked the other, and whether AI jobs serialized or overlapped.

Stop conditions:

- Any required pre-upload gate fails.
- Active parse tasks or AI jobs exist before upload.
- Sample size or hash mismatches.
- A third upload would be needed.
- Any service/Docker/Ollama/model/config/secret/override mutation would be required.
- Any DB/MinIO/Docker volume/task/artifact/log deletion would be required.
- Skeleton fallback or silent degradation appears.
- Signed URLs or secrets would need to be committed.

No-cleanup boundary:

- Do not delete created tasks, DB rows, MinIO objects, AI raw traces, parsed artifacts, or logs after validation.
- Record created IDs and artifacts as validation evidence.

## 8. Proposed Next Lucode Task

Suggested next task name:

`P0 Controlled Concurrency Validation Run`

Suggested authorization:

- Allow exactly two controlled production uploads.
- Use the two approved sample paths and hashes listed in this report.
- Require the warm-up/readiness gates above.
- Preserve all forbidden-operation boundaries.
- Report `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.

## 9. Commands Run

| Workspace | Command | Exit | Notes |
| --- | --- | ---: | --- |
| dev | `git status --short --branch` | 0 | `main...origin/main` |
| dev | `git fetch origin` | 0 | succeeded |
| dev | `git pull --ff-only origin main` | 0 | already up to date |
| dev | `tail -n 30 TaskAndReport/TASK_TRACKING_LIST.md` | 0 | found task 40 assigned to Lucode |
| dev | `rg -n "\\| Lucode \\||Next Actor" TaskAndReport/TASK_TRACKING_LIST.md` | 0 | task 40 actionable |
| dev | `git log -1 --oneline && git status --short --branch` | 0 | HEAD `eb127c6`; clean |
| dev | task/context `sed -n ...` reads | 0 | task brief and required context read |
| prod | `git status --short --branch && git rev-parse HEAD && git rev-parse origin/main` | 0 | production behind origin; local override present |
| prod | `git fetch origin` | 0 | updated origin/main to `eb127c6` |
| prod | override marker `rg` | 0 | strict AI/model and local-only MinIO console present |
| prod | `docker compose ps` | 0 | read-only service state; services healthy |
| prod | `curl -fsS http://localhost:8081/cms/ >/dev/null && echo CMS_OK` | 0 | CMS reachable |
| prod | `curl -fsS http://localhost:8081/__proxy/db/health` | 0 | DB healthy |
| prod | dependency-health with `mineruSubmitProbe=true` | 0 | MinerU/MinIO OK, Ollama timeout before warm-up |
| prod | active tasks query via `/__proxy/db/tasks` | 0 | active tasks `0` |
| prod | active AI jobs query via `/__proxy/db/ai-metadata-jobs` | 0 | active AI jobs `0` |
| prod | bounded direct Ollama warm-up | 0 | succeeded; load about `6.76s` |
| prod | warm dependency-health with `mineruSubmitProbe=true` | 0 | passed; Ollama duration `699ms` |
| dev | external sample `find ... -print` | 0 | read-only file list |
| prod | proven sample `stat` and `shasum -a 256` | 0 | size/hash matched |
| dev | external sample size inventory `find ... -exec stat ...` | 0 | read-only size inventory |
| dev | `shasum -a 256` on initial selected external candidates | 1 | command quoted one path incorrectly; successful hashes for `G7_Textbook_ready_to_print.pdf`, `走向成功_英语_二模卷16篇.pdf`, `G8_Workbook_.pdf`; path error corrected below |
| dev | corrected `shasum -a 256` on selected external candidates | 0 | hashes collected |
| dev | `find ... -iname '*.pdf' | wc -l` | 0 | `19` PDFs |
| dev | `date '+%Y-%m-%dT%H-%M-%S%z'` | 0 | report timestamp |

## 10. Skipped Checks And Reasons

Skipped by task design:

- Production uploads: forbidden in task 40.
- Task/AI polling: no uploads were created.
- Docker/service mutation: forbidden.
- Production fast-forward/deploy/rebuild/restart/rollback: forbidden.
- Sample copying or normalization: forbidden.
- Cleanup of existing validation artifacts: forbidden.

## 11. Risks And Residual Debt

- Ollama readiness remains cold-load sensitive. The first dependency-health attempt failed at about `14999ms`; warm-up then restored health. The actual concurrency run should not start without an explicit warm-up gate.
- Several external sample files are 0-byte placeholders or unavailable local content. They must be excluded unless their local content is confirmed later.
- First concurrency run should avoid combining multiple very large files. Use one proven large file plus one smaller file first.
- Production workspace remains behind latest docs-only `origin/main`, and task 40 did not authorize production fast-forward or deploy.
- Concurrency validation will create durable production validation artifacts; Lucia/Director should explicitly accept the two-sample cap before running it.

## 12. Guardrail Confirmation

Confirmed:

- No production upload was created.
- No production release-readiness claim occurred.
- No production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation was run.
- No Ollama restart/start/stop/kill/reload was run.
- No model, timeout, config, secret, or override value was changed.
- No DB rows, MinIO objects, Docker volumes, tasks, artifacts, or logs were deleted.
- No external sample was copied, moved, renamed, edited, deleted, normalized, or synchronized to GitHub.
- No skeleton fallback or silent degradation was added.

Lucia review is required.
