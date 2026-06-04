# P0 Canonical TOC And RawLaTeX Scaffold From Official Popo Tree

Issued at: 2026-06-04T12:47:22+0800

Owner: Luceon

## Mainline Goal

Implement Luceon layer-3 deterministic structure compiler:

```text
official MinerU-Popo tree/raw tree
  -> canonical_toc.json
  -> chapter_spans.json
  -> rawlatex_scaffold.json
```

This task must turn already completed MinerU-Popo official structure output into complete, traceable chapter containers for later per-chapter LLM cleaning. It must not rerun MinerU-Popo inference for the same structure target.

## Architecture Boundary

Accepted layer split:

1. MinerU parses PDF into page/block/raw assets.
2. MinerU-Popo performs base structure normalization and produces official tree/raw tree.
3. Luceon deterministic rules compile complete source-traceable chapter containers.
4. LLM cleans inside each chapter container only and must not decide whole-book structure.

This task is layer 3 only.

## Allowed Writes

- Luceon adapter/server code for deterministic canonical TOC, chapter spans, and RawLaTeX scaffold.
- Focused tests and fixtures.
- CleanService-compatible extra artifact refs.
- Task report and ledger row.

## Forbidden Scope

- Do not modify MinerU-Popo upstream/core/model code.
- Do not rerun MinerU-Popo inference to validate this task.
- Do not call an LLM to decide book-level structure.
- Do not generate invented titles, text, formulas, tables, or figure captions.
- Do not rename image/audio/resource hash names.
- Do not clean or delete MinIO/DB/Docker volumes or historical artifacts.

## Required Outputs

- `canonical_toc.json`: stable node ids, normalized kind, title/original title, source trace, parent/children, confidence, warnings.
- `chapter_spans.json`: source order/page ranges, block ids, asset/formula/table/image ref placeholders, warnings.
- `rawlatex_scaffold.json`: manifest and per-container `.tex` placeholders bound to source spans; not final CleanLaTeX.

## Acceptance Criteria

- Existing official Popo tree evidence compiles without Popo inference.
- Every kept node has traceability or explicit warning.
- RawLaTeX scaffold contains no invented textbook content.
- Existing seven CleanService artifacts remain compatible.
- Focused tests and build gates pass.

