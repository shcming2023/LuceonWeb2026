# P0 RawCode Bridge Asset Root Copy For Visual Fidelity Report

## Status

ACCEPTED_CODE_LEVEL_NARROW_FIX

## Root Cause

The fixed `4.1` pilot proved that `deepseek-v4-flash` preserved linked image references, but the validation still returned `BLOCKED` because the RawCode bundle contained `image_map.json` references without the corresponding physical image files under `images/`.

This means the visual reference contract was fixed, but the local RawCode bridge still lacked asset file packaging.

## Fix

Changed `scripts/cleanlatex-pack-to-rawcode.mjs`:

- Added optional `--asset-root <dir>`.
- For each declared image in `pack.assets.images`, the bridge now searches the asset root by `raw_ref`, `source_path`, `normalized_ref`, and hash basename.
- Copies found assets into the RawCode bundle at the normalized `images/<hash>` path.
- Records copied/missing asset counts in `manifest.json` and command output.
- Default behavior remains unchanged when `--asset-root` is omitted.

## Validation

Commands run in `/Users/concm/Dev_workspace/Luceon2026`:

```bash
node --check scripts/cleanlatex-pack-to-rawcode.mjs
node server/tests/rawcode2cleancode-runner-smoke.mjs
git diff --check
```

Result: PASS.

Additional local smoke:

- Constructed a one-pack fixture in `/tmp`.
- Provided a local `--asset-root` containing one hash-named image file.
- Verified the output RawCode bundle copied the image and returned `assetCopy.copiedCount=1`, `missingCount=0`.

## Boundaries

- No DB, MinIO, runtime worker, GPU, LLM, or production metadata mutation.
- No MinerU/MinerU-Popo upstream change.
- No asset hash rename.
- No credential written to repo or evidence.

## Next Step

Extract the existing A800 MinerU images into a local asset root, regenerate RawCode with `--asset-root`, and rerun the controlled `deepseek-v4-flash` `4.1` pilot.
