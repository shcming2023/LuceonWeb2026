# P0 CleanLaTeX Section Pack Contract And Pilot Design

Task ID: TASK-20260604-143649-P0-CleanLaTeX-Section-Pack-Contract-And-Pilot-Design

## Mainline Goal

Define the contract between Luceon Layer 3 canonical structure and the next CleanLaTeX stage.

The current pipeline has proven:

```text
MinerU -> official MinerU-Popo tree -> contents-first canonical_toc -> chapter_spans -> rawlatex_scaffold
```

The next step must not jump directly to whole-book LLM cleaning. It must first define a source-bound, section-level pack format that controls what the LLM sees, what it may change, and how output remains traceable to original source blocks/assets.

## Scope

This is a design-only task.

Required outputs:

- Section pack schema
- Exercise pack schema
- LLM prompt contract
- CleanLaTeX output contract
- Source preservation rules
- Asset hash preservation rules
- First pilot selection: `1.1` and `4.1`
- Acceptance standards for reviewable CleanLaTeX without boundary drift, image loss, formula loss, or source loss

## Write Boundary

Allowed files:

- `TaskAndReport/*CleanLaTeX-Section-Pack-Contract-And-Pilot-Design_TASK.md`
- `TaskAndReport/*CleanLaTeX-Section-Pack-Contract-And-Pilot-Design_DESIGN.md`
- `TaskAndReport/*CleanLaTeX-Section-Pack-Contract-And-Pilot-Design_REPORT.md`
- `TaskAndReport/TASK_TRACKING_LIST.md`

Forbidden actions:

- Do not modify business code.
- Do not call LLM.
- Do not generate CleanLaTeX yet.
- Do not rerun MinerU, MinerU-Popo, GPU, or MPS jobs.
- Do not mutate DB, MinIO, or production task/material metadata.
- Do not alter official MinerU-Popo outputs.
- Do not rename image/audio/asset hash names.
- Do not touch local private role files such as `AGENTS.md` or `.agents/**`.

## Positive Acceptance

- Design clearly defines machine-readable `section_pack.json` and `exercise_pack.json` contracts.
- Design clearly separates `pack.json` truth from derived `prompt.md`.
- Design defines the LLM prompt constraints and CleanLaTeX output envelope.
- Design preserves source block IDs, page/bbox/source ordering, image hash names, formulas, and tables.
- Design states how pilot sections `1.1` and `4.1` will be validated.
- Design explicitly prevents LLM from changing whole-book structure.

## Negative Acceptance

- No implementation code is introduced.
- No CleanLaTeX output is claimed.
- No production readiness, L3, go-live, or full-book automation claim is made.
- No source truth is invented.
