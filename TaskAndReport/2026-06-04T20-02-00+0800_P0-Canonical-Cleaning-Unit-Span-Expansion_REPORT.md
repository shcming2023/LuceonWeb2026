# P0 Canonical Cleaning Unit Span Expansion Report

## Status

ACCEPTED_CODE_LEVEL_ROOT_CAUSE_FIX

## Corrected Root Cause

The previous `4.1` pilot should not be classified primarily as a future image/table-to-text limitation.

The real upstream blocker is narrower and earlier:

- Luceon cleaning unit pack source span binding was too narrow.
- It bound a canonical section to the matched title/opening body ids and child exercise title.
- It did not expand along official Popo body order to include the full section body and child exercise body blocks before the next same-level or upper-level canonical boundary.
- For `4.1`, this meant Exercise 4.1 title node `2928` could be present while body nodes `2929-2963` were omitted.

Visual asset fidelity is now working, but text span completeness still needed this canonical cleaning unit expansion.

## Fix

Changed `luceon_service/service.py`:

- Added official source rows in body order.
- Added canonical cleaning unit span expansion:
  - starts from the canonical node's matched source block order;
  - walks official Popo body order;
  - stops at the next canonical boundary that is after the current node and at the same or higher structural level;
  - skips current ancestors and descendants as stop boundaries, so child Exercise bodies remain inside the parent section pack;
  - falls back to forward title/number matching when a later boundary was initially bound to a Contents-page source row.
- Records span expansion metadata in `pack.source_span.span_expansion`.

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
print('targeted cleaning unit span expansion test passed')
PY
```

Result: PASS. The fixture verifies that a `4.1` pack includes child Exercise 4.1 body blocks and stops before `4.2`.

```bash
node --check scripts/cleanlatex-pack-to-rawcode.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node server/tests/rawcode2cleancode-runner-smoke.mjs
git diff --check
```

Result: PASS.

Real A800 Math 2022 read-only source-order probe:

- Start: `4.1` source ids `2885,2886,2887,2888`
- Boundary: next `4.2` section
- Expansion result includes:
  - `2928` Exercise 4.1 title
  - all `2929-2963` Exercise 4.1 body blocks
  - not `2964` / `4.2` boundary

## Boundaries

- No MinerU/MinerU-Popo upstream change.
- No inference rerun.
- No LLM call in this code-level fix.
- No DB, MinIO, runtime worker, GPU, or production metadata mutation.
- No section/page/hash hardcoding.

## Next Step

Regenerate the `4.1` fixed pack/RawCode with expanded source span and rerun the controlled `deepseek-v4-flash` pilot. Expected improvement: Exercise 4.1 text content should now be available to the cleaner, so prior `missing_content` review item should reduce or disappear unless genuine extraction gaps remain.
