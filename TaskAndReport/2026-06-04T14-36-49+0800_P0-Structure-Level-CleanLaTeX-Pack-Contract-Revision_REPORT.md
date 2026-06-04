# P0 Structure-Level CleanLaTeX Pack Contract Revision Report

Task ID: TASK-20260604-143649-P0-Structure-Level-CleanLaTeX-Pack-Contract-Revision

Branch: `codex/task-328-cleanlatex-section-pack-contract`

## Summary

Revised the Task 328 CleanLaTeX pack design from semantic `section/exercise` packs into a structure-level cleaning unit contract.

The design now defines:

- `luceon-cleanlatex-cleaning-unit-pack/v1`
- `pack_level`
- `pack_selection_policy`
- split policy
- merge policy
- semantic kind as metadata/prompt guidance only
- source preservation rules
- asset hash preservation rules
- pilot selection by structural stability and bounded source span

## Main Decision

Pack boundary selection must be driven by:

```text
canonical tree level
source span continuity
block/page/char size
child count
asset/formula/table density
split/merge policy
```

Semantic labels such as section, lesson, topic, exercise, grammar focus, 课, or 节 are not primary boundary drivers.

## Pilot Choice

The pilots remain:

```text
1.1 Different types of numbers
4.1 Colectingand classifyingdata
```

They are selected because they are stable mid-level nodes with bounded source spans, not because they are named sections.

## Boundary

No business code was changed.

No LLM call, CleanLaTeX generation, MinerU/MinerU-Popo inference, GPU/MPS job, DB mutation, MinIO mutation, or product metadata update was performed.

## Checks

```bash
git diff --check
# Exit code 0
```

## Next Recommended Task

```text
P0 Source-Bound Cleaning Unit Pack Generator For CleanLaTeX Pilot
```

The implementation should generate packs for `1.1` and `4.1` using v327 artifacts, but should not call LLM until a separate pilot-cleaning task is authorized.
