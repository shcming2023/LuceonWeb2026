# Rollback

Keep the previous package, its immutable image digests, verified SQLite/MySQL backups, runtime config, skill snapshot, and Compose inventory before deployment.

If acceptance fails, run `./scripts/rollback /path/to/previous-release-package`. Restore the matching database snapshots before accepting new work. Do not delete or modify frozen MinIO assets. Clear only the failed deployment's transient Redis queue and retain its logs and manifests for diagnosis.
