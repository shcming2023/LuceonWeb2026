# P0 Controlled Concurrency Validation Run Authorization

Decision ID:
`TASK-20260508-193439-P0-Controlled-Concurrency-Validation-Run-Authorization`

Decision requested by:
Lucia

Requested at:
2026-05-08T19:34:39+0800

Project:
Luceon2026

Related completed task:
`TASK-20260508-191709-P0-Controlled-Concurrency-Validation-Plan-And-Preflight`

Related report:
`TaskAndReport/2026-05-08T19-28-05+0800_P0-Controlled-Concurrency-Validation-Plan-And-Preflight_REPORT.md`

Related Lucia review:
`TaskAndReport/2026-05-08T19-34-39+0800_P0-Controlled-Concurrency-Validation-Plan-And-Preflight_LUCIA_REVIEW.md`

## Decision Needed

Director needs to decide whether Lucia may issue the actual controlled production concurrency validation run.

This is not production release readiness. It is a bounded validation artifact run only.

## Lucia Recommendation

Approve the exact two-upload controlled concurrency validation run.

Reason:

- Task 40 preflight found active parse/task states `0` and active AI metadata jobs `0`.
- MinIO and MinerU submit probe passed.
- Ollama cold readiness remains sensitive, but one bounded non-mutating warm-up succeeded and warm dependency-health passed.
- The proposed first run is conservative: concurrency `2`, maximum uploads `2`, one proven large sample plus one smaller read-only external sample.
- The plan contains clear stop conditions and no-cleanup boundaries.

## Approval Scope If Director Agrees

Lucia may issue a Lucode task allowing exactly:

1. Confirm production override boundary:
   - `DISABLE_AI_SKELETON_FALLBACK=true`
   - `OLLAMA_TIER2_MODEL=qwen3.5:9b`
   - MinIO console mapping `127.0.0.1:19001:9001`
2. Confirm production services are healthy with read-only checks.
3. Confirm CMS, DB, MinIO, MinerU submit probe, and active task/job gates.
4. Perform exactly one bounded non-mutating Ollama warm-up before upload.
5. Run warm dependency-health with `mineruSubmitProbe=true`.
6. If all gates pass, create exactly two controlled production uploads close together:
   - `/Users/concm/prod_workspace/Luceon2026/testpdf/G7_Workbook_ready_to_print.pdf`
   - `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
7. Poll only the two created task IDs and related AI jobs.
8. Report controlled validation evidence as `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.

## Still Forbidden

- Production release-readiness declaration.
- More than two controlled uploads.
- Third replacement upload if either selected upload fails.
- Production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- Ollama restart, start, stop, kill, reload, model change, timeout change, config change, secret change, or production-local override change.
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning, task/artifact/log deletion or cleanup.
- External sample copy, move, rename, edit, delete, normalization, pollution, or GitHub sync.
- Skeleton fallback or silent degradation.
- Signed MinIO URL or secret persistence in reports.

## Options

### Option A: Approve Exact Two-Upload Run

Lucia issues a scoped Lucode task for the exact two-sample run under the boundaries above.

### Option B: Require Smaller Local-Only Second Sample

Director requests replacing the external sample with another already-local production sample before upload authorization.

### Option C: Hold Concurrency Validation

Director pauses the concurrency lane and asks Lucia to route the next task to another validation track.

## Heartbeat Autonomy Boundary

Decision requested timestamp:
2026-05-08T19:34:39+0800

Heartbeat wait evidence:
0 unanswered Lucia heartbeat checks at creation.

If this decision remains unanswered after two Lucia heartbeat checks, Lucia may choose Option A as the smallest conservative continuation only if no new risk evidence appears and the task ledger would otherwise stall. That autonomous choice must be recorded before Lucode execution.

Autonomy may not be used for production release readiness, destructive production operation, service/config/model/secret mutation, data deletion, or broader release acceptance.
