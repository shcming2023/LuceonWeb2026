# P0 CleanLaTeX Section Pack Contract And Pilot Design Report

Task ID: TASK-20260604-143649-P0-CleanLaTeX-Section-Pack-Contract-And-Pilot-Design

Branch: `codex/task-328-cleanlatex-section-pack-contract`

## Summary

Completed the design contract for moving from v327 canonical structure toward CleanLaTeX without letting LLM decide whole-book structure.

The design defines:

- `luceon-cleanlatex-section-pack/v1`
- `luceon-cleanlatex-exercise-pack/v1`
- derived `prompt.md` contract
- `luceon-cleanlatex-output/v1`
- source block/page/bbox preservation rules
- image/audio/resource hash preservation rules
- validation manifest expectations
- pilot sections `1.1` and `4.1`

## Main Decision

CleanLaTeX should operate on source-bound packs:

```text
section as primary cleaning unit
exercise as secondary cleaning unit
chapter as assembly container
unit as grouping container
```

The pack JSON is the source of truth. `prompt.md` is only a derived LLM input view.

## Pilot Choice

Pilot A:

```text
1.1 Different types of numbers
```

Pilot B:

```text
4.1 Colectingand classifyingdata
```

Rationale:

- `1.1` validates ordinary explanatory text/math cleanup.
- `4.1` validates the newly repaired Chapter 4 container and likely table/chart/data material.

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
P0 Source-Bound Section Pack Generator For CleanLaTeX Pilot
```

The implementation should generate packs for `1.1` and `4.1` only, using v327 `canonical_toc`, `chapter_spans`, `official_popo_tree`, and MinerU parsed artifacts. It should not call LLM until a separate pilot-cleaning task is authorized.
