# P0 Popo ChunkPlan Cache And NativeFunction Alignment Report

Reported by: Luceon
Reported at: 2026-06-02T12:39:04+0800
Task ID: TASK-20260602-123904-P0-Popo-ChunkPlan-Cache-And-NativeFunction-Alignment
Branch: `codex/popo-chunk-plan-cache`

## Result

Status: `IMPLEMENTED_READY_FOR_PRODUCTION_VALIDATION`

The Luceon adapter now keeps MinerU-Popo native function usage while removing repeated full-document planning from every chunk resume.

## Changes

- Added persistent `chunk_plan.json` under the raw doc directory.
- `chunk_plan.json` stores schema, chunk profile, chunk size, doc stem, `doc_blocks`, `large_block_linking`, and task-family ranges/chunks.
- The first run builds the plan using MinerU-Popo native functions.
- Subsequent resume with matching `doc_stem` and `chunk_size` reuses the plan and skips full-document replanning.
- Profile archive now moves stale `chunk_plan.json` with stale raw chunks.
- Progress probing reads plan task counts when `chunk_plan.json` exists.
- Smoke tests verify plan reuse without calling `_build_chunks` again.

## Verification

Passed:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/chunk_checkpoint_runner.py luceon_service/tests/test_popo_invocation_boundary.py
git diff --check
```

```bash
node --check server/lib/task-actions-routes.mjs
npx tsc --noEmit
npm run build
```

`npm run build` completed with the existing Vite large chunk warning.

## Boundaries

- No MinerU-Popo core/model changes.
- No broad parameter guessing.
- No DB/MinIO cleanup or source asset mutation.
- No production completion/readiness/release claim.

## Next Validation

Rebuild `mineru-popo` and resume `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`. Expected: first run writes `chunk_plan.json`; a later resume reads the plan directly and reaches `running_chunk`/MPS generation without repeating full-document CPU planning.

## Production Validation

Validated by Luceon at 2026-06-02T12:41-12:47+0800.

Observed:

- `mineru-popo` was rebuilt and loaded the updated adapter.
- Same-job recoverable resume was accepted for `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`.
- The host MPS worker stayed idle during this validation: `active_generations=0`, `model_loaded=false`, `last_error=null`.
- `chunk_checkpoint_runner.py --chunk-size 4` ran at about 99.9% CPU for about 3 minutes 51 seconds before `chunk_plan.json` was written.
- Luceon canceled the job to avoid leaving another long-running validation process active.

Conclusion:

`PRODUCTION_VALIDATION_PARTIAL_PASS_IMPLEMENTED_BUT_INITIAL_PLAN_BUILD_STILL_BLOCKS`: the adapter now has the desired plan cache implementation, but the first full-book plan build is still too slow for the current validation window. This confirms the remaining blocker is not MPS generation; it is the initial native-function planning phase over the full 891-page / 19361-block document. Future work should treat plan build as a separate bounded/background stage or reduce the planning input before it reaches the expensive native filters, while still avoiding MinerU-Popo core changes.
