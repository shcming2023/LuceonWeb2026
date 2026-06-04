# P0 Popo TOC Review View Filter And Evidence Packaging Fix Task

Task ID: `TASK-20260604-111148-P0-Popo-TOC-Review-View-Filter-And-Evidence-Packaging-Fix`

## Objective

Make Luceon produce two clearly separated Popo-derived views:

- `official_popo_tree` / `raw_tree`: complete official MinerU-Popo tree, preserved for evidence and audit.
- `toc_view` / `review_tree`: a derived human review surface that only keeps outline-like structure for operator inspection.

This task must not modify MinerU-Popo upstream code, model weights, or official pipeline invocation.

## Scope

Allowed:

- `luceon_service/service.py`
- `luceon_service/tests/test_popo_invocation_boundary.py`
- Task/report ledger documents under `TaskAndReport/`

Forbidden:

- MinerU-Popo upstream source edits.
- Raw Material source mutation, image hash rename, or PDF sample mutation.
- Frontend direct GPU calls.
- Secret or credential commits.
- Broad UI redesign or unrelated CleanService protocol refactor.

## Current Evidence

A800 UAT for `a800-math-2022-fresh-uat-v1` proved the official MinerU-Popo pipeline completed a 891-page Math textbook and produced a valid full document tree. Human review found the raw tree unsuitable as the operator TOC surface because it includes front matter, teaching feature blocks, supplement/blank nodes, and full document tree detail.

## Acceptance Criteria

Positive:

- Official Popo tree remains available as a raw evidence artifact.
- Review-facing tree filters supplement types, front matter wrappers, blank nodes, and common teaching feature blocks.
- Review-facing tree preserves outline structures such as Unit, numbered sections, Exercise, Practice questions, Past paper questions, Glossary, and Index.
- Review-facing tree does not flood body text into review artifacts.
- Existing CleanService seven-artifact compatibility remains intact.

Negative:

- Do not change MinerU-Popo official pipeline.
- Do not remove existing required artifact roles.
- Do not store full artifact content in task/material metadata.
- Do not claim product/UAT acceptance beyond code-level validation.

