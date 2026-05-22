# TASK-20260522-092145-P0-CleanService-Canonical-Raw-Material-Seed-NoPost

## 1. Task Summary

Create the first canonical Raw Material seed for a single Director-authorized
candidate, without dispatching Mineru2Table.

This task performs one narrowly scoped MinIO write boundary:

```text
eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
```

It must extract the source `content_list_v2.json` from the existing legacy
MinerU ZIP and write only that canonical object. No CleanService POST, LLM call,
DB write, source code change, cleanup, or broader migration is allowed.

## 2. Mainline Objective

Answer the next critical-path question:

> Can Luceon prepare a valid canonical Raw Material ObjectRef from an existing
> completed MinerU result so the next task can attempt exactly one real
> Mineru2Table dispatch against a true `eduassets-raw` input?

This is a true prerequisite for the first success-path dispatch. The current
MinIO has no `eduassets-raw` bucket and no canonical
`mineru/{materialId}/{assetVersion}/content_list_v2.json` object.

## 3. Director Authorization

The Director explicitly authorized Task 240 to perform this one controlled
MinIO write while keeping the following prohibitions:

- no `POST /api/v1/jobs`;
- no LLM/API call;
- no Luceon DB write;
- no business source code change;
- no data cleanup;
- no wider migration.

## 4. Selected Candidate

Luceon selected the candidate:

```text
materialId: 1842780526581841
title: 向树叶学习：人工光合作用
parseTaskId: task-1779085089451
assetVersion: v1
```

Selection rationale:

- small source PDF, about `86 KB`;
- educational/science content rather than personal material;
- existing MinerU parse completed;
- AI metadata already analyzed;
- current task state is `review-pending`;
- legacy MinerU ZIP contains a `content_list_v2.json`;
- extracted `content_list_v2.json` is small, about `31 KB`, with `71` blocks and
  only `title` / `paragraph` block types.

## 5. Current Evidence From Luceon

Current Luceon main:

```text
4b92d81b9f963ab1203b2686d341d946f85635e4
```

Current runtime:

- `cms-upload-server` is Compose-visible and healthy.
- `mineru2table-api` is healthy and loopback-bound.
- CleanService remains disabled:
  - `CLEANSERVICE_ENABLED=false`
  - `CLEANSERVICE_ENDPOINT=http://mineru2table:8000`

Current MinIO bucket inventory from `cms-upload-server`:

```text
eduassets
eduassets-parsed
```

Canonical Raw Material bucket is absent:

```text
eduassets-raw: absent
```

Selected material evidence:

```text
source PDF:
  bucket: eduassets
  object: originals/1842780526581841/source.pdf
  size: 86884 bytes

legacy MinerU ZIP:
  bucket: eduassets-parsed
  object: parsed/1842780526581841/mineru-result.zip
  size: 79737 bytes

legacy parsed markdown:
  bucket: eduassets-parsed
  object: parsed/1842780526581841/full.md
  size: 3867 bytes

legacy manifest:
  bucket: eduassets-parsed
  object: parsed/1842780526581841/artifact-manifest.json
  size: 3246 bytes
```

ZIP entries include:

```text
向树叶学习：人工光合作用/auto/向树叶学习：人工光合作用_content_list_v2.json
```

## 6. Critical Path Scope

Do only this:

1. Reconfirm the selected candidate and source ZIP with read-only checks.
2. Reconfirm `eduassets-raw` does not already contain the target canonical
   object.
3. Create the `eduassets-raw` bucket if absent.
4. Extract only the ZIP entry:

   ```text
   向树叶学习：人工光合作用/auto/向树叶学习：人工光合作用_content_list_v2.json
   ```

5. Validate the extracted JSON locally before upload:
   - valid JSON;
   - parsed block count can be derived;
   - no free-text transformation or model generation;
   - byte content is exactly the ZIP entry content.
6. Upload the extracted bytes to:

   ```text
   eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
   ```

7. Verify the uploaded object by `statObject` and by reading it back:
   - size matches extracted bytes;
   - SHA256 matches extracted bytes;
   - parsed block count remains the same.
8. Verify no `eduassets-clean/toc-rebuild/1842780526581841/v1/` outputs were
   created.
9. Verify Mineru2Table `jobs.json` remains unchanged.
10. Write a report and update the ledger.

## 7. Authorized Runtime/Data Operation

Only these MinIO mutations are authorized:

- create bucket `eduassets-raw` if absent;
- upload one object:

  ```text
  eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
  ```

The uploaded object must be an exact byte copy of the ZIP entry listed above.

No other MinIO object may be created, overwritten, deleted, listed for cleanup,
renamed, moved, or backfilled as part of this task.

## 8. Environment And Write Boundary

Allowed Luceon2026 files:

- `TaskAndReport/2026-05-22T09-21-45+0800_P0-CleanService-Canonical-Raw-Material-Seed-NoPost_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden file changes:

- No `server/**` or `src/**`.
- No `docker-compose*.yml`.
- No `.env*`.
- No package or lock files.
- No PRD, architecture, or contract docs.
- No AGENTS.md or `.agents/**`.
- No external Mineru2Table repository changes.

Forbidden runtime/data operations:

- No `POST /api/v1/jobs`.
- No CleanService worker tick or scheduler activation.
- No `CLEANSERVICE_ENABLED=true`.
- No LLM/API call.
- No Luceon DB write.
- No source PDF overwrite, move, rename, or deletion.
- No legacy parsed ZIP overwrite, move, rename, or deletion.
- No upload of `middle.json`, `model.json`, markdown, PDF, images, or manifest.
- No write to `eduassets-clean`.
- No Docker image build.
- No Docker service restart/rebuild/recreate.
- No Docker network mutation.
- No Docker volume cleanup/prune.
- No Mineru2Table restart/rebuild/recreate.
- No job-store cleanup, truncation, or manual edit.
- No secret or credential value printing in reports.

## 9. Fast Validation Target

Smallest useful proof:

- `eduassets-raw` exists.
- `eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json` exists.
- The uploaded object SHA256 equals the extracted ZIP entry SHA256.
- Extracted and uploaded JSON parse to the same block count.
- Mineru2Table `jobs.json` remains unchanged.
- No POST occurred.

## 10. Stop Rules

Stop immediately and report a specific blocked classification if:

1. The selected ZIP is missing.
2. The expected `content_list_v2.json` entry is missing.
3. The extracted content is not valid JSON.
4. The target canonical object already exists with a different SHA256.
5. Uploading would require overwriting an existing non-identical object.
6. Any MinIO write beyond the single authorized bucket/object would be needed.
7. Any DB write, LLM call, Docker mutation, or CleanService POST would be needed.
8. `jobs.json` changes unexpectedly.

Do not repair by widening scope.

## 11. Positive Acceptance Criteria

Luceon can accept if:

- Only the authorized bucket/object mutation occurred.
- The uploaded canonical object exactly matches the legacy ZIP entry bytes.
- Object size and SHA256 are recorded.
- Parsed block count and basic block types are recorded.
- No `eduassets-clean` output is created.
- `jobs.json` remains unchanged.
- No source/config files are modified except report and ledger.
- No `POST`, LLM/API call, DB write, Docker mutation, source code change,
  cleanup, delete, rename, or wider migration occurs.
- `git diff --check` passes.

## 12. Negative Acceptance Criteria

The task fails if:

- Any CleanService dispatch POST is sent.
- Any LLM/API call occurs.
- Any Luceon DB write occurs.
- Any source code/config file is modified.
- Any object other than the authorized canonical `content_list_v2.json` is
  created or modified.
- Any legacy source/parsed object is deleted, renamed, moved, or overwritten.
- Any `eduassets-clean` object is created.
- Mineru2Table `jobs.json` changes.
- Any Docker service/image/network/volume mutation occurs.
- The report prints raw credentials.
- The report claims UAT, L3, release-readiness, production-readiness, pressure
  PASS, production上线, or go-live.

## 13. Required AI/Data Governance Red Lines

1. ID-only / source-only extraction: this task may copy source JSON bytes from
   the MinerU ZIP. It must not ask a model to generate, summarize, rewrite, or
   invent content.
2. Asset hash locking: no image/audio/resource hash names may be renamed. This
   task does not move resource assets.
3. Pure layout/code-generation boundary: no LaTeX/TikZ or custom command
   generation is in scope.

## 14. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T09-21-45+0800_P0-CleanService-Canonical-Raw-Material-Seed-NoPost_REPORT.md
```

The report must include:

- Branch and exact HEAD.
- Director authorization summary.
- Selected candidate identity:
  - `materialId`
  - `parseTaskId`
  - `assetVersion`
  - title
- Source ZIP bucket/object/size.
- Exact ZIP entry copied.
- Extracted bytes size and SHA256.
- Uploaded canonical bucket/object/size/SHA256.
- Parsed block count and basic block types.
- Whether `eduassets-raw` was created or already existed.
- Proof that `eduassets-clean/toc-rebuild/1842780526581841/v1/` was not written.
- `jobs.json` before/after size/hash/key-count.
- Whether any POST was sent: must be `no`.
- Confirmation that no LLM/API call, DB write, source code change, Docker
  mutation, cleanup, delete, rename, or wider migration occurred.
- Final classification:
  - `CANONICAL_RAW_MATERIAL_SEEDED_NO_POST`, or
  - a specific blocked classification.

## 15. Review Boundary

Acceptance means only:

- A single selected existing MinerU result has been seeded into canonical Raw
  Material object storage for a future one-shot Mineru2Table dispatch.

Acceptance does not mean:

- Mineru2Table dispatch has happened.
- CleanService is active.
- Raw Material migration/backfill is complete.
- Luceon DB metadata references the new object.
- Clean Material artifacts exist.
- UAT, L3, pressure PASS, release readiness, production readiness,
  production上线, or go-live.
