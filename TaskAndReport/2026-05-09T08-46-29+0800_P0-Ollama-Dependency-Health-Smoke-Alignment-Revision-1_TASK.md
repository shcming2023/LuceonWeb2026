# Lucode Task Brief: P0 Ollama Dependency Health Smoke Alignment Revision 1

- Task ID: `TASK-20260509-084629-P0-Ollama-Dependency-Health-Smoke-Alignment-Revision-1`
- Issued at: 2026-05-09T08:46:29+0800
- Issued by: Lucia
- Next Actor: Lucode
- Priority: P0
- Current main at issue time: `45983a3`
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production path: `/Users/concm/prod_workspace/Luceon2026`

## Objective

Use the smallest responsible code-level revision, or a clearly evidenced no-code conclusion if no change is needed, to remove the pass-1 Ollama dependency-health readiness blocker before production-candidate validation pass 2.

This task is revision cycle 1 of the Director's two-revision-cycle timebox. It does not consume validation pass 2.

## Accepted Background

Task 52 pass 1 reported:

- production and development synced to `4ff4791`
- CMS/DB/MinIO/MinerU and MinerU submit probe passed
- Task 50 diagnostic classification passed in production
- no controlled upload was run because Ollama `qwen3.5:9b` dependency-health smoke timed out on the cold check and again after one bounded warm-up

Lucia's later independent review observed that current dependency-health can pass in warm state:

- default dependency-health: Ollama `ok=true`, `durationMs=11212`
- dependency-health with MinerU submit probe: MinerU probe HTTP `202`, task id `2aac6910-0c32-42e8-b09a-3a4937393ee6`, Ollama `ok=true`, `durationMs=552`

This indicates a readiness-smoke / cold-load stability boundary, not model absence.

## Required Investigation

Inspect the Ollama smoke path in `/ops/dependency-health` and compare it with the production Ollama provider semantics.

At minimum, verify whether the dependency-health smoke request should be aligned with `server/services/ai/providers/ollama.mjs`, especially:

- top-level `think:false`
- `options.think:false`
- `stream:false`
- a very low `num_predict`
- the required model `qwen3.5:9b`
- timeout behavior and error reporting

Do not weaken strict AI behavior or make dependency-health silently pass when actual chat generation is unavailable.

## Authorized Scope

You may:

1. Modify repository code and focused tests needed for dependency-health Ollama smoke alignment.
2. Add or update focused assertions in `server/tests/dependency-health-smoke.mjs` or a narrowly scoped equivalent.
3. Run local repository checks.
4. Run read-only runtime dependency-health checks against `http://localhost:8081/__proxy/upload` if useful for evidence.

## Non-Goals And Hard Stops

Do not:

- declare production release readiness
- run production deploy/rebuild/restart/rollback or broad Docker/Compose actions
- restart, kill, reload, or change Ollama
- change model selection, secrets, production timeout override, or `docker-compose.override.yml`
- delete or mutate DB rows, MinIO objects, Docker volumes, logs, task artifacts, or sample files
- create production validation uploads
- enable skeleton fallback or silent degradation
- broaden the fix into unrelated AI metadata or queue architecture changes

If the only viable fix would require any hard-stop action, write a blocked report instead.

## Acceptance Criteria

- The dependency-health Ollama smoke request is either aligned with production provider no-think semantics, or the report proves no code change is needed.
- Existing semantics remain intact:
  - missing required Ollama model still fails when strict no-skeleton is active
  - Ollama chat failure still reports `ollama.ok=false` and `chatOk=false`
  - Ollama remains non-blocking for parse (`blockingParse=false`)
  - overall dependency-health `ok` still reflects MinIO, MinerU, and AI readiness as designed
- Focused test coverage proves the request shape and failure behavior.
- No production data, sample, secret, model, override, Docker volume, or release-status mutation occurs.

## Required Checks

At minimum:

```bash
git status --short --branch
git diff --check
node server/tests/dependency-health-smoke.mjs
npx pnpm@10.4.1 exec tsc --noEmit
npx pnpm@10.4.1 run build
```

If you run runtime checks, keep them bounded and report exact commands and JSON fields.

## Required Report

Create:

`TaskAndReport/YYYY-MM-DDTHH-MM-SS+0800_P0-Ollama-Dependency-Health-Smoke-Alignment-Revision-1_REPORT.md`

Update `TaskAndReport/TASK_TRACKING_LIST.md` row 53 with:

- status
- report path
- branch / HEAD
- whether a code revision was applied
- revision cycle count used
- validation pass count remaining
- exact next actor and next action

Expected next actor: `Lucia`.

Do not start production-candidate validation pass 2 without a new Lucia task.
