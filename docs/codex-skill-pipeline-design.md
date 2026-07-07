# Codex Skill Pipeline Design

Date: 2026-07-07

This document defines the next LuceonWeb pipeline layer: MinerU and Popo remain the first-stage GPU parsing flow, while Codex skills produce refined ElegantBook LaTeX/PDF outputs as versioned downstream artifacts.

## Goals

1. Preserve existing ElegantBook outputs, including the 123 legacy self-loop sample results.
2. Allow legacy results to be refreshed in batches by the new Codex skill without overwriting the old outputs.
3. Automatically create a Codex skill job after a newly uploaded PDF finishes MinerU and Popo.
4. Keep multi-stage async processing robust across GPU services, Codex skills, MinIO, MySQL, and the review UI.
5. Make every output traceable by source Popo manifest, skill, run id, quality state, and publication state.

## Non-Goals

1. LuceonWeb does not execute LaTeX generation synchronously inside the request path.
2. LuceonWeb does not replace or delete legacy output objects during refresh.
3. The first implementation may expose queued/dry-run Codex jobs before enabling live Codex execution.

## Artifact Lineage

Each material can have many ElegantBook outputs. The database registry is the source of truth for UI selection and promotion, while MinIO manifests remain the durable artifact source.

Required lineage fields:

- `material_id`
- `review_asset_id`
- `popo_run_id`
- source Popo manifest bucket/object
- output manifest bucket/object
- output origin: `legacy_selfloop`, `codex_elegantbook`, `codex_refined`, or `codex_skill`
- skill name and skill version
- Codex job id when applicable
- quality status: `unchecked`, `passed`, `needs_review`, or `failed`
- publication status: `candidate`, `published`, `promoted`, `archived`, or `failed`

Legacy outputs keep their existing MinIO paths, usually under `eduassets-latex/latex/{material_id}/{popo_run_id}/manifest.json`.

New Codex skill outputs are written to versioned paths, for example:

```text
eduassets-elegantbook/elegantbook/{material_id}/{popo_run_id}/{codex_run_id}/manifest.json
eduassets-elegantbook/elegantbook/{material_id}/{popo_run_id}/{codex_run_id}/compiled.pdf
eduassets-elegantbook/elegantbook/{material_id}/{popo_run_id}/{codex_run_id}/refined-overleaf.zip
```

No refresh may write into a legacy object prefix. A refresh creates a new output row and a new MinIO prefix.

## Job State Machine

`codex_skill_jobs.status` uses this state machine:

```text
queued -> running -> dry_run_succeeded -> validating -> published
queued -> cancelled
running -> failed
dry_run_succeeded -> failed
validating -> failed
failed -> queued
cancelled -> queued
```

State meaning:

- `queued`: intent has been recorded and is safe to retry.
- `running`: a worker owns the job.
- `dry_run_succeeded`: the worker prepared prompts and staging outputs but did not publish.
- `validating`: output exists and quality checks are running.
- `published`: output manifest has been stored in MinIO and registered in `material_outputs`.
- `failed`: no promotion occurred; error is stored on the job.
- `cancelled`: user or operator stopped a pending job.

## Output Promotion

`material_outputs.is_current = true` means this is the default UI output. At most one current ElegantBook output should exist per user/material/output type.

Promotion rules:

1. Legacy output can remain current until a Codex output passes quality gates.
2. A new output starts as `candidate`.
3. A quality-passed candidate may be promoted to default.
4. Promotion updates the registry row, not legacy MinIO objects.
5. Failed candidates remain visible for audit only if the UI explicitly requests them.

## Auto Trigger

After the GPU pipeline syncs a Popo success into `materials.popo_manifest_*`, LuceonWeb should create a Codex job with:

- `mode = "new_pdf"` for newly submitted PDFs.
- `mode = "refresh_legacy"` for existing legacy samples.
- idempotency key derived from user, material, Popo manifest, skill name, skill version, and mode.

The trigger must be idempotent. Re-running inventory sync should not create duplicate active jobs for the same Popo manifest and skill version.

## Batch Refresh Plan

The 123 legacy samples are refreshed in controlled batches:

1. First 10 representative samples.
2. Next 30 samples after QA review.
3. Remaining samples after the quality gates are stable.

Each batch creates new `codex_skill_jobs` rows and new `material_outputs` rows. Legacy rows remain queryable and downloadable.

Operational commands:

```bash
# Create the first 10 legacy refresh jobs.
curl -X POST http://127.0.0.1:28080/api/materials/codex-jobs/batch-refresh-legacy \
  -H 'Content-Type: application/json' \
  -d '{"limit":10}'

# Dry-run 3-5 queued jobs into local staging only.
DATABASE_URL=sqlite:////data/mineru.db \
python3 /app/scripts/codex_skill_worker.py --limit 5 --staging-root /data/codex-skill-work

# Publish a dry-run job only after real compiled.pdf and refined-overleaf.zip exist in staging.
DATABASE_URL=sqlite:////data/mineru.db \
python3 /app/scripts/codex_skill_worker.py --job-id 1 --publish-staging --target-bucket eduassets-elegantbook
```

Batch sizing convention:

- Batch A: `limit = 10`
- Batch B: `limit = 30`
- Batch C: `limit = 123` or an explicit `material_ids` list

## Consistency Rules

1. Database rows are written before worker execution so a crash leaves a visible `queued` or `running` job.
2. Workers write to local staging first.
3. MinIO publication is final only after the manifest and referenced objects exist.
4. `material_outputs` registration happens after publication validation.
5. Promotion is a separate step from publication.
6. Retries reuse lineage but produce a new run id unless the previous run never published.
7. API responses expose status separately for GPU pipeline, Codex job, output registry, and review UI selection.

## Current Runtime Evidence

On 2026-07-07, the local review runtime database was migrated from `20260705_add_latex_material_stage` to `20260707_add_codex_skill_pipeline_tables`.

The first representative dry-run batch created 5 `refresh_legacy` jobs and wrote local staging evidence:

```text
job 1 pdf-uatlatex-20260706065844-05-95f334cd dry_run_succeeded runtime/backend/codex-skill-work/job-1
job 2 pdf-uatlatex-20260706065844-04-62cbd128 dry_run_succeeded runtime/backend/codex-skill-work/job-2
job 3 pdf-uatlatex-20260706065844-03-43101368 dry_run_succeeded runtime/backend/codex-skill-work/job-3
job 4 pdf-uatlatex-20260706065844-02-2cf774d5 dry_run_succeeded runtime/backend/codex-skill-work/job-4
job 5 pdf-uatlatex-20260706065844-01-037fdccc dry_run_succeeded runtime/backend/codex-skill-work/job-5
```

These jobs are not published because dry-run staging intentionally contains prompt/report evidence only. Publication requires real `compiled.pdf` and LaTeX ZIP files.

## First Implementation Slice

The first implementation should deliver:

- `material_outputs` registry table.
- `codex_skill_jobs` queue table.
- API to create, list, get, cancel, and retry Codex jobs.
- Review compare page selection among registered/discovered ElegantBook outputs.
- A dry-run worker that writes local staging evidence and does not publish.

Live Codex invocation and auto-trigger-on-Popo can be enabled after the dry-run path is validated.
