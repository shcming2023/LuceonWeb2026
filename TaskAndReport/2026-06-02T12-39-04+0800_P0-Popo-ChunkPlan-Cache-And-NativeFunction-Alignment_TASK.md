# P0 Popo ChunkPlan Cache And NativeFunction Alignment Task

Issued by: Luceon
Issued at: 2026-06-02T12:39:04+0800
Task ID: TASK-20260602-123904-P0-Popo-ChunkPlan-Cache-And-NativeFunction-Alignment

## Objective

Fix the Luceon adapter scheduling issue exposed by Task 316: after micro chunking, `chunk_checkpoint_runner.py` repeatedly recomputes full-document Popo chunk planning before each chunk and can saturate CPU before MPS generation starts.

## Scope

Allowed files:

- `luceon_service/chunk_checkpoint_runner.py`
- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `TaskAndReport/**`

Forbidden:

- MinerU-Popo upstream core/model changes.
- Broad parameter guessing or MPS profile churn.
- UI polish, DB cleanup, MinIO cleanup, source asset mutation.

## Requirements

- Continue using MinerU-Popo native functions for filtering, adaptive chunking, rendering, generation, parsing, and raw record writing.
- Generate `chunk_plan.json` once per document/profile.
- Persist enough plan data to resume the next missing chunk without recomputing full-book filter/adaptive-chunk work.
- Reuse `chunk_plan.json` on subsequent resume when `doc_stem` and `chunk_size` match.
- Archive stale `chunk_plan.json` together with stale raw chunks when profile compatibility requires reset.
- Expose plan-derived total chunk counts through progress where available.

## Acceptance

Positive:

- Focused Python smoke proves plan persistence and reuse.
- Python compile passes.
- `git diff --check` passes.
- Node/TypeScript/build gates pass before main merge.

Negative:

- Do not change MinerU-Popo original source.
- Do not claim full large-PDF completion until production resume proves it.
- Do not alter source PDF/image hash names.
