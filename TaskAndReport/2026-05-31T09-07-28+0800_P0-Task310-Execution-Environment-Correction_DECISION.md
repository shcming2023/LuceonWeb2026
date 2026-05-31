# P0 Task310 Execution Environment Correction

Decision time: `2026-05-31T09:07:28+0800`

Related task:

```text
TASK-20260531-074623-P0-Popo-TocRebuild-Repeatable-Real-RawMaterial-Closure-To-Main
```

## Decision

Task 310 must be executed in the production/control runtime:

```text
/Users/concm/prod_workspace/Luceon2026
```

Use the existing production/control MinIO data and Luceon runtime APIs. Do not execute the real-sample Popo/toc-rebuild proof from the dev container's empty MinIO environment.

## Reason

Task 310 is a real Raw Material repeatability proof. The dev container report shows:

- default `minioadmin:minioadmin` is invalid;
- dev `.env` has empty `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY`;
- dev MinIO lacks required `mineru-result.zip` and `full.md` sample objects.

Those facts mean the dev environment is the wrong data plane for this task. They do not justify sharing MinIO credentials or syncing production sample data into dev.

## Instructions

1. Do not provide raw MinIO credentials to lucode for this task.
2. Do not sync or copy production sample data into dev MinIO.
3. Do not relabel dev MinIO absence as a product/runtime blocker.
4. Luceon owns the real-sample runtime execution and evidence collection in the production/control workspace.
5. If production/control execution exposes a code defect, Luceon will issue a narrow follow-up implementation task to lucode with exact evidence.

## Boundary

This decision authorizes only the already scoped Task 310 runtime path:

```text
hard cap 3 samples
sequential
stop on first failure
no cleanup/migration/bulk rerun
no readiness/release-readiness/go-live claim
```
