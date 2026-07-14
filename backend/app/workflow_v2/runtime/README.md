# Worker V2 deterministic runtime

This directory contains the project-owned execution snapshot for the first
three Worker V2 stages. Production code must not depend on a user's
`~/.codex/skills` directory for these stages.

The initial snapshots were imported on 2026-07-11 from:

- `pdf-clean-markdown-rebuild/scripts`: canonical clean-material builder and
  its outline helpers.
- `material-semantic-annotator/scripts/annotate_material.py`: semantic
  annotation.
- `cleanlatex-to-elegantbook/scripts`: CleanLaTeX bridge and deterministic
  ElegantBook builder.

Changes to these files are application changes. They require contract-version
updates, regression fixtures, and a new golden-set run before historical
materials can be refreshed.
