# P0 RawCode2CleanCode Pack Bridge Validator And Production UAT Report

Task ID: `TASK-20260604-163901-P0-RawCode2CleanCode-Pack-Bridge-Validator-And-Production-UAT`

Status: `完成关闭`

Branch: `codex/rawcode2cleancode-review-fixes`

Implementation HEAD: `9610526`

## Scope

Review and tighten the `RawCode -> CleanCode` implementation landed in `main@d703080`.

This closeout focused only on the current mainline bridge:

```text
Task329 cleaning_unit_packs.json -> RawCode bundle -> RawCode2CleanCode runner -> CleanCode candidate
```

No MinerU, MinerU-Popo, DB, MinIO write, runtime worker post, or LLM call was performed.

## Review Findings

1. The original runner was safe as a local UAT runner, but it only accepted a bespoke RawCode bundle. It did not directly consume the real Task329 `cleaning_unit_pack` artifact shape, so fixture-only tests could not prove the current production mainline.
2. The original validator could mark deterministic output as `PASS` even when visible raw separators (`<|txt_split|>`) and duplicated large text segments remained. That was too optimistic for CleanCode quality.
3. Documentation had trailing whitespace and `scripts/run-tests.sh` still printed stage `1/3` after adding a fourth test stage.

## Revisions

- Added `scripts/cleanlatex-pack-to-rawcode.mjs`.
  - Converts Task329 `luceon-cleanlatex-cleaning-unit-pack/v1` artifacts to `RawCode2CleanCode/v0` RawCode bundles.
  - Emits `rawcode2cleancode-uat-manifest.json` for the existing runner.
  - Preserves source pack IDs, source block IDs, source hash evidence, page ranges, structure boundary, and asset hash names.
  - Remains local-file only with zero production side effects.
- Tightened `scripts/rawcode2cleancode-pilot.mjs` validator.
  - Residual `<|txt_split|>` markers now produce `NEEDS_REVIEW`.
  - Repeated large normalized text segments now produce `NEEDS_REVIEW`.
  - The runner still produces candidates, but no longer claims clean PASS for clearly dirty output.
- Extended `server/tests/rawcode2cleancode-runner-smoke.mjs`.
  - Added pack-adapter coverage.
  - Added regression coverage for split-marker and duplicate-text downgrade.
- Fixed documentation trailing whitespace and test stage numbering.

## Verification

Development checks:

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/cleanlatex-pack-to-rawcode.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node --check scripts/rawcode2cleancode-runner.mjs
node --check server/tests/rawcode2cleancode-runner-smoke.mjs
git diff --check
```

Production/control checks on `origin/codex/rawcode2cleancode-review-fixes@9610526`:

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/cleanlatex-pack-to-rawcode.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node --check scripts/rawcode2cleancode-runner.mjs
git diff --check origin/main...HEAD
```

All checks passed.

## Production UAT Evidence

Evidence directory:

```text
/Users/concm/prod_workspace/Luceon2026/TaskAndReport/evidence/2026-06-04_RawCode2CleanCode_Review_Fixes_UAT
```

Inputs:

- MinIO bucket: `eduassets-clean`
- Prefix: `toc-rebuild/4134323036518274/v329-cleanlatex-pack-generator-a800-math-2022-prod-uat/`
- Read-only files copied locally:
  - `cleaning_unit_packs.json`
  - `cleanlatex_pack_manifest.json`

Adapter result:

- `packCount=2`
- `materialId=4134323036518274`
- `version=rawcode-from-v329`
- side effects: `db_writes=0`, `minio_writes=0`, `runtime_worker_posts=0`

Runner result:

- `ok=true`
- `completedSampleCount=2`
- `llmApiCall=0`
- `dbWrite=0`
- `minioWrite=0`
- `runtimeWorkerPost=0`

Quality statuses:

| Chapter | Status | Reason |
| --- | --- | --- |
| `toc-0003` / `1.1 Different types of numbers` | `NEEDS_REVIEW` | 639 `<|txt_split|>` markers and repeated large text segments remain. |
| `toc-0024` / `4.1 Colectingand classifyingdata` | `NEEDS_REVIEW` | 8 `<|txt_split|>` markers and repeated large text segments remain. |

This is the correct P0.1 outcome: the bridge and candidate packaging work, but the deterministic cleaner is not sufficient to claim clean content quality on real A800 Math 2022 packs.

## Closure

Accepted for mainline as a safe bridge and validator hardening step.

Next mainline task should use the same pack bridge and run a controlled true cleaner path for one unit, while preserving the current `NEEDS_REVIEW` quality gates.

No production metadata was mutated. No evidence directory was committed.
