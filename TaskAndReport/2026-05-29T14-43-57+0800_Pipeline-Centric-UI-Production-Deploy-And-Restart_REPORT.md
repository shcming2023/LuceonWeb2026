# Pipeline-Centric UI Production Deploy And Restart Report

Executed at: `2026-05-29T14:43:57+0800`

Requested by: Director

Deployed source: `main@43914ecea2de0e1ee29aea17ec83689f96d269d4`

Related accepted task: `TASK-20260529-132613-P0-Task-And-Library-Pipeline-Centric-Simplification-UI-NoBackendMutation`

## Scope

Deploy the accepted pipeline-centric UI changes to the local production service at:

```text
http://127.0.0.1:8081/cms/
```

## Commands

Validated source state:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

Result:

```text
## main...origin/main
HEAD = origin/main = 43914ecea2de0e1ee29aea17ec83689f96d269d4
```

Built frontend image:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml build cms-frontend
```

Build result:

```text
vite v6.3.5 building for production
1655 modules transformed
dist/assets/index-9GZSQ5F6.css
dist/assets/index-BcMiOFX7.js
built successfully
```

Recreated frontend only:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --no-deps --force-recreate cms-frontend
```

## Runtime Result

Container status after restart:

```text
cms-frontend       Up (healthy), 0.0.0.0:8081->80/tcp
cms-upload-server  Up (healthy), unchanged
cms-db-server      Up (healthy), unchanged
cms-minio          Up (healthy), unchanged
```

HTTP checks:

```text
GET http://127.0.0.1:8081/cms/ => 200 OK
GET http://127.0.0.1:8081/__proxy/upload/health => {"ok":true,"service":"upload-server"}
GET http://127.0.0.1:8081/__proxy/db/health => {"ok":true,"service":"db-server"}
GET http://127.0.0.1:8081/__proxy/upload/ops/dependency-health => ok=true, blocking=false
```

Browser verification:

```text
/cms/tasks => PASS: task page visible, pipeline column visible, output packet labels visible
/cms/library => PASS: library visible, advanced filter visible, Clean Mat output packet visible
/cms/tasks/task-1779854322261 => PASS: task detail visible, mainline pipeline visible, NEXT OPERATOR ACTION visible
/cms/asset/4436337599748917 => PASS: asset detail visible, mainline pipeline and toc-rebuild context visible
```

## Boundary

Performed:

- frontend Docker image rebuild;
- `cms-frontend` recreate/restart;
- read-only HTTP and browser verification.

Not performed:

- DB write/cleanup/migration;
- MinIO object write/delete/move/copy/cleanup;
- Docker volume mutation;
- `cms-upload-server`, `cms-db-server`, or `cms-minio` restart;
- upload, submit-probe, runtime processing, pressure test, UAT claim, readiness claim, or go-live claim.

## Conclusion

Deployment and restart completed successfully for the accepted UI changes. The updated pipeline-centric UI is available at:

```text
http://127.0.0.1:8081/cms/
```
