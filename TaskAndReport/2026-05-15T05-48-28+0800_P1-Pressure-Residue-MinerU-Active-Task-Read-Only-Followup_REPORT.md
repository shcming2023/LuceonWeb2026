# Test Acceptance Report: P1 Pressure Residue MinerU Active Task Read-Only Followup

- Task ID: `TASK-20260515-054828-P1-Pressure-Residue-MinerU-Active-Task-Read-Only-Followup`
- Task brief: `TaskAndReport/2026-05-15T05-48-28+0800_P1-Pressure-Residue-MinerU-Active-Task-Read-Only-Followup_TASK.md`
- Role: `TestAcceptanceEngineer`
- Report time: `2026-05-15T06:10+0800`
- Recommendation: `blocked / still-running-with-advancing-evidence`

## Scope And Boundaries

This report is based on the Director task brief. The validation was read-only.

- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path: `/Users/concm/prod_workspace/Luceon2026`
- Production path entered: yes, read-only.
- GitHub sync: not run.
- No upload, cleanup, cancel, stop, repair, retry, reparse, re-AI, DB/MinIO/Docker volume/data mutation, Docker down/restart/rebuild, service ownership mutation, settings/secrets/config/model/sample mutation, pressure PASS, L3, release-readiness, production-readiness, or go-live claim was performed.

## Target

- Parse task: `task-1778765417422`
- Material: `2274129919986463`
- File: `06第六章 长期股权投资与合营安排.pdf`
- MinerU task: `dcdb27f3-fac6-4ede-b456-a96fe358b0da`

## Snapshot Summary

| Snapshot | Local time | Luceon task state | Direct MinerU state | Log/progress evidence |
| --- | --- | --- | --- | --- |
| 1 | `2026-05-15T05:54+0800` | `running/mineru-processing`, progress `50` | `processing`, `error=null`, `completed_at=null` | Stale log summary at `Table-ocr det 65/66`, last business signal around `2026-05-15 04:58:40`; no terminal failure. |
| 2 | `2026-05-15T06:10+0800` | `running/mineru-processing`, progress `50` | `processing`, `error=null`, `completed_at=null` | New advancing evidence: `Table-ocr det` reached `66/66`, then `Table-ocr rec ch 1150/1150`, `Table-wireless 66/66`, `Table-wired 57/57`, then `OCR-det ch 7/45`. |

## Commands And Evidence

Development workspace:

- `git status --short --branch`: exit `0`; current branch `development-engineer/p0-post-validation-ollama-mineru-blockers`; shared workspace has many unrelated modified/untracked files.
- Read required role/project/task documents with `sed`/`rg`: exit `0`.

Production workspace:

- `bash ops/runtime-ownership-status.sh`: exit `0`; services healthy, `luceon-mineru` and `luceon-sidecar` present, `luceon-supervisor` absent, upload health OK.
- `curl -fsS http://localhost:8081/__proxy/upload/health`: exit `0`; `{"ok":true,"service":"upload-server"}`.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/upload/ops/mineru/active-task`: exit `0`; target remained active.
- `curl -sS --max-time 20 http://127.0.0.1:8083/tasks/dcdb27f3-fac6-4ede-b456-a96fe358b0da`: exit `0`; both snapshots returned `status=processing`, `completed_at=null`, `error=null`.
- `curl -sS --max-time 10 http://127.0.0.1:8083/health`: exit `0`; final snapshot returned `queued_tasks=1`, `processing_tasks=1`, `completed_tasks=91`, `failed_tasks=0`.
- `tail -n 100 /Users/concm/ops/logs/mineru-api.err.log`: exit `0`; showed continued MinerU progress after the earlier stale `Table-ocr det 65/66` point.
- `stat`/mtime check: exit `0`; at `2026-05-15T06:10:19+0800`, `mineru-api.err.log` mtime was `2026-05-15T06:06:23+0800`, about `3.9` minutes old; `mineru-api.log` was current due polling requests.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/tasks`: exit `0`; target task remained `running/mineru-processing`.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/materials`: exit `0`; material `2274129919986463` remained `processing`, `mineruStatus=processing`, `aiStatus=pending`, with no parsed prefix/files count yet.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/ai-metadata-jobs`: exit `0`; no AI job for the target task/material.
- `curl -sS --max-time 15 http://localhost:8081/__proxy/db/task-events?taskId=task-1778765417422`: exit `0`; recent events showed continued MinerU parsing messages, then observation-stale message at `2026-05-14T22:08:24.693Z`.

## Runtime Evidence

The target did not reach terminal success or terminal failure during this follow-up.

Final direct MinerU task state:

- `task_id=dcdb27f3-fac6-4ede-b456-a96fe358b0da`
- `status=processing`
- `completed_at=null`
- `error=null`
- `queued_ahead=0`

Final Luceon task/material state:

- Parse task: `running/mineru-processing`, progress `50`.
- Material: `processing`, `mineruStatus=processing`, `aiStatus=pending`.
- Parsed artifacts: not available yet in material metadata.
- AI job: none created for the target task/material.

Log evidence nuance:

- Earlier active-task summaries made the target look stuck at `Table-ocr det 65/66`.
- Raw MinerU stderr later showed `Table-ocr det` completed to `66/66` after about `1:05:28`, then subsequent stages advanced.
- At final snapshot, active-task progress semantics showed `OCR-det ch`, `7/45`, `16%`, with `lastProgressObservedAt=2026-05-14T22:06:04.000Z`.
- A warning line appeared in raw MinerU log: `'NoneType' object has no attribute 'reshape'`, but the process continued and direct MinerU task status remained `processing` with `error=null`; this was not treated as terminal failure.

## Boundary Judgment

- Terminal success path: not reached.
- Terminal failure path: not reached.
- Still running but advancing: met. The task advanced beyond the prior stale `Table-ocr det 65/66` point.
- Clear hang/stall: not met at final snapshot because new progress appeared.
- Observation-stale: still present at the Luceon/sidecar summary layer, but raw MinerU logs and active-task progress show recent advancement.

## Skipped Checks

- Browser UI/console checks were skipped because shell/API/log evidence was sufficient for this read-only residue follow-up.
- No `/result` download was attempted because direct MinerU status was still `processing`.
- No dependency-health submit probe was intentionally run as a separate command for this task; `runtime-ownership-status.sh` includes a submit-probe section, and that output was only used as service context, not as task outcome evidence.

## Risks And Residuals

- The task remains active and may still later complete, fail, or stall.
- The log observation layer can lag or present stale summaries even while raw MinerU processing continues.
- The target has already spent a long time in MinerU processing; the largest pause observed was around table OCR detection before progress resumed.
- No decision should be made to cleanup, cancel, retry, repair, reparse, or re-AI this task from this report alone.

## Director Attention Items

The follow-up uncovered three acceptance-boundary issues that should be judged by Director rather than silently absorbed into this report:

1. Page/task semantics and actual MinerU log progress can diverge. The UI/API summary continued to present `日志观测滞后` and stale phase/progress summaries, while raw MinerU logs showed the task had progressed beyond the earlier `Table-ocr det 65/66` point into later OCR/table stages. This mismatch is not friendly to manual judgment during long-running validation.
2. Current MinerU active/success/failure judgment appears incomplete if it relies mainly on task state, active-task summaries, or sidecar observation. For this task, accurate interpretation required reading direct MinerU task status plus raw MinerU stderr/stdout logs. Director should decide whether future runtime validation must explicitly include raw MinerU log-tail evidence before classifying MinerU active/stalled/failed.
3. The prior pressure-test outcome needs a Director-level interpretation boundary. Task 151 was correctly reported as `FAILED` under its explicit task criterion because at least one terminal failed pressure task existed. However, from an operational product perspective, the run also showed that most tasks reached review, large files largely succeeded, and the remaining failures were a small number of AI-recognition failures that may be retryable after policy/metadata hardening. Director should decide whether future pressure-test acceptance should distinguish `overall pipeline failed` from `partial AI retry required`, instead of treating any retryable AI failure as whole-run failure.

## Recommendation To Director

Recommend `blocked / still-running-with-advancing-evidence` for this follow-up.

Director should decide whether to:

- continue read-only monitoring later;
- define a longer stale threshold for this specific MinerU task;
- or dispatch an architecture/ops diagnosis of why the log-observation layer reports stale summaries during active MinerU work.
- review the pressure-test acceptance semantics so retryable AI failures, mostly successful large-file processing, and UI/log semantic drift are represented separately.
