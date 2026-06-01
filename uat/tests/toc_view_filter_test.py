from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("boto3", types.SimpleNamespace(client=lambda *args, **kwargs: None))

from luceon_service.service import (
    _filter_toc_view_tree,
    _flatten_tree,
    _render_tree_markdown,
    _render_tree_preview,
)


def collect_titles(node):
    titles = [node.get("title")]
    for child in node.get("children") or []:
        titles.extend(collect_titles(child))
    return titles


def test_toc_view_filter_removes_supplement_nodes():
    tree = {
        "type": "root",
        "title": "",
        "content": "",
        "children": [
            {
                "type": "text",
                "title": "Unit 1",
                "content": "Main section",
                "block_ids": [1],
                "location": [],
                "children": [
                    {
                        "type": "page_footnote",
                        "title": "Page 1 - page_footnote",
                        "content": "footnote",
                        "block_ids": [2],
                        "location": [],
                        "children": [],
                    },
                    {
                        "type": "text",
                        "title": "Lesson 1",
                        "content": "Lesson body",
                        "block_ids": [3],
                        "location": [],
                        "children": [],
                    },
                ],
            },
            {
                "type": "page_number",
                "title": "Page 1 - page_number",
                "content": "1",
                "block_ids": [4],
                "location": [],
                "children": [],
            },
            {
                "type": "header",
                "title": "Page 1 - header",
                "content": "Header",
                "block_ids": [5],
                "location": [],
                "children": [],
            },
            {
                "type": "footer",
                "title": "Page 1 - footer",
                "content": "Footer",
                "block_ids": [6],
                "location": [],
                "children": [],
            },
            {
                "type": "page_title",
                "title": "Page 1 - page_title",
                "content": "Page title",
                "block_ids": [7],
                "location": [],
                "children": [],
            },
            {
                "type": "aside_text",
                "title": "Page 1 - aside_text",
                "content": "Aside",
                "block_ids": [8],
                "location": [],
                "children": [],
            },
        ],
    }

    filtered = _filter_toc_view_tree(tree)
    titles = collect_titles(filtered)
    flattened = _flatten_tree(filtered)
    readable = _render_tree_preview(filtered)
    markdown = _render_tree_markdown(filtered)

    assert "Unit 1" in titles
    assert "Lesson 1" in titles
    assert "Page 1 - page_number" not in titles
    assert "Page 1 - page_footnote" not in titles
    assert "Page 1 - header" not in titles
    assert "Page 1 - footer" not in titles
    assert "Page 1 - page_title" not in titles
    assert "Page 1 - aside_text" not in titles
    assert all(row["type"] == "text" for row in flattened)
    assert "Page 1 -" not in readable
    assert "Page 1 -" not in markdown


if __name__ == "__main__":
    test_toc_view_filter_removes_supplement_nodes()
    print("toc view filter test passed")
