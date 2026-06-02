# P0 Official Popo FullBackground Large PDF Completion Run And Evidence Collection Task

Issued by: Luceon
Issued at: 2026-06-02T15:20:00+0800
Task ID: TASK-20260602-152000-P0-Official-Popo-FullBackground-Large-PDF-Completion-Run-And-Evidence-Collection

## Objective

Run the same large PDF v6 Popo full-background job through the official MinerU-Popo pipeline and collect durable evidence until success, failure, timeout, or operator cancellation.

This is an evidence run, not a code-change task.

## Target

- Luceon task: `task-1780291805535`
- Material ID: `4134323036518274`
- Popo job: `luceon-task-1780291805535-toc-rebuild-v6-1780366071573`
- Mode: `full-background`
- Resume: `true`
- Pipeline: official `/app/post_processing/run_inference.py --resume`

## Requirements

- Do not change MinerU-Popo official pipeline.
- Do not reintroduce Luceon chunk runner.
- Monitor once per hour:
  - Popo adapter job status and progress.
  - raw chunk files under `outputs/inference_raw/mineru/4134323036518274`.
  - MPS worker health.
  - Popo container process/CPU view.
  - cancel/release state if applicable.
- If completed, inspect `rebuilt_markdown.md`, tree artifacts, and CleanService metadata.
- If failed/timeout/canceled, summarize the exact failure and whether it is a hardware/deployment boundary or source-data/content issue.

## Boundaries

- No DB/MinIO cleanup.
- No object deletion or source asset mutation.
- No source image hash rename.
- No release/readiness/L3/go-live claim from this task alone.
