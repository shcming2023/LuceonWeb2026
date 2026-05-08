# P0 Stage-Queued Sample Validation Run Authorization

Decision ID:
`TASK-20260508-214325-P0-Stage-Queued-Sample-Validation-Run-Authorization`

Decision requested by:
Lucia

Requested at:
2026-05-08T21:43:25+0800

Project:
Luceon2026

Related task:
`TASK-20260508-194744-P0-Stage-Queued-Sample-Validation-Plan-And-Preflight`

Related revised report:
`TaskAndReport/2026-05-08T21-07-00+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_REVISED_REPORT.md`

Related Lucia review:
`TaskAndReport/2026-05-08T21-43-25+0800_P0-Stage-Queued-Sample-Validation-Plan-And-Preflight_LUCIA_REVIEW.md`

## Decision Needed

Director needs to decide whether Lucia may issue the actual controlled stage-queued production validation run.

This is not production release readiness. It is a bounded validation artifact run only.

## Lucia Recommendation

Approve a scoped Lucode validation-run task using the corrected stage-queued流水 model.

Reason:

- The revised report now matches Director's model: upload intake may accept the next sample after prior upload/storage intake is durable.
- MinerU and Ollama heavy stages are constrained to effective single-worker evidence.
- The first wave uses true samples only from the specified sample directory.
- The run has explicit stop conditions and no-cleanup boundaries.

## Approval Scope If Director Agrees

Lucia may issue a Lucode task allowing:

1. Up to three controlled production uploads in this order:
   - `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/期末质量分析及建议（曹云童 ）.pdf`
   - `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/走向成功_英语_二模卷16篇.pdf`
   - `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/4.XxwlAs2026/sample/Cambridge IGCSE(0580)  Core and Extended Mathematics_2018(Cambridge  University Press).pdf`, only if samples 1 and 2 pass the stage-queued gates
2. Start the next upload after prior sample upload/storage intake is durable, not after prior terminal completion.
3. Prove MinerU active parse-running count remains `<=1`.
4. Prove Ollama active metadata/Ollama-running count remains `<=1`.
5. Run warm-up/readiness gates before upload:
   - production override boundary check;
   - CMS/DB/service health;
   - active task/job count;
   - sample size/SHA-256 confirmation;
   - one bounded non-mutating Ollama warm-up;
   - warm dependency-health with `mineruSubmitProbe=true`.
6. Poll only created task IDs and related AI jobs.
7. Report `PASS`, `FAILED_ACCEPTED_EVIDENCE`, `BLOCKED`, or `INCONCLUSIVE`.

## Still Forbidden

- Production release-readiness declaration.
- Production deploy, fast-forward, rebuild, restart, rollback, or Docker mutation.
- Ollama restart, start, stop, kill, reload.
- Model, timeout, config, secret, or production-local override changes.
- DB row deletion, MinIO object deletion, Docker volume deletion/pruning, task/artifact/log deletion or cleanup.
- External sample copy, move, rename, edit, delete, normalization, pollution, or GitHub sync.
- Skeleton fallback or silent degradation.
- Signed MinIO URL or secret persistence in reports.
- More than the approved upload count.

## Options

### Option A: Approve Stage-Queued First Wave

Approve the scoped run above.

### Option B: Approve Only First Two Samples

Approve samples 1 and 2 only; defer the large Cambridge sample to a later decision.

### Option C: Hold Production Validation

Do not issue a production validation-run task yet; keep the evidence as planning only.

## Heartbeat Autonomy Boundary

Decision requested timestamp:
2026-05-08T21:43:25+0800

Heartbeat wait evidence:
0 unanswered Lucia heartbeat checks at creation.

If this decision remains unanswered after two Lucia heartbeat checks, Lucia may choose the smallest conservative continuation only if no new risk evidence appears and the task ledger would otherwise stall. The conservative continuation is Option B, not Option A: approve only the first two samples under the stage-queued rules.

Autonomy may not be used for production release readiness, destructive production operation, service/config/model/secret mutation, data deletion, or broader release acceptance.
