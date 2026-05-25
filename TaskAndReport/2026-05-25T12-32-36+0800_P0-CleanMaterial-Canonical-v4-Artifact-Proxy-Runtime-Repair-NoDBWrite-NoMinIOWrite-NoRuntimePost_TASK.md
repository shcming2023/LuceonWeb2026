# TASK-20260525-123236-P0-CleanMaterial-Canonical-v4-Artifact-Proxy-Runtime-Repair-NoDBWrite-NoMinIOWrite-NoRuntimePost

Issued at: 2026-05-25T12:32:36+0800

Actor: Luceon

## Mainline Objective

Resolve the Task 277/278 blocker where DB metadata records canonical
`toc-rebuild v4` clean artifacts, but the current product proxy cannot read
those `eduassets-clean` ObjectRefs.

## Scope

Luceon may perform the narrowest runtime repair needed to make already-existing
canonical v4 clean artifacts readable through the existing product proxy.

Allowed operations:

- inspect current running `cms-upload-server` code and logs;
- inspect exact MinIO object existence for the canonical clean prefix;
- rebuild and recreate only the `upload-server` service if the running image is
  stale relative to current `main`;
- run read-only proxy GET verification for the seven canonical v4 clean
  artifact ObjectRefs.

## Forbidden Operations

- DB POST/PATCH/PUT/DELETE/apply;
- MinIO put/copy/move/delete/write/delete-marker/cleanup;
- runtime POST, submit-probe, Mineru2Table query/probe, or raw2clean service
  execution;
- broad Docker/Compose restart, dependency restart, volume/network/prune;
- job-store edit/delete/cleanup/reset;
- upload, retry, reparse, Re-AI, repair, rollback, batch, pressure test;
- model, env, secret, sample, source asset, or local override mutation;
- production readiness, UAT, L3, pressure PASS, release readiness, production
  online, or go-live claim.

## Stop Rule

Stop if the repair requires changing DB metadata, writing MinIO objects,
rerunning CleanService, or modifying business source code beyond deploying the
already-accepted current `main` upload-server code.

## Required Report

Write a Luceon report with:

- root cause;
- exact runtime action;
- before/after evidence;
- seven artifact GET verification with size/SHA match;
- remaining blocker, if any;
- explicit safety boundary.

