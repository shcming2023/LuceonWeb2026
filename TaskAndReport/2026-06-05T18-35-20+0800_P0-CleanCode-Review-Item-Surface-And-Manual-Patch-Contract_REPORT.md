# P0 CleanCode Review Item Surface And Manual Patch Contract Report

## Summary

Implemented a code/test-level review surface for RawCode2CleanCode output.

The runner now turns LLM `unresolved_items` and non-PASS validator checks into durable, traceable, manually editable review item artifacts instead of leaving them as loose reports.

## Scope

- Added `review_items.json` per CleanCode unit.
- Added `review_patch_contract.json` per CleanCode unit.
- Exposed both artifact paths in `clean_manifest.json`, bundle `manifest.json`, CLI output, and UAT runner evidence.
- Preserved existing `unresolved_items.json`, `quality_report.json`, `clean.md`, `source_map.json`, and `image_map.json`.

## Review Item Contract

Each review item contains:

- stable `review_item_id`
- `unit_id` / `unit_title`
- `origin`: `llm_unresolved_item` or `validator_check`
- `type`, `severity`, `status`
- `source_block_ids`
- source match method and warnings
- `source_refs` with block/page/bbox/type/order/text excerpt when available
- `source_excerpt` and `clean_excerpt`
- reason and suggested action
- `asset_hashes` and `asset_refs` when linked visual evidence is known
- per-item manual patch contract

The source matcher is conservative:

- explicit source block IDs are used first;
- otherwise `source_excerpt` is matched directly against `source_map.source_blocks`;
- if no match exists, the item remains open with a source match warning instead of guessing.

## Manual Patch Contract

Allowed item actions:

- `accept_clean_excerpt`
- `edit_clean_excerpt`
- `mark_source_ocr_issue_accepted`
- `keep_unresolved`
- `request_reparse`

Acceptance constraints:

- all review items must be closed for final unit acceptance;
- manual patches must not change the cleaning unit boundary;
- manual patches must not rename assets;
- manual patches must preserve source block references.

## Files Changed

- `scripts/rawcode2cleancode-pilot.mjs`
- `scripts/rawcode2cleancode-runner.mjs`
- `server/tests/rawcode2cleancode-runner-smoke.mjs`

## Validation

Passed:

```bash
node server/tests/rawcode2cleancode-runner-smoke.mjs
node --check scripts/rawcode2cleancode-pilot.mjs
node --check scripts/rawcode2cleancode-runner.mjs
node --check server/tests/rawcode2cleancode-runner-smoke.mjs
git diff --check
```

Additional CLI smoke:

```bash
rm -rf /tmp/luceon-cleancode-review-surface-smoke
node scripts/rawcode2cleancode-pilot.mjs --fixture --cleaner llm-dry-run --out /tmp/luceon-cleancode-review-surface-smoke --force
```

Observed output paths:

- `/tmp/luceon-cleancode-review-surface-smoke/cleancode/sample-material/v0/chapters/chapter_001/review_items.json`
- `/tmp/luceon-cleancode-review-surface-smoke/cleancode/sample-material/v0/chapters/chapter_001/review_patch_contract.json`

Sample `review_items.json` output produced:

- schema `luceon-cleancode-review-items/v1`
- status `open`
- item count `1`
- item id `review-chapter_001-0001`
- source match method `source_excerpt_direct_substring`
- source block id `b001`
- manual action set including `edit_clean_excerpt`

Sample `review_patch_contract.json` output produced:

- schema `luceon-cleancode-review-patch-contract/v1`
- all five allowed manual actions
- final acceptance requires all review items closed
- patch boundary/hash/source-reference constraints enabled

## Boundaries

No MinerU change.
No MinerU-Popo change.
No LLM prompt main-logic change.
No DB write.
No MinIO write.
No runtime worker post.
No production deployment.
No final CleanCode publishability or go-live claim.

## Status

`ACCEPTED_CODE_LEVEL_REVIEW_SURFACE_READY_FOR_PRODUCT_REVIEW_WORKBENCH`

Next mainline step is productizing these review item artifacts into an editable review workbench or applying them to a controlled real DeepSeek batch to measure human review workload.
