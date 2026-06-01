# P0 Popo TocRebuild Bounded/Recoverable Invocation Boundary

Issued by: Luceon
Issued at: 2026-06-01T16:07:07+0800
Task ID: TASK-20260601-160707-P0-Popo-TocRebuild-Bounded-Recoverable-Invocation-Boundary
Priority: P0
Mainline: PDF -> Raw Material -> Popo toc-rebuild -> reviewable Clean Material surface

## 1. Objective

Make Luceon adapter invocation of MinerU-Popo safe for Home Mac mini MPS and large real Raw Material inputs without modifying MinerU-Popo core.

The target boundary is:

- interactive/manual toc-rebuild defaults to a bounded profile that can finish in a reviewable time window;
- full-document toc-rebuild for large PDFs is an explicit recoverable background mode, with durable progress evidence and resume semantics;
- preflight estimates chunk count and rough duration before dispatch;
- progress probing reads the real normalized label and raw chunk metadata correctly, fixing the current false `normalized_pages=4` / `inference_chunks_total=1` report on an 891-page workbook.

## 2. Current Evidence

### 2.1 Canceled large interactive run

Large PDF Popo job canceled to release MPS:

- jobId: `luceon-task-1780291805535-toc-rebuild-v2-1780298498453`
- taskId: `task-1780291805535`
- materialId: `4134323036518274`
- assetVersion: `v2`
- source input: `eduassets-parsed/parsed/4134323036518274/mineru-result.zip`
- cancel endpoint used: `POST /api/v1/jobs/{job_id}:cancel`
- post-cancel adapter status: `canceled`

The outer Luceon parse task was already `failed/stage=ai`, so `/__proxy/upload/tasks/task-1780291805535/cancel` correctly refused direct task cancellation. This is not part of the Popo adapter fix.

### 2.2 Real Raw Material scale

The large PDF raw material exists and MinerU parsing completed:

- original file: `Cambridge IGCSE(0580)  Core and Extended Mathematics_2022(Cambridge  University Press).pdf`
- pages in normalized label: `891`
- `mineru-result.zip`: `149816298` bytes
- `full.md`: `1524109` bytes
- `artifact-manifest.json`: `2176112` bytes

### 2.3 MinerU-Popo native chunking evidence

Read-only review of MinerU-Popo native `adaptive_chunk` behavior showed:

- env chunk size in deployment: `POPO_MPS_CHUNK_SIZE=10`
- original chunking groups by page boundaries with overlap, not by fixed page count alone
- estimated chunk families for material `4134323036518274`:
  - `contd`: `92` chunks
  - `title`: `96` chunks
  - `image`: `95` chunks
  - total: about `283` generation chunks
- first completed raw chunk:
  - `outputs/inference_raw/mineru/4134323036518274/contd_chunk_0000.json`
  - JSON fields include `task=contd`, `chunk_index=0`, `range=[1,16]`, `pages=[1,2,3,4,5,12,13,14,15,16]`, `parsed`

This proves Luceon currently can start MinerU-Popo native chunking, but a full 891-page run is not an interactive UAT target on Home Mac mini MPS.

### 2.4 Known progress probe bug

The adapter reported:

- `normalized_pages=4`
- `normalized_blocks=0`
- `inference_chunks_total=1`

while the normalized label actually contains 891 pages under `data["pages"]`. The current probe is treating the top-level label object keys (`model`, `doc_id`, `input_label`, `pages`) as pages. This must be fixed in Luceon adapter.

### 2.5 Out of scope adjacent failure

The second large PDF failed with MinIO AccessKey error before Popo chunking. That is a storage/task-entry issue and must not be folded into this task.

## 3. Scope

### 3.1 Allowed write scope

Implementation should be done in the development workspace:

```text
/Users/concm/Dev_workspace/Luceon2026
```

Allowed files are limited to Luceon adapter/integration surfaces and focused tests/reports:

- `luceon_service/service.py`
- `luceon_service/app.py`, only if API response/request fields are needed
- `server/lib/task-actions-routes.mjs`, only if Luceon dispatch needs bounded/full mode selection
- focused tests under `server/tests/**`, `luceon_service/**`, or equivalent existing test locations
- `TaskAndReport/*_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

### 3.2 Forbidden write scope

Do not modify:

- `/Users/concm/prod_workspace/MineruPopo/**`
- MinerU-Popo core algorithms such as `post_processing/inference.py`
- model files, weights, tokenizer files, or inference framework files
- MinIO credentials, DB secrets, Docker volumes, or persistent object data
- existing sample PDFs or raw artifacts
- unrelated UI polish, broad refactors, historical compatibility cleanup, or MinIO AccessKey handling

Read-only review of MinerU-Popo code and runtime artifacts is allowed for contract matching.

## 4. Required Behavior

### 4.1 Preflight estimator

Before running Popo toc-rebuild, Luceon adapter must estimate:

- normalized page count from the real normalized label shape, especially `data["pages"]`;
- normalized block count from page contents, not top-level dict keys;
- per-family chunk counts for `contd`, `title`, and `image`;
- aggregate `inference_chunks_total`;
- rough duration or risk class based on observed MPS throughput and chunk count.

The estimator should match MinerU-Popo native chunking semantics closely enough for operational decisions. It must not require changing MinerU-Popo core.

### 4.2 Bounded interactive default

Manual "调用 Popo 重新目录重建" / interactive toc-rebuild must default to a bounded profile for large inputs.

The bounded profile may use a page window, chunk cap, task-family cap, or another explicit adapter-level bound. The important contract is that the interactive path does not silently launch hundreds of serialized MPS generations for a large PDF.

The user/operator must be able to see that bounded mode was selected and why.

### 4.3 Recoverable full mode

Full-document toc-rebuild for large PDFs must be explicit background work.

It must:

- persist preflight estimate and mode selection;
- persist completed raw chunks and progress evidence;
- avoid redoing already completed chunks on resume where the raw chunk output is present and valid;
- stop launching new chunks after cancellation;
- return actionable status if full mode cannot continue, rather than being killed as a silent interactive timeout.

If true resume requires an adapter-level manifest or checkpoint file, implement the smallest durable structure needed.

### 4.4 Progress probe correction

The progress API must report truthfully for the large workbook shape:

- `normalized_pages` should be `891` for material `4134323036518274`;
- `inference_chunks_total` should reflect the estimator result, not `1`;
- `chunks_by_task` should be derived from real raw chunk JSON metadata;
- `active_chunk` and `last_completed_chunk` should come from `task`, `chunk_index`, `range`, `pages`, and `parsed` fields, not brittle filename-only assumptions;
- completed block counts must only count valid parsed structures.

### 4.5 Cancellation boundary

Adapter cancellation must mark the job canceled and prevent launching further chunks.

It is acceptable to document that the current host MPS `/generate` call cannot be preempted mid-generation unless the host worker exposes a cancellation primitive. Do not expand this task into host worker protocol redesign unless it is strictly necessary for preventing subsequent chunks.

## 5. Acceptance Criteria

### 5.1 Positive acceptance

Pass all of the following:

1. A focused test or smoke fixture using the 891-page normalized label shape reports `normalized_pages=891` and a realistic chunk total near the observed native estimate (`contd=92`, `title=96`, `image=95`, total about `283`) unless the task documents a precise algorithmic reason for a different number.
2. A bounded interactive toc-rebuild on a real Raw Material sample completes and writes reviewable artifacts without launching an unbounded full-document run.
3. A full-mode request on the large Raw Material records explicit background/recoverable mode, preflight estimate, and progress evidence instead of presenting as ordinary interactive UAT.
4. Cancellation of a running or queued full job prevents the adapter from starting additional chunks after the cancel state is observed.
5. Existing small/workbook successful paths remain usable.

### 5.2 Negative acceptance

The implementation must not:

- modify MinerU-Popo core or model files;
- rename image/audio/hash assets;
- inject generated free text as source truth;
- store full artifact document bodies or unauthorized large structures inside Luceon metadata;
- broaden into MinIO AccessKey repair for the second large PDF;
- claim readiness, pressure PASS, release readiness, L3, or go-live.

## 6. AI/Data Governance Red Lines

Because this task touches AI post-processing and Clean Material surface:

1. ID-only extraction: model-derived structure selection must remain traceable to source page/block/chunk references and must not invent source truth.
2. Asset hash locking: image/resource hash names must remain unchanged.
3. Pure layout boundary: no LaTeX/TikZ custom macro or unrelated layout generation work is authorized.

## 7. Deliverables

- code changes limited to the allowed scope;
- focused tests/smoke evidence;
- report file:

```text
TaskAndReport/2026-06-01T16-07-07+0800_P0-Popo-TocRebuild-Bounded-Recoverable-Invocation-Boundary_REPORT.md
```

- updated `TaskAndReport/TASK_TRACKING_LIST.md` with evidence and final status.
