# Luceon2026 PRD v0.4 Independent CleanService Services Addendum

- **Document status**: Candidate Product Requirement Addendum (Proposed / Pending Review)
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

---

## 7. MinIO Input & Output Contracts (Data Handoff Protocols)

To ensure strict data boundaries and quality control, this section defines the product-level data contracts (inputs and outputs) for both the `toc-rebuild` and `RawMaterial2CleanMaterial` pipeline stages.

### 7.1 TOC Rebuild (Mineru2Table) Contract

* **Service Identifier**: `toc-rebuild`
* **Logical Role**: Structural parsing and layout analysis.
* **Input Contract**:
  * Source document raw parsing results stored under `eduassets-raw/mineru/{materialId}/v{N}/`.
  * The primary consumed file **must** be the canonical MinerU output `content_list_v2.json` containing block indices and parsed segments.
* **Output Contract**:
  * All generated structural assets must be written to `eduassets-clean/toc-rebuild/{materialId}/v{N}/`.
  * The service **must** successfully write exactly the following **7 required files** to consider a job successful:
    1. `flooded_content.json` (role: `flooded_content`): Contains fully mapped logic structures matching text segments.
    2. `logic_tree.json` (role: `logic_tree`): The reconstructed hierarchical document tree representation.
    3. `readable_tree.md` (role: `readable_tree`): A human-readable Markdown outline of the table-of-contents structure.
    4. `skeleton.json` (role: `skeleton`): A fallback schema structure mapping raw page/block metrics.
    5. `unresolved_anchors.json` (role: `unresolved_anchors`): Records of any section links or header references that could not be resolved during reconstruction.
    6. `provenance.json` (role: `provenance`): The tamper-proof metadata and cryptographic signature file.
    7. `metrics.json` (role: `metrics`): Contains LLM token usage, estimated costs, and structural validation scores.

### 7.2 Raw Material to Clean Material (RawMaterial2CleanMaterial) Contract

* **Service Identifier**: `md-clean` (or proposed stage name)
* **Logical Role**: Comprehensive block cleaning, LaTeX/TikZ code normalization, text standardization, and final Clean Material delivery.
* **Status**: **Future / Proposed Stage**. The contracts specified here are candidate specifications and are not yet active in the runtime.
* **Input Contract**:
  * The service requires **both** the mainline raw parse and the completed TOC rebuild structural prep.
  * Inputs are retrieved from:
    * `eduassets-raw/mineru/{materialId}/v{N}/content_list_v2.json` (Raw Material)
    * `eduassets-clean/toc-rebuild/{materialId}/v{N}/logic_tree.json` (TOC structure)
    * `eduassets-clean/toc-rebuild/{materialId}/v{N}/flooded_content.json` (Structure-to-block mapping)
* **Proposed Output Prefix**: `eduassets-clean/raw2clean/{materialId}/v{N}/`
* **Proposed Output Contract (Minimum Proposed Files)**:
  * The clean service proposes to write the following core assets upon successful execution:
    1. `clean_blocks.json` (role: `clean_blocks`): Standardized, normalized block-level elements.
    2. `clean_markdown.md` (role: `clean_markdown`): A high-fidelity, clean Markdown document with correct rendering-compliant math blocks.
    3. `clean_manifest.json` (role: `clean_manifest`): A catalog of all cleaned assets and valid external image/media hash bindings.
    4. `quality_report.json` (role: `quality_report`): Detailed metrics on text cleanliness, code validation, and schema compliance scores.
    5. `unresolved_items.json` (role: `unresolved_items`): Log of untranslated formulas or unrecognized block layouts requiring human intervention.
    6. `provenance.json` (role: `provenance`): Standard cryptographic pipeline lineage linking back to the raw source, Mineru2Table structural outputs, and the clean service version.
    7. `metrics.json` (role: `metrics`): Detailed LLM cost and execution metrics.
