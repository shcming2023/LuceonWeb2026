# Architect Report: P1 Release Readiness Final Refresh After MinerU Recovery And Helper Sync

- Task ID: `TASK-20260515-121739-P1-Release-Readiness-Final-Refresh-After-MinerU-Recovery-And-Helper-Sync`
- Role: Architect
- Report date: 2026-05-15
- Workspace: `/Users/concm/Library/CloudStorage/OneDrive-个人/Mac/项目开发/3.Luceon2026`
- Production deployment path referenced read-only: `/Users/concm/prod_workspace/Luceon2026`

## Recommendation

`CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS`

Current evidence supports Director asking User for a release-boundary decision only with explicit limitations recorded. It does not support declaring production readiness, L3, pressure PASS, release approval, or go-live readiness.

## Blocker Refresh

### 1. Production source drift / local override

Status: conditionally mitigated for decision purposes.

Task 163 classified the production drift: five tracked dirty files were EOL-only / no semantic diff, and `docker-compose.override.yml` was production-local runtime configuration. Task 176 then intentionally synced only the no-submit helper and two docs files into production without commit/push or service mutation. The production tree is still dirty by design, so this remains a disclosure item, not a hidden blocker.

Current read-only production status observed:

- HEAD: `1716add Dispatch dependency health production validation`
- Branch: `main...origin/main`
- Dirty tracked/local files include the previously classified files plus the intentionally synced helper/docs files:
  - `.gitignore`
  - `docker-compose.override.yml`
  - `docs/codex/TEST_MATRIX.md`
  - `docs/deploy/PRODUCTION_RUNTIME_OWNERSHIP.md`
  - `ops/runtime-ownership-status.sh`
  - `server/db-server.mjs`
  - `server/tests/worker-smoke.mjs`
  - `src/app/components/BatchUploadModal.tsx`
  - `src/app/pages/SourceMaterialsPage.tsx`

Architect view: acceptable for User decision only if Director discloses the exact dirty-production boundary and the local override contract.

### 2. Dependency-health timing semantics

Status: mitigated.

Tasks 164 and 166 implemented, deployed, and read-only verified the Ollama readiness timing fields. Current production dependency-health still reports:

- `readinessState=resident-chat-succeeded`
- `readinessSeverity=info`
- `probeTimeoutMs=15000`
- `recommendedClientTimeoutMs=20000`
- `blockingAi=false`
- `readinessBlocking=false`
- `blockingParse=false`
- `submitProbe.enabled=false`

Architect view: this blocker is closed for decision purposes. It is not a proof of cold-start success under all future conditions, but the previous misleading timing gap is corrected.

### 3. AI residual disposition

Status: mitigated by explicit User decision, with residual disclosure required.

Task 167 recorded the User decision to treat known pressure-window `failed/ai` residuals as visible manual retry candidates for this readiness track. Current read-only active-task status still reports:

- `activeTask=null`
- `queuedTasks=0`
- `takeoverRequiredCount=0`
- `historicalAiFailureCount=6`

Architect view: not a blocker if the boundary remains explicit: these residuals are not counted as success, are not hidden, and were not repaired/retried/reparsed/re-AI in this track.

### 4. Rollback / recovery / error-path evidence

Status: partially mitigated, still the main limitation.

Tasks 168 and 170 turned the rollback/error-path question into evidence. Task 170 found a real critical blocker: MinerU health was green while submit admission failed with HTTP 500, and the helper default unexpectedly ran a submit-probe. Task 171 diagnosed the primary issue as `MINERU_SUBMIT_API_BROKEN` with a secondary service-ownership/config mismatch risk. Task 173 performed the separately authorized scoped MinerU-only recovery and exactly one authorized submit-path verification; the synthetic submit returned HTTP 202 and closed admission. Tasks 174 and 176 then hardened and synced the helper so read-only status no longer creates a submit probe by default.

Current read-only production evidence:

- Docker services are up and healthy: `cms-db-server`, `cms-frontend`, `cms-minio`, `cms-upload-server`.
- `cms-minio` console remains local-only at `127.0.0.1:19001->9001/tcp`.
- Helper default output says `dependency health without MinerU submit probe (read-only)`.
- Helper default output says `MinerU submit probe skipped`.
- Helper default output says `RUN_MINERU_SUBMIT_PROBE=0; no synthetic MinerU task was created by this helper`.
- Dependency health returned HTTP 200 with `ok=true`, `blocking=false`, and `mineru.submitProbe.enabled=false`.
- Admission circuit returned closed with `lastSuccessfulSubmitAt=2026-05-15T03:40:26.616Z`.
- Direct MinerU `/health` returned healthy with `queued_tasks=0`, `processing_tasks=0`, `completed_tasks=1`, `failed_tasks=0`.

Architect view: the live submit-path blocker and helper hazard are mitigated, but no fresh real PDF upload has been executed after recovery, and no rollback/restore/failure-injection rehearsal has been completed. This is not enough for a readiness claim, but it is enough to ask User whether to accept the limitation or require additional validation.

## Evidence Matrix

| Evidence | What it supports | What it does not prove |
| --- | --- | --- |
| Task 163 source drift classification | Production drift/local override is known and bounded enough for disclosure. | It does not make production clean or remove the local override dependency. |
| Tasks 164 / 166 dependency-health implementation and production verification | Ollama readiness timing is no longer misleading, and current dependency-health is non-blocking. | It does not prove every future cold-start path or all model residency edge cases. |
| Task 167 User decision | Known `failed/ai` residuals may remain visible manual retry candidates in this track. | It does not convert those residuals into success or acceptance evidence. |
| Tasks 168 / 170 rollback/error-path evidence | Read-only evidence process found a real MinerU submit blocker and helper side-effect risk. | It did not itself repair or validate a user PDF flow. |
| Tasks 171 / 173 MinerU diagnosis and recovery | MinerU submit path recovered after scoped MinerU-only recovery, verified once by authorized synthetic submit. | It does not prove a fresh real PDF upload succeeds after recovery. |
| Tasks 174 / 176 no-submit helper hardening and production sync | Default runtime helper is now read-only/no-submit in code and production source. | It does not prevent an operator from explicitly enabling submit-probe later. |
| Current read-only checks | Services are healthy, admission closed, active task clean, dependency-health non-blocking without submit-probe. | They do not constitute pressure, batch, soak, fresh serial validation, L3, or release readiness. |

## Residual Risks

1. No real PDF upload after MinerU recovery.
   - Severity: Medium to High depending on User risk tolerance.
   - Decision impact: must be disclosed. If User requires post-recovery end-to-end proof, Director should dispatch a separately authorized TestAcceptanceEngineer task for exactly one controlled PDF upload.

2. Rollback/restore/failure-injection rehearsal not completed.
   - Severity: Medium.
   - Decision impact: not necessarily blocking a release-boundary discussion, but blocking any strong operational-readiness claim. A rehearsal should be a separate task with explicit user authorization and blast-radius limits.

3. Single-machine dependency ownership remains operationally fragile.
   - Severity: Medium.
   - Decision impact: MinerU host tmux session, Ollama host dependency, and Docker services are observable and currently healthy, but this is not an HA or fully automated recovery model.

4. Historical `failed/ai` residuals remain visible.
   - Severity: Medium.
   - Decision impact: already accepted by User for this track as manual retry candidates, provided they remain visible and are not counted as success.

5. Production remains intentionally dirty/local.
   - Severity: Low to Medium.
   - Decision impact: acceptable only with exact disclosure of local override and synced helper/docs files. Director remains responsible for deciding whether to record/sync these repository-side later.

6. Submit-probe is now opt-in, not impossible.
   - Severity: Low.
   - Decision impact: helper default is safe/read-only, but operator discipline is still required for `RUN_MINERU_SUBMIT_PROBE=1` or `--submit-probe`.

## Recommended Next Actor

Next Actor: `Director`

Recommended Director action:

Ask User for a release-boundary decision with the limitations above, instead of issuing more read-only checks. The decision should explicitly distinguish:

- accepting `CONDITIONAL_GO_WITH_EXPLICIT_LIMITATIONS`;
- requiring exactly one controlled real PDF upload after MinerU recovery before decision;
- requiring rollback/recovery rehearsal before decision;
- holding `NO_GO` if the User does not accept the no-new-upload / no-rehearsal limitations.

## Forbidden Operations Confirmation

During this Architect task I did not run:

- `git fetch`, `git pull`, `git push`, commit, or GitHub sync;
- production deploy/rebuild/restart/rollback;
- upload, pressure/batch/soak/fresh serial validation;
- `mineruSubmitProbe=true`, `RUN_MINERU_SUBMIT_PROBE=1`, `--submit-probe`, or any submit-probe action;
- DB/MinIO/Docker volume/data mutation;
- cleanup/cancel/repair/retry/reparse/re-AI;
- config/secret/model/sample mutation;
- PRD truth, role contract, project-state, or handoff edits.
