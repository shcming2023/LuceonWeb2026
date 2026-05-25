# P0 RawMaterial2CleanMaterial Bounded Mini Batch Pilot StopOnFirstFailure Task

Task ID: `TASK-20260525-144319-P0-RawMaterial2CleanMaterial-Bounded-Mini-Batch-Pilot-StopOnFirstFailure`

Issued at: 2026-05-25T14:43:19+0800

Owner: Luceon

Baseline: `main@fa1703898998f167fc6653d381ad1e4f8c8cf136`

## Mainline Objective

Validate whether the RawMaterial2CleanMaterial closed loop can move from three
successful canonical samples into a very small bounded mini-batch without new
shape fixes, namespace recovery, or side-effect drift.

This is still a pilot. It is not batch readiness, release readiness, production
readiness, UAT, L3, pressure PASS, production online, or go-live.

## Batch Cap

Hard cap: exactly these three samples, processed sequentially:

| Order | Material | Task | Title | Raw seed SHA | Raw seed size |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `3884430250123676` | `task-1779085090064` | `期末质量分析及建议（曹云童 ）` | `c5604562bf9e27383e922b42e8a547dbb7d8f6ac24a30a7354d9a27a428b737f` | 29392 |
| 2 | `696446087521346` | `task-1779010154264` | `曹云童八年级咬文嚼字` | `14e1ac847c487c9960a1d5be07c89e73f87ba3354722a427b8c7579a7c6132a9` | 65276 |
| 3 | `3228822025029647` | `task-1779085087347` | `PDF document-4F18-A8A3-62-0` | `6516df5be0a7d3bbfa8593a73075491800cb40f897e62b980c0354e5c6f1c8ad` | 39538 |

All three parsed ZIPs were read-only preflighted before task issuance and each
contains exactly one `_content_list_v2.json`.

## Critical Path Scope

Implement and run one bounded mini-batch harness that:

1. runs dry-run preflight for all three samples with no writes and no POSTs;
2. processes samples sequentially in the listed order;
3. stops on first failure and reports the exact failed sample/stage;
4. for each sample, proves raw seed SHA/size before any CleanService POST;
5. writes only that sample's raw seed if missing and exact;
6. submits at most one CleanService `toc-rebuild` POST per sample;
7. uses only `assetVersion=v1`; no fallback namespace/version recovery;
8. writes only that sample's raw2clean candidate artifact if missing and exact;
9. patches only that sample's task and material metadata;
10. verifies read-back and product-surface discoverability.

## Allowed Operations

For each target sample only:

- DB GET for the target material/task;
- parsed ZIP GET;
- exact raw seed `putObject` to
  `eduassets-raw/mineru/<materialId>/v1/content_list_v2.json`;
- at most one CleanService `POST /api/v1/jobs`;
- job query polling for that one job;
- exact candidate `putObject` to
  `eduassets-clean/raw-material-2-clean-material/<materialId>/v1/candidate.json`;
- exactly two DB PATCHes:
  - `tasks/<taskId>`
  - `materials/<materialId>`;
- local product-surface verification.

## Forbidden Operations

- more than 3 samples;
- parallel execution;
- second POST for any sample;
- automatic fallback to `v2` or another namespace;
- extra diagnostic MinIO writes;
- MinIO delete, copy, move, cleanup, or broad bucket scan;
- Docker/Compose restart/recreate/rebuild, volume mutation, or service mutation;
- job-store manual edit;
- source/sample/env/secret/model mutation;
- pressure testing, stress testing, or broad batch execution;
- final quality acceptance;
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Stop Rule

Stop immediately and report blocked if any sample:

- fails dry-run/preflight;
- has raw seed SHA/size mismatch;
- has an existing target object with different content;
- has an existing non-completed target CleanService job;
- fails the single allowed CleanService POST or completion;
- fails artifact verification;
- requires a new raw2clean shape compatibility fix;
- would embed full candidate content in DB metadata;
- fails product-surface read-back.

Do not continue to later samples after a failure.

## Review Boundary

Acceptance means only that this three-sample mini-batch pilot repeated the
closed loop under bounded, stop-on-first-failure rules.

Acceptance does not mean general batch readiness, service readiness, quality
acceptance, UAT, L3, pressure PASS, release readiness, production readiness,
production online, or go-live.

