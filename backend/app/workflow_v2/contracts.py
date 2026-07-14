from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class StageContract:
    key: str
    order: int
    skill_name: str
    version: str
    owner: str
    input_schema: str
    output_schema: str
    artifact_prefix: str
    retry_scope: str
    acceptance_gates: tuple[str, ...]
    llm_policy: str
    runtime_snapshot_sha256: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["acceptance_gates"] = list(self.acceptance_gates)
        return data


LEGACY_WORKFLOW_VERSION = "worker-v2.0.0-draft1"
CORE_CONVERGENCE_WORKFLOW_VERSION = "worker-v2.1.0-core-convergence1"
STRICT_COMPILE1_WORKFLOW_VERSION = "worker-v2.2.0-strict-compile1"
STRICT_COMPILE2_WORKFLOW_VERSION = "worker-v2.2.1-strict-compile2"
STRICT_COMPILE3_WORKFLOW_VERSION = "worker-v2.2.2-strict-compile3"
STRICT_COMPILE4_WORKFLOW_VERSION = "worker-v2.2.3-strict-compile4"
STRICT_COMPILE5_WORKFLOW_VERSION = "worker-v2.2.4-strict-compile5"
STRICT_COMPILE6_WORKFLOW_VERSION = "worker-v2.2.5-strict-compile6"
STRICT_COMPILE7_WORKFLOW_VERSION = "worker-v2.2.6-strict-compile7"
STRICT_COMPILE8_WORKFLOW_VERSION = "worker-v2.2.7-strict-compile8"
STRICT_COMPILE9_WORKFLOW_VERSION = "worker-v2.2.8-strict-compile9"
STRICT_COMPILE10_WORKFLOW_VERSION = "worker-v2.2.9-strict-compile10"
STRICT_COMPILE11_WORKFLOW_VERSION = "worker-v2.2.10-strict-compile11"
STRICT_COMPILE12_WORKFLOW_VERSION = "worker-v2.2.11-strict-compile12"
STRICT_COMPILE13_WORKFLOW_VERSION = "worker-v2.2.12-strict-compile13"
STRICT_COMPILE15_WORKFLOW_VERSION = "worker-v2.2.13-strict-compile15"
WORKFLOW_VERSION = "worker-v2.3"


LEGACY_STAGE_CONTRACTS = (
    StageContract(
        key="canonical_clean_material",
        order=10,
        skill_name="pdf-clean-markdown-rebuild",
        version="v2.0.0-draft1",
        owner="workflow_code",
        input_schema="luceon.workflow.canonical-input/v1",
        output_schema="luceon.clean-material/v2",
        artifact_prefix="canonical-clean",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "source_pdf_and_popo_lineage_verified",
            "all_source_pages_accounted_for",
            "image_references_resolve",
            "clean_markdown_schema_valid",
        ),
        llm_policy="LLM may resolve bounded OCR and outline ambiguities; it cannot publish or waive gates.",
        runtime_snapshot_sha256="dcafaf1c34d0522368fee3809b1f1b8057ca790f94ee68a93531925ff3432a40",
    ),
    StageContract(
        key="semantic_annotation",
        order=20,
        skill_name="material-semantic-annotator",
        version="v2.0.0-draft1",
        owner="workflow_code",
        input_schema="luceon.clean-material/v2",
        output_schema="luceon.semantic-annotation/v2",
        artifact_prefix="semantic-annotation",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "every_clean_block_assigned_exactly_once",
            "outline_coverage_complete",
            "question_and_answer_relations_valid",
            "annotation_schema_valid",
        ),
        llm_policy="LLM returns schema-constrained block classifications; deterministic coverage validation owns acceptance.",
        runtime_snapshot_sha256="5916505e071e7d684e7e28e95edf3026bc35f3ce23d9a2a62d459edf476f2556",
    ),
    StageContract(
        key="deterministic_elegantbook",
        order=30,
        skill_name="cleanlatex-to-elegantbook",
        version="v2.0.0-draft1",
        owner="workflow_code",
        input_schema="luceon.semantic-annotation/v2",
        output_schema="luceon.elegantbook-candidate/v2",
        artifact_prefix="elegantbook-candidate",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "latex_project_schema_valid",
            "source_outline_mapping_preserved",
            "assets_are_local_and_traceable",
            "candidate_compiles_reproducibly",
        ),
        llm_policy="No LLM by default; ambiguous semantic-to-LaTeX mapping must be an explicit bounded task.",
        runtime_snapshot_sha256="1966d77cd307ef32c24d93d803cd8180b8cbe8a5ce8e48c478817d57531e058f",
    ),
    StageContract(
        key="bounded_llm_polish",
        order=40,
        skill_name="refine-elegantbook-latex",
        version="v2.0.0-draft1",
        owner="llm_gateway",
        input_schema="luceon.latex-polish-task/v1",
        output_schema="luceon.latex-patch/v1",
        artifact_prefix="refined-candidate",
        retry_scope="finding_and_stage_only",
        acceptance_gates=(
            "patch_scope_allowed",
            "protected_invariants_unchanged",
            "patched_candidate_compiles",
            "model_call_recorded_by_gateway",
        ),
        llm_policy="LLM returns a bounded patch and rationale only; workflow code applies and validates it.",
    ),
    StageContract(
        key="independent_final_review",
        order=50,
        skill_name="finished-textbook-final-review",
        version="v2.0.0-draft1",
        owner="independent_qa",
        input_schema="luceon.final-review-input/v2",
        output_schema="luceon.final-review-evidence/v2",
        artifact_prefix="final-review",
        retry_scope="failed_findings_only",
        acceptance_gates=(
            "compiled_pdf_hash_bound_to_renders",
            "all_pages_reviewed",
            "deterministic_hard_gates_passed",
            "visual_qa_passed",
            "publisher_has_not_accepted_model_self_attestation",
        ),
        llm_policy="Vision LLM may emit page findings; only the independent QA aggregator decides pass or block.",
    ),
)


CORE_CONVERGENCE_STAGE_CONTRACTS = (
    StageContract(
        key="canonical_clean_material",
        order=10,
        skill_name="pdf-clean-markdown-rebuild",
        version="v2.1.0-core1",
        owner="workflow_code",
        input_schema="luceon.workflow.canonical-input/v2",
        output_schema="luceon.clean-material/v3",
        artifact_prefix="canonical-clean",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "source_pdf_and_popo_lineage_verified",
            "all_source_pages_accounted_for",
            "canonical_blocks_are_stable",
            "image_references_resolve",
            "cleaning_actions_are_allowlisted",
        ),
        llm_policy="DeepSeek Flash may resolve a bounded OCR ambiguity; code owns cleaning, lineage, and acceptance.",
    ),
    StageContract(
        key="outline_reconstruction",
        order=20,
        skill_name="pdf-clean-markdown-rebuild:outline",
        version="v1.0.0",
        owner="workflow_code",
        input_schema="luceon.clean-material/v3",
        output_schema="luceon.outline-reconstruction/v1",
        artifact_prefix="outline-reconstruction",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "outline_depth_is_two_or_three",
            "outline_titles_are_source_evidenced",
            "outline_has_no_duplicates_or_level_jumps",
            "outline_and_body_are_bidirectionally_covered",
            "unresolved_outline_items_block_acceptance",
        ),
        llm_policy="DeepSeek Flash may classify supplied heading candidates only; it cannot invent titles or waive evidence gates.",
    ),
    StageContract(
        key="semantic_annotation",
        order=30,
        skill_name="material-semantic-annotator",
        version="v2.1.0-core1",
        owner="workflow_code",
        input_schema="luceon.outline-reconstruction/v1",
        output_schema="luceon.semantic-annotation/v3",
        artifact_prefix="semantic-annotation",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "every_clean_block_assigned_exactly_once",
            "outline_and_body_are_bidirectionally_covered",
            "question_formula_table_media_relations_valid",
            "no_unexplained_content_loss",
        ),
        llm_policy="DeepSeek Flash returns bounded classifications and relations; deterministic conservation validation owns acceptance.",
    ),
    StageContract(
        key="deterministic_elegantbook",
        order=40,
        skill_name="cleanlatex-to-elegantbook",
        version="v2.1.0-core1",
        owner="workflow_code",
        input_schema="luceon.semantic-annotation/v3",
        output_schema="luceon.elegantbook-candidate/v3",
        artifact_prefix="elegantbook-candidate",
        retry_scope="this_stage_only",
        acceptance_gates=(
            "latex_project_schema_valid",
            "outline_content_and_lineage_invariants_preserved",
            "assets_are_local_and_traceable",
            "candidate_compiles_reproducibly_in_texlive_2025",
        ),
        llm_policy="No LLM. The builder consumes only accepted structured artifacts.",
    ),
    StageContract(
        key="bounded_deepseek_polish_qa",
        order=50,
        skill_name="refine-elegantbook-latex:bounded-core-gates",
        version="v1.0.0",
        owner="workflow_code",
        input_schema="luceon.elegantbook-candidate/v3",
        output_schema="luceon.worker-core-acceptance/v1",
        artifact_prefix="core-accepted-elegantbook",
        retry_scope="failed_gate_only",
        acceptance_gates=(
            "deepseek_tasks_are_schema_bounded",
            "outline_gate_passed",
            "content_conservation_gate_passed",
            "elegantbook_reproducibility_gate_passed",
            "model_cannot_self_attest_acceptance",
        ),
        llm_policy="DeepSeek Flash may answer explicit ambiguity tasks; project validators apply changes and decide all gates.",
    ),
)


STRICT_COMPILE1_STAGE_CONTRACTS = tuple(
    replace(
        contract,
        version="v2.2.0-strict-compile1",
        output_schema="luceon.elegantbook-candidate/v4",
        acceptance_gates=contract.acceptance_gates + (
            "self_contained_cjk_font_bundled",
            "no_missing_glyphs_or_private_use_residue",
            "no_obvious_layout_overflow",
        ),
    )
    if contract.key == "deterministic_elegantbook"
    else replace(
        contract,
        version="v1.1.0-strict-compile1",
        input_schema="luceon.elegantbook-candidate/v4",
        output_schema="luceon.worker-core-acceptance/v2",
    )
    if contract.key == "bounded_deepseek_polish_qa"
    else contract
    for contract in CORE_CONVERGENCE_STAGE_CONTRACTS
)


STRICT_COMPILE2_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.version}+strict2")
    for contract in STRICT_COMPILE1_STAGE_CONTRACTS
)


STRICT_COMPILE3_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.version}+strict3")
    for contract in STRICT_COMPILE2_STAGE_CONTRACTS
)


STRICT_COMPILE4_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.version}+strict4")
    for contract in STRICT_COMPILE3_STAGE_CONTRACTS
)


STRICT_COMPILE5_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.version}+strict5")
    for contract in STRICT_COMPILE4_STAGE_CONTRACTS
)


STRICT_COMPILE6_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.version}+strict6")
    for contract in STRICT_COMPILE5_STAGE_CONTRACTS
)


STRICT_COMPILE7_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.6-strict7")
    for contract in STRICT_COMPILE6_STAGE_CONTRACTS
)


STRICT_COMPILE8_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.7-strict8")
    for contract in STRICT_COMPILE7_STAGE_CONTRACTS
)


STRICT_COMPILE9_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.8-strict9")
    for contract in STRICT_COMPILE8_STAGE_CONTRACTS
)


STRICT_COMPILE10_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.9-strict10")
    for contract in STRICT_COMPILE9_STAGE_CONTRACTS
)


STRICT_COMPILE11_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.10-strict11")
    for contract in STRICT_COMPILE10_STAGE_CONTRACTS
)


STRICT_COMPILE12_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.11-strict12")
    for contract in STRICT_COMPILE11_STAGE_CONTRACTS
)


STRICT_COMPILE13_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.12-strict13")
    for contract in STRICT_COMPILE12_STAGE_CONTRACTS
)


STRICT_COMPILE15_STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.2.13-strict14")
    for contract in STRICT_COMPILE13_STAGE_CONTRACTS
)


STAGE_CONTRACTS = tuple(
    replace(contract, version=f"{contract.key}.v2.3")
    for contract in STRICT_COMPILE15_STAGE_CONTRACTS
)


def contracts_for_version(workflow_version: str) -> tuple[StageContract, ...]:
    if workflow_version == LEGACY_WORKFLOW_VERSION:
        return LEGACY_STAGE_CONTRACTS
    if workflow_version == CORE_CONVERGENCE_WORKFLOW_VERSION:
        return CORE_CONVERGENCE_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE1_WORKFLOW_VERSION:
        return STRICT_COMPILE1_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE2_WORKFLOW_VERSION:
        return STRICT_COMPILE2_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE3_WORKFLOW_VERSION:
        return STRICT_COMPILE3_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE4_WORKFLOW_VERSION:
        return STRICT_COMPILE4_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE5_WORKFLOW_VERSION:
        return STRICT_COMPILE5_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE6_WORKFLOW_VERSION:
        return STRICT_COMPILE6_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE7_WORKFLOW_VERSION:
        return STRICT_COMPILE7_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE8_WORKFLOW_VERSION:
        return STRICT_COMPILE8_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE9_WORKFLOW_VERSION:
        return STRICT_COMPILE9_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE10_WORKFLOW_VERSION:
        return STRICT_COMPILE10_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE11_WORKFLOW_VERSION:
        return STRICT_COMPILE11_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE12_WORKFLOW_VERSION:
        return STRICT_COMPILE12_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE13_WORKFLOW_VERSION:
        return STRICT_COMPILE13_STAGE_CONTRACTS
    if workflow_version == STRICT_COMPILE15_WORKFLOW_VERSION:
        return STRICT_COMPILE15_STAGE_CONTRACTS
    return STAGE_CONTRACTS


def contract_for(workflow_version: str, stage_key: str) -> StageContract:
    for contract in contracts_for_version(workflow_version):
        if contract.key == stage_key:
            return contract
    raise KeyError(stage_key)


def stage_contracts() -> list[dict]:
    return [contract.to_dict() for contract in STAGE_CONTRACTS]
