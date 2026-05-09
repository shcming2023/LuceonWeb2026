# P0 Ollama Dependency Health Smoke Alignment Revision 1 Report

- Task: `TASK-20260509-084629-P0-Ollama-Dependency-Health-Smoke-Alignment-Revision-1`
- Assignee: Lucode
- Issued by: Lucia
- Report time: 2026-05-09T08:55:58+0800
- Development workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Branch: `lucode/p0-ollama-dependency-health-smoke-alignment-revision-1`
- Base HEAD before revision: `3c470c6`
- Branch HEAD: remote branch HEAD after push; exact final HEAD is reported in Lucode final response.
- Result: code revision applied
- Revision cycle count used: 1 of 2
- Validation pass count: still 1 of 2; pass 2 not run

## Scope Confirmation

This work was based on Lucia task brief:

`TaskAndReport/2026-05-09T08-46-29+0800_P0-Ollama-Dependency-Health-Smoke-Alignment-Revision-1_TASK.md`

Lucode did not run production-candidate validation pass 2, did not create production uploads, did not restart/rebuild production, did not restart/kill/reload Ollama, and did not change model, timeout, secret, production override, DB, MinIO, Docker volume, logs, samples, or release status.

## Investigation

Compared the dependency-health Ollama smoke request in `server/upload-server.mjs` with production provider semantics in `server/services/ai/providers/ollama.mjs`.

Observed gap:

- Production `OllamaProvider.extractMetadata()` sends:
  - `stream:false`
  - top-level `think:false`
  - `options.think:false`
  - configured model `qwen3.5:9b`
- Dependency-health smoke previously sent:
  - `stream:false`
  - `options.num_predict:2`
  - no top-level `think:false`
  - no `options.think:false`

This made the readiness smoke less aligned with the production no-think provider path and could trigger unnecessary thinking behavior in Qwen-family runtime behavior.

## Implementation Summary

Changed `server/upload-server.mjs` dependency-health Ollama `/api/chat` smoke request to:

- keep `stream:false`
- add top-level `think:false`
- add `options.think:false`
- reduce healthcheck generation budget to `num_predict:1`
- keep required model selection unchanged as `REQUIRED_OLLAMA_MODEL`
- keep existing 15s bounded smoke timeout unchanged
- keep explicit failure behavior unchanged: chat failure still sets `ollama.ok=false` and `chatOk=false`

Updated `server/tests/dependency-health-smoke.mjs` to:

- run dependency-health smoke under strict no-skeleton test env
- route `OLLAMA_API_URL` to the mock Ollama server
- capture the mock `/api/chat` request body
- assert model, `stream:false`, top-level `think:false`, `options.think:false`, and `num_predict:1`
- assert missing required `qwen3.5:9b` model fails without invoking `/api/chat`
- preserve existing assertions that Ollama down or chat failure does not block parse

## Files Changed

- `server/upload-server.mjs`
- `server/tests/dependency-health-smoke.mjs`
- `TaskAndReport/2026-05-09T08-55-58+0800_P0-Ollama-Dependency-Health-Smoke-Alignment-Revision-1_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

## Commands Run

| Command | Result |
| --- | --- |
| `git status --short --branch` | PASS; initial main clean and later branch dirty only with intended files |
| `git fetch origin` | PASS |
| `git pull --ff-only origin main` | PASS; already up to date |
| `git switch -c lucode/p0-ollama-dependency-health-smoke-alignment-revision-1` | PASS |
| `git diff --check` | PASS, exit 0 |
| `node server/tests/dependency-health-smoke.mjs` | First run failed 35 passed / 5 failed because the mock lacked `express.json()` and could not inspect request body; fixed test mock |
| `node server/tests/dependency-health-smoke.mjs` | PASS, 40 passed / 0 failed, exit 0 |
| `npx pnpm@10.4.1 exec tsc --noEmit` | PASS, exit 0 |
| `npx pnpm@10.4.1 run build` | PASS, exit 0; Vite existing chunk-size warning only |

## Evidence

Focused smoke pass included these new assertions:

- `ollama smoke should use required model`
- `ollama smoke should disable streaming`
- `ollama smoke should disable top-level thinking`
- `ollama smoke should disable options thinking`
- `ollama smoke should use a minimal token budget`
- `ollama.ok should be false when required model is missing`
- `missing model error should name required model`
- `ollama smoke should not run when required model is missing`
- `missing ollama model should not block parse`

Existing failure semantics remained covered:

- Ollama down reports `ollama.ok=false`.
- Ollama chat HTTP failure reports `ollama.ok=false`, `chatOk=false`, and `Smoke test HTTP 503`.
- Ollama remains non-blocking for parse: `blocking=false` when only Ollama is down or missing required model.

## Runtime Checks

No production runtime dependency-health check was run after the code revision because the task explicitly forbids production deploy/rebuild/restart/rollback, and the revised code is not active in production until Lucia reviews and authorizes integration/deployment.

## Skipped Checks

- Production-candidate validation pass 2: skipped by task instruction.
- Production upload validation: skipped by task instruction.
- Production deploy/rebuild/restart: skipped by hard stop.
- Ollama restart/kill/reload: skipped by hard stop.
- Production dependency-health validation of the new request shape: skipped because deploying the code to production is outside this task.

## Risks And Residual Debt

- This revision aligns dependency-health smoke request semantics with the production provider no-think path. It does not by itself prove production cold-load readiness until the change is reviewed, integrated, deployed under authorization, and validation pass 2 is run.
- The 15s smoke timeout was intentionally left unchanged because changing timeout policy was not necessary for this smallest-scope alignment and could weaken the gate without Lucia/Director review.

## GitHub Sync

- Commit: remote branch HEAD after push; exact final HEAD is reported in Lucode final response.
- Remote branch: `origin/lucode/p0-ollama-dependency-health-smoke-alignment-revision-1`

## Next Action Recommendation

Next Actor: Lucia.

Recommended status: `已完成待 Lucia 审查`.

Lucia should review the code/test diff. If accepted, Lucia may integrate this branch and then issue a separate validation pass 2 task. Lucode must not start pass 2 without a new Lucia task.
