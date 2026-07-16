# SQLite integrity repair evidence

- Detection: pipeline run `94` froze MinerU and Popo successfully, but its terminal inventory sync recorded `sqlite3.OperationalError: disk I/O error`.
- Pre-repair `PRAGMA integrity_check`: multiple `wrong # of entries in index ...` findings, including `idx_review_user_manifest`.
- Consequence: the corrupted unique index admitted three duplicate `review_assets` identities for the four-sample UAT runs.
- Safety backup: `runtime/backups/mineru-pre-index-repair-20260716-124323.db`, 1,647,013,888 bytes.
- Repair: stopped the four SQLite-writing Luceon containers; merged only three pairs whose business columns were byte-identical and differed only by `id` and `created_at`; repointed `materials` and `material_outputs` to the earliest identity; rebuilt all SQLite indexes.
- Canonical mappings retained: `2422` over `2423`, `2418` over `2424`, and `2419` over `2425`.
- Post-repair source database checks: full `PRAGMA integrity_check = ok`; `PRAGMA foreign_key_check` returned zero rows; duplicate review-identity groups = 0.
- Post-repair consistency backup: `runtime/backups/mineru-post-index-repair-20260716-125616.db`, 1,647,013,888 bytes; cold `PRAGMA quick_check(1) = ok`.
- Idempotency verification: replaying inventory sync for runs `93` and `94` retained exactly one review identity per current Popo manifest.

No MinIO object, frozen MinerU/Popo artifact, historical output artifact, or unrelated database row was deleted.
