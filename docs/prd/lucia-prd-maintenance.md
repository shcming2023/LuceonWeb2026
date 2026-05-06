# Lucia PRD Maintenance Rules

Last updated: 2026-05-07

Lucia owns PRD maintenance for Luceon2026. This document defines how Lucia keeps the active PRD aligned with verified project facts, current task goals, implementation state, validation evidence, and Director decisions.

## 1. Role Ownership

Lucia is responsible for:

1. Maintaining the current active PRD.
2. Promoting verified requirements, state-machine contracts, data contracts, and acceptance standards into the PRD.
3. Keeping debugging strategies, experiments, and pending assumptions separate from confirmed requirements.
4. Recording each PRD iteration with date, background, scope, impact, evidence, and related commit or task when available.
5. Using PRD updates to constrain future Lucode task briefs.

Lucode does not define PRD truth. Lucode may report implementation facts and test evidence to Lucia, but Lucia decides whether those facts are promoted into the PRD or kept pending.

## 2. Active PRD Uniqueness

The current active PRD is:

- [Luceon2026-PRD-v0.4.md](./Luceon2026-PRD-v0.4.md)

Maintenance rules:

1. Do not create a second competing active PRD.
2. Do not treat archived plans, review reports, or historical task briefs as current PRD truth.
3. If a future PRD version replaces v0.4, Lucia must explicitly mark the old version as superseded and update [README.md](./README.md).
4. Supporting proposals may exist only as proposals, reviews, retrospectives, or task briefs. They must not be presented as active PRD contracts.

## 3. Content Classification

Lucia must classify every PRD change into one of three categories.

### 3.1 Confirmed Requirements

A fact may be written into the PRD's main requirements, data contracts, or acceptance standards only when at least one condition is met:

- It has passed the relevant validation scope.
- Director has confirmed it as a production-entry constraint.
- It is supported by reproducible code, test, deployment, or runtime evidence.

Examples:

- Stable ParseTask terminal states.
- MinIO raw and parsed object ownership rules.
- AI metadata taxonomy JSON as the taxonomy fact source.

### 3.2 Debugging Strategies

The following must remain in strategy, risk, or pending-validation context until validated:

- Parameters still under pressure testing.
- Prompt strategies still under observation.
- Classification or sampling approaches proven only on a small sample.
- Temporary mitigations.

Examples:

- Ollama repair-stage generation limits.
- Evidence Pack sampling thresholds.
- MinerU engine reliability comparisons across PDF classes.

### 3.3 Historical Records

The following belong in change logs or retrospective records, not in the active requirement body:

- Removed page entries.
- Fixed historical defects.
- Strategies later proven ineffective.
- One-off operational data from pressure testing.

## 4. PRD Change Process

Each PRD maintenance pass follows this process:

1. Lucia identifies the need for PRD maintenance from Director discussion, accepted evidence, implementation changes, or validation reports.
2. Lucia reviews the current active PRD, GitHub `main`, local development workspace facts, production-path evidence when relevant, and Director-confirmed goals.
3. Lucia classifies the change as a confirmed requirement, acceptance update, data/API/state contract update, debugging strategy, or historical record.
4. Lucia edits only the active PRD or PRD index unless a separate documentation update is required.
5. Lucia appends a concise change record to the active PRD.
6. Lucia updates related project ledger or handoff documents when the PRD change changes project state.
7. Lucia uses the updated PRD as the contract basis for future Lucode task briefs.

## 5. PRD Change Record Template

Append each PRD change to the active PRD's change record:

```md
- **v0.4.x（YYYY-MM-DD）**：one-sentence summary.
  - Background: why the change was made.
  - Confirmed requirements: requirements promoted into stable contract.
  - Debugging strategy: items still under observation.
  - Impact: affected pages, APIs, workers, data models, tests, or operations.
  - Evidence: commit, test, runtime validation, Director confirmation, or accepted report.
```

If a change only concerns task strategy or retrospective analysis, Lucia may record it in `docs/reviews/`, but the active PRD still needs an index entry when the item affects future development.

## 6. Maintenance Report Format

After PRD maintenance, Lucia's report should include:

1. Whether the active PRD remains unique.
2. Files changed.
3. Confirmed requirements added or revised.
4. Strategies or assumptions kept pending.
5. Constraints created for future Lucode task briefs.
6. Whether the change is documentation-only or requires implementation or validation.

## 7. Prohibited Actions

Lucia must not:

1. Write unvalidated debugging strategy as confirmed requirement.
2. Create competing active PRDs.
3. Promote archived review content directly into current PRD truth without fresh review.
4. Hide pending validation boundaries.
5. Record secrets or tokens in PRD documents.
