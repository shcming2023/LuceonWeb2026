# TASK-20260522-132951-P0-Mineru2Table-v2-Output-Quality-And-Integration-Threshold-Review

## 1. Mainline Objective

Task 245 proved that standalone Mineru2Table can complete one real `toc-rebuild` job and write the seven required output artifacts under:

```text
eduassets-clean/toc-rebuild/1842780526581841/v2/
```

Task 246 answers the next mainline question:

```text
Is the v2 output good enough, as a structural asset, to justify moving into Luceon-side orchestration and metadata integration?
```

This is a read-only review task. It must not rerun Mineru2Table or mutate data.

## 2. Director Authorization

The Director approved:

```text
Task 246: read-only review of v2 output quality and integration threshold.
```

## 3. Critical Path Scope

Do only this:

1. Read the canonical input object:

   ```text
   eduassets-raw/mineru/1842780526581841/v1/content_list_v2.json
   ```

2. Read the Task 245 v2 output objects:

   ```text
   eduassets-clean/toc-rebuild/1842780526581841/v2/
   ```

3. Compare the output at a structural level:
   - `logic_tree.json`
   - `readable_tree.md`
   - `flooded_content.json`
   - `skeleton.json`
   - `unresolved_anchors.json`
   - `metrics.json`
   - `provenance.json`

4. Decide whether the current output is:
   - acceptable for minimal Luceon orchestrator/metadata integration;
   - acceptable only with guardrails;
   - blocked for mainline integration.

5. Record concrete defects and deferrable side work.

## 4. Review Questions

Answer these questions with evidence:

- Does `logic_tree.json` contain a meaningful structure beyond an empty root?
- Does `readable_tree.md` present a human-readable outline useful to an operator?
- Does `flooded_content.json` preserve all source blocks while attaching structural metadata?
- Does `skeleton.json` preserve source block coverage?
- Does `unresolved_anchors.json` obey ID/source-reference-only discipline?
- Does `metrics.json` provide usable cost/token evidence?
- Does `provenance.json` provide enough traceability for Luceon to record output ObjectRefs?
- Are there defects that must be fixed before Luceon orchestrator wiring?
- Are there defects that can safely be deferred until after minimal integration?

## 5. Environment And Write Boundary

### Luceon Workspace

```text
/Users/concm/prod_workspace/Luceon2026
```

Allowed writes:

- this task brief;
- Task 246 report;
- `TaskAndReport/TASK_TRACKING_LIST.md`.

Forbidden:

- `server/**`;
- `src/**`;
- package manifests or lockfiles;
- Docker/Compose files;
- `.env*`;
- PRD/architecture/contract docs;
- private role files (`AGENTS.md`, `.agents/**`).

### Runtime/Data Boundary

Allowed:

- read-only MinIO object reads/listing for the canonical input, Task 242 `v1` evidence, and Task 245 `v2` outputs;
- read-only `jobs.json` inspection;
- read-only container health/log inspection if needed.

Forbidden:

- `POST /api/v1/jobs`;
- `chat/completions`;
- MinIO object write/delete/cleanup/move/rename;
- DB write;
- Docker build/recreate/restart/down;
- source-code edit;
- manual job-store edit;
- cleanup or reuse of the contaminated `v1` prefix;
- UAT/L3/readiness/pressure PASS/go-live claim.

## 6. Fast Validation Target

Produce a short, evidence-backed recommendation:

```text
Proceed to Luceon minimal orchestration design
```

or:

```text
Block integration until specific quality/safety defects are fixed
```

## 7. Stop Rules

Stop and report a blocker if:

- the v2 output objects are missing or unreadable;
- read-only access would require mutating runtime/data;
- evidence shows the v2 output is structurally empty or equivalent to Task 242's failed output;
- provenance/metrics are too broken for Luceon to safely record traceability.

## 8. Report Requirements

Create:

```text
TaskAndReport/2026-05-22T13-29-51+0800_P0-Mineru2Table-v2-Output-Quality-And-Integration-Threshold-Review_REPORT.md
```

The report must include:

- exact Luceon HEAD;
- read-only boundary confirmation;
- source and output object inventory;
- structure summary for `logic_tree.json` and `readable_tree.md`;
- source/output block coverage observations;
- provenance and metrics assessment;
- integration threshold decision;
- must-fix-before-orchestration items;
- deferrable side work;
- explicit statement that no runtime/data mutation or readiness claim was made.

## 9. Review Boundary

Acceptance means only:

```text
Luceon has a grounded quality/threshold decision for the Task 245 v2 output.
```

It does not mean:

- Luceon orchestration is implemented;
- database persistence is implemented;
- output quality is product-final;
- RawMaterial2CleanMaterial has run;
- UAT, L3, pressure PASS, release readiness, production readiness, production上线, or go-live.
