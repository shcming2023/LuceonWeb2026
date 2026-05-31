# P0 Popo MPS Workbook Completion Profile And Progress-Safe Timeout

Task ID: `TASK-20260531-155006-P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout`

Issued at: `2026-05-31T15:50:06+0800`

Issued by: Luceon

Execution owner: lucode

Review / UAT owner: Luceon

## Objective

Close the current Popo/toc-rebuild mainline blocker on the same workbook-class real Raw Material sample:

```text
taskId=task-1779854322261
materialId=3926938009250504
source=parsed/3926938009250504/mineru-result.zip
target=Home Mac mini / Apple MPS / host-mps worker
```

The goal is not a general refactor and not a hardware escape. The success target is:

```text
task-1779854322261 -> Popo on MPS -> readable rebuilt_markdown.md
```

If full completion still cannot be reached inside the task, the fallback acceptable result is a sharper, progress-backed blocker that proves exactly which chunk/stage/profile remains blocking and preserves enough partial-progress evidence for Luceon to make the next decision.

## Current Evidence

Task 312 narrowed the failure:

```text
Before bounded MPS profile:
RuntimeError: Invalid buffer size: 120.93 GiB

After bounded MPS profile:
Job exceeded maximum execution time
```

Runtime evidence from Task 312:

```text
POPO_INFERENCE_BACKEND=host-mps
POPO_MAX_CONCURRENT_JOBS=1
POPO_MAX_NEW_TOKENS=256
POPO_MPS_CHUNK_SIZE=10
POPO_MPS_RENDER_SCALE=1.0
POPO_MPS_MIN_PIXELS=3136
POPO_MPS_MAX_PIXELS=589824
POPO_JOB_TIMEOUT_SECONDS=3600
POPO_GENERATE_TIMEOUT_SECONDS=900
```

Small real sample remained healthy:

```text
taskId=task-1780132950215
assetVersion=v6
rebuilt_markdown.md HTTP 200, size 3296
readable_tree.md HTTP 200, size 297
logic_tree.json HTTP 200, size 13681
```

Workbook sample still failed:

```text
taskId=task-1779854322261
assetVersion=v6
status=failed
cleanState=failed
error=Job exceeded maximum execution time
host worker reached generation_count=43
host worker last_error=null before final status readback
```

## Director-Provided Reference

The Director supplied a GPU-server runbook where MinerU and MinerU-Popo were successfully tested on a much larger A800/CUDA machine. Use it only as a scheduling and pipeline-shape reference, not as a hardware assumption.

Applicable lessons:

- Popo does not directly consume the original PDF; the intended chain is MinerU outputs -> label normalization -> inference -> build tree.
- Successful large-file inference is expected to be a long async job, not a short synchronous request.
- The reference flow exposes stage states such as `running_normalization`, `running_inference`, and `running_build_tree`.
- Progress evidence should include block/page counts, current stage, command return codes, output files, and timing.
- Large-file processing should initially run with concurrency 1.
- The final tree should preserve alignment between inference blocks and tree locations/block IDs.

Do not copy server addresses, tokens, GPU assumptions, CUDA settings, or Jupyter access details into code, reports, or committed docs.

## Required Strategy

Implement the shortest path that can close the same workbook sample on MPS:

1. First try a faster bounded MPS profile that still avoids the prior `120.93 GiB` buffer explosion.
2. If profile tuning alone is not enough, make the adapter progress-aware and timeout-safe enough that long MPS jobs are not killed without partial-progress evidence.

Both paths may be used in the same implementation if that is the shortest reliable route.

## Scope And Write Boundaries

Allowed Luceon2026 repo areas:

```text
docker-compose.popo.yml
server/services/cleanservice/**
server/lib/task-actions-routes.mjs
server/tests/**
TaskAndReport/*_REPORT.md
```

Allowed external MinerU-Popo overlay areas, only if needed for adapter/profile/progress behavior:

```text
luceon_service/**
post_processing/**
README_LUCEON.md
```

If external MinerU-Popo overlay changes are required, record exact changed files and local commit/diff evidence in the report. Do not present those overlay changes as upstream MinerU-Popo changes.

Forbidden:

```text
AGENTS.md
.agents/**
.env
secrets
source PDFs
MinIO object contents except newly generated clean outputs
DB records except normal task/job metadata created by an authorized rerun
upstream MinerU-Popo core algorithm rewrites unrelated to invocation/progress/profile
UI polish
historical global compatibility migration
pressure/release/L3/go-live docs or claims
```

## Implementation Requirements

### A. Faster bounded MPS profile

Provide a documented profile attempt matrix, for example:

```text
chunk_size
render_scale
min_pixels
max_pixels
max_new_tokens
generate_timeout_seconds
job_timeout_seconds
```

At minimum, compare the Task 312 profile against one faster bounded candidate. The chosen candidate must remain on MPS and must not reintroduce the 120.93 GiB attention-buffer failure.

### B. Progress-aware adapter behavior

If a job runs longer than the previous timeout window, it must expose durable progress rather than remaining at `current_step=init`.

Minimum durable progress fields:

```text
current_step
stage_started_at
stage_finished_at
normalized_pages
normalized_blocks
inference_chunks_total
inference_chunks_completed
inference_blocks_validated
last_completed_chunk
last_error
output_files_present
elapsed_seconds
```

Minimum stage states:

```text
queued
running_normalization
running_inference
running_build_tree
succeeded
failed
timeout
canceled
```

If timeout occurs, the job state must preserve:

```text
which stage timed out
which chunk/page/block range was active
how many chunks/blocks completed
whether partial inference artifacts exist
whether retry/resume is possible
```

### C. Workbook UAT handoff

Lucode does not need to run production UAT in the production workspace. Lucode must provide:

- branch and commit;
- exact runtime env/profile to deploy;
- exact rerun command or endpoint payload for `task-1779854322261`;
- expected job state fields for Luceon to inspect;
- report with checks and any external overlay commit/diff.

Luceon will pull, deploy, and run production UAT in `/Users/concm/prod_workspace/Luceon2026`.

## Positive Acceptance

Pass requires all of the following:

1. Small real sample remains non-regressed or the implementation explains why no small rerun is necessary and preserves existing pass evidence.
2. Workbook sample `task-1779854322261` produces readable `rebuilt_markdown.md` under Home Mac mini MPS, with proxy readback HTTP 200.
3. Generated artifact paths remain under the expected `toc-rebuild/3926938009250504/<version>/` prefix.
4. Source asset hash names and raw parsed objects are not renamed or rewritten.
5. Job status and metadata are consistent with output reality.
6. If a long job exceeds any configured window, the job state includes durable stage/chunk/block progress rather than only `current_step=init`.

## Negative Acceptance

The task must be rejected if any of the following happens:

- switches validation target away from MPS;
- claims A800/CUDA evidence as proof of Home Mac mini MPS completion;
- reintroduces `Invalid buffer size: 120.93 GiB` on the workbook sample;
- produces output by manually editing MinIO objects or source assets;
- renames image/hash assets;
- hides timeout behind `completed` metadata;
- only increases timeout without progress evidence or bounded profile reasoning;
- broadens into UI cleanup, generic queue architecture, historical migration, pressure testing, release readiness, or go-live wording.

## Required Checks

Run focused checks matching touched files.

Minimum expected checks:

```text
git diff --check
node --check for touched .mjs files
npx tsc --noEmit if server contract files changed
python -m py_compile for touched external Python overlay files
focused smoke/unit tests for changed cleanservice/task-action code, if applicable
```

If a check is skipped, report why.

## Required Report

Create:

```text
TaskAndReport/2026-05-31T15-50-06+0800_P0-Popo-MPS-Workbook-Completion-Profile-And-Progress-Safe-Timeout_REPORT.md
```

Report result must be one of:

```text
READY_FOR_LUCEON_UAT_WORKBOOK_MPS_OUTPUT
READY_FOR_LUCEON_UAT_PROGRESS_BACKED_BLOCKER
CHANGES_REQUIRED_<specific_reason>
```

The report must include:

- changed files;
- implementation summary;
- profile matrix;
- workbook run evidence or exact handoff command for Luceon UAT;
- progress fields evidence;
- artifact/hash preservation statement;
- checks run with exact commands and results;
- residual risks and next recommendation.
