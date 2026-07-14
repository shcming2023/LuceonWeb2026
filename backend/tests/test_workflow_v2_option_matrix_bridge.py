from app.workflow_v2.runtime.elegantbook.scripts.semantic_markdown_to_cleanlatex import convert_markdown, normalize_source_bullets, promote_metadata_article_titles, transpose_option_matrices


def test_transposes_three_adjacent_html_option_columns() -> None:
    markdown = """<table><tr><td>1. A. about</td></tr><tr><td>2. A. got</td></tr><tr><td>3. A. ease</td></tr></table>

<table><tr><td>B. for</td></tr><tr><td>B. get</td></tr><tr><td>B. easy</td></tr></table>

<table><tr><td>C. with</td></tr><tr><td>C. getting</td></tr><tr><td>C. easily</td></tr></table>"""
    result = transpose_option_matrices(markdown)
    assert "1. A. about    B. for    C. with" in result
    assert "3. A. ease    B. easy    C. easily" in result
    assert "<table" not in result


def test_transposes_vertical_text_option_columns_with_compact_numbering() -> None:
    markdown = """1. A. three
2. A. I
3.A.bore

B. third
B. me
B. boring

C. thirdly
C. myself
C. bored"""
    assert transpose_option_matrices(markdown).splitlines() == [
        "1. A. three    B. third    C. thirdly",
        "2. A. I    B. me    C. myself",
        "3. A. bore    B. boring    C. bored",
    ]


def test_promotes_plain_article_title_only_when_followed_by_metadata() -> None:
    markdown = """Stop Being a People-Pleaser

语篇类型: 议论文 词数: 273 难度: 3级

ordinary paragraph

Language tips
"""
    result = promote_metadata_article_titles(markdown)
    assert result.startswith("# Stop Being a People-Pleaser\n")
    assert "\nLanguage tips\n" in result


def test_promotes_split_article_title_as_one_heading() -> None:
    markdown = """<!-- page_idx: 3 -->

Looking Back on This Past

School Year

语篇类型: 应用文 词数: 368 难度: 3级
"""
    result = promote_metadata_article_titles(markdown)
    assert "# Looking Back on This Past School Year" in result
    assert result.count("# ") == 1


def test_does_not_repromote_metadata_title_when_accepted_page_heading_exists() -> None:
    markdown = """<!-- page_idx: 3 -->
# Looking Back on This Past School Year

Looking Back on This Past

School Year

语篇类型: 应用文 词数: 368 难度: 3级
"""
    result = promote_metadata_article_titles(markdown)
    assert result.count("# ") == 1


def test_does_not_promote_question_without_article_metadata() -> None:
    markdown = "7. How far can Mika ride?\n\nOrdinary explanation.\n"
    assert promote_metadata_article_titles(markdown) == markdown


def test_splits_inline_source_arrows_into_real_bullets() -> None:
    markdown = "Intro. ▶ First tip. ▶ Second tip. $\\triangle right$ Third tip."
    assert normalize_source_bullets(markdown).splitlines() == [
        "Intro.",
        "",
        "- First tip.",
        "- Second tip.",
        "- Third tip.",
    ]


def test_long_ocr_image_alt_is_not_rendered_as_a_caption() -> None:
    alt = "Emily passage text " * 20
    latex = convert_markdown(f"![{alt}](images/photo.jpg)\n")
    assert r"\includegraphics" in latex
    assert r"\caption" not in latex
    assert "Emily passage text" not in latex
