# Upgrade

1. Stop new task intake and verify that PipelineRun, WorkflowJob, and StageRun have no queued or running records.
2. Run `./scripts/backup`; retain its checksums and the previous release directory.
3. Run the new package preflight and image pull/load.
4. Stop the previous Compose project, run the new migration, and start the new project with `--no-build --pull never` through `./scripts/start`.
5. Run target-host acceptance without editing code, rebuilding images, recreating containers, or changing environment values during the freeze window.

Redis is transient and is not migrated. Durable MinerU and Popo assets remain in MinIO and are not copied or rewritten.
