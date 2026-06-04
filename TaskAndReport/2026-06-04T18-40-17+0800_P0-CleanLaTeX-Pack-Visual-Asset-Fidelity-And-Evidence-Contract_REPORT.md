# P0 CleanLaTeX Pack Visual Asset Fidelity And Evidence Contract Report

## Status

ACCEPTED_CODE_LEVEL_WITH_ROOT_CAUSE_EVIDENCE

## Scope

This task closes the visual asset fidelity gap between official MinerU/MinerU-Popo outputs, Luceon cleaning unit packs, RawCode, and RawCode2CleanCode validation.

No MinerU or MinerU-Popo upstream code was changed. No MinerU/MinerU-Popo inference was rerun. No DB, MinIO, runtime worker, GPU, or production metadata mutation was performed.

## Root Cause

The missing flow diagram in the `4.1 Colectingand classifyingdata` CleanCode pilot was not caused by DeepSeek cleaning and was not caused by missing upstream extraction.

Observed evidence from the existing A800 Math 2022 artifacts:

- MinerU `content_list.json` contains the image asset on `page_idx=121` with hash name `71ef028a11659ad184c2c55a77eec9c6447b1168a81d59e273fb945c43d6929f.jpg`.
- Official MinerU-Popo output contains an image node on page 122: node `id=2884`, `type=image`, `image=2885`, immediately linked to the `4.1` source span.
- The old Luceon cleaning unit pack for `toc-0024` had `assets.images=[]`, and the old RawCode `image_map.json` also had `images=[]`.

Therefore the real defect was in Luceon layer-3 pack generation: it selected canonical text span block ids, but did not pull linked official Popo image/table nodes into the same cleaning unit, and did not reconcile Popo normalized bbox coordinates with MinerU content_list bbox coordinates.

## Implementation

Changed files:

- `luceon_service/service.py`
- `scripts/cleanlatex-pack-to-rawcode.mjs`
- `scripts/rawcode2cleancode-pilot.mjs`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- `server/tests/rawcode2cleancode-runner-smoke.mjs`

Key changes:

- Build a MinerU asset index from `content_list.json` for image/table assets, preserving original hash names.
- Associate official Popo image/table nodes to MinerU assets through source id, page, and bbox matching.
- Normalize bbox coordinate systems before comparison, so Popo normalized coordinates and MinerU pixel/thousandth coordinates can match without hardcoding.
- Add related image/table nodes to cleaning unit packs when they link to selected source span ids through fields such as `image`, `table`, or `contd`.
- Add `visual_evidence_requirements` to cleaning unit packs and prompts.
- Preserve asset refs and asset hash names in RawCode `source_map.json` and `image_map.json`.
- Extend RawCode2CleanCode validation so a visual evidence requirement must either keep the linked image ref or create an unresolved review item.

## Validation

Commands run in `/Users/concm/Dev_workspace/Luceon2026`:

```bash
python3 -m py_compile luceon_service/app.py luceon_service/service.py
```

Result: PASS.

```bash
python3 - <<'PY'
import sys, types
sys.path.insert(0, '.')
sys.modules.setdefault('boto3', types.SimpleNamespace(client=lambda *args, **kwargs: None))
from luceon_service.tests.test_popo_invocation_boundary import test_cleanlatex_pilot_packs_are_structure_level_and_source_bound

test_cleanlatex_pilot_packs_are_structure_level_and_source_bound()
print('targeted cleanlatex pack visual asset test passed')
PY
```

Result: PASS. The test forces normalized Popo bbox to match a MinerU-style scaled bbox and verifies the `4.1` pack carries the image hash and `asset-linked` visual requirement.

```bash
node --check scripts/cleanlatex-pack-to-rawcode.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node --check scripts/rawcode2cleancode-runner.mjs
node server/tests/rawcode2cleancode-runner-smoke.mjs
```

Result: PASS. Smoke case 13 verifies that visual evidence requirements cannot be silently dropped by CleanCode output.

```bash
git diff --check
```

Result: PASS.

Additional read-only replay against existing A800 Math 2022 evidence:

- Input tree: `TaskAndReport/evidence/2026-06-04_A800_Math_2022_UAT/extracted/popo_outputs/cambridge_igcse_0580_math_2022_luceon_fresh_uat.json`
- Input MinerU zip: `TaskAndReport/evidence/2026-06-04_A800_Math_2022_UAT/extracted/mineru-result.zip`
- Asset index counts: `images=1438`, `tables=373`
- Real `4.1` span ids `2885,2886,2887,2888,2928` now resolve related asset blocks, including image hash `71ef028a11659ad184c2c55a77eec9c6447b1168a81d59e273fb945c43d6929f.jpg`.

## Boundaries

- No hardcoded section number, page number, or image hash was added to production code.
- No upstream MinerU/MinerU-Popo algorithm or pipeline behavior was changed.
- No LLM call was made in this task.
- No API credential was written to code, report, env, or evidence.
- Evidence directories remain local/untracked.

## Next Mainline

Regenerate the RawCode pack artifacts from the fixed adapter output, then rerun the controlled `deepseek-v4-flash` pilot for `4.1`. Expected behavior is not automatic PASS: it should either preserve the linked visual asset reference or explicitly produce an unresolved item for human review.
