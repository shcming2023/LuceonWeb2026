# P0 Popo FullBackground Chunk Checkpoint Runner

Issued by: Luceon
Issued at: 2026-06-02T11:35:29+0800
Task ID: TASK-20260602-113529-P0-Popo-FullBackground-Chunk-Checkpoint-Runner

## Objective

Fix the Luceon adapter full-background execution boundary so large PDF Popo runs are chunk-checkpointed and resumable instead of being killed by a single whole-document subprocess timeout.

## Scope

Allowed:

- `luceon_service/app.py`
- `luceon_service/service.py`
- `luceon_service/chunk_checkpoint_runner.py`
- focused adapter tests and TaskAndReport records

Forbidden:

- modifying MinerU-Popo core files under `/Users/concm/prod_workspace/MineruPopo`
- model files, MinIO credentials, DB secrets, Docker volumes, or sample PDFs
- UI polish or unrelated storage repair

## Requirements

- Adapter must not run full-background through one monolithic `run_inference.py` subprocess.
- Full-background must process one missing Popo chunk at a time.
- Each chunk must persist raw record and checkpoint before the next chunk starts.
- Existing raw chunk files must be skipped on resume.
- Timeout must apply to one chunk execution, not the entire document.
- Cancel must prevent launching the next chunk.
- Terminal timeout/failed/canceled recoverable jobs must be resumable with the same job id and work directory.
- MPS active-generation stalls must remain visible in progress/health evidence.

## Acceptance

- Python smoke and compile checks pass.
- TypeScript/build checks pass.
- No MinerU-Popo core changes.
- Production validation is a separate step after deployment.
