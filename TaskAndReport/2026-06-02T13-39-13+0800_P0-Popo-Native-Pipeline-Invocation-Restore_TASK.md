# P0 Popo Native Pipeline Invocation Restore Task

Issued by: Luceon
Issued at: 2026-06-02T13:39:13+0800
Task ID: TASK-20260602-133913-P0-Popo-Native-Pipeline-Invocation-Restore

## Objective

Restore the Luceon MinerU-Popo adapter to the official MinerU-Popo pipeline shape documented in `README_zh.md`:

```text
label_normalization.py -> run_inference.py -> get_json_tree.py
```

The previous Luceon-owned chunk checkpoint runner was an adapter scheduling invention and should not be refined further.

## Scope

Allowed files:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `docker-compose.popo.yml`
- `TaskAndReport/**`

Forbidden:

- MinerU-Popo upstream core/model changes.
- Self-written chunk runner continuation.
- Broad parameter guessing.
- DB/MinIO cleanup or source asset mutation.

## Requirements

- Full-background and bounded-preview paths must call official `post_processing/run_inference.py`.
- Full-background may pass official `--resume` for document-level resume.
- Remove Luceon-owned `luceon_service/chunk_checkpoint_runner.py`.
- Remove microchunk/profile/cache behavior tied to that runner.
- Keep Luceon outer responsibilities only: job status, timeout/cancel, workdir reuse, artifact collection, read-only progress observation.
- Keep host MPS worker as the `popo_generate` backend only; do not alter official pipeline scheduling.

## Acceptance

Positive:

- Focused Python smoke passes.
- Python compile passes.
- `git diff --check` passes.
- Node/TypeScript/build gates pass.
- `rg` confirms no active code references to `chunk_checkpoint_runner.py`.

Negative:

- No MinerU-Popo original source modifications.
- No full large-PDF completion/readiness/release claim until production evidence proves it.
- No source asset hash/path mutation.
