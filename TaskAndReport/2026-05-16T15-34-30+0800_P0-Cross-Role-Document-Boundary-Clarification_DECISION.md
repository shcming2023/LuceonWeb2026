# P0 Cross Role Document Boundary Clarification Decision

- Timestamp: 2026-05-16T15:34:30+0800
- Decision owner: User
- Recorded by: Luceon

## Decision

Because Luceon and Lucode exchange task briefs, reports, role guides, workflow notes, and evidence through GitHub, each side may read the other side's role settings and process documents.

This must not confuse role identity or authority.

## Rule

- Luceon may read Lucode rules to understand implementation/report expectations, but Luceon remains Luceon.
- Lucode may read Luceon rules to understand review, validation, and acceptance expectations, but Lucode remains Lucode.
- Reading another role document is coordination context only, not permission transfer.
- Active authority comes from the task ledger row, task brief, explicit user decision, and verified evidence.
- If role documents appear to conflict, stop and escalate instead of guessing.

## Boundary

This is a workflow/documentation clarification only. It does not authorize production mutation, deployment, validation upload, pressure test, submit-probe, DB/MinIO/Docker volume operation, model change, secret/config change, merge-to-main by Lucode, or readiness/go-live claim.
