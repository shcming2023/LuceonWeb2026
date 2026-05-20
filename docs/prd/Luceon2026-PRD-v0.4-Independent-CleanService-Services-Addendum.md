# Luceon2026 PRD v0.4 Independent CleanService Services Addendum

- **Document status**: Approved Product Requirement Addendum
- **Task ID**: `TASK-20260520-143129-P0-Independent-CleanService-Service-Model-PRD-And-Architecture-Alignment`
- **Date**: 2026-05-20
- **Scope**: Product-scoped requirements for independent, Docker-deployed CleanService integrations (including Mineru2Table and future RawMaterial2CleanMaterial services).

---

## 1. Purpose & Core Philosophy

This addendum formally defines the product requirements and operational boundaries for introducing **independent CleanService integrations** into the Luceon2026 platform.

The core philosophy of the next-stage pipeline is defined as:
* **Luceon Control Plane**: Luceon main project remains the sole orchestrator, task control plane, review desk, and audit system. It retains total authority over asset identities (`materialId`), processing tasks (`parseTaskId`), asset versions (`assetVersion`), job idempotency keys (`job_id`), cost metrics, and final acceptance.
* **Service Independence**: Heavy data processing/cleaning tasks—such as table-of-contents structural reconstruction (`Mineru2Table`) and final content cleaning (`RawMaterial2CleanMaterial`)—are decoupled into **separately developed, independently Docker-deployed microservices**.
* **API Collaboration**: Luceon communicates with these services asynchronously via a stable, secure, and idempotent API contract (CleanService Protocol v1) utilizing MinIO ObjectRefs as the exclusive handoff vehicle.

---

## 2. Mainline Maintained & Side-by-Side Compatibility

### 2.1 Preserving Phase 1 Mainline
Luceon's mainline Phase 1 pipeline remains fully active and authoritative:
```text
PDF source -> Raw Intake -> local MinerU parse -> parsed artifacts (MinIO) -> Ollama qwen3.5:9b -> AI metadata -> operator review
```
The raw parsed outputs and initial AI metadata produced by this mainline constitute the **Raw Material**.

### 2.2 Side-by-Side Coexistence
1. **Prerequisite Principle**: Raw Material is a **durable, non-overwritable, and inspectable asset layer**. It is a prerequisite for any CleanService; under no circumstances may a CleanService overwrite or corrupt Raw Material.
2. **Optional CleanStage**: Future CleanService processing runs as an optional, side-by-side post-processing pipeline. It must **never** block, delay, or silently alter the mainline Phase 1 path unless an explicit future product decision/governance policy is configured and approved.
3. **No-Silent-Degradation**: If a CleanService fails, is skipped, or is disabled, the platform must degrade gracefully. The system must never silently serve partial, skeleton, or placeholder outputs as if they were fully successful cleaned assets.

---

## 3. The Clean stage Lifecycle & Operator Experience

Operators must have absolute clarity regarding the state of each asset as it moves through the pipeline. The system must support tracking distinct, side-by-side stages.

### 3.1 Asset Pipeline Stages & Operator States

An educational asset's lifecycle involves two sequential clean stage validations:
1. **TOC Rebuild / Structural Prep (Mineru2Table)**
2. **Final Cleaning & Normalization (RawMaterial2CleanMaterial)**

#### Operator-Facing State Matrix

| State Label | Meaning to Operator | UI Action / Visual indicator |
| --- | --- | --- |
| **Raw Material Available** | Phase 1 mainline complete. Raw parse and initial AI metadata are ready. Optional clean stages are not yet admitted. | Highlight raw status. Expose "Initiate TOC Rebuild" button. |
| **TOC Rebuild Pending** | Job registered in Luceon's registry and queued. Waiting for local machine admission. | Gray/spinner state labeled "Queued (TOC Rebuild)". |
| **TOC Rebuild Running** | Active processing on Mineru2Table container. | Animated progress bar. Expose active cancellation option. |
| **TOC Rebuild Review-Needed** | Mineru2Table successfully completed, but unresolved structural anchors or cost soft-limits require operator triage. | Warning badge. Highlight "Unresolved Anchors count". Expose diff editor. |
| **TOC Rebuild Completed** | All required structural artifacts successfully reconstructed and verified. Provenance written. | Green badge. Expose "Structured Layout" view. |
| **TOC Rebuild Failed** | Service failed (quota exceeded, timeout, upstream error) or returned corrupted output. | Red badge. Provide diagnostic code and "Retry Clean Stage" button. |
| **TOC Rebuild Skipped** | Skipped by policy (e.g. legacy asset, parsed-only layout, file ineligible for structure extraction). | Low-contrast badge. Provide skip reason. |

A parallel, subsequent set of states must be exposed for the **RawMaterial2CleanMaterial** final clean stage (e.g. `Final Clean Pending`, `Final Clean Completed`, `Final Clean Failed`), ensuring the operator can clearly distinguish structural preparation from final content cleaning.

---

## 4. Required Operator Interface Capabilities

To support this model, the Luceon operator interface (Workbench and Task Detail) must provide the following:
1. **Interactive Layout Cockpit**: An visual interface to inspect rebuilt chapter/section tables alongside original layout elements.
2. **Unresolved Anchor Registry**: Highlight and count all unresolved section anchors, broken links, or low-confidence table extractions. Operators must not be forced to scan terminal logs to discover structural discrepancies.
3. **Cost Triage Panel**: Display projected and actual LLM costs. When costs cross the Luceon soft limit (`¥5`), pause the task and render an explicit "Approve Cost Overrun" or "Halt Processing" decision desk.
4. **Provenance Audit Trail**: A read-only audit block in the UI showing the exact implementation version, git commit, input file hashes, and output signatures proving the integrity of the Clean Material (Strict Provenance).

---

## 5. Mandatory Data Governance & Technical Boundaries

To preserve educational alignment quality, all integrated CleanServices must adhere to these product-level governance boundaries:

### 5.1 ID-Only Extraction (No Free-Text Hallucination)
Any service generating a structured TOC, chapter index, or section mapping must do so by referencing existing Block IDs or source references. **No service is permitted to synthesize, summarize, or rewrite educational content** into the structural trees unless a future task explicitly authorizes creative AI augmentation.

### 5.2 Asset Hash Locking
All resource attachments (images, audio, inline formulas, SVGs) must preserve their original cryptographic hashes through all clean stages. Services must not rename, regenerate, or strip resource identities.

### 5.3 Pure Code Generation Boundary
If a clean service produces or standardizes code-like educational assets (e.g. LaTeX source, TikZ diagrams, Markdown blocks), it must restrict output to canonical, standard packages and markdown formats. The use of custom macros, fragile custom commands, or unverified packages is strictly forbidden to ensure downstream rendering compatibility.

### 5.4 No-Silent-Fallback
* **Skeleton Policy**: A structural "skeleton" json is an acceptable diagnostic/fallback file, but it must never be represented as successful clean output.
* **Failure Visibility**: Storage failures, hard cost limit rejections (`quota_exceeded`), and engine crashes must immediately raise a terminal failure state. Under no circumstances may a raw parse be repackaged and served under a successful "Clean" label.

---

## 6. Legacy Asset Policy

* All existing objects in `eduassets` / `eduassets-parsed` are classified as **Legacy Assets**.
* Legacy assets are exempted from CleanService pipeline requirements and must remain discoverable in their historical form.
* **No Pseudo-Provenance**: Do not invent fake provenance records or backfill version numbers for legacy assets.
* Wording in the UI must explicitly indicate `Legacy Asset (No Clean Stage Available)` for all such items.
