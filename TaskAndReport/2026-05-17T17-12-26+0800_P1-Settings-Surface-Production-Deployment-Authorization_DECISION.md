# TASK-20260517-171226-P1-Settings-Surface-Production-Deployment-Authorization

## Decision Needed

Task 214 has been accepted at code/review level on Lucode branch `lucode/task-214-settings-effective-semantics` / `b33db90`.

User decision is needed before Luceon mutates production services.

## Recommended Option A

Approve scoped production deployment and read-only validation of Task 214.

Allowed scope:

- integrate the accepted Task 214 frontend source changes into the production workspace;
- run repository/static checks needed for production integration;
- rebuild/restart the minimum required frontend service;
- validate read-only endpoints/pages:
  - `/cms/settings`
  - `/cms/`
  - upload/db health endpoints if needed for smoke context;
- verify deployed frontend assets no longer expose the misleading Settings strings/routes.

Not allowed:

- upload files;
- run submit-probe;
- run pressure test;
- run backup import/export;
- run cleanup, repair, reparse, or re-AI;
- mutate DB/MinIO objects, Docker volumes, model files, secrets, sample files, or production data;
- declare readiness, L3, pressure PASS, production上线, release readiness, or go-live.

## Option B

Hold production deployment for now and keep Task 214 accepted only at code level.

## Luceon Recommendation

Choose Option A.

Reason: Task 214 is a front-end Settings governance cleanup with narrow blast radius. Deploying it will prevent operators from seeing misleading active controls while preserving backend compatibility and data. The validation can be kept read-only and reversible.
