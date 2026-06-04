# P0 Contents First Canonical TOC Spine And Span Binding

Issued at: 2026-06-04T13:11:10+0800

Owner: Luceon

## Goal

Fix layer-3 canonical TOC generation so the book's Contents page is the primary global TOC spine when available.

The official Popo/review tree must still be preserved and used for body/source binding, but its parent/child hierarchy must not be trusted as the whole-book directory authority when a contents page exists.

## Scope

Allowed:

- Parse Contents from MinerU markdown extracted from `mineru-result.zip`.
- Build canonical TOC from Contents first.
- Reconcile/bind official Popo/review tree nodes to contents entries by stable numbering/title signals.
- Keep body exercises as source-bound child containers where available.
- Preserve fallback behavior when no Contents markdown exists.

Forbidden:

- Do not rerun MinerU-Popo inference.
- Do not call LLM.
- Do not invent textbook content.
- Do not modify MinerU-Popo upstream/core/model code.
- Do not rename source asset hashes.
- Do not clean DB/MinIO/Docker volumes.

## Acceptance Criteria

- A800 Math 2022 evidence should compile with Unit 1-6, not Unit Project as fake units.
- Contents sections should cover `1.5`, `12.1`, and `15.4`.
- Contents expected section count should match canonical section count.
- Section-to-unit placement should not inherit Task 324 review tree hierarchy drift.
- Existing Task 325 artifact contract remains compatible.
