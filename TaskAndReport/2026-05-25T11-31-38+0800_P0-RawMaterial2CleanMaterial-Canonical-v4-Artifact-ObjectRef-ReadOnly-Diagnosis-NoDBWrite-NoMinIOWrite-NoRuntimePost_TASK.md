# TASK-20260525-113138-P0-RawMaterial2CleanMaterial-Canonical-v4-Artifact-ObjectRef-ReadOnly-Diagnosis-NoDBWrite-NoMinIOWrite-NoRuntimePost

Issued at: 2026-05-25T11:31:38+0800

Actor: Luceon

## Mainline Objective

Diagnose the current mainline blocker found by Task 277:

```text
accepted toc-rebuild v4 metadata points to required artifact ObjectRefs,
but exact read-only proxy GET for readable_tree.md returns key-not-found.
```

The mainline question for this task is:

```text
Is the RawMaterial2CleanMaterial artifact-backed draft blocked by missing
objects, bucket/config mismatch, stale metadata/ObjectRefs, proxy resolver
behavior, or a prior v4 job artifact persistence gap?
```

This is a read-only diagnosis task only. It does not repair metadata or storage.

## Critical Path Scope

Luceon may perform only exact read-only probes:

1. Read current GitHub `main` and TaskAndReport state.
2. Read canonical material and task records:

   ```text
   GET /__proxy/db/materials/1842780526581841
   GET /__proxy/db/tasks/task-1779085089451
   ```

3. Extract current `toc-rebuild v4` service metadata from material/task.
4. Attempt exact proxy GETs for recorded `eduassets-clean` ObjectRefs from the
   accepted metadata, especially the required roles:

   ```text
   readable_tree
   logic_tree
   skeleton
   flooded_content
   ```

5. Compare material summary, task summary, and operatorDecision artifact
   snapshot ObjectRefs for drift.
6. Use exact read-only control probes only when needed to separate proxy
   resolver behavior from object availability. These probes may include:

   - `objectName` vs incorrect `object` query parameter behavior;
   - exact v4 ObjectRefs from task metadata;
   - exact v4 ObjectRefs from material/operatorDecision snapshot if present.

## Forbidden Operations

- DB POST/PATCH/PUT/DELETE or apply.
- MinIO put/copy/move/delete/write/delete-marker/cleanup.
- MinIO list or broad bucket scan.
- Runtime POST, submit-probe, Mineru2Table query/probe, or raw2clean service
  execution.
- Docker/Compose restart/recreate/build/down/up/volume/prune/network mutation.
- Job-store edit/delete/cleanup/reset.
- Upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test.
- Model, env, secret, sample, source asset, or local override mutation.
- Production deployment or production validation.
- UAT, L3, pressure PASS, release readiness, production readiness, production
  online, or go-live claim.

## Stop Rule

Stop and report blocked instead of widening scope if diagnosis would require:

- storage mutation;
- DB metadata correction;
- bucket listing;
- service rerun/POST;
- Docker/runtime changes;
- manual MinIO object creation;
- broad forensic cleanup outside the canonical sample.

## Required Report

Write a `*_REPORT.md` recording:

- exact read-only probes and statuses;
- current material/task `toc-rebuild v4` metadata shape;
- whether required ObjectRefs agree across task/material/operatorDecision;
- which exact ObjectRefs are retrievable or missing;
- most likely blocker classification;
- recommended next mainline task;
- explicit no-write/no-runtime/no-readiness boundary.

