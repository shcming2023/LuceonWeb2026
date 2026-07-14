from app.workflow_v2.runtime.canonical.scripts import build_outline_decision as outline
from app.workflow_v2.runtime.canonical.scripts.build_outline_decision import close_numbered_outline_hierarchy


def candidate(candidate_id, title, page, *, source="popo_document_tree", row_type="footer"):
    return {
        "candidate_id": candidate_id,
        "candidate_type": "body_structural_heading",
        "source": source,
        "title_text": title,
        "page": page,
        "evidence": {"row_type": row_type},
    }


def test_hierarchy_closure_inserts_chapter_and_reparents_numbered_children():
    decision = {
        "final_outline": [
            {"title": "SECTION 2", "level": 1, "parent_title": "", "page": 100},
            {"title": "8.1 First skill", "level": 1, "parent_title": "", "page": 120},
            {"title": "8.2 Second skill", "level": 1, "parent_title": "", "page": 124},
        ]
    }
    candidates = [
        candidate("topic", "Chapter 8. Topic 1", 115),
        candidate("chapter", "Chapter 8: Reading and writing", 118),
    ]

    result = close_numbered_outline_hierarchy(decision, candidates)
    outline = result["final_outline"]

    chapter = next(item for item in outline if item["title"] == "Chapter 8: Reading and writing")
    children = [item for item in outline if item["title"].startswith("8.")]
    assert chapter["level"] == 2
    assert chapter["parent_title"] == "SECTION 2"
    assert all(item["level"] == 3 and item["parent_title"] == chapter["title"] for item in children)
    assert outline.index(chapter) < min(outline.index(item) for item in children)


def test_hierarchy_closure_clamps_repeated_parent_anchor_before_first_child():
    decision = {
        "final_outline": [
            {"title": "SECTION 2", "level": 1, "parent_title": "", "page": 100},
            {"title": "9.1 Composition", "level": 1, "parent_title": "", "page": 219},
        ]
    }
    candidates = [candidate("chapter", "Chapter 9: Composition", 220)]

    outline = close_numbered_outline_hierarchy(decision, candidates)["final_outline"]
    chapter = next(item for item in outline if item["title"] == "Chapter 9: Composition")
    child = next(item for item in outline if item["title"] == "9.1 Composition")

    assert chapter["page"] == child["page"] == 219
    assert outline.index(chapter) < outline.index(child)


def test_hierarchy_closure_does_not_invent_parent_without_candidate_evidence():
    decision = {"final_outline": [{"title": "4.2 Local label", "level": 1, "parent_title": "", "page": 20}]}

    result = close_numbered_outline_hierarchy(decision, [])

    assert result["final_outline"] == [{"title": "4.2 Local label", "level": 1, "parent_title": "", "page": 20, "order": 0}]
    assert result["hierarchy_closure"]["changed"] is False


def test_llm_outline_cache_reuses_successful_structured_decision(monkeypatch, tmp_path):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("WORKFLOW_V2_CANONICAL_OUTLINE_CACHE", str(tmp_path))
    calls = []

    def fake_call(*_args):
        calls.append(1)
        return (
            {
                "verdict": "ok",
                "final_outline": [
                    {
                        "title": "Chapter 1: Reading",
                        "level": 1,
                        "parent_title": "",
                        "page": 10,
                        "candidate_ids": ["chapter-1"],
                    }
                ],
            },
            {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

    monkeypatch.setattr(outline, "call_deepseek", fake_call)
    candidates = [candidate("chapter-1", "Chapter 1: Reading", 10, source="contents", row_type="")]
    decision = {"selected_outline": [], "rejected_candidates": [], "llm": {}}
    first = outline.maybe_review_with_llm(
        decision,
        candidates,
        enabled=True,
        base_url="https://example.invalid",
        model="test-model",
        timeout=1,
        max_risk_candidates=100,
    )
    second = outline.maybe_review_with_llm(
        {"selected_outline": [], "rejected_candidates": [], "llm": {}},
        candidates,
        enabled=True,
        base_url="https://example.invalid",
        model="test-model",
        timeout=1,
        max_risk_candidates=100,
    )

    assert len(calls) == 1
    assert first["llm"]["cache_hit"] is False
    assert second["llm"]["cache_hit"] is True
    assert second["final_outline"] == first["final_outline"]


def test_hierarchy_closure_merges_duplicate_nodes_and_lineage():
    decision = {
        "final_outline": [
            {
                "title": "1.5 Explicit meaning",
                "level": 3,
                "parent_title": "Chapter 1: Reading",
                "page": 23,
                "candidate_ids": ["toc"],
            },
            {
                "title": "1.5 Explicit meaning",
                "level": 3,
                "parent_title": "Chapter 1: Reading",
                "page": 23,
                "candidate_ids": ["synthetic"],
            },
        ]
    }

    result = close_numbered_outline_hierarchy(decision, [])

    assert len(result["final_outline"]) == 1
    assert result["final_outline"][0]["candidate_ids"] == ["toc", "synthetic"]
    assert result["hierarchy_closure"]["repairs"] == [
        {"action": "merge_duplicate_node", "title": "1.5 Explicit meaning", "page": 23}
    ]


def test_hierarchy_closure_merges_synthetic_duplicate_at_different_page():
    decision = {
        "final_outline": [
            {
                "title": "7.3 Writer's craft",
                "level": 3,
                "parent_title": "Chapter 7: Language",
                "page": 167,
                "source": "contents",
                "candidate_ids": ["contents"],
                "evidence": {"block_ids": [1, 2]},
            },
            {
                "title": "7.3 Writer's craft",
                "level": 3,
                "parent_title": "Chapter 7: Language",
                "page": 173,
                "source": "synthetic_parent_from_topic",
                "candidate_ids": ["synthetic"],
                "evidence": {"block_ids": []},
            },
        ]
    }

    result = close_numbered_outline_hierarchy(decision, [])

    assert len(result["final_outline"]) == 1
    assert result["final_outline"][0]["page"] == 167
    assert result["final_outline"][0]["candidate_ids"] == ["contents", "synthetic"]
