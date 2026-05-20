# Delivery Report: P0 Independent CleanService Service Model PRD And Architecture Alignment

- **Task ID**: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- **Delivery Date**: 2026-05-20
- **Author**: Lucode (Development Engineer & Product Manager)
- **Reviewer / Owner**: Luceon (Architect & Director)
- **Status**: Ready for luceon Review
- **Branch**: `lucode/task-223-independent-cleanservice-service-model`

---

## 1. Executive Summary

This documentation-only, control-plane task achieves total alignment across product requirements, architecture vision, API protocols, and decision records for the **Independent CleanService Service Model**.

It formally decouples heavy document extraction and text cleaning workloads into **separately developed, independently Docker-deployed microservices** (specifically `Mineru2Table` and `RawMaterial2CleanMaterial`), while maintaining Luceon as the absolute orchestrator, task manager, review cockpit, version allocator, and provenance authority.

---

## 2. Document & Codex Deliverables

We have created and modified the following 7 files within the allowed boundaries:

1. **[NEW] PRD Addendum**: [Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md](file:///workspace/dev/Luceon2026/docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md)
   * Formally preserves the Phase 1 mainline (`upload -> MinIO -> MinerU -> parsed artifacts -> Ollama qwen3.5:9b -> AI metadata -> operator review`) as a prerequisite raw material.
   * Defines optional, asynchronous, non-blocking side-by-side post-processing stages (`toc-rebuild` and `RawMaterial2CleanMaterial`) and outlines specific operator states.
   * Specifies operator dashboard capabilities: layout cockpit, unresolved anchor triage, cost overrun panels, and provenance audits.
   * Restricts clean output from using silent fallback or pseudo-provenance.
2. **[NEW] Architectural Decision Record (ADR)**: [2026-05-20_independent-cleanservice-service-model.md](file:///workspace/dev/Luceon2026/docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md)
   * Captures the physical boundary, collaborative API pattern, and a detailed responsibility matrix.
   * Codifies strong container-level isolation, granular scale-out, and provenance immutability benefits.
3. **[MODIFY] PRD Index**: [README.md](file:///workspace/dev/Luceon2026/docs/prd/README.md)
   * Registers the new PRD addendum as the formal supplementary product requirement document.
4. **[MODIFY] Pipeline Vision**: [Luceon2026-Asset-Pipeline-Vision.md](file:///workspace/dev/Luceon2026/docs/architecture/Luceon2026-Asset-Pipeline-Vision.md)
   * Explicitly establishes the two independent, decoupled clean stages (TOC Rebuild and final Cleaning) and defines the stable `CleanService Registry` fields.
   * Restructures target directories to replace legacy `token_stats.json` with the newly defined 7 exact files.
5. **[MODIFY] API Protocol**: [CleanService-Protocol-v1.md](file:///workspace/dev/Luceon2026/docs/contracts/CleanService-Protocol-v1.md)
   * Adds **Section 5.1 API Security & Credential Isolation** detailing storage credential segregation, access control allowlists (`ALLOWED_MINIO_ENDPOINTS/BUCKETS`), token-based authentication (`Authorization: Bearer <API_KEY>`), and loopback ingress constraints.
   * Updates job state schemas and terminal response shapes to demand exactly 7 target files, explicitly replacing `token_stats.json` with `metrics.json` and adding `unresolved_anchors.json`.
6. **[MODIFY] Adaptation Plan**: [CleanService-Mineru2Table-Adaptation-Plan.md](file:///workspace/dev/Luceon2026/docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md)
   * Outlines current standalone API endpoints (`/api/v1/extract`, `/api/v1/tasks`, `/api/v1/tasks/{task_id}`) and documents the functional gap to Protocol v1.
   * Establishes a **Transition Strategy Matrix** recommending direct protocol implementation (**Option A**) for production, and outlines rigid sunset criteria (sandbox-only, hard ceiling of 5 processed materials, sunset date of 2026-06-15, and no-write privilege) for Option C.
7. **[MODIFY] Project Ledger**: [TASK_TRACKING_LIST.md](file:///workspace/dev/Luceon2026/TaskAndReport/TASK_TRACKING_LIST.md)
   * Updates Task 223 status to `Ready for luceon Review` and transfers actor role to `luceon`.

---

## 3. Local Verification Logs

All files were subjected to local sanity and whitespace compliance checks in the development container.

### 3.1 Syntax & Whitespace Compliance Check
Command executed to verify formatting, trailing whitespaces, and git anomalies:
```bash
git diff --check origin/main..HEAD
```
* **Exit code**: `0`
* **Output**: (None - clean check pass)

### 3.2 File Boundaries & Modifiers Audit
Command executed to verify exact changes staged:
```bash
git diff --name-status --cached origin/main
```
* **Exit code**: `0`
* **Output**:
```text
M       TaskAndReport/TASK_TRACKING_LIST.md
M       docs/architecture/Luceon2026-Asset-Pipeline-Vision.md
A       docs/codex/decisions/2026-05-20_independent-cleanservice-service-model.md
M       docs/contracts/CleanService-Mineru2Table-Adaptation-Plan.md
M       docs/contracts/CleanService-Protocol-v1.md
A       docs/prd/Luceon2026-PRD-v0.4-Independent-CleanService-Services-Addendum.md
M       docs/prd/README.md
```

---

## 4. Key Architectural & Product Decisions

1. **Decoupled Repositories**: Mineru2Table (`shcming2023/Mineru2Table2026`) and the future RawMaterial2CleanMaterial service are physical and repository-level independent projects, avoiding monolith bloat.
2. **Luceon Sovereignty**: Luceon maintains absolute control over asset metadata, versioning (`assetVersion`), task states, and cost thresholds; the services behave as pure, stateless workers.
3. **Rigid Output Schema**: Standardized exactly 7 required output files under `toc-rebuild/{materialId}/{assetVersion}/`, replacing legacy `token_stats.json` with the more comprehensive `metrics.json` and adding `unresolved_anchors.json`.
4. **Credential Segregation**: CleanService containers must never consume storage credentials from HTTP requests; credentials are loaded exclusively from local container environment variables, and ingress is bounded by loopback/alias isolation.

---

## 5. Remaining Luceon/User Decisions

1. **Option A Implementation Schedule**: Authorize the development task on `/Users/concm/prod_workspace/Mineru2Tables` to implement the CleanService Protocol v1.
2. **Cost Triage Threshold Tuning**: Confirm if the `¥5` (soft warning) and `¥8` (hard stop) cost ceilings require environment-specific overrides in multi-user settings.
3. **Task 222 Verification**: Review and accept the pending evidence-only correction for Task 222 (Raw Material Canonical Adapter).

---

## 6. Strict Data & Runtime Safety Affirmation

* **Zero Code Mutation**: No files under `server/**` or `src/**` were modified.
* **Zero Service Mutation**: No Docker, Compose, network, or container configs were altered.
* **Zero Runtime Mutation**: No database records, MinIO objects, tasks, metadata records, or model checkpoints were modified.
* **Pure Documentation Scope**: The mainline Phase 1 pipeline remains 100% untouched and fully operational.
