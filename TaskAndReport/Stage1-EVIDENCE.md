# Stage 1 Evidence - Dependency Audit And Build Preflight

Collected at: `2026-05-26T15:32:27+0800`

Scope: non-destructive static and configuration preflight. No production deployment, upload, submit-probe, pressure run, DB write, MinIO write, Docker volume mutation, or go-live/readiness claim was performed.

Full-UAT supplement collected at: `2026-05-26T16:22:05+0800` after user authorization for real UAT. Runtime-mutating checks below were performed under that authorization only.

## Commands

| Check | Command | Result |
| :--- | :--- | :--- |
| Shell syntax | `bash -n uat/smoke-test.sh uat/release-gate.sh uat/stress-test-concurrency.sh uat/fault-injection-admission.sh uat/fault-injection-worker-crash.sh ops/start-luceon-runtime.sh` | `PASS` |
| Diff whitespace | `git diff --check` | `PASS` |
| Release gate help | `bash uat/release-gate.sh --help` | `PASS`; help states non-interactive mode cannot fake destructive stages |
| TypeScript | `npx tsc --noEmit` | `PASS` |
| Production build | `npm run build` | `PASS`; Vite chunk-size warning only |
| Compose contract fail-fast | `docker compose config --quiet` with no MinIO credentials | `PASS_AS_BLOCKING_PRECHECK`; failed because `MINIO_ACCESS_KEY` is required |
| Compose contract with non-default preflight credentials | `MINIO_ACCESS_KEY=preflight_nondefault MINIO_SECRET_KEY=preflight_nondefault_secret docker compose config --quiet` | `PASS` |
| TypeScript after UAT fixes | `npx tsc --noEmit` | `PASS` |
| Production build after UAT fixes | `npm run build` | `PASS`; Vite chunk-size warning only |
| Docker no-cache build | `docker compose build --no-cache` | `PASS`; frontend image build ran `pnpm run build` successfully |

## Contract Findings

- `CMS_PORT` is now locked to default `8081` in compose and `.env.example`.
- MinIO no longer uses `latest` in compose; it is locked to `minio/minio:RELEASE.2025-09-07T16-13-09Z`.
- Compose now requires explicit MinIO credentials instead of falling back to `minioadmin`.
- `ops/start-luceon-runtime.sh` also fails fast if credentials are unset, empty, or `minioadmin`.

## Pending

- Dependency vulnerability audit (`pnpm audit` or equivalent) was not run in this no-mutation collection pass and remains pending for formal release evidence.
