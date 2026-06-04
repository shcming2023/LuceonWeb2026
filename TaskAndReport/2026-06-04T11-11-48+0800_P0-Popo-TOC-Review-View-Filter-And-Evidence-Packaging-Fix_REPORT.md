# P0 Popo TOC Review View Filter And Evidence Packaging Fix Report

Task ID: `TASK-20260604-111148-P0-Popo-TOC-Review-View-Filter-And-Evidence-Packaging-Fix`

Branch: `codex/task-324-popo-toc-review-view`

## Summary

Implemented an adapter-only TOC review view over official MinerU-Popo output.

The official tree is now preserved as raw evidence, while the existing user-facing `logic_tree`, `readable_tree`, `rebuilt_markdown`, and `flooded_content` are generated from a filtered review tree.

## Changes

- Added TOC review filtering rules in `luceon_service/service.py`.
- The filter now:
  - removes supplement node types such as page/header/footer/aside nodes;
  - promotes children out of front matter wrappers instead of dropping useful descendants;
  - hides common teaching feature blocks such as TIP, LINK, WORKED EXAMPLE, APPLY YOUR SKILLS, REFLECTION, SELF ASSESSMENT, SUMMARY, and related feature sections;
  - preserves outline nodes such as Unit, numbered sections, Exercise, Practice questions, Past paper questions, Glossary, and Index;
  - clears node body content in the review tree so the review surface stays outline-oriented.
- Added explicit artifact refs:
  - `toc_view.json`
  - `review_tree.json`
  - `official_popo_tree.json`
  - `raw_tree.json`
- Existing seven-artifact roles remain compatible:
  - `logic_tree.json` continues to point at the review tree.
  - `readable_tree.md`, `rebuilt_markdown.md`, and `flooded_content.json` are derived from the review tree.

## Verification

Commands run:

```bash
PYTHONPATH=. python3 luceon_service/tests/test_popo_invocation_boundary.py
python3 -m py_compile luceon_service/app.py luceon_service/service.py luceon_service/tests/test_popo_invocation_boundary.py
node server/tests/cleanservice-output-verifier-smoke.mjs
node server/tests/cleanservice-metadata-apply-executor-smoke.mjs
git diff --check
```

Results:

- `PASS popo invocation boundary tests`
- Python compile passed.
- CleanService output verifier smoke passed 9/9.
- CleanService metadata apply executor smoke passed all 13 cases.
- `git diff --check` passed.

## Boundary

No MinerU-Popo upstream code or model behavior was changed. This is a Luceon adapter view and packaging fix only.

