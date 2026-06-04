# P0 CleanLaTeX Pack Linked Asset Visual Requirement Fix Report

## Status

ACCEPTED_CODE_LEVEL_NARROW_FIX

## Scope

This is a narrow follow-up to Task 333. During the fixed-pack replay, Luceon correctly recovered linked image/table assets for `4.1`, but `visual_evidence_requirements` remained empty because the requirement generator depended only on visual-reference terms in text.

## Root Cause

Using text terms alone is not robust. Real OCR can join or distort words such as `flow diagram`, while official Popo and MinerU can still provide linked image/table assets through structural relations and source evidence.

The presence of a linked visual asset inside a cleaning unit is itself a review/cleaning requirement. It must not depend on whether the adjacent text contains a clean English visual keyword.

## Fix

Changed `luceon_service/service.py` so `visual_evidence_requirements` is emitted when either:

- text contains visual-reference terms; or
- the pack has linked image assets.

This remains generic and does not hardcode section `4.1`, any page number, or any image hash.

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

Result: PASS.

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
git diff --check
```

Result: PASS.

## Boundaries

- No MinerU/MinerU-Popo upstream change.
- No inference rerun.
- No LLM call in this code-level fix.
- No credential, DB, MinIO, runtime worker, or GPU mutation.

## Next Step

Regenerate fixed pack/RawCode artifacts from existing A800 evidence and run the controlled `deepseek-v4-flash` `4.1` pilot.
