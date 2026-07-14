#!/usr/bin/env python3
"""Build a first-pass printable Standard package from a Clean package.

This MVP is intentionally conservative: it preserves Clean text verbatim,
builds a structured StandardDocument around it, copies only referenced media,
renders simple print HTML, and writes audit reports.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_SRC_RE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)
HTML_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
UPPER_PART_RE = re.compile(r"^[A-Z]\.\s+")
QUESTION_RE = re.compile(r"^\d+\.\s+")
OPTION_RE = re.compile(r"^(?:[a-h][.)]|\([a-h]\))\s+")
ANSWER_BLANK_RE = re.compile(r"(\\_){2,}|_{2,}")
WORKBOOK_INSTRUCTION_RE = re.compile(
    r"^\*{0,2}\d+\s+(?:Circle|Complete|Write|Choose|Read|Look|Match|Ask|Answer|Listen|Correct|Use|Fill|Tick|Put|Order|Number|Underline|Make|Play|Say|Draw|Find|Change|Rewrite)\b",
    re.I,
)
WORKBOOK_UNNUMBERED_INSTRUCTION_RE = re.compile(
    r"^(?:"
    r"ABOUT YOU\b|"
    r"COMPREHENSION\b|"
    r"LISTEN\b.*\b(?:Circle|Write|Complete|Answer)\b|"
    r"Some\b.*\b(?:Find|Correct)\b.*\bmistakes?\b|"
    r"(?:Choose|Complete|Write|Look|Read|Find|Correct|Fill|Circle|Answer|Ask|Tell|Work with a partner)\b"
    r")",
    re.I,
)
WORKBOOK_NUMBERED_QUESTION_INSTRUCTION_RE = re.compile(
    r"^\*{0,2}\d{1,2}\s+.+\?\s+(?:Write|Circle|Choose|Match|Complete|Tick|Put|Order|Number|Underline|Make|Draw|Find|Change|Rewrite)\b",
    re.I,
)
WORKBOOK_EXERCISE_HEADING_RE = re.compile(r"^\*{0,2}Exercise\s+\d{1,3}\b", re.I)
WORKBOOK_SECTION_GROUP_HEADING_RE = re.compile(r"^PART\s+\d+\s+(?:Write|Learner's Log)\b", re.I)
WORKBOOK_NUMBERED_ITEM_RE = re.compile(r"^\d{1,2}\s+\S+")
WORKBOOK_GRAMMAR_EQUIVALENCE_RE = re.compile(r"^\d{1,2}\s*=\s+\S+")
WORKBOOK_NUMBERED_EXPLANATION_RE = re.compile(
    r"^\d+\.\s+(?:"
    r"We\b|To\b|Use\b|Don't\b|Do not\b|"
    r"In\b|The\b|After\b|Sometimes\b|Remember\b|Omit\b|"
    r"You can\b|You sometimes\b|When\b|What kind of\b|How many\b|Who questions\b|Some common\b|There are\b|"
    r"describe\b|tell\b|classify\b|show\b|"
    r"Family\b|Have\b|An?\s+\w+\s+can\b"
    r")",
    re.I,
)
EXPLANATION_SIGNAL_RE = re.compile(
    r"\b(?:we use|regular verbs|irregular verbs|base form|present|past|future|conditional|passive|pronouns|modal verbs|look!)\b",
    re.I,
)
EXPLANATION_TABLE_SIGNAL_RE = re.compile(
    r"\b(?:we use|we form|we make|if-clause|direct speech|reported speech|reported question|fact|wish|past simple|past perfect|present perfect|passive|conditional)\b",
    re.I,
)
GRAMMAR_PARADIGM_TABLE_SIGNAL_RE = re.compile(
    r"(?:possessive adjectives?.*possessive pronouns?|possessive pronouns?.*possessive adjectives?|affirmative.*(?:short form|negative)|(?:short form|negative).*affirmative|base form.*past participles?|past participles?.*base form)",
    re.I | re.S,
)
GRAMMAR_EXPLANATION_TABLE_HEADER_RE = re.compile(
    r"(?:"
    r"\bexamples?\b.*\bexplanation\b|"
    r"\bsubject\b.*\bbe\b|"
    r"\bsubject pronoun\b.*\bpossessive adjective\b|"
    r"\blong form\b.*\bcontraction\b|"
    r"\bstatement\b.*\b(?:yes/no|wh-)\s+question\b|"
    r"\bquestion word\(s\).*\b(?:be|do|modal|have to|verb)\b|"
    r"\bwh- questions?\b.*\banswers?\b|"
    r"\bsubject\b.*\bverb\b|"
    r"\btime expressions?\b|"
    r"\bpreposition\b.*\bexamples?\b|"
    r"\bquantity\b.*\bexamples?\b|"
    r"\bbase form\b.*-s form\b|"
    r"\bsimple adjective\b.*\bsuperlative adjective\b|"
    r"\bthere\b.*\bbe\b.*\bphrase\b|"
    r"\bverb\b.*-ing form\b.*\brule\b|"
    r"\bjar of\b.*\bcan of\b|"
    r"\bin\b.*\bnear\b.*\bnext to\b.*\bon\b.*\bat\b.*\bto\b|"
    r"\bsingular\b.*\bplural\b|"
    r"\byes/no question\b.*\bwh- question\b|"
    r"\bshort answers?\b|"
    r"\bprepositional phrase\b|"
    r"\bbase form\b.*\bpast form\b|"
    r"\bverb\b.*\b-ing form\b.*\brule\b|"
    r"\bfrequency\b.*\bpresent\b.*\bpast\b.*\bfuture\b"
    r")",
    re.I | re.S,
)
GRAMMAR_PARADIGM_HEADER_RE = re.compile(
    r"\baffirmative\b.*\bnegative\b.*\bquestions?\b.*\bshort answers?\b",
    re.I | re.S,
)
GRAMMAR_PARADIGM_SUBJECT_BOUNDARY_RE = re.compile(
    r"(?<=[a-z'’])\s*(?=(?:you|he|she|it|we|they)(?:\b|['’]))",
    re.I,
)
FRONT_MATTER_NUMBER_RUN_RE = re.compile(r"^(?:\d+\s+){4,}\d+$")
TABLE_RE = re.compile(r"^\s*<table[\s>]", re.I)
TABLE_END_RE = re.compile(r"</table>\s*$", re.I)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
HTML_COMMENT_LINE_RE = re.compile(r"^\s*<!--.*?-->\s*$")
VISIBLE_ARTIFACT_PATTERNS = {
    "escaped_table_tag": re.compile(r"&lt;/?(?:table|tbody|thead|tr|td|th)\b", re.I),
    "visible_html_comment": re.compile(r"&lt;!--|<!--"),
    "source_empty_chunk_marker": re.compile(r"source_empty_chunk"),
}
CAPTION_RE = re.compile(r"^[▲▼▶◀]|[▲▼▶◀]\s")
SHORT_MARKER_RE = re.compile(r"^(?:[①②③④⑤⑥⑦⑧⑨⑩]|\d+\.?|[A-Z])$")
FOOTNOTE_MARKER_RE = re.compile(r"\$\^\{\d+\}\$")
INLINE_DOLLAR_RE = re.compile(r"\$(?!\$)(.+?)(?<!\\)\$")
DISPLAY_MATH_RE = re.compile(r"^\$\$\s*(.*?)\s*\$\$$", re.S)
MATH_BREAK_CHARS = set("\n，。；：？！、;")
MATH_ALLOWED_CHARS = set(r"\{}^_+-=*/().,|<>[] ")

SECTION_LABELS = {
    "before you read": "before_you_read",
    "reading comprehension": "comprehension_questions",
    "vocabulary practice": "vocabulary_practice",
    "word link": "vocabulary_box",
    "did you know?": "note",
    "explore more": "explore_more",
    "review unit": "review_unit",
}

WORKBOOK_SECTION_LABELS = {
    "assessment practice",
    "do you know how?",
    "do you understand?",
    "practice",
    "practice & problem solving",
    "leveled practice",
    "reflect",
    "act 1",
    "act 2",
    "act 3",
    "sequel",
}
WORKBOOK_INSTRUCTION_START_RE = re.compile(
    r"^(?:Choose|Complete|Write|Look|Read|Find|Correct|Fill|Circle|Answer|Ask|Tell|Work|"
    r"Determine|Classify|Evaluate|Simplify|Solve|Graph|Use|Draw|Estimate|Compare|Order|"
    r"Match|Name|Identify|Explain|Describe|Select|Calculate|Convert|Round|Model|Represent|"
    r"Make|Copy|Connect|Decide|Show)\b",
    re.I,
)

PASSAGE_STOP_LABELS = {
    "reading comprehension",
    "vocabulary practice",
    "word link",
    "did you know?",
    "explore more",
    "review unit",
}

PROFILE_CHOICES = {"reading_textbook", "grammar_workbook", "exercise_workbook", "math_textbook"}
WORKBOOK_PROFILES = {"grammar_workbook", "exercise_workbook"}
MATH_PROFILES = {"math_textbook"}


@dataclass
class Line:
    no: int
    text: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_heading_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_text_for_compare(value: str) -> str:
    without_images = IMAGE_RE.sub("", value)
    without_comments = HTML_COMMENT_RE.sub("", without_images)
    return re.sub(r"\s+", " ", without_comments).strip()


def normalize_review_text(value: str) -> str:
    translated = (
        value.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
        .replace("—", "-")
    )
    no_tags = re.sub(r"<[^>]+>", " ", translated)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip().lower()


def normalize_review_compact_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_review_text(value))


class SimpleTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[dict[str, str]]] = []
        self._table_depth = 0
        self._current_row: list[dict[str, str]] | None = None
        self._current_cell: list[str] | None = None
        self._current_cell_tag = "td"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._table_depth += 1
            return
        if not self._table_depth:
            return
        if tag == "tr":
            self._current_row = []
            return
        if tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
            self._current_cell_tag = tag
            return
        if tag == "br" and self._current_cell is not None:
            self._current_cell.append("\n")

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._current_cell is not None and self._current_row is not None:
            self._current_row.append({"tag": self._current_cell_tag, "text": "".join(self._current_cell)})
            self._current_cell = None
            self._current_cell_tag = "td"
            return
        if tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None
            return
        if tag == "table":
            self._table_depth = max(0, self._table_depth - 1)


def normalize_table_cell_text(value: str) -> str:
    normalized = html.unescape(value).replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    return normalized.strip()


def split_question_run(value: str) -> list[str]:
    parts = [part.strip() for part in re.findall(r"[^?]+\?", value) if part.strip()]
    if len(parts) <= 1:
        return []
    if re.sub(r"\s+", "", "".join(parts)) != re.sub(r"\s+", "", value):
        return []
    return parts


def split_short_answer_run(value: str) -> list[str]:
    if not re.match(r"^(?:Yes|No),", value, re.I):
        return []
    parts = [part.strip() for part in re.split(r"(?<=\.)\s*(?=(?:Yes|No),)", value) if part.strip()]
    return parts if len(parts) > 1 else []


def split_subject_run(value: str) -> list[str]:
    parts = [part.strip() for part in GRAMMAR_PARADIGM_SUBJECT_BOUNDARY_RE.split(value) if part.strip()]
    return parts if len(parts) > 1 else []


def split_grammar_paradigm_cell(value: str) -> list[str]:
    normalized = normalize_table_cell_text(value)
    if not normalized:
        return [""]

    explicit_lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    if len(explicit_lines) > 1:
        return explicit_lines

    for splitter in (split_question_run, split_short_answer_run, split_subject_run):
        parts = splitter(normalized)
        if parts:
            return parts
    return [normalized]


def parse_simple_table_rows(table_html: str) -> list[list[dict[str, str]]]:
    parser = SimpleTableParser()
    parser.feed(table_html)
    parser.close()
    return parser.rows


def reflow_grammar_paradigm_table(table_html: str) -> str:
    rows = parse_simple_table_rows(table_html)
    if len(rows) != 2:
        return table_html
    header_cells, body_cells = rows
    if len(header_cells) != len(body_cells) or len(header_cells) < 4:
        return table_html

    header_text = " ".join(normalize_table_cell_text(cell.get("text", "")) for cell in header_cells)
    if not GRAMMAR_PARADIGM_HEADER_RE.search(header_text):
        return table_html

    split_columns = [split_grammar_paradigm_cell(cell.get("text", "")) for cell in body_cells]
    split_counts = [len(parts) for parts in split_columns]
    common_counts = Counter(split_counts)
    target_count, frequency = common_counts.most_common(1)[0]
    if target_count < 3 or frequency != len(split_columns):
        return table_html

    header_html = "".join(
        f'<{cell.get("tag", "td")}>{html.escape(normalize_table_cell_text(cell.get("text", "")))}</{cell.get("tag", "td")}>'
        for cell in header_cells
    )
    body_rows: list[str] = []
    for row_index in range(target_count):
        rendered_cells = []
        for cell_index, cell in enumerate(body_cells):
            tag = cell.get("tag", "td")
            rendered_cells.append(f"<{tag}>{html.escape(split_columns[cell_index][row_index])}</{tag}>")
        body_rows.append(f'<tr>{"".join(rendered_cells)}</tr>')
    return f'<table class="grammar-paradigm-table"><tr>{header_html}</tr>{"".join(body_rows)}</table>'


def coalesce_display_math_lines(lines: list[Line]) -> list[Line]:
    coalesced: list[Line] = []
    in_math = False
    start_no = 0
    buffer: list[str] = []
    for line in lines:
        stripped = line.text.strip()
        if stripped == "$$":
            if in_math:
                buffer.append(stripped)
                coalesced.append(Line(start_no, "\n".join(buffer)))
                buffer = []
                in_math = False
            else:
                in_math = True
                start_no = line.no
                buffer = [stripped]
            continue
        if in_math:
            buffer.append(line.text)
            continue
        coalesced.append(line)
    if in_math and buffer:
        coalesced.append(Line(start_no, "\n".join(buffer)))
    return coalesced


def coalesce_html_table_lines(lines: list[Line]) -> list[Line]:
    coalesced: list[Line] = []
    in_table = False
    start_no = 0
    buffer: list[str] = []
    for line in lines:
        stripped = line.text.strip()
        if not in_table and TABLE_RE.match(stripped):
            in_table = True
            start_no = line.no
            buffer = [line.text]
            if TABLE_END_RE.search(stripped):
                coalesced.append(Line(start_no, "\n".join(buffer)))
                buffer = []
                in_table = False
            continue
        if in_table:
            buffer.append(line.text)
            if TABLE_END_RE.search(stripped):
                coalesced.append(Line(start_no, "\n".join(buffer)))
                buffer = []
                in_table = False
            continue
        coalesced.append(line)
    if in_table and buffer:
        coalesced.append(Line(start_no, "\n".join(buffer)))
    return coalesced


def infer_standard_profile(markdown: str, clean_manifest: dict[str, Any], requested_profile: str = "auto") -> str:
    if requested_profile != "auto":
        if requested_profile not in PROFILE_CHOICES:
            raise ValueError(f"Unsupported Standard profile: {requested_profile}")
        return requested_profile

    title_text = " ".join(
        str(clean_manifest.get(key) or "")
        for key in ["title", "filename", "source_pdf_name", "input_filename"]
    ).lower()
    if "reading explorer" in title_text or "reader" in title_text:
        return "reading_textbook"
    if "grammar" in title_text:
        return "grammar_workbook"
    if "workbook" in title_text or "exercise" in title_text:
        return "exercise_workbook"

    instruction_count = sum(
        1
        for line in markdown.splitlines()
        if WORKBOOK_INSTRUCTION_RE.match(line.strip())
        or WORKBOOK_UNNUMBERED_INSTRUCTION_RE.match(line.strip())
        or WORKBOOK_NUMBERED_QUESTION_INSTRUCTION_RE.match(line.strip())
    )
    answer_blank_count = len(ANSWER_BLANK_RE.findall(markdown))
    if instruction_count >= 1 and answer_blank_count >= 1:
        return "exercise_workbook"
    formula_delimiter_count = markdown.count("$")
    if formula_delimiter_count >= 500 or (
        formula_delimiter_count >= 100 and ("数学" in title_text or "math" in title_text)
    ):
        return "math_textbook"
    return "reading_textbook"


def image_refs(markdown: str) -> list[str]:
    refs: list[str] = []
    for match in IMAGE_RE.finditer(markdown):
        path = match.group(2).strip()
        if path and not path.startswith(("http://", "https://", "data:")):
            refs.append(path)
    for match in HTML_IMG_SRC_RE.finditer(markdown):
        path = html.unescape(match.group(1)).strip()
        if path and not path.startswith(("http://", "https://", "data:", "#")):
            refs.append(path)
    return sorted(set(refs))


def is_image_only_markdown(markdown: str) -> bool:
    stripped = markdown.strip()
    if not stripped:
        return False
    if not image_refs(stripped):
        return False
    without_markdown_images = IMAGE_RE.sub("", stripped)
    without_images = HTML_IMG_TAG_RE.sub("", without_markdown_images)
    return not without_images.strip()


def load_image_semantics(raw_dir: Path | None) -> dict[str, dict[str, Any]]:
    if not raw_dir:
        return {}
    data = read_json(raw_dir / "image_semantics.json")
    items = data.get("items") or data.get("images") or []
    by_path: dict[str, dict[str, Any]] = {}
    for item in items:
        path = str(item.get("path") or item.get("image_ref") or "").strip()
        if path:
            by_path[path] = item
    return by_path


def extract_outline(lines: list[Line]) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    stack: list[str] = []
    for line in lines:
        match = HEADING_RE.match(line.text)
        if not match:
            continue
        level = len(match.group(1))
        title = normalize_heading_title(match.group(2))
        stack = stack[: level - 1]
        stack.append(title)
        outline.append(
            {
                "title": title,
                "level": level,
                "line": line.no,
                "path": stack.copy(),
            }
        )
    return outline


def is_section_label(text: str) -> str | None:
    return SECTION_LABELS.get(text.strip().lower())


def classify_line(text: str, heading_level: int | None, in_passage: bool, profile: str) -> tuple[str, str, dict[str, Any]]:
    stripped = text.strip()
    lower = stripped.lower()
    layout: dict[str, Any] = {}
    subtype = ""

    if heading_level:
        heading_title = stripped.lstrip("#").strip()
        if profile in WORKBOOK_PROFILES and WORKBOOK_SECTION_GROUP_HEADING_RE.match(heading_title):
            return "question_group", "exercise_section", {"keep_together": True, "profile_intent": "exercise_group"}
        if profile in WORKBOOK_PROFILES:
            if heading_level == 1:
                return "unit_opener", "heading", {"break_before": "page"}
            return "section", "lesson_heading", {"break_before": "page"} if heading_level == 2 else {}
        if heading_level == 1:
            return "unit_opener", "heading", {"break_before": "page"}
        if heading_level == 2:
            return "section", "lesson_heading", {"break_before": "page"}
        if heading_level == 3:
            return "reading_passage", "passage_heading", {"layout_hint": "two_column"}
        return "heading", "", {}

    label_type = is_section_label(stripped)
    if label_type:
        keep = label_type in {"before_you_read", "comprehension_questions", "vocabulary_practice", "review_unit"}
        return label_type, "section_label", {"keep_together": keep}

    if IMAGE_RE.search(stripped):
        layout = {"keep_together": True}
        if profile in WORKBOOK_PROFILES:
            layout["profile_intent"] = "figure_relation_candidate"
        return "captioned_figure", "", layout
    if TABLE_RE.match(stripped):
        subtype = "table_question"
        return "table", subtype, {"keep_together": True, "profile_intent": subtype} if subtype else {"keep_together": True}
    if stripped.startswith("$$") or stripped.endswith("$$"):
        return "formula", "", {"keep_together": True}
    if CAPTION_RE.search(stripped):
        return "caption", "", {"keep_together": True}
    if profile in WORKBOOK_PROFILES and (
        WORKBOOK_EXERCISE_HEADING_RE.match(stripped)
        or WORKBOOK_INSTRUCTION_RE.match(stripped)
        or WORKBOOK_UNNUMBERED_INSTRUCTION_RE.match(stripped)
        or WORKBOOK_NUMBERED_QUESTION_INSTRUCTION_RE.match(stripped)
    ):
        return "question_group", "exercise_instruction", {"keep_together": True, "profile_intent": "exercise_group"}
    if profile in WORKBOOK_PROFILES and WORKBOOK_NUMBERED_ITEM_RE.match(stripped):
        subtype = "fill_blank" if ANSWER_BLANK_RE.search(stripped) else "exercise_item"
        return "question", subtype, {"keep_together": True, "profile_intent": subtype}
    if UPPER_PART_RE.match(stripped):
        return "question_group", "exercise_part", {"keep_together": True}
    if QUESTION_RE.match(stripped):
        return "question", "", {"keep_together": True}
    if OPTION_RE.match(stripped):
        return "option", "", {"keep_together": True}
    if ANSWER_BLANK_RE.search(stripped):
        return "answer_blank", "", {"keep_together": True}
    if lower.startswith(("fact ", "main idea", "detail", "reference", "vocabulary")):
        subtype = "reading_marker" if in_passage else "exercise_marker"
        return "note" if not in_passage else "reading_passage", subtype, {"layout_hint": "two_column"} if in_passage else {}
    if in_passage:
        return "reading_passage", "paragraph", {"layout_hint": "two_column"}
    if len(stripped) <= 80 and stripped.endswith(":"):
        return "note", "label", {"keep_together": True}
    return "paragraph", "", {}


def is_explanation_table_context(context_text: str) -> bool:
    return bool(
        EXPLANATION_TABLE_SIGNAL_RE.search(context_text)
        or GRAMMAR_PARADIGM_TABLE_SIGNAL_RE.search(context_text)
        or GRAMMAR_EXPLANATION_TABLE_HEADER_RE.search(context_text)
    )


def is_mergeable_short_marker(block: dict[str, Any]) -> bool:
    text = str(block.get("markdown") or "").strip()
    if not SHORT_MARKER_RE.match(text):
        return False
    return block.get("type") in {"paragraph", "caption", "note", "question"}


def merge_block_into(target: dict[str, Any], source: dict[str, Any], reason: str, prepend: bool = False) -> None:
    markdown_parts = [source.get("markdown", ""), target.get("markdown", "")] if prepend else [target.get("markdown", ""), source.get("markdown", "")]
    text_parts = [source.get("text", ""), target.get("text", "")] if prepend else [target.get("text", ""), source.get("text", "")]
    target["markdown"] = "\n".join(part for part in markdown_parts if part)
    target["text"] = "\n".join(part for part in text_parts if part)
    target["line_start"] = min(int(target["line_start"]), int(source["line_start"]))
    target["line_end"] = max(int(target["line_end"]), int(source["line_end"]))
    target.setdefault("evidence", {})["clean_lines"] = [target["line_start"], target["line_end"]]
    target.setdefault("layout", {})["keep_together"] = True
    target.setdefault("standard_transforms", []).append(
        {
            "type": "short_marker_merged",
            "source_block_id": source.get("id"),
            "source_lines": [source.get("line_start"), source.get("line_end")],
            "reason": reason,
        }
    )
    if source.get("image_refs"):
        target.setdefault("image_refs", []).extend(source["image_refs"])
        target["image_refs"] = sorted(set(target["image_refs"]))
    if source.get("media"):
        target.setdefault("media", []).extend(source["media"])


def merge_short_marker_blocks(blocks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    merged: list[dict[str, Any]] = []
    transforms: list[dict[str, Any]] = []
    for block in blocks:
        if (
            merged
            and merged[-1].get("type") == "label_marker"
            and merged[-1].get("subtype") == "isolated_marker"
            and int(block["line_start"]) - int(merged[-1]["line_end"]) <= 3
            and block.get("type") not in {"unit_opener", "section"}
        ):
            marker = merged.pop()
            transform = {
                "type": "short_marker_merged",
                "target_block_id": block.get("id"),
                "source_block_id": marker.get("id"),
                "source_text": marker.get("markdown"),
                "source_lines": [marker.get("line_start"), marker.get("line_end")],
                "reason": "adjacent_next_context",
            }
            merge_block_into(block, marker, "adjacent_next_context", prepend=True)
            transforms.append(transform)

        if not is_mergeable_short_marker(block):
            merged.append(block)
            continue

        target: dict[str, Any] | None = None
        reason = ""
        if merged and int(block["line_start"]) - int(merged[-1]["line_end"]) <= 3 and merged[-1].get("type") not in {"unit_opener", "section"}:
            target = merged[-1]
            reason = "adjacent_previous_context"
        elif int(block["line_start"]) - int(block["line_end"]) == 0:
            target = None

        if target is None:
            block["type"] = "answer_blank" if block.get("markdown", "").strip().rstrip(".").isdigit() else "label_marker"
            block["subtype"] = "isolated_marker"
            block.setdefault("layout", {})["keep_together"] = True
            merged.append(block)
            continue

        transform = {
            "type": "short_marker_merged",
            "target_block_id": target.get("id"),
            "source_block_id": block.get("id"),
            "source_text": block.get("markdown"),
            "source_lines": [block.get("line_start"), block.get("line_end")],
            "reason": reason,
        }
        merge_block_into(target, block, reason)
        transforms.append(transform)
    return merged, transforms


def add_remaining_short_marker_issues(blocks: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    for block in blocks:
        text = str(block.get("markdown") or "").strip()
        if is_mergeable_short_marker(block):
            block["status"] = "needs_review"
            issues.append(
                {
                    "type": "very_short_text_block",
                    "severity": "review",
                    "block_id": block["id"],
                    "line": block["line_start"],
                    "text": text,
                }
            )


def annotate_question_relations(blocks: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    current_group: dict[str, Any] | None = None
    current_question: dict[str, Any] | None = None
    group_count = 0
    question_count = 0
    grouped_question_count = 0
    ungrouped_question_count = 0
    fill_blank_question_count = 0
    option_count = 0
    parented_option_count = 0
    orphan_option_count = 0
    answer_blank_count = 0
    parented_answer_blank_count = 0
    orphan_answer_blank_count = 0
    table_question_count = 0
    parented_table_question_count = 0
    orphan_table_question_count = 0
    figure_relation_candidate_count = 0
    parented_figure_relation_candidate_count = 0
    orphan_figure_relation_candidate_count = 0

    def is_explanation_table(block: dict[str, Any], previous_block: dict[str, Any] | None, next_block: dict[str, Any] | None) -> bool:
        context_text = "\n".join(
            str(candidate.get("markdown") or "")
            for candidate in [previous_block, block, next_block]
            if candidate
        )
        return is_explanation_table_context(context_text)

    for index, block in enumerate(blocks):
        block_type = block.get("type")
        subtype = block.get("subtype")
        if block_type in {"captioned_figure", "table"}:
            parent = current_question or current_group
            if block_type == "table" and subtype == "table_question" and not parent:
                previous_block = blocks[index - 1] if index > 0 else None
                next_block = blocks[index + 1] if index + 1 < len(blocks) else None
                if is_explanation_table(block, previous_block, next_block):
                    block["subtype"] = "explanation_table"
                    block.setdefault("layout", {})["profile_intent"] = "explanation_table"
                    subtype = "explanation_table"
            if parent:
                parent.setdefault("children", []).append(block["id"])
                block["parent_id"] = parent["id"]
                relation_type = "uses_table" if block_type == "table" else "uses_figure"
                relations.append({"from": parent["id"], "type": relation_type, "to": block["id"]})
            if subtype == "table_question":
                table_question_count += 1
                if parent:
                    parented_table_question_count += 1
                else:
                    orphan_table_question_count += 1
            if block_type == "captioned_figure" and block.get("layout", {}).get("profile_intent") == "figure_relation_candidate":
                figure_relation_candidate_count += 1
                if parent:
                    parented_figure_relation_candidate_count += 1
                else:
                    orphan_figure_relation_candidate_count += 1
            continue
        if block_type in {"unit_opener", "section", "reading_passage", "captioned_figure", "table"}:
            if block_type in {"unit_opener", "section", "reading_passage"}:
                current_group = None
                current_question = None
            continue
        if block_type in {"before_you_read", "comprehension_questions", "vocabulary_practice", "review_unit", "question_group"}:
            current_group = block
            current_question = None
            group_count += 1
            block.setdefault("layout", {})["keep_together"] = True
            block.setdefault("children", [])
            continue
        if block_type == "question":
            question_count += 1
            if subtype == "fill_blank":
                fill_blank_question_count += 1
            current_question = block
            block.setdefault("children", [])
            if current_group:
                current_group.setdefault("children", []).append(block["id"])
                block["parent_id"] = current_group["id"]
                relations.append({"from": current_group["id"], "type": "contains_question", "to": block["id"]})
                grouped_question_count += 1
            else:
                ungrouped_question_count += 1
            continue
        if block_type == "option":
            option_count += 1
            parent = current_question or current_group
            if parent:
                parent.setdefault("children", []).append(block["id"])
                block["parent_id"] = parent["id"]
                relations.append({"from": parent["id"], "type": "contains_option", "to": block["id"]})
                parented_option_count += 1
            else:
                orphan_option_count += 1
            continue
        if block_type == "answer_blank":
            answer_blank_count += 1
            parent = current_question or current_group
            if parent:
                parent.setdefault("children", []).append(block["id"])
                block["parent_id"] = parent["id"]
                relations.append({"from": parent["id"], "type": "contains_answer_blank", "to": block["id"]})
                parented_answer_blank_count += 1
            else:
                orphan_answer_blank_count += 1

    return {
        "question_groups": group_count,
        "questions": question_count,
        "grouped_questions": grouped_question_count,
        "ungrouped_questions": ungrouped_question_count,
        "fill_blank_questions": fill_blank_question_count,
        "options": option_count,
        "parented_options": parented_option_count,
        "orphan_options": orphan_option_count,
        "answer_blanks": answer_blank_count,
        "parented_answer_blanks": parented_answer_blank_count,
        "orphan_answer_blanks": orphan_answer_blank_count,
        "table_questions": table_question_count,
        "parented_table_questions": parented_table_question_count,
        "orphan_table_questions": orphan_table_question_count,
        "figure_relation_candidates": figure_relation_candidate_count,
        "parented_figure_relation_candidates": parented_figure_relation_candidate_count,
        "orphan_figure_relation_candidates": orphan_figure_relation_candidate_count,
    }


def build_blocks(
    lines: list[Line],
    image_semantics: dict[str, dict[str, Any]],
    profile: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    blocks: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    issue_candidates: list[dict[str, Any]] = []
    heading_stack: list[str] = []
    in_passage = False

    for line in lines:
        stripped = line.text.strip()
        if not stripped or HTML_COMMENT_LINE_RE.match(stripped):
            continue

        heading_match = HEADING_RE.match(stripped)
        heading_level = len(heading_match.group(1)) if heading_match else None
        if heading_match:
            title = normalize_heading_title(heading_match.group(2))
            heading_stack = heading_stack[: heading_level - 1]
            heading_stack.append(title)
            in_passage = heading_level == 3 and profile not in WORKBOOK_PROFILES
        elif stripped.lower() in PASSAGE_STOP_LABELS:
            in_passage = False

        block_type, subtype, layout = classify_line(stripped, heading_level, in_passage, profile)
        block_id = f"b-{len(blocks) + 1:05d}"
        refs = image_refs(stripped)
        evidence: dict[str, Any] = {"clean_lines": [line.no, line.no]}
        pages: list[int] = []
        raw_block_refs: list[str] = []
        for ref in refs:
            semantic = image_semantics.get(ref)
            if semantic:
                if semantic.get("page_idx") is not None:
                    pages.append(int(semantic["page_idx"]))
                if semantic.get("block_ref"):
                    raw_block_refs.append(str(semantic["block_ref"]))
        if pages:
            evidence["pages"] = sorted(set(pages))
        if raw_block_refs:
            evidence["raw_block_refs"] = raw_block_refs

        block = {
            "id": block_id,
            "type": block_type,
            "subtype": subtype,
            "heading_path": heading_stack.copy(),
            "line_start": line.no,
            "line_end": line.no,
            "status": "ok",
            "layout": layout,
            "markdown": stripped,
            "text": IMAGE_RE.sub("", stripped).strip(),
            "image_refs": refs,
            "children": [],
            "evidence": evidence,
        }
        if refs:
            block["media"] = [{"path": ref, "raw_semantics": image_semantics.get(ref, {})} for ref in refs]
            for ref in refs:
                relations.append({"from": block_id, "type": "contains_media", "to": ref})
                if not image_semantics.get(ref):
                    issue_candidates.append(
                        {
                            "type": "missing_raw_image_semantics",
                            "severity": "review",
                            "block_id": block_id,
                            "line": line.no,
                            "image": ref,
                        }
                    )

        blocks.append(block)

        if heading_match and heading_level == 3 and profile not in WORKBOOK_PROFILES:
            in_passage = True

    return blocks, relations, issue_candidates


def strip_display_math(markdown: str) -> str:
    match = DISPLAY_MATH_RE.match(markdown.strip())
    if match:
        return normalize_latex_answer_blanks(match.group(1).strip())
    return normalize_latex_answer_blanks(markdown.strip().strip("$").strip())


def normalize_latex_answer_blanks(value: str) -> str:
    return re.sub(r"(?:\\_){2,}|_{2,}", r"\\underline{\\hspace{1.2cm}}", value)


TD_RE = re.compile(r"<td>(.*?)</td>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def strip_html_cell_text(value: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", value or "")).strip()


def table_cells(markdown: str) -> list[str]:
    return [strip_html_cell_text(match.group(1)) for match in TD_RE.finditer(markdown or "")]


def table_first_cell(markdown: str) -> str:
    cells = table_cells(markdown)
    return cells[0].strip().lower() if cells else ""


def is_definition_example_table(markdown: str) -> bool:
    cells = [cell.lower() for cell in table_cells(markdown)[:2]]
    return bool(cells and cells[0] == "definition" and (len(cells) == 1 or cells[1] == "example"))


def is_vocabulary_word_table(markdown: str) -> bool:
    return table_first_cell(markdown) == "vocabulary word"


def is_short_word_bank_block(block: dict[str, Any]) -> bool:
    if block.get("type") != "paragraph":
        return False
    text = str(block.get("markdown") or "").strip()
    if not text or len(text) > 180:
        return False
    if TABLE_RE.match(text) or IMAGE_RE.search(text):
        return False
    return True


def is_vocabulary_label_block(block: dict[str, Any]) -> bool:
    return str(block.get("markdown") or "").strip().lower() == "vocabulary"


def is_use_vocabulary_followup(block: dict[str, Any] | None) -> bool:
    return str((block or {}).get("markdown") or "").strip().lower() == "use vocabulary in writing"


def is_vocabulary_review_context(blocks: list[dict[str, Any]], index: int) -> bool:
    start = max(0, index - 18)
    end = min(len(blocks), index + 3)
    context = "\n".join(str(blocks[pos].get("markdown") or "") for pos in range(start, end)).lower()
    return "vocabulary review" in context or "\nvocabulary\n" in f"\n{context}\n"


def paired_vocabulary_child_ids(blocks: list[dict[str, Any]], index: int) -> tuple[str, list[str]]:
    block = blocks[index]
    markdown = str(block.get("markdown") or "")
    if block.get("type") != "table" or block.get("subtype") != "table_question":
        return "", []
    if not is_vocabulary_review_context(blocks, index):
        return "", []

    if is_definition_example_table(markdown):
        cursor = index - 1
        word_ids: list[str] = []
        while cursor >= 0 and is_short_word_bank_block(blocks[cursor]):
            word_ids.append(str(blocks[cursor].get("id") or ""))
            cursor -= 1
        word_ids.reverse()
        if cursor >= 0 and is_vocabulary_label_block(blocks[cursor]) and word_ids:
            child_ids = [*word_ids, str(block.get("id") or "")]
            next_block = blocks[index + 1] if index + 1 < len(blocks) else None
            if is_use_vocabulary_followup(next_block):
                child_ids.append(str(next_block.get("id") or ""))
            return "word_bank_paragraphs_plus_definition_table", child_ids

    if table_first_cell(markdown) == "definition" and index > 0:
        previous = blocks[index - 1]
        if previous.get("type") == "table" and is_vocabulary_word_table(str(previous.get("markdown") or "")):
            child_ids = [str(previous.get("id") or ""), str(block.get("id") or "")]
            if index > 1:
                before_pair = blocks[index - 2]
                before_text = str(before_pair.get("markdown") or "").strip().lower()
                if before_pair.get("type") == "paragraph" and "connect each vocabulary word" in before_text:
                    child_ids.insert(0, str(before_pair.get("id") or ""))
            next_block = blocks[index + 1] if index + 1 < len(blocks) else None
            if is_use_vocabulary_followup(next_block):
                child_ids.append(str(next_block.get("id") or ""))
            return "two_table_vocabulary_definition_pair", child_ids

    return "", []


def apply_paired_vocabulary_groups(blocks: list[dict[str, Any]], relations: list[dict[str, Any]]) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    grouped_ids: set[str] = set()
    by_id = {str(block.get("id") or ""): block for block in blocks}
    for index, block in enumerate(blocks):
        layout_kind, child_ids = paired_vocabulary_child_ids(blocks, index)
        child_ids = [child_id for child_id in child_ids if child_id and child_id in by_id]
        if not layout_kind or not child_ids:
            continue
        if any(child_id in grouped_ids for child_id in child_ids):
            continue
        group_id = f"paired-vocab:{block.get('id')}"
        table_ids = [child_id for child_id in child_ids if by_id[child_id].get("type") == "table"]
        group = {
            "id": group_id,
            "layout": layout_kind,
            "children": child_ids,
            "table_ids": table_ids,
            "line_start": by_id[child_ids[0]].get("line_start"),
            "line_end": by_id[child_ids[-1]].get("line_end") or by_id[child_ids[-1]].get("line_start"),
            "heading_path": by_id[child_ids[0]].get("heading_path") or [],
        }
        groups.append(group)
        grouped_ids.update(child_ids)
        for child_id in child_ids:
            child = by_id[child_id]
            child["parent_id"] = group_id
            child.setdefault("layout", {})["paired_vocabulary_child"] = True
            child.setdefault("layout", {})["keep_together"] = True
        first = by_id[child_ids[0]]
        first.setdefault("layout", {})["paired_vocabulary_group"] = {
            "id": group_id,
            "layout": layout_kind,
            "children": child_ids,
            "table_ids": table_ids,
        }
        relations.append({"from": group_id, "type": "paired_vocabulary_contains", "to": child_ids})

    return {
        "schema": "luceon-standard-paired-vocabulary-rule/v1",
        "policy": "generic_vocabulary_review_pattern_no_material_id_or_page_rules",
        "group_count": len(groups),
        "patched_table_count": sum(len(group["table_ids"]) for group in groups),
        "layout_counts": dict(Counter(str(group["layout"]) for group in groups)),
        "groups": groups,
    }


def apply_paired_vocabulary_relation_delta(relation_summary: dict[str, Any], paired_summary: dict[str, Any]) -> dict[str, Any]:
    updated = dict(relation_summary)
    table_count = int(paired_summary.get("patched_table_count") or 0)
    group_count = int(paired_summary.get("group_count") or 0)
    if table_count:
        updated["question_groups"] = int(updated.get("question_groups") or 0) + group_count
        updated["parented_table_questions"] = int(updated.get("parented_table_questions") or 0) + table_count
        updated["orphan_table_questions"] = max(0, int(updated.get("orphan_table_questions") or 0) - table_count)
    return updated


def normalized_block_text(block: dict[str, Any] | None) -> str:
    return re.sub(r"\s+", " ", str((block or {}).get("markdown") or "")).strip()


def classify_workbook_table_attachment_family(
    block: dict[str, Any],
    previous_block: dict[str, Any] | None,
    next_block: dict[str, Any] | None,
) -> tuple[str, str]:
    table_text = normalized_block_text(block)
    previous_text = normalized_block_text(previous_block)
    next_text = normalized_block_text(next_block)
    heading = " > ".join(str(item) for item in block.get("heading_path") or [])
    table_lower = table_text.lower()
    context_lower = f"{previous_text} {next_text}".lower()

    if next_block and next_block.get("type") == "table":
        return "", ""
    if "Topic Review" in heading and "Vocabulary Term" in table_text and next_text == "Use Vocabulary in Writing":
        return "single_table_vocabulary_review", "topic_review_vocabulary_table_before_use_vocabulary_followup"
    if "scatter plot" in context_lower and "temperature" in table_lower and "tickets sold" in table_lower:
        return "exercise_scatter_plot_data_table", "scatter_plot_prompt_with_temperature_ticket_data_table"
    if "scatter plot" in context_lower and "distance" in table_lower and "airfare" in table_lower:
        return "exercise_scatter_plot_data_table", "scatter_plot_prompt_with_distance_airfare_data_table"
    if "bar diagram" in context_lower:
        return "example_bar_diagram_table_model", "bar_diagram_instruction_with_model_table"
    if "frequency table" in context_lower and "digital" in table_lower and "print" in table_lower:
        return "example_frequency_table_explanation", "frequency_table_explanation_with_categorical_data_table"
    if (
        "mean" in table_lower
        and ("mad" in table_lower or "absolute deviation" in table_lower)
        and (
            "computes the mean" in previous_text.lower()
            or "you can use dot plots" in previous_text.lower()
            or "measures of center and variability" in previous_text.lower()
        )
    ):
        return "example_statistics_summary_table", "mean_mad_summary_table_in_statistics_explanation"
    if "look for a pattern" in previous_text.lower() and "exponent form" in table_lower:
        return "example_pattern_or_rate_table", "pattern_prompt_with_exponent_table"
    if "constant of proportionality" in next_text.lower() and "distance" in table_lower and "time" in table_lower:
        return "example_pattern_or_rate_table", "rate_table_before_constant_of_proportionality_step"
    return "", ""


def apply_workbook_table_attachment_groups(
    blocks: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    for index, block in enumerate(blocks):
        if block.get("type") != "table" or block.get("subtype") != "table_question" or block.get("parent_id"):
            continue
        previous_block = blocks[index - 1] if index > 0 else None
        next_block = blocks[index + 1] if index + 1 < len(blocks) else None
        family, reason = classify_workbook_table_attachment_family(block, previous_block, next_block)
        if not family:
            continue
        group_id = f"workbook-table-attachment:{block.get('id')}"
        block["parent_id"] = group_id
        block.setdefault("layout", {})["workbook_table_attachment_family"] = family
        block.setdefault("layout", {})["keep_together"] = True
        relations.append({"from": group_id, "type": "workbook_table_attachment_contains", "to": [block.get("id")]})
        group = {
            "id": group_id,
            "family": family,
            "reason": reason,
            "children": [block.get("id")],
            "table_ids": [block.get("id")],
            "line_start": block.get("line_start"),
            "line_end": block.get("line_end") or block.get("line_start"),
            "heading_path": block.get("heading_path") or [],
        }
        groups.append(group)
        family_counts[family] += 1
    return {
        "schema": "luceon-standard-workbook-table-attachment-rule/v1",
        "policy": "narrow_source_context_families_no_material_id_or_page_rules",
        "group_count": len(groups),
        "patched_table_count": sum(len(group["table_ids"]) for group in groups),
        "family_counts": dict(family_counts),
        "groups": groups,
    }


def apply_workbook_table_attachment_relation_delta(
    relation_summary: dict[str, Any],
    table_attachment_summary: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(relation_summary)
    table_count = int(table_attachment_summary.get("patched_table_count") or 0)
    group_count = int(table_attachment_summary.get("group_count") or 0)
    if table_count:
        updated["question_groups"] = int(updated.get("question_groups") or 0) + group_count
        updated["parented_table_questions"] = int(updated.get("parented_table_questions") or 0) + table_count
        updated["orphan_table_questions"] = max(0, int(updated.get("orphan_table_questions") or 0) - table_count)
    return updated


def apply_workbook_virtual_question_groups(
    blocks: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    active_group: dict[str, Any] | None = None
    by_group_id: dict[str, dict[str, Any]] = {}
    starter_counts: Counter[str] = Counter()
    stop_counts: Counter[str] = Counter()
    grouped_question_count = 0

    for block in blocks:
        block_type = str(block.get("type") or "")
        block_id = str(block.get("id") or "")
        if block_type in {"unit_opener", "section", "reading_passage"}:
            active_group = None
            stop_counts["hard_section_reset"] += 1
            continue

        text = normalized_block_text(block)
        starter_kind = ""
        if block_type == "paragraph":
            norm = text.strip("* ").lower()
            if norm in WORKBOOK_SECTION_LABELS:
                starter_kind = "section_label"
            elif WORKBOOK_INSTRUCTION_START_RE.match(text):
                starter_kind = "instruction_paragraph"
            elif text.endswith(":") and len(text) <= 120:
                starter_kind = "colon_label"

        if starter_kind:
            group_id = f"workbook-virtual-group:{block_id}"
            active_group = {
                "id": group_id,
                "starter_block_id": block_id,
                "starter_kind": starter_kind,
                "children": [],
                "line_start": block.get("line_start"),
                "line_end": block.get("line_end") or block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "text": text[:300],
            }
            groups.append(active_group)
            by_group_id[group_id] = active_group
            block.setdefault("layout", {})["workbook_virtual_group_starter"] = starter_kind
            starter_counts[starter_kind] += 1
            continue

        if block_type == "paragraph":
            if len(text) > 180 and not WORKBOOK_INSTRUCTION_START_RE.match(text):
                active_group = None
                stop_counts["long_paragraph_reset"] += 1
            continue

        if block_type == "question" and active_group and not block.get("parent_id"):
            block["parent_id"] = active_group["id"]
            block.setdefault("layout", {})["workbook_virtual_group_child"] = True
            active_group["children"].append(block_id)
            active_group["line_end"] = block.get("line_end") or block.get("line_start")
            relations.append({"from": active_group["id"], "type": "contains_question", "to": block_id})
            grouped_question_count += 1

    materialized_groups = [group for group in groups if group.get("children")]
    for group in materialized_groups:
        starter = next((block for block in blocks if str(block.get("id") or "") == group["starter_block_id"]), None)
        if starter:
            starter.setdefault("layout", {})["workbook_virtual_group"] = {
                "id": group["id"],
                "starter_kind": group["starter_kind"],
                "children": group["children"],
            }
    return {
        "schema": "luceon-standard-workbook-virtual-question-group-rule/v1",
        "policy": "guarded_virtual_group_long_paragraph_reset_questions_only_no_table_attachment",
        "group_count": len(materialized_groups),
        "grouped_question_count": grouped_question_count,
        "starter_counts": dict(starter_counts),
        "stop_counts": dict(stop_counts),
        "groups": materialized_groups,
    }


def apply_workbook_virtual_question_group_relation_delta(
    relation_summary: dict[str, Any],
    virtual_group_summary: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(relation_summary)
    question_count = int(virtual_group_summary.get("grouped_question_count") or 0)
    group_count = int(virtual_group_summary.get("group_count") or 0)
    if question_count:
        updated["question_groups"] = int(updated.get("question_groups") or 0) + group_count
        updated["grouped_questions"] = int(updated.get("grouped_questions") or 0) + question_count
        updated["ungrouped_questions"] = max(0, int(updated.get("ungrouped_questions") or 0) - question_count)
    return updated


NUMBERED_QUESTION_START_RE = re.compile(r"^(\d{1,3})\.\s+")


def numbered_question_index(block: dict[str, Any]) -> int | None:
    match = NUMBERED_QUESTION_START_RE.match(normalized_block_text(block))
    if not match:
        return None
    return int(match.group(1))


def is_short_option_fragment(block: dict[str, Any] | None) -> bool:
    if not block or block.get("type") != "paragraph":
        return False
    text = normalized_block_text(block)
    return len(text) <= 120 and bool(re.match(r"^(?:[A-D©⑭]|\([A-D]\))\s+", text))


def find_recent_question_anchor(
    blocks: list[dict[str, Any]],
    index: int,
    heading_path: list[Any],
) -> dict[str, Any] | None:
    for cursor in range(index - 1, max(-1, index - 8), -1):
        candidate = blocks[cursor]
        if candidate.get("heading_path") != heading_path:
            break
        if candidate.get("type") in {"unit_opener", "section", "reading_passage"}:
            break
        if candidate.get("type") == "paragraph":
            text = normalized_block_text(candidate)
            if len(text) > 180 and not is_short_option_fragment(candidate):
                break
        if candidate.get("type") == "question" and numbered_question_index(candidate) is not None:
            return candidate
    return None


def apply_workbook_question_continuation_groups(
    blocks: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    by_group_id: dict[str, dict[str, Any]] = {}
    grouped_question_count = 0
    trigger_counts: Counter[str] = Counter()

    for index, block in enumerate(blocks):
        if block.get("type") != "question" or block.get("parent_id"):
            continue
        current_number = numbered_question_index(block)
        if current_number is None:
            continue
        heading_path = block.get("heading_path") or []
        previous = blocks[index - 1] if index > 0 else None
        anchor = find_recent_question_anchor(blocks, index, heading_path)
        if not anchor:
            continue
        anchor_number = numbered_question_index(anchor)
        if anchor_number is None or current_number <= anchor_number or current_number - anchor_number > 2:
            continue
        trigger = "question_run_continuation"
        if previous and previous.get("type") == "captioned_figure":
            trigger = "image_interrupted_question_run"
        elif is_short_option_fragment(previous):
            trigger = "short_option_interrupted_question_run"
        elif "3-Act Mathematical Modeling" in " > ".join(str(item) for item in heading_path):
            trigger = "three_act_question_continuation"
        group_id = str(anchor.get("parent_id") or "")
        if not group_id:
            group_id = f"workbook-question-continuation:{anchor.get('id')}"
            anchor["parent_id"] = group_id
            anchor.setdefault("layout", {})["workbook_question_continuation_child"] = True
            group = {
                "id": group_id,
                "anchor_block_id": anchor.get("id"),
                "trigger": "anchor_question",
                "children": [anchor.get("id")],
                "line_start": anchor.get("line_start"),
                "line_end": anchor.get("line_end") or anchor.get("line_start"),
                "heading_path": heading_path,
            }
            groups.append(group)
            by_group_id[group_id] = group
            relations.append({"from": group_id, "type": "contains_question", "to": anchor.get("id")})
            grouped_question_count += 1
        group = by_group_id.get(group_id)
        if not group:
            group = {
                "id": group_id,
                "anchor_block_id": anchor.get("id"),
                "trigger": "existing_parent_group",
                "children": [],
                "line_start": anchor.get("line_start"),
                "line_end": anchor.get("line_end") or anchor.get("line_start"),
                "heading_path": heading_path,
            }
            groups.append(group)
            by_group_id[group_id] = group
        block["parent_id"] = group_id
        block.setdefault("layout", {})["workbook_question_continuation_child"] = True
        group.setdefault("children", []).append(block.get("id"))
        group["line_end"] = block.get("line_end") or block.get("line_start")
        relations.append({"from": group_id, "type": "contains_question", "to": block.get("id")})
        grouped_question_count += 1
        trigger_counts[trigger] += 1

    materialized_groups = [group for group in groups if group.get("children")]
    return {
        "schema": "luceon-standard-workbook-question-continuation-rule/v1",
        "policy": "numbered_question_continuation_same_heading_with_short_or_image_interruptions",
        "group_count": len(materialized_groups),
        "grouped_question_count": grouped_question_count,
        "trigger_counts": dict(trigger_counts),
        "groups": materialized_groups,
    }


def apply_workbook_question_continuation_relation_delta(
    relation_summary: dict[str, Any],
    continuation_summary: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(relation_summary)
    question_count = int(continuation_summary.get("grouped_question_count") or 0)
    group_count = int(continuation_summary.get("group_count") or 0)
    if question_count:
        updated["question_groups"] = int(updated.get("question_groups") or 0) + group_count
        updated["grouped_questions"] = int(updated.get("grouped_questions") or 0) + question_count
        updated["ungrouped_questions"] = max(0, int(updated.get("ungrouped_questions") or 0) - question_count)
    return updated


def looks_like_math(candidate: str) -> bool:
    compact = candidate.strip()
    if len(compact) < 2:
        return False
    without_blanks = re.sub(r"(?:\\_)+|_{2,}", "", compact).strip()
    if not without_blanks:
        return False
    if "\\" in compact:
        return bool(re.search(r"\\[A-Za-z]+", compact))
    if "^" in compact or "_" in compact:
        return bool(re.search(r"[A-Za-z0-9]", compact))
    if "=" in compact and re.search(r"[A-Za-z]", compact):
        return True
    return False


def auto_wrap_bare_math(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        char = text[cursor]
        previous = text[cursor - 1] if cursor > 0 else ""
        can_start = (
            char == "\\"
            or char == "("
            or char.isdigit()
            or ("A" <= char <= "Z")
            or ("a" <= char <= "z")
        )
        if not can_start or (previous and (previous.isalnum() or previous == "\\")):
            parts.append(char)
            cursor += 1
            continue

        end = cursor
        while end < length:
            current = text[end]
            if current in MATH_BREAK_CHARS:
                break
            if current.isascii() and (current.isalnum() or current in MATH_ALLOWED_CHARS):
                end += 1
                continue
            break

        candidate = text[cursor:end].strip()
        if looks_like_math(candidate):
            leading = text[cursor:end][: len(text[cursor:end]) - len(text[cursor:end].lstrip())]
            trailing = text[cursor:end][len(text[cursor:end].rstrip()) :]
            raw_formula = candidate.rstrip(".,")
            formula = normalize_latex_answer_blanks(raw_formula)
            suffix = candidate[len(raw_formula) :]
            parts.append(f"{leading}\\({formula}\\){suffix}{trailing}")
            cursor = end
            continue

        parts.append(char)
        cursor += 1
    return "".join(parts)


def render_inline_markdown(text: str) -> str:
    placeholders: list[str] = []
    html_placeholders: list[str] = []

    def keep_inline_math(match: re.Match[str]) -> str:
        placeholders.append(f"\\({normalize_latex_answer_blanks(match.group(1).strip())}\\)")
        return f"@@MATH{len(placeholders) - 1}@@"

    def keep_answer_blank(match: re.Match[str]) -> str:
        html_placeholders.append('<span class="answer-line"></span>')
        return f"@@HTML{len(html_placeholders) - 1}@@"

    protected = INLINE_DOLLAR_RE.sub(keep_inline_math, text)
    protected = auto_wrap_bare_math(protected)
    protected = re.sub(r"(?:\\_)+|_{2,}", keep_answer_blank, protected)
    escaped = html.escape(protected)
    for index, value in enumerate(placeholders):
        escaped = escaped.replace(f"@@MATH{index}@@", html.escape(value))
    for index, value in enumerate(html_placeholders):
        escaped = escaped.replace(f"@@HTML{index}@@", value)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = escaped.replace("\\_\\_\\_\\_", "____")
    return escaped


def render_table_cell_text(text: str) -> str:
    placeholder = "@@ANSWER_LINE@@"
    protected = re.sub(r"(?:\\_)+|_{2,}", placeholder, text)
    escaped = html.escape(protected)
    return escaped.replace(placeholder, '<span class="answer-line"></span>')


PAIRED_VOCAB_SOURCE_BLANK = "@@SOURCE_BLANK_BOX@@"


def reconstruct_paired_vocabulary_blank_text(text: str) -> tuple[str, list[str]]:
    rules: list[tuple[str, str, str]] = [
        ("leading_you_when", r"^(\s*\d+\.\s+You)\s+(when\b)", rf"\1 {PAIRED_VOCAB_SOURCE_BLANK} \2"),
        ("leading_a_is", r"^(\s*\d+\.\s+A)\s+(is\b)", rf"\1 {PAIRED_VOCAB_SOURCE_BLANK} \2"),
        ("leading_the_states", r"^(\s*\d+\.\s+The)\s+(states\b)", rf"\1 {PAIRED_VOCAB_SOURCE_BLANK} \2"),
        ("use_the_to", r"\b(use the)\s+(to\b)", rf"\1 {PAIRED_VOCAB_SOURCE_BLANK} \2"),
        ("terminal_is_an", r"\b(is a\(n\))\s*\.$", rf"\1 {PAIRED_VOCAB_SOURCE_BLANK}."),
    ]
    applied: list[str] = []
    result = text
    for rule_id, pattern, replacement in rules:
        updated, count = re.subn(pattern, replacement, result, flags=re.I)
        if count:
            applied.append(rule_id)
            result = updated
    return result, applied


def render_paired_vocabulary_cell_text(text: str) -> str:
    reconstructed, _rules = reconstruct_paired_vocabulary_blank_text(text)
    rendered = render_table_cell_text(reconstructed)
    return rendered.replace(PAIRED_VOCAB_SOURCE_BLANK, '<span class="answer-line answer-line-source"></span>')


def render_table_with_answer_spaces(table_html: str) -> str:
    def render_cell(match: re.Match[str]) -> str:
        raw = match.group(1)
        text = strip_html_cell_text(raw)
        if not text:
            return '<td class="answer-cell"><div class="answer-space"></div></td>'
        return f"<td>{render_paired_vocabulary_cell_text(text)}</td>"

    return TD_RE.sub(render_cell, table_html)


def render_paired_vocabulary_group(group: dict[str, Any], blocks_by_id: dict[str, dict[str, Any]]) -> str:
    child_ids = [str(child_id) for child_id in group.get("children") or []]
    child_blocks = [blocks_by_id[child_id] for child_id in child_ids if child_id in blocks_by_id]
    layout_kind = str(group.get("layout") or "")
    tables = [block for block in child_blocks if block.get("type") == "table"]
    word_blocks = [
        block
        for block in child_blocks
        if block.get("type") in {"paragraph", "note"} and not is_use_vocabulary_followup(block)
    ]
    follow_ups = [block for block in child_blocks if is_use_vocabulary_followup(block)]
    classes = f"block block-question_group paired-vocab-group paired-vocab-{safe_slug(layout_kind)}"
    if layout_kind == "two_table_vocabulary_definition_pair" and len(tables) >= 2:
        body = (
            '<div class="paired-vocab-grid">'
            f'<div class="paired-vocab-panel">{render_table_with_answer_spaces(str(tables[0].get("markdown") or ""))}</div>'
            f'<div class="paired-vocab-panel">{render_table_with_answer_spaces(str(tables[1].get("markdown") or ""))}</div>'
            "</div>"
        )
    else:
        words = [
            str(block.get("markdown") or "").strip()
            for block in word_blocks
            if str(block.get("markdown") or "").strip() and str(block.get("markdown") or "").strip().lower() != "vocabulary"
        ]
        word_bank = (
            '<div class="paired-vocab-word-bank">'
            + "".join(f"<span>{html.escape(word)}</span>" for word in words)
            + "</div>"
            if words
            else ""
        )
        table = render_table_with_answer_spaces(str(tables[-1].get("markdown") or "")) if tables else ""
        body = word_bank + f'<div class="paired-vocab-table">{table}</div>'
    follow = "".join(f'<p class="paired-vocab-follow">{html.escape(str(block.get("markdown") or ""))}</p>' for block in follow_ups)
    return f'<section id="{html.escape(str(group.get("id") or ""))}" class="{classes}">{body}{follow}</section>'


def render_block(block: dict[str, Any]) -> str:
    markdown = block.get("markdown") or ""
    block_type = block.get("type") or "paragraph"
    classes = ["block", f"block-{block_type}"]
    image_relation = block.get("image_relation") if isinstance(block.get("image_relation"), dict) else {}
    image_relation_category = safe_slug(str(image_relation.get("category") or "")).lower() if image_relation else ""
    image_relation_action = safe_slug(str(image_relation.get("action") or "")).lower() if image_relation else ""
    if image_relation_category:
        classes.append(f"image-relation-{image_relation_category}")
    if image_relation_action:
        classes.append(f"image-action-{image_relation_action}")
    if block.get("layout", {}).get("keep_together"):
        classes.append("keep-together")
    if block.get("layout", {}).get("layout_hint") == "two_column":
        classes.append("two-column")
    cls = " ".join(classes)

    heading = HEADING_RE.match(markdown)
    if heading:
        level = min(len(heading.group(1)) + 1, 6)
        return f'<h{level} id="{html.escape(block["id"])}" class="{cls}">{render_inline_markdown(heading.group(2))}</h{level}>'

    image_match = IMAGE_RE.search(markdown)
    if image_match:
        parts: list[str] = []
        cursor = 0
        for match in IMAGE_RE.finditer(markdown):
            before = markdown[cursor : match.start()].strip()
            alt = match.group(1).strip() or "image"
            src = match.group(2).strip()
            if before:
                parts.append(f'<figcaption>{render_inline_markdown(before)}</figcaption>')
            parts.append(f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy">')
            after_alt_caption = alt if alt != "image" else ""
            if after_alt_caption:
                parts.append(f'<figcaption>{render_inline_markdown(after_alt_caption)}</figcaption>')
            cursor = match.end()
        after = markdown[cursor:].strip()
        if after:
            parts.append(f'<figcaption>{render_inline_markdown(after)}</figcaption>')
        return f'<figure id="{html.escape(block["id"])}" class="{cls}">{"".join(parts)}</figure>'

    if TABLE_RE.match(markdown):
        table_html = reflow_grammar_paradigm_table(markdown)
        return f'<div id="{html.escape(block["id"])}" class="{cls} table-wrap">{table_html}</div>'

    if block_type == "formula" or DISPLAY_MATH_RE.match(markdown.strip()):
        return f'<div id="{html.escape(block["id"])}" class="{cls} math-display">\\[{html.escape(strip_display_math(markdown))}\\]</div>'

    tag = "p"
    if block_type in {"before_you_read", "comprehension_questions", "vocabulary_practice", "explore_more", "review_unit"}:
        tag = "h4"
    elif block_type in {"question_group", "question", "option"}:
        tag = "div"
    elif block_type in {"caption"}:
        tag = "figcaption"
    return f'<{tag} id="{html.escape(block["id"])}" class="{cls}">{render_inline_markdown(markdown)}</{tag}>'


def render_html(document: dict[str, Any], source_title: str) -> str:
    blocks = document["blocks"]
    blocks_by_id = {str(block.get("id") or ""): block for block in blocks}
    skip_ids: set[str] = set()
    body_parts: list[str] = []
    for block in blocks:
        block_id = str(block.get("id") or "")
        group = (block.get("layout") or {}).get("paired_vocabulary_group")
        if isinstance(group, dict):
            body_parts.append(render_paired_vocabulary_group(group, blocks_by_id))
            skip_ids.update(str(child_id) for child_id in group.get("children") or [])
            continue
        if block_id in skip_ids:
            continue
        body_parts.append(render_block(block))
    body = "\n".join(body_parts)
    outline_items = "\n".join(
        f'<li class="level-{item["level"]}">{html.escape(item["title"])}</li>' for item in document["outline"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(source_title)}</title>
  <style>
    @page {{ size: A4; margin: 16mm 15mm 18mm; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: #111; font-family: Georgia, "Times New Roman", serif; font-size: 10.5pt; line-height: 1.46; }}
    main {{ max-width: 178mm; margin: 0 auto; }}
    h1, h2, h3, h4 {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.18; margin: 0 0 8pt; break-after: avoid; }}
    h2.block-unit_opener {{ break-before: page; padding-top: 4mm; }}
    h4 {{ margin-top: 10pt; border-top: 0.5pt solid #aaa; padding-top: 5pt; }}
    p, .block {{ margin: 0 0 6pt; }}
    .keep-together, figure, table, .table-wrap {{ break-inside: avoid; page-break-inside: avoid; }}
    .two-column.block-reading_passage:not(h4):not(h3) {{ column-count: 2; column-gap: 8mm; text-align: left; }}
    figure {{ margin: 8pt 0 10pt; text-align: center; }}
    figure img {{ max-width: 100%; max-height: 120mm; object-fit: contain; }}
    figure.image-relation-helper_icon {{ display: inline-flex; align-items: center; margin: 0 2.5mm 2pt 0; text-align: left; vertical-align: middle; break-inside: avoid; page-break-inside: avoid; }}
    figure.image-relation-helper_icon img {{ width: auto; max-width: 13mm; max-height: 14mm; object-fit: contain; border: 0; }}
    figure.image-relation-helper_icon figcaption {{ display: none; }}
    figcaption {{ font-size: 9pt; line-height: 1.3; margin-top: 3pt; color: #333; text-align: left; }}
    .block-question_group, .block-question, .block-option {{ font-family: Arial, Helvetica, sans-serif; }}
    .block-question {{ margin-top: 5pt; }}
    .block-option {{ margin-left: 12pt; }}
    .block-vocabulary_box, .block-note {{ border: 0.5pt solid #999; padding: 5pt 7pt; margin: 7pt 0; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8pt 0; }}
    td, th {{ border: 0.5pt solid #777; padding: 3pt 5pt; vertical-align: top; }}
    .toc {{ font-family: Arial, Helvetica, sans-serif; margin-bottom: 14pt; }}
    .toc ol {{ margin: 0; padding-left: 18pt; column-count: 2; column-gap: 10mm; }}
    .toc li {{ break-inside: avoid; }}
    .toc .level-2 {{ margin-left: 10pt; }}
    .toc .level-3 {{ margin-left: 20pt; color: #333; }}
    .math-display, mjx-container[jax="SVG"][display="true"] {{ overflow-x: auto; overflow-y: hidden; max-width: 100%; }}
    mjx-container {{ break-inside: avoid; }}
    .answer-line {{ display: inline-block; width: 16mm; border-bottom: 0.8pt solid #111; vertical-align: -0.1em; margin: 0 1.5mm; }}
    .paired-vocab-group {{ border: 0.5pt solid #999; padding: 6pt 7pt; margin: 8pt 0; break-inside: avoid; page-break-inside: avoid; }}
    .paired-vocab-grid {{ display: grid; grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.25fr); gap: 7pt; align-items: start; }}
    .paired-vocab-word-bank {{ border: 0.5pt solid #9a7b93; padding: 4pt 6pt; margin-bottom: 6pt; display: flex; flex-wrap: wrap; gap: 3pt 10pt; }}
    .paired-vocab-word-bank span {{ white-space: nowrap; }}
    .paired-vocab-group table {{ margin: 0; }}
    .answer-cell {{ min-height: 18pt; }}
    .answer-space {{ display: block; min-height: 16pt; border-bottom: 0.8pt solid #111; margin: 3pt 1pt; }}
    .paired-vocab-follow {{ margin-top: 5pt; font-weight: 600; }}
  </style>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['\\\\(', '\\\\)']],
        displayMath: [['\\\\[', '\\\\]']],
        processEscapes: true,
        tags: 'ams'
      }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
  <main>
    <section class="toc">
      <h1>{html.escape(source_title)}</h1>
      <ol>{outline_items}</ol>
    </section>
    {body}
  </main>
</body>
</html>
"""


def build_standard_md(blocks: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(block.get("markdown") or "").strip() for block in blocks if str(block.get("markdown") or "").strip()) + "\n"


def copy_referenced_images(clean_dir: Path, out_dir: Path, refs: list[str]) -> list[str]:
    missing: list[str] = []
    image_dir = out_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for ref in sorted(set(refs)):
        src_candidates = [
            clean_dir / ref,
            clean_dir / "raw_input" / ref,
            clean_dir.parent / "raw_input" / ref,
        ]
        src = next((candidate for candidate in src_candidates if candidate.exists()), src_candidates[0])
        dst = out_dir / ref
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dst)
        else:
            missing.append(ref)
    return missing


def image_dimensions(path: Path) -> dict[str, int] | None:
    try:
        data = path.read_bytes()[:65536]
    except Exception:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return {"width": int(width), "height": int(height), "area": int(width * height)}
    if not data.startswith(b"\xff\xd8"):
        return None
    cursor = 2
    sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
    while cursor + 9 < len(data):
        while cursor < len(data) and data[cursor] == 0xFF:
            cursor += 1
        if cursor >= len(data):
            break
        marker = data[cursor]
        cursor += 1
        if marker in {0xD8, 0xD9}:
            continue
        if cursor + 2 > len(data):
            break
        length = struct.unpack(">H", data[cursor : cursor + 2])[0]
        if length < 2 or cursor + length > len(data):
            break
        if marker in sof_markers and cursor + 7 < len(data):
            height, width = struct.unpack(">HH", data[cursor + 3 : cursor + 7])
            return {"width": int(width), "height": int(height), "area": int(width * height)}
        cursor += length
    return None


def neighboring_block(blocks: list[dict[str, Any]], index: int, offset: int) -> dict[str, Any] | None:
    cursor = index + offset
    while 0 <= cursor < len(blocks):
        candidate = blocks[cursor]
        if candidate.get("type") not in {"unit_opener", "section"}:
            return candidate
        cursor += offset
    return None


def classify_workbook_figure(
    block: dict[str, Any],
    clean_dir: Path,
    previous_block: dict[str, Any] | None,
    next_block: dict[str, Any] | None,
    parent_block: dict[str, Any] | None,
) -> dict[str, Any]:
    image_ref = str((block.get("image_refs") or [""])[0])
    dims = image_dimensions(clean_dir / image_ref) if image_ref else None
    area = int(dims.get("area") or 0) if dims else 0
    width = int(dims.get("width") or 0) if dims else 0
    height = int(dims.get("height") or 0) if dims else 0
    max_side = max(width, height)
    is_small = bool(dims and (area <= 20000 or max_side <= 160))
    previous_text = str(previous_block.get("markdown") or "") if previous_block else ""
    next_text = str(next_block.get("markdown") or "") if next_block else ""
    context_text = f"{previous_text}\n{next_text}"
    parent_type = str(parent_block.get("type") or "") if parent_block else ""

    if is_small:
        category = "helper_icon"
        action = "compress_keep_near"
        requires_source_visual_check = False
    elif parent_type in {"question", "question_group"} or ANSWER_BLANK_RE.search(context_text):
        category = "exercise_key_figure"
        action = "keep_with_exercise"
        requires_source_visual_check = True
    elif EXPLANATION_SIGNAL_RE.search(context_text) or block.get("heading_path"):
        category = "explanation_key_figure"
        action = "keep_with_explanation"
        requires_source_visual_check = True
    else:
        category = "decorative"
        action = "compress_or_keep_low_priority"
        requires_source_visual_check = False

    if not dims:
        category = "needs_dimension_review"
        action = "inspect_image_dimensions"
        requires_source_visual_check = True

    return {
        "block_id": block["id"],
        "image": image_ref,
        "category": category,
        "action": action,
        "requires_source_visual_check": requires_source_visual_check,
        "dimensions": dims or {},
        "parent_id": block.get("parent_id", ""),
        "parent_type": parent_type,
        "previous_block": {"id": previous_block.get("id"), "type": previous_block.get("type")} if previous_block else {},
        "next_block": {"id": next_block.get("id"), "type": next_block.get("type")} if next_block else {},
        "heading_path": block.get("heading_path", []),
    }


def build_image_relation_report(profile: str, blocks: list[dict[str, Any]], clean_dir: Path) -> dict[str, Any]:
    if profile not in WORKBOOK_PROFILES:
        return {
            "schema": "luceon-standard-image-relation-report/v1",
            "profile": profile,
            "items": [],
            "count": 0,
            "category_counts": {},
            "action_counts": {},
            "source_visual_check_count": 0,
        }

    by_id = {str(block["id"]): block for block in blocks}
    items: list[dict[str, Any]] = []
    for index, block in enumerate(blocks):
        if block.get("type") != "captioned_figure":
            continue
        previous_block = neighboring_block(blocks, index, -1)
        next_block = neighboring_block(blocks, index, 1)
        parent_id = str(block.get("parent_id") or "")
        parent_block = by_id.get(parent_id)
        item = classify_workbook_figure(block, clean_dir, previous_block, next_block, parent_block)
        block["image_relation"] = {
            "category": item["category"],
            "action": item["action"],
            "requires_source_visual_check": item["requires_source_visual_check"],
        }
        items.append(item)

    category_counts = Counter(item["category"] for item in items)
    action_counts = Counter(item["action"] for item in items)
    return {
        "schema": "luceon-standard-image-relation-report/v1",
        "profile": profile,
        "items": items,
        "count": len(items),
        "category_counts": dict(category_counts),
        "action_counts": dict(action_counts),
        "source_visual_check_count": sum(1 for item in items if item["requires_source_visual_check"]),
    }


def resolve_local_source_root(raw_dir: Path | None, source_root: str) -> Path | None:
    candidates: list[Path] = []
    if source_root:
        candidates.append(Path(source_root))
        candidates.append(Path(source_root.replace("/data/pipeline-work", "runtime/backend/pipeline-work")))
        candidates.append(Path.cwd() / source_root.lstrip("/"))
        candidates.append(Path.cwd() / source_root.replace("/data/pipeline-work", "runtime/backend/pipeline-work").lstrip("/"))
    if raw_dir:
        candidates.append(raw_dir)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_content_image_evidence(raw_dir: Path | None) -> dict[str, dict[str, Any]]:
    if not raw_dir:
        return {}
    manifest = read_json(raw_dir / "manifest.json")
    content_file = str(manifest.get("content_file") or "").strip()
    source_root = resolve_local_source_root(raw_dir, str(manifest.get("source_root") or ""))
    if not content_file or not source_root:
        return {}
    content_path = source_root / content_file
    if not content_path.exists():
        return {}
    try:
        rows = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    evidence: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        image_ref = str(row.get("img_path") or row.get("image_path") or "").strip()
        if not image_ref:
            continue
        evidence[image_ref] = {
            "page_idx": row.get("page_idx"),
            "page_number": int(row["page_idx"]) + 1 if row.get("page_idx") is not None else None,
            "bbox": row.get("bbox") or [],
            "content": row.get("content") or "",
            "sub_type": row.get("sub_type") or "",
            "raw_type": row.get("type") or "",
        }
    return evidence


def load_content_table_evidence(raw_dir: Path | None) -> dict[str, list[dict[str, Any]]]:
    if not raw_dir:
        return {}
    manifest = read_json(raw_dir / "manifest.json")
    content_file = str(manifest.get("content_file") or "").strip()
    source_root = resolve_local_source_root(raw_dir, str(manifest.get("source_root") or ""))
    if not content_file or not source_root:
        return {}
    content_path = source_root / content_file
    if not content_path.exists():
        return {}
    try:
        rows = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    evidence: dict[str, list[dict[str, Any]]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or row.get("type") != "table":
            continue
        table_body = str(row.get("table_body") or row.get("html") or row.get("content") or "")
        key = normalize_review_text(table_body)
        if not key:
            continue
        evidence_item = {
            "page_idx": row.get("page_idx"),
            "page_number": int(row["page_idx"]) + 1 if row.get("page_idx") is not None else None,
            "bbox": row.get("bbox") or [],
            "content": table_body,
            "raw_type": row.get("type") or "",
            "img_path": row.get("img_path") or "",
        }
        evidence.setdefault(key, []).append(evidence_item)
        compact_key = normalize_review_compact_text(table_body)
        if len(compact_key) >= 40:
            evidence.setdefault(f"compact:{compact_key}", []).append(evidence_item)
    return evidence


def load_content_text_evidence(raw_dir: Path | None) -> dict[str, list[dict[str, Any]]]:
    if not raw_dir:
        return {}
    manifest = read_json(raw_dir / "manifest.json")
    content_file = str(manifest.get("content_file") or "").strip()
    source_root = resolve_local_source_root(raw_dir, str(manifest.get("source_root") or ""))
    if not content_file or not source_root:
        return {}
    content_path = source_root / content_file
    if not content_path.exists():
        return {}
    try:
        rows = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    evidence: dict[str, list[dict[str, Any]]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or row.get("type") in {"table", "image"}:
            continue
        content = str(row.get("text") or row.get("content") or "")
        key = normalize_review_text(content)
        if not key:
            continue
        evidence.setdefault(key, []).append(
            {
                "page_idx": row.get("page_idx"),
                "page_number": int(row["page_idx"]) + 1 if row.get("page_idx") is not None else None,
                "bbox": row.get("bbox") or [],
                "content": content,
                "raw_type": row.get("type") or "",
                "img_path": row.get("img_path") or "",
            }
        )
    return evidence


def build_image_visual_confirmation_packets(
    image_relation_report: dict[str, Any],
    content_image_evidence: dict[str, dict[str, Any]],
    source_pdf: str,
) -> dict[str, Any]:
    priorities = {
        "exercise_key_figure": 1,
        "explanation_key_figure": 2,
        "needs_dimension_review": 3,
    }
    items: list[dict[str, Any]] = []
    excluded = Counter()
    for item in image_relation_report.get("items") or []:
        category = str(item.get("category") or "")
        if category not in priorities:
            excluded[category] += 1
            continue
        image_ref = str(item.get("image") or "")
        evidence = content_image_evidence.get(image_ref, {})
        has_bbox = bool(evidence.get("bbox")) and evidence.get("page_idx") is not None
        if not source_pdf:
            crop_status = "source_pdf_missing"
        elif has_bbox:
            crop_status = "ready_for_source_crop"
        else:
            crop_status = "needs_page_bbox"
        packets_item = {
            "type": "image_source_visual_confirmation",
            "priority": priorities[category],
            "block_id": item.get("block_id"),
            "image": image_ref,
            "category": category,
            "action": item.get("action"),
            "dimensions": item.get("dimensions") or {},
            "parent_id": item.get("parent_id", ""),
            "parent_type": item.get("parent_type", ""),
            "previous_block": item.get("previous_block") or {},
            "next_block": item.get("next_block") or {},
            "heading_path": item.get("heading_path") or [],
            "source_pdf": source_pdf,
            "source_pdf_available": bool(source_pdf),
            "source_page_idx": evidence.get("page_idx"),
            "source_page_number": evidence.get("page_number"),
            "source_bbox": evidence.get("bbox") or [],
            "source_content": str(evidence.get("content") or "")[:1000],
            "source_sub_type": evidence.get("sub_type") or "",
            "crop_status": crop_status,
            "recommended_next_step": "crop_source_region_then_compare" if crop_status == "ready_for_source_crop" else "locate_page_bbox_before_visual_compare",
        }
        items.append(packets_item)

    items.sort(key=lambda row: (int(row["priority"]), int(row.get("source_page_idx") or 10**9), str(row.get("block_id") or "")))
    return {
        "schema": "luceon-standard-image-visual-confirmation-packets/v1",
        "selection_policy": "content_bearing_workbook_images_only",
        "source_pdf": source_pdf,
        "source_pdf_available": bool(source_pdf),
        "items": items,
        "count": len(items),
        "priority_counts": dict(Counter(str(item["priority"]) for item in items)),
        "category_counts": dict(Counter(item["category"] for item in items)),
        "crop_status_counts": dict(Counter(item["crop_status"] for item in items)),
        "excluded_category_counts": dict(excluded),
    }


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug[:80] or "item"


def render_single_source_page(source_pdf: str, page_number: int, temp_dir: Path, dpi: int = 180) -> Path | None:
    if not shutil.which("pdftoppm"):
        return None
    prefix = temp_dir / f"source_page_{page_number}"
    completed = subprocess.run(
        [
            "pdftoppm",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-r",
            str(dpi),
            "-png",
            source_pdf,
            str(prefix),
        ],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if completed.returncode != 0:
        return None
    rendered = sorted(temp_dir.glob(f"{prefix.name}*.png"))
    return rendered[0] if rendered else None


def add_source_pdf_crops_to_packets(packets: dict[str, Any], out_dir: Path, crop_dir_name: str = "source_crops") -> dict[str, Any]:
    items = packets.get("items") or []
    source_pdf = str(packets.get("source_pdf") or "")
    if not items:
        summary = {"source_crop_generation": "empty", "source_crop_count": 0, "source_crop_status_counts": {}, "source_crop_dir": ""}
        packets["source_crop_summary"] = summary
        return summary

    crop_dir = out_dir / crop_dir_name
    crop_dir_ref = f"{crop_dir_name.rstrip('/')}/"
    crop_dir.mkdir(parents=True, exist_ok=True)
    status_counts: Counter[str] = Counter()
    crop_count = 0
    if not source_pdf or not Path(source_pdf).exists():
        for item in items:
            item["source_crop_status"] = "source_pdf_missing"
        status_counts["source_pdf_missing"] = len(items)
        summary = {
            "source_crop_generation": "attempted",
            "source_crop_count": 0,
            "source_crop_status_counts": dict(status_counts),
            "source_crop_dir": crop_dir_ref,
        }
        packets["source_crop_summary"] = summary
        return summary
    if not shutil.which("pdftoppm"):
        for item in items:
            item["source_crop_status"] = "pdftoppm_missing"
        status_counts["pdftoppm_missing"] = len(items)
        summary = {
            "source_crop_generation": "attempted",
            "source_crop_count": 0,
            "source_crop_status_counts": dict(status_counts),
            "source_crop_dir": crop_dir_ref,
        }
        packets["source_crop_summary"] = summary
        return summary

    try:
        from PIL import Image  # type: ignore
    except Exception:
        for item in items:
            item["source_crop_status"] = "pillow_missing"
        status_counts["pillow_missing"] = len(items)
        summary = {
            "source_crop_generation": "attempted",
            "source_crop_count": 0,
            "source_crop_status_counts": dict(status_counts),
            "source_crop_dir": crop_dir_ref,
        }
        packets["source_crop_summary"] = summary
        return summary

    with tempfile.TemporaryDirectory(prefix="luceon-source-crops-") as temp_name:
        temp_dir = Path(temp_name)
        page_cache: dict[int, Path | None] = {}
        for index, item in enumerate(items, start=1):
            page_number = item.get("source_page_number")
            bbox = item.get("source_bbox") or []
            if not isinstance(page_number, int) or len(bbox) != 4:
                item["source_crop_status"] = "needs_page_bbox"
                status_counts["needs_page_bbox"] += 1
                continue
            block_id = safe_slug(str(item.get("block_id") or f"packet_{index}"))
            category = safe_slug(str(item.get("category") or "image"))
            crop_name = f"{index:04d}-{block_id}-{category}.png"
            crop_path = crop_dir / crop_name
            crop_ref = f"{crop_dir_ref}{crop_name}"
            if crop_path.exists():
                item["source_crop"] = crop_ref
                item["source_crop_status"] = "reused"
                item["source_crop_method"] = "pdftoppm_180dpi_normalized_bbox_0_1000"
                try:
                    with Image.open(crop_path) as existing_crop:
                        item["source_crop_size"] = [existing_crop.size[0], existing_crop.size[1]]
                except Exception:
                    pass
                crop_count += 1
                status_counts["reused"] += 1
                continue
            if page_number not in page_cache:
                page_cache[page_number] = render_single_source_page(source_pdf, page_number, temp_dir)
            page_image_path = page_cache[page_number]
            if not page_image_path:
                item["source_crop_status"] = "page_render_failed"
                status_counts["page_render_failed"] += 1
                continue
            try:
                with Image.open(page_image_path) as page_image:
                    width, height = page_image.size
                    x0, y0, x1, y1 = [float(value) for value in bbox]
                    left = int(round(x0 / 1000.0 * width))
                    top = int(round(y0 / 1000.0 * height))
                    right = int(round(x1 / 1000.0 * width))
                    bottom = int(round(y1 / 1000.0 * height))
                    margin = max(4, int(round(min(width, height) * 0.006)))
                    left = max(0, left - margin)
                    top = max(0, top - margin)
                    right = min(width, right + margin)
                    bottom = min(height, bottom + margin)
                    if right <= left or bottom <= top:
                        item["source_crop_status"] = "invalid_bbox"
                        status_counts["invalid_bbox"] += 1
                        continue
                    crop = page_image.crop((left, top, right, bottom))
                    crop.save(crop_path)
                    item["source_crop"] = f"{crop_dir_ref}{crop_name}"
                    item["source_crop_status"] = "created"
                    item["source_crop_bbox_px"] = [left, top, right, bottom]
                    item["source_crop_size"] = [right - left, bottom - top]
                    item["source_crop_method"] = "pdftoppm_180dpi_normalized_bbox_0_1000"
                    crop_count += 1
                    status_counts["created"] += 1
            except Exception as exc:
                item["source_crop_status"] = "crop_failed"
                item["source_crop_error"] = str(exc)[:300]
                status_counts["crop_failed"] += 1

    summary = {
        "source_crop_generation": "generated" if crop_count == len(items) else "attempted",
        "source_crop_count": crop_count,
        "source_crop_status_counts": dict(status_counts),
        "source_crop_dir": crop_dir_ref,
    }
    packets["source_crop_summary"] = summary
    return summary


def skip_source_pdf_crops_for_packets(packets: dict[str, Any]) -> dict[str, Any]:
    items = packets.get("items") or []
    for item in items:
        item.pop("source_crop", None)
        item.pop("source_crop_bbox_px", None)
        item.pop("source_crop_size", None)
        item.pop("source_crop_method", None)
        item.pop("source_crop_error", None)
        item["source_crop_status"] = "not_generated"
    summary = {
        "source_crop_generation": "skipped",
        "source_crop_count": 0,
        "source_crop_status_counts": {"not_generated": len(items)} if items else {},
        "source_crop_dir": "",
        "recommended_next_step": "run backend/scripts/generate_standard_source_crops.py for review artifacts",
    }
    packets["source_crop_summary"] = summary
    return summary


def build_image_visual_confirmation_html(packets: dict[str, Any]) -> str:
    rows: list[str] = []
    for item in (packets.get("items") or [])[:300]:
        heading = " > ".join(item.get("heading_path") or [])
        source_page = item.get("source_page_number") or ""
        bbox = item.get("source_bbox") or []
        source_crop = str(item.get("source_crop") or "")
        source_crop_html = (
            f"<div><h3>Source PDF Crop</h3><img src=\"{html.escape(source_crop)}\" alt=\"source crop\"></div>"
            if source_crop
            else "<div><h3>Source PDF Crop</h3><p>No crop artifact.</p></div>"
        )
        rows.append(
            "<article class=\"packet\">"
            f"<h2>{html.escape(str(item.get('block_id') or ''))} - {html.escape(str(item.get('category') or ''))}</h2>"
            f"<p><strong>Action:</strong> {html.escape(str(item.get('action') or ''))} | "
            f"<strong>Crop:</strong> {html.escape(str(item.get('crop_status') or ''))} | "
            f"<strong>Source Crop:</strong> {html.escape(str(item.get('source_crop_status') or ''))} | "
            f"<strong>Page:</strong> {html.escape(str(source_page))} | "
            f"<strong>BBox:</strong> {html.escape(str(bbox))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(heading)}</p>"
            "<div class=\"images\">"
            f"<div><h3>Standard Image</h3><img src=\"{html.escape(str(item.get('image') or ''))}\" alt=\"{html.escape(str(item.get('category') or 'image'))}\"></div>"
            f"{source_crop_html}"
            "</div>"
            f"<pre>{html.escape(str(item.get('source_content') or ''))}</pre>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Image Visual Confirmation</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    .summary {{ padding: 12px 14px; border: 1px solid #bbb; margin-bottom: 18px; }}
    .packet {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 14px 0; }}
    h1, h2 {{ margin: 0 0 8px; }}
    h2 {{ font-size: 16px; }}
    .images {{ display: flex; gap: 18px; align-items: flex-start; flex-wrap: wrap; }}
    h3 {{ font-size: 13px; margin: 0 0 6px; }}
    img {{ max-width: 360px; max-height: 260px; object-fit: contain; border: 1px solid #ccc; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 8px; max-width: 960px; }}
  </style>
</head>
<body>
  <h1>Image Visual Confirmation</h1>
  <section class="summary">
    <p><strong>Count:</strong> {html.escape(str(packets.get("count") or 0))}</p>
    <p><strong>Category Counts:</strong> {html.escape(json.dumps(packets.get("category_counts") or {}, ensure_ascii=False))}</p>
    <p><strong>Crop Status Counts:</strong> {html.escape(json.dumps(packets.get("crop_status_counts") or {}, ensure_ascii=False))}</p>
    <p><strong>Source Crop Summary:</strong> {html.escape(json.dumps(packets.get("source_crop_summary") or {}, ensure_ascii=False))}</p>
    <p><strong>Excluded:</strong> {html.escape(json.dumps(packets.get("excluded_category_counts") or {}, ensure_ascii=False))}</p>
  </section>
  {"".join(rows)}
</body>
</html>
"""


def render_pdf(html_path: Path, pdf_path: Path, chrome_path: str | None) -> tuple[bool, str]:
    chrome = chrome_path or os.getenv("CHROME_BIN") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome).exists() and not shutil.which(chrome):
        return False, f"Chrome not found: {chrome}"
    temp_pdf_path = pdf_path.with_name(f"{pdf_path.stem}.tmp{pdf_path.suffix}")
    if temp_pdf_path.exists():
        temp_pdf_path.unlink()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={temp_pdf_path}",
        f"file://{html_path.resolve()}",
    ]
    try:
        completed = subprocess.run(cmd, text=True, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        if temp_pdf_path.exists() and temp_pdf_path.stat().st_size > 0:
            shutil.move(str(temp_pdf_path), str(pdf_path))
            return True, "Chrome timed out after 120s but wrote a non-empty PDF"
        return False, "Chrome timed out after 120s and PDF is missing or empty"
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout or f"Chrome exited {completed.returncode}")[-2000:]
    if not temp_pdf_path.exists() or temp_pdf_path.stat().st_size == 0:
        return False, "Chrome returned success but PDF is missing or empty"
    shutil.move(str(temp_pdf_path), str(pdf_path))
    return True, "ok"


def pdf_page_count(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        try:
            import pdfplumber  # type: ignore

            with pdfplumber.open(str(pdf_path)) as pdf:
                return len(pdf.pages)
        except Exception:
            try:
                completed = subprocess.run(["pdfinfo", str(pdf_path)], text=True, capture_output=True, timeout=20)
                if completed.returncode == 0:
                    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.M)
                    if match:
                        return int(match.group(1))
            except Exception:
                return None
            return None


def acceptance_status(gates: dict[str, dict[str, Any]]) -> str:
    if any(gate.get("status") == "fail" for gate in gates.values()):
        return "fail"
    if any(gate.get("status") == "review" for gate in gates.values()):
        return "review"
    return "pass"


def find_source_pdf(raw_dir: Path | None, source_pdf_path: Path | None = None) -> str:
    if source_pdf_path and source_pdf_path.exists():
        return str(source_pdf_path.resolve())
    if not raw_dir:
        return ""
    candidates = [
        raw_dir.parent / "rebuild_input" / "pdf-e71fe159994b50f3_origin.pdf",
        raw_dir.parent / "rebuild_input" / "origin.pdf",
    ]
    candidates.extend(sorted((raw_dir.parent / "rebuild_input").glob("*_origin.pdf")))
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return ""


def clean_standard_profile(clean_standard: dict[str, Any], requested_profile: str) -> str:
    if requested_profile != "auto":
        return requested_profile
    candidates = clean_standard.get("profile_candidates") if isinstance(clean_standard.get("profile_candidates"), list) else []
    if candidates:
        profile = str(candidates[0].get("profile") or "")
        if profile in PROFILE_CHOICES:
            return profile
    return "auto"


CANONICAL_BLOCK_TYPE_TO_INTERNAL = {
    "unit": "unit_opener",
    "exercise_group": "question_group",
    "figure": "captioned_figure",
}


def clean_standard_asset_map(clean_standard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(asset.get("id") or ""): asset
        for asset in clean_standard.get("assets") or []
        if isinstance(asset, dict) and asset.get("id")
    }


def clean_standard_source_map(clean_standard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(source.get("id") or ""): source
        for source in clean_standard.get("source_map") or []
        if isinstance(source, dict) and source.get("id")
    }


def canonical_block_layout(block_type: str, subtype: str, markdown: str, profile: str) -> dict[str, Any]:
    if block_type == "unit_opener":
        return {"break_before": "page"}
    if block_type == "section" and subtype == "lesson_heading":
        return {"break_before": "page"}
    if block_type in {"captioned_figure", "caption", "table", "formula", "question_group", "question", "option", "answer_blank"}:
        layout: dict[str, Any] = {"keep_together": True}
        if block_type == "captioned_figure" and profile in WORKBOOK_PROFILES:
            layout["profile_intent"] = "figure_relation_candidate"
        if block_type == "table" and profile in WORKBOOK_PROFILES:
            layout["profile_intent"] = subtype or "table_question"
        return layout
    if IMAGE_RE.search(markdown):
        return {"keep_together": True}
    return {}


def adapt_clean_standard_outline(clean_standard: dict[str, Any], blocks_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    for item in clean_standard.get("outline") or []:
        if not isinstance(item, dict):
            continue
        block_id = str(item.get("block_id") or "")
        block = blocks_by_id.get(block_id, {})
        outline.append(
            {
                "title": str(item.get("title") or ""),
                "level": int(item.get("level") or 1),
                "line": int(block.get("line_start") or 0),
                "path": item.get("path") if isinstance(item.get("path"), list) else [],
            }
        )
    return outline


def adapt_clean_standard_relations(clean_standard: dict[str, Any], asset_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    for relation in clean_standard.get("relations") or []:
        if not isinstance(relation, dict):
            continue
        target = str(relation.get("to") or "")
        asset = asset_by_id.get(target)
        if asset:
            target = str(asset.get("path") or target)
        relation_type = str(relation.get("type") or "contains")
        if relation_type == "contains" and (asset or target.startswith("images/")):
            relation_type = "contains_media"
        relations.append(
            {
                "from": str(relation.get("from") or ""),
                "type": relation_type,
                "to": target,
                "confidence": relation.get("confidence"),
                "evidence_refs": relation.get("evidence_refs") or [],
            }
        )
    return relations


def adapt_clean_standard_blocks(clean_standard: dict[str, Any], profile: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    canonical_blocks = clean_standard.get("blocks") if isinstance(clean_standard.get("blocks"), list) else []
    if not canonical_blocks:
        return [], [], []
    asset_by_id = clean_standard_asset_map(clean_standard)
    source_by_id = clean_standard_source_map(clean_standard)
    blocks: list[dict[str, Any]] = []
    issue_candidates: list[dict[str, Any]] = []
    for index, block in enumerate(canonical_blocks, start=1):
        if not isinstance(block, dict):
            continue
        block_id = str(block.get("id") or f"b-{index:05d}")
        markdown = str(block.get("markdown") or block.get("text") or "").strip()
        canonical_type = str(block.get("type") or "paragraph")
        block_type = CANONICAL_BLOCK_TYPE_TO_INTERNAL.get(canonical_type, canonical_type)
        subtype = str(block.get("subtype") or "")
        line_start = int(block.get("order") or index)
        asset_refs = [str(asset_ref) for asset_ref in block.get("asset_refs") or [] if str(asset_ref)]
        image_paths = [str(asset_by_id[asset_ref].get("path") or "") for asset_ref in asset_refs if asset_ref in asset_by_id]
        image_paths = [path for path in image_paths if path]
        inline_refs = image_refs(markdown)
        for ref in inline_refs:
            if ref not in image_paths:
                image_paths.append(ref)
        source_refs = [str(source_ref) for source_ref in block.get("source_refs") or [] if str(source_ref)]
        sources = [source_by_id[source_ref] for source_ref in source_refs if source_ref in source_by_id]
        evidence: dict[str, Any] = {
            "clean_standard_order": line_start,
            "source_refs": source_refs,
        }
        pages = sorted(
            {
                int(source["page_index"])
                for source in sources
                if isinstance(source, dict) and source.get("page_index") is not None
            }
        )
        if pages:
            evidence["pages"] = pages
        raw_refs = [
            str(source.get("source_block_id") or "")
            for source in sources
            if isinstance(source, dict) and source.get("source_block_id")
        ]
        if raw_refs:
            evidence["raw_block_refs"] = raw_refs
        review_flags = [str(flag) for flag in block.get("review_flags") or [] if str(flag)]
        blockers = [str(item) for item in block.get("blockers") or [] if str(item)]
        status = "needs_review" if review_flags or blockers else "ok"
        adapted = {
            "id": block_id,
            "type": block_type,
            "canonical_type": canonical_type,
            "subtype": subtype,
            "heading_path": block.get("outline_path") if isinstance(block.get("outline_path"), list) else [],
            "line_start": line_start,
            "line_end": line_start,
            "status": status,
            "layout": canonical_block_layout(block_type, subtype, markdown, profile),
            "markdown": markdown,
            "text": str(block.get("text") or IMAGE_RE.sub("", markdown)).strip(),
            "image_refs": image_paths,
            "children": [],
            "evidence": evidence,
            "source_refs": source_refs,
            "asset_refs": asset_refs,
            "review_flags": review_flags,
            "blockers": blockers,
        }
        if image_paths:
            adapted["media"] = [
                {"path": path, "asset": next((asset_by_id[asset_ref] for asset_ref in asset_refs if asset_by_id.get(asset_ref, {}).get("path") == path), {})}
                for path in image_paths
            ]
        blocks.append(adapted)
        for flag in review_flags:
            issue_candidates.append(
                {
                    "type": "clean_standard_review_flag",
                    "severity": "review",
                    "block_id": block_id,
                    "line": line_start,
                    "text": flag,
                }
            )
        for blocker in blockers:
            issue_candidates.append(
                {
                    "type": "clean_standard_blocker",
                    "severity": "fail",
                    "block_id": block_id,
                    "line": line_start,
                    "text": blocker,
                }
            )
    relations = adapt_clean_standard_relations(clean_standard, asset_by_id)
    return blocks, relations, issue_candidates


def load_clean_standard_canonical(clean_standard: dict[str, Any], profile: str) -> dict[str, Any]:
    blocks, relations, issue_candidates = adapt_clean_standard_blocks(clean_standard, profile)
    if not blocks:
        return {}
    blocks_by_id = {str(block.get("id") or ""): block for block in blocks}
    outline = adapt_clean_standard_outline(clean_standard, blocks_by_id)
    return {
        "outline": outline,
        "blocks": blocks,
        "relations": relations,
        "issue_candidates": issue_candidates,
        "short_marker_transforms": [],
        "relation_summary": annotate_question_relations(blocks, relations),
    }


def detect_visible_artifacts(html_text: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for name, pattern in VISIBLE_ARTIFACT_PATTERNS.items():
        matches = list(pattern.finditer(html_text))
        if matches:
            items.append(
                {
                    "type": name,
                    "count": len(matches),
                    "sample": matches[0].group(0)[:120],
                }
            )
    return {
        "schema": "luceon-standard-visible-artifacts/v1",
        "count": sum(int(item["count"]) for item in items),
        "items": items,
    }


def build_visual_review_packets(
    blocks: list[dict[str, Any]],
    source_pdf: str,
    content_table_evidence: dict[str, list[dict[str, Any]]] | None = None,
    content_text_evidence: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    packets: list[dict[str, Any]] = []
    table_evidence_offsets: Counter[str] = Counter()
    text_evidence_offsets: Counter[str] = Counter()
    for block in blocks:
        markdown = str(block.get("markdown") or "")
        block_type = block.get("type")
        needs_table_review = block_type == "table"
        formula_candidate_text = FOOTNOTE_MARKER_RE.sub("", markdown).replace("\\$", "")
        image_only = is_image_only_markdown(markdown)
        needs_formula_review = (not image_only and "$" in formula_candidate_text) or block_type == "formula"
        if not (needs_table_review or needs_formula_review):
            continue
        packet_type = "table_visual_review" if needs_table_review else "formula_visual_review"
        evidence: dict[str, Any] = {}
        if needs_table_review and content_table_evidence:
            key = normalize_review_text(markdown)
            compact_key = normalize_review_compact_text(markdown)
            compact_lookup_key = f"compact:{compact_key}"
            lookup_key = key if content_table_evidence.get(key) else compact_lookup_key
            matches = content_table_evidence.get(lookup_key) or []
            if matches:
                evidence = matches[min(table_evidence_offsets[lookup_key], len(matches) - 1)]
                table_evidence_offsets[lookup_key] += 1
        elif needs_formula_review and content_text_evidence:
            key = normalize_review_text(markdown)
            matches = content_text_evidence.get(key) or []
            if matches:
                evidence = matches[min(text_evidence_offsets[key], len(matches) - 1)]
                text_evidence_offsets[key] += 1
        has_bbox = bool(evidence.get("bbox")) and evidence.get("page_idx") is not None
        if not source_pdf:
            crop_status = "source_pdf_missing"
        elif has_bbox:
            crop_status = "ready_for_source_crop"
        else:
            crop_status = "needs_page_bbox"
        packets.append(
            {
                "type": packet_type,
                "block_id": block["id"],
                "block_type": block.get("type") or "",
                "block_subtype": block.get("subtype") or "",
                "parent_id": block.get("parent_id") or "",
                "profile_intent": (block.get("layout") or {}).get("profile_intent") or "",
                "clean_lines": [block["line_start"], block["line_end"]],
                "heading_path": block.get("heading_path", []),
                "clean_text": markdown,
                "source_pdf": source_pdf,
                "source_pdf_available": bool(source_pdf),
                "page_candidates": [evidence.get("page_number")] if evidence.get("page_number") else block.get("evidence", {}).get("pages", []),
                "source_page_idx": evidence.get("page_idx"),
                "source_page_number": evidence.get("page_number"),
                "source_bbox": evidence.get("bbox") or [],
                "source_content": str(evidence.get("content") or ""),
                "source_raw_type": evidence.get("raw_type") or "",
                "source_image": evidence.get("img_path") or "",
                "crop_status": crop_status,
                "recommended_next_step": "crop_source_region_then_vision_or_human_review" if crop_status == "ready_for_source_crop" else "locate_page_bbox_before_visual_compare",
            }
        )
    return {
        "schema": "luceon-standard-visual-review-packets/v1",
        "source_pdf": source_pdf,
        "source_pdf_available": bool(source_pdf),
        "items": packets,
        "count": len(packets),
        "type_counts": dict(Counter(item["type"] for item in packets)),
    }


def build_standard_review_outcomes(
    visual_review_packets: dict[str, Any],
    image_visual_confirmation_packets: dict[str, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for index, packet in enumerate(visual_review_packets.get("items") or [], start=1):
        packet_type = str(packet.get("type") or "")
        block_id = str(packet.get("block_id") or f"visual-{index}")
        source_evidence_ready = bool(packet.get("source_pdf_available") and packet.get("source_page_number") and packet.get("source_bbox"))
        items.append(
            {
                "outcome_id": f"visual:{packet_type}:{block_id}",
                "packet_source": "standard_visual_review_packets.json",
                "packet_type": packet_type,
                "block_id": block_id,
                "block_type": packet.get("block_type") or "",
                "block_subtype": packet.get("block_subtype") or "",
                "parent_id": packet.get("parent_id") or "",
                "profile_intent": packet.get("profile_intent") or "",
                "decision": "pending",
                "status": "open",
                "basic_print_blocking": True,
                "source_evidence_ready": source_evidence_ready,
                "clean_lines": packet.get("clean_lines") or [],
                "heading_path": packet.get("heading_path") or [],
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop": packet.get("source_crop") or "",
                "source_crop_status": packet.get("source_crop_status") or "",
                "evidence": [],
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
                "allowed_decisions": [
                    "accepted",
                    "accepted_by_rule",
                    "non_blocking",
                    "needs_page_bbox",
                    "needs_source_crop",
                    "needs_layout_fix",
                    "needs_reconstruction",
                    "rejected",
                ],
                "next_action": "review_source_against_standard",
            }
        )
    for index, packet in enumerate(image_visual_confirmation_packets.get("items") or [], start=1):
        category = str(packet.get("category") or "image")
        block_id = str(packet.get("block_id") or f"image-{index}")
        source_evidence_ready = bool(packet.get("source_pdf_available") and packet.get("source_page_number") and packet.get("source_bbox"))
        items.append(
            {
                "outcome_id": f"image:{category}:{block_id}",
                "packet_source": "image_visual_confirmation_packets.json",
                "packet_type": "image_source_visual_confirmation",
                "block_id": block_id,
                "image": packet.get("image") or "",
                "category": category,
                "action": packet.get("action") or "",
                "parent_id": packet.get("parent_id") or "",
                "parent_type": packet.get("parent_type") or "",
                "decision": "pending",
                "status": "open",
                "basic_print_blocking": True,
                "source_evidence_ready": source_evidence_ready,
                "heading_path": packet.get("heading_path") or [],
                "source_page_number": packet.get("source_page_number"),
                "source_bbox": packet.get("source_bbox") or [],
                "source_crop": packet.get("source_crop") or "",
                "source_crop_status": packet.get("source_crop_status") or "",
                "evidence": [],
                "reviewer": "",
                "reviewed_at": "",
                "notes": "",
                "allowed_decisions": [
                    "accepted",
                    "accepted_by_rule",
                    "non_blocking",
                    "needs_page_bbox",
                    "needs_source_crop",
                    "needs_layout_fix",
                    "needs_reconstruction",
                    "rejected",
                ],
                "next_action": "review_source_crop_against_standard_image",
            }
        )
    decision_counts = Counter(item["decision"] for item in items)
    open_blocking_count = sum(1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking"))
    return {
        "schema": "luceon-standard-review-outcomes/v1",
        "policy": "independent_review_layer_no_direct_content_edits",
        "items": items,
        "count": len(items),
        "decision_counts": dict(decision_counts),
        "open_blocking_count": open_blocking_count,
        "closed_count": sum(1 for item in items if item.get("status") == "closed"),
    }


def review_outcome_gate(review_outcomes: dict[str, Any]) -> dict[str, Any]:
    open_blocking_count = int(review_outcomes.get("open_blocking_count") or 0)
    return {
        "status": "review" if open_blocking_count else "pass",
        "outcome_count": int(review_outcomes.get("count") or 0),
        "open_blocking_count": open_blocking_count,
        "decision_counts": review_outcomes.get("decision_counts") or {},
    }


def sync_image_visual_crops_to_review_outcomes(
    image_visual_confirmation_packets: dict[str, Any],
    review_outcomes: dict[str, Any],
) -> dict[str, Any]:
    outcomes_by_id = {
        str(item.get("outcome_id") or ""): item
        for item in review_outcomes.get("items") or []
        if isinstance(item, dict)
    }
    for packet in image_visual_confirmation_packets.get("items") or []:
        category = str(packet.get("category") or "image")
        block_id = str(packet.get("block_id") or "")
        if not block_id:
            continue
        outcome = outcomes_by_id.get(f"image:{category}:{block_id}")
        if not outcome:
            continue
        outcome["source_crop"] = packet.get("source_crop") or outcome.get("source_crop") or ""
        outcome["source_crop_status"] = packet.get("source_crop_status") or outcome.get("source_crop_status") or ""
        if packet.get("source_crop"):
            outcome["source_evidence_ready"] = True
    return review_outcomes


def visual_packet_outcome_id(packet: dict[str, Any]) -> str:
    return f"visual:{packet.get('type') or ''}:{packet.get('block_id') or ''}"


def image_packet_outcome_id(packet: dict[str, Any]) -> str:
    category = str(packet.get("category") or "image")
    block_id = str(packet.get("block_id") or "")
    return f"image:{category}:{block_id}"


def block_context(document: dict[str, Any], block_id: str) -> dict[str, Any]:
    blocks = document.get("blocks") if isinstance(document.get("blocks"), list) else []
    for index, block in enumerate(blocks):
        if str(block.get("id") or "") != block_id:
            continue
        return {
            "block": summarize_neighbor(block),
            "previous_block": summarize_neighbor(blocks[index - 1] if index > 0 else None),
            "next_block": summarize_neighbor(blocks[index + 1] if index + 1 < len(blocks) else None),
        }
    return {"block": {}, "previous_block": {}, "next_block": {}}


def build_visual_outcome_review(
    review_outcomes: dict[str, Any],
    visual_review_packets: dict[str, Any],
    image_visual_confirmation_packets: dict[str, Any],
    document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document = document or {}
    visual_packets_by_outcome = {
        visual_packet_outcome_id(packet): packet
        for packet in visual_review_packets.get("items") or []
        if isinstance(packet, dict)
    }
    image_packets_by_outcome = {
        image_packet_outcome_id(packet): packet
        for packet in image_visual_confirmation_packets.get("items") or []
        if isinstance(packet, dict)
    }
    items: list[dict[str, Any]] = []
    for outcome in review_outcomes.get("items") or []:
        if not isinstance(outcome, dict):
            continue
        outcome_id = str(outcome.get("outcome_id") or "")
        packet_type = str(outcome.get("packet_type") or "")
        packet = image_packets_by_outcome.get(outcome_id) or visual_packets_by_outcome.get(outcome_id) or {}
        block_id = str(outcome.get("block_id") or packet.get("block_id") or "")
        source_crop = str(outcome.get("source_crop") or packet.get("source_crop") or "")
        standard_image = str(outcome.get("image") or packet.get("image") or "")
        review_mode = "metadata_review"
        if packet_type == "image_source_visual_confirmation":
            review_mode = "image_side_by_side"
        elif packet_type == "table_visual_review":
            review_mode = "table_text_and_source_crop"
        elif packet_type == "formula_visual_review":
            review_mode = "formula_text_and_source_crop"
        items.append(
            {
                "outcome_id": outcome_id,
                "packet_type": packet_type,
                "status": outcome.get("status") or "",
                "decision": outcome.get("decision") or "",
                "basic_print_blocking": bool(outcome.get("basic_print_blocking")),
                "block_id": block_id,
                "block_type": outcome.get("block_type") or packet.get("block_type") or "",
                "block_subtype": outcome.get("block_subtype") or packet.get("block_subtype") or "",
                "parent_id": outcome.get("parent_id") or packet.get("parent_id") or "",
                "profile_intent": outcome.get("profile_intent") or packet.get("profile_intent") or "",
                "category": outcome.get("category") or packet.get("category") or "",
                "action": outcome.get("action") or packet.get("action") or "",
                "heading_path": outcome.get("heading_path") or packet.get("heading_path") or [],
                "review_mode": review_mode,
                "standard_image": standard_image,
                "source_crop": source_crop,
                "side_by_side_ready": bool(standard_image and source_crop) if packet_type == "image_source_visual_confirmation" else bool(source_crop),
                "source_crop_status": outcome.get("source_crop_status") or packet.get("source_crop_status") or "",
                "source_page_number": outcome.get("source_page_number") or packet.get("source_page_number"),
                "source_bbox": outcome.get("source_bbox") or packet.get("source_bbox") or [],
                "source_evidence_ready": bool(outcome.get("source_evidence_ready")),
                "clean_lines": outcome.get("clean_lines") or packet.get("clean_lines") or [],
                "clean_text": str(packet.get("clean_text") or "")[:5000],
                "source_content": str(packet.get("source_content") or "")[:5000],
                "next_action": outcome.get("next_action") or "",
                "notes": outcome.get("notes") or "",
                "context": block_context(document, block_id),
            }
        )

    packet_type_counts = Counter(str(item.get("packet_type") or "") for item in items)
    decision_counts = Counter(str(item.get("decision") or "") for item in items)
    open_by_packet_type = Counter(
        str(item.get("packet_type") or "")
        for item in items
        if item.get("status") == "open" and item.get("basic_print_blocking")
    )
    side_by_side_ready_by_type = Counter(
        str(item.get("packet_type") or "")
        for item in items
        if item.get("side_by_side_ready")
    )
    return {
        "schema": "luceon-standard-visual-outcome-review/v1",
        "policy": "outcome_centric_side_by_side_review_no_content_edits",
        "items": items,
        "count": len(items),
        "packet_type_counts": dict(packet_type_counts),
        "decision_counts": dict(decision_counts),
        "open_blocking_count": sum(
            1 for item in items if item.get("status") == "open" and item.get("basic_print_blocking")
        ),
        "open_blocking_by_packet_type": dict(open_by_packet_type),
        "side_by_side_ready_by_packet_type": dict(side_by_side_ready_by_type),
    }


def build_visual_outcome_review_html(report: dict[str, Any]) -> str:
    cards: list[str] = []
    for item in (report.get("items") or [])[:500]:
        heading = " > ".join(item.get("heading_path") or [])
        context = item.get("context") if isinstance(item.get("context"), dict) else {}
        block_context_json = json.dumps(context, ensure_ascii=False, indent=2)
        standard_image = str(item.get("standard_image") or "")
        source_crop = str(item.get("source_crop") or "")
        clean_text = str(item.get("clean_text") or "")
        source_content = str(item.get("source_content") or "")
        if item.get("packet_type") == "image_source_visual_confirmation":
            left = (
                f"<img src=\"{html.escape(standard_image)}\" alt=\"standard image\">"
                if standard_image
                else "<p>No Standard image reference.</p>"
            )
            right = (
                f"<img src=\"{html.escape(source_crop)}\" alt=\"source crop\">"
                if source_crop
                else "<p>No source crop artifact.</p>"
            )
        else:
            left = f"<pre>{html.escape(clean_text)}</pre>" if clean_text else "<p>No Standard text.</p>"
            source_crop_html = (
                f"<img src=\"{html.escape(source_crop)}\" alt=\"source crop\">"
                if source_crop
                else "<p>No source crop artifact.</p>"
            )
            right = f"{source_crop_html}<pre>{html.escape(source_content)}</pre>" if source_content else source_crop_html
        cards.append(
            "<article class=\"outcome\">"
            f"<h2>{html.escape(str(item.get('outcome_id') or ''))}</h2>"
            f"<p><strong>Status:</strong> {html.escape(str(item.get('status') or ''))} | "
            f"<strong>Decision:</strong> {html.escape(str(item.get('decision') or ''))} | "
            f"<strong>Packet:</strong> {html.escape(str(item.get('packet_type') or ''))} | "
            f"<strong>Subtype:</strong> {html.escape(str(item.get('block_subtype') or ''))}</p>"
            f"<p><strong>Heading:</strong> {html.escape(heading)} | "
            f"<strong>Page:</strong> {html.escape(str(item.get('source_page_number') or ''))} | "
            f"<strong>Crop:</strong> {html.escape(str(item.get('source_crop_status') or ''))}</p>"
            f"<p><strong>Next Action:</strong> {html.escape(str(item.get('next_action') or ''))}</p>"
            "<div class=\"pair\">"
            f"<section><h3>Standard</h3>{left}</section>"
            f"<section><h3>Source PDF Evidence</h3>{right}</section>"
            "</div>"
            f"<details><summary>Context</summary><pre>{html.escape(block_context_json)}</pre></details>"
            "</article>"
        )
    summary = {
        key: report.get(key)
        for key in [
            "count",
            "packet_type_counts",
            "decision_counts",
            "open_blocking_count",
            "open_blocking_by_packet_type",
            "side_by_side_ready_by_packet_type",
        ]
    }
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Visual Outcome Review</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    .summary {{ padding: 12px 14px; border: 1px solid #bbb; margin-bottom: 18px; }}
    .outcome {{ break-inside: avoid; border-top: 1px solid #bbb; padding: 16px 0; }}
    h1, h2 {{ margin: 0 0 8px; }}
    h2 {{ font-size: 16px; }}
    h3 {{ font-size: 13px; margin: 0 0 6px; }}
    .pair {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; align-items: start; }}
    img {{ max-width: 100%; max-height: 420px; object-fit: contain; border: 1px solid #ccc; background: #fff; }}
    pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 8px; max-height: 320px; overflow: auto; }}
    details {{ margin-top: 10px; }}
  </style>
</head>
<body>
  <h1>Visual Outcome Review</h1>
  <section class="summary"><pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre></section>
  {"".join(cards)}
</body>
</html>
"""


def refresh_visual_outcome_review_artifacts(standard_dir: Path) -> dict[str, Any]:
    review_outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    visual_review_packets = read_json(standard_dir / "standard_visual_review_packets.json")
    image_visual_confirmation_packets = read_json(standard_dir / "image_visual_confirmation_packets.json")
    document = read_json(standard_dir / "standard_document.json")
    report = build_visual_outcome_review(review_outcomes, visual_review_packets, image_visual_confirmation_packets, document)
    write_json(standard_dir / "visual_outcome_review.json", report)
    (standard_dir / "visual_outcome_review.html").write_text(build_visual_outcome_review_html(report), encoding="utf-8")
    return report


def build_issue_candidate_disposition_audit(
    issue_candidates: list[dict[str, Any]],
    image_relation_report: dict[str, Any],
    review_outcomes: dict[str, Any],
) -> dict[str, Any]:
    relation_by_block = {
        str(item.get("block_id") or ""): item
        for item in image_relation_report.get("items") or []
        if isinstance(item, dict) and item.get("block_id")
    }
    image_outcome_by_block = {
        str(item.get("block_id") or ""): item
        for item in review_outcomes.get("items") or []
        if isinstance(item, dict) and item.get("packet_type") == "image_source_visual_confirmation" and item.get("block_id")
    }
    items: list[dict[str, Any]] = []
    for issue in issue_candidates:
        block_id = str(issue.get("block_id") or "")
        issue_type = str(issue.get("type") or "")
        relation_item = relation_by_block.get(block_id)
        outcome = image_outcome_by_block.get(block_id)
        category = str((relation_item or {}).get("category") or "")
        action = str((relation_item or {}).get("action") or "")
        requires_source_visual_check = bool((relation_item or {}).get("requires_source_visual_check"))
        disposition = "needs_review"
        classification = "needs_review"
        reason = "unclassified_issue_candidate"
        resolved_by = ""
        basic_print_blocking = True

        if issue_type != "missing_raw_image_semantics":
            reason = "unsupported_issue_type"
        elif not relation_item:
            reason = "missing_image_relation_item"
        elif category == "helper_icon" and action == "compress_keep_near" and not requires_source_visual_check:
            disposition = "helper_icon_compact_rendering"
            classification = "helper_icon_artifact"
            reason = "small_helper_icon_excluded_from_source_visual_confirmation"
            resolved_by = "image_relation_report"
            basic_print_blocking = False
        elif category in {"exercise_key_figure", "explanation_key_figure"} and requires_source_visual_check:
            outcome_status = str((outcome or {}).get("status") or "")
            outcome_decision = str((outcome or {}).get("decision") or "")
            outcome_blocking = bool((outcome or {}).get("basic_print_blocking"))
            if outcome_status == "closed" and outcome_decision == "accepted_by_rule" and not outcome_blocking:
                disposition = "covered_by_visual_outcome"
                classification = "visual_outcome_covered"
                reason = "key_figure_closed_by_review_outcome"
                resolved_by = str((outcome or {}).get("outcome_id") or "")
                basic_print_blocking = False
            else:
                disposition = "real_context_gap"
                classification = "real_context_gap"
                reason = "key_figure_requires_open_or_missing_visual_outcome_closure"
        elif category == "explanation_key_figure":
            disposition = "explanation_artifact"
            classification = "helper_or_explanation_artifact"
            reason = "explanation_figure_does_not_require_question_parent"
            resolved_by = "image_relation_report"
            basic_print_blocking = False
        else:
            reason = "unclassified_image_relation_category"

        items.append(
            {
                "type": issue_type,
                "block_id": block_id,
                "line": issue.get("line"),
                "image": issue.get("image") or "",
                "severity": issue.get("severity") or "",
                "disposition": disposition,
                "classification": classification,
                "reason": reason,
                "basic_print_blocking": basic_print_blocking,
                "resolved_by": resolved_by,
                "image_relation": {
                    "category": category,
                    "action": action,
                    "requires_source_visual_check": requires_source_visual_check,
                    "parent_id": (relation_item or {}).get("parent_id") or "",
                    "parent_type": (relation_item or {}).get("parent_type") or "",
                    "previous_block": (relation_item or {}).get("previous_block") or {},
                    "next_block": (relation_item or {}).get("next_block") or {},
                    "heading_path": (relation_item or {}).get("heading_path") or [],
                },
                "review_outcome": {
                    "outcome_id": (outcome or {}).get("outcome_id") or "",
                    "status": (outcome or {}).get("status") or "",
                    "decision": (outcome or {}).get("decision") or "",
                    "basic_print_blocking": bool((outcome or {}).get("basic_print_blocking")),
                    "source_crop": (outcome or {}).get("source_crop") or "",
                    "source_crop_status": (outcome or {}).get("source_crop_status") or "",
                    "source_page_number": (outcome or {}).get("source_page_number"),
                    "source_bbox": (outcome or {}).get("source_bbox") or [],
                },
            }
        )

    disposition_counts = Counter(str(item.get("disposition") or "") for item in items)
    classification_counts = Counter(str(item.get("classification") or "") for item in items)
    category_counts = Counter(str((item.get("image_relation") or {}).get("category") or "") for item in items)
    unresolved_blocking_count = sum(1 for item in items if item.get("basic_print_blocking"))
    return {
        "schema": "luceon-standard-issue-candidate-disposition-audit/v1",
        "policy": {
            "scope": "context_integrity_and_review_threshold_gate_explanation",
            "accepted_by_rule_note": "accepted_by_rule is deterministic evidence closure, not human visual final approval.",
            "review_threshold_basis": "unresolved_blocking_issue_count",
        },
        "count": len(items),
        "issue_type_counts": dict(Counter(str(item.get("type") or "") for item in items)),
        "disposition_counts": dict(disposition_counts),
        "classification_counts": dict(classification_counts),
        "image_category_counts": dict(category_counts),
        "unresolved_blocking_count": unresolved_blocking_count,
        "non_blocking_count": len(items) - unresolved_blocking_count,
        "covered_by_visual_outcome_count": int(disposition_counts.get("covered_by_visual_outcome") or 0),
        "helper_icon_artifact_count": int(disposition_counts.get("helper_icon_compact_rendering") or 0),
        "real_context_gap_count": int(disposition_counts.get("real_context_gap") or 0),
        "items": items,
    }


def issue_candidate_gate_payloads(audit: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    issue_count = int(audit.get("count") or 0)
    unresolved_blocking_count = int(audit.get("unresolved_blocking_count") or 0)
    threshold = 50
    shared = {
        "issue_candidate_count": issue_count,
        "unresolved_blocking_count": unresolved_blocking_count,
        "disposition_counts": audit.get("disposition_counts") or {},
        "classification_counts": audit.get("classification_counts") or {},
        "review_threshold_basis": "unresolved_blocking_issue_count",
    }
    context_gate = {
        "status": "review" if unresolved_blocking_count else "pass",
        **shared,
    }
    threshold_gate = {
        "status": "review" if unresolved_blocking_count > threshold else "pass",
        **shared,
        "threshold": threshold,
    }
    return context_gate, threshold_gate


def build_issue_candidate_disposition_audit_html(audit: dict[str, Any]) -> str:
    rows: list[str] = []
    for item in audit.get("items") or []:
        relation = item.get("image_relation") or {}
        outcome = item.get("review_outcome") or {}
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('disposition') or ''))}</td>"
            f"<td>{html.escape(str(item.get('classification') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('line') or ''))}</td>"
            f"<td>{html.escape(str(relation.get('category') or ''))}</td>"
            f"<td>{html.escape(str(relation.get('action') or ''))}</td>"
            f"<td>{html.escape(str(outcome.get('status') or ''))}</td>"
            f"<td>{html.escape(str(outcome.get('decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('reason') or ''))}</td>"
            f"<td>{html.escape(' > '.join(relation.get('heading_path') or []))}</td>"
            "</tr>"
        )
    summary = {
        key: audit.get(key)
        for key in [
            "count",
            "issue_type_counts",
            "disposition_counts",
            "classification_counts",
            "image_category_counts",
            "unresolved_blocking_count",
            "non_blocking_count",
            "covered_by_visual_outcome_count",
            "helper_icon_artifact_count",
            "real_context_gap_count",
        ]
    }
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Issue Candidate Disposition Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Issue Candidate Disposition Audit</h1>
  <pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre>
  <table><thead><tr><th>Disposition</th><th>Classification</th><th>Block</th><th>Line</th><th>Image Category</th><th>Action</th><th>Outcome Status</th><th>Outcome Decision</th><th>Reason</th><th>Heading</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</body>
</html>
"""


def refresh_issue_candidate_disposition_audit_artifacts(standard_dir: Path) -> dict[str, Any]:
    issue_candidates = read_json(standard_dir / "standard_issue_candidates.json").get("items") or []
    image_relation_report = read_json(standard_dir / "image_relation_report.json")
    review_outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    audit = build_issue_candidate_disposition_audit(issue_candidates, image_relation_report, review_outcomes)
    write_json(standard_dir / "issue_candidate_disposition_audit.json", audit)
    (standard_dir / "issue_candidate_disposition_audit.html").write_text(
        build_issue_candidate_disposition_audit_html(audit),
        encoding="utf-8",
    )
    return audit


def apply_issue_candidate_gates_to_acceptance(standard_dir: Path, audit: dict[str, Any] | None = None) -> dict[str, Any]:
    audit = audit or refresh_issue_candidate_disposition_audit_artifacts(standard_dir)
    acceptance_path = standard_dir / "standard_acceptance_report.json"
    manifest_path = standard_dir / "manifest.json"
    quality_path = standard_dir / "standard_quality_score.json"
    acceptance = read_json(acceptance_path)
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    context_gate, threshold_gate = issue_candidate_gate_payloads(audit)
    gates["context_integrity"] = context_gate
    gates["review_threshold"] = threshold_gate
    acceptance["gates"] = gates
    acceptance["status"] = acceptance_status(gates)
    summary = acceptance.get("summary") if isinstance(acceptance.get("summary"), dict) else {}
    summary["issue_candidate_count"] = int(audit.get("count") or 0)
    summary["issue_candidate_unresolved_blocking_count"] = int(audit.get("unresolved_blocking_count") or 0)
    summary["issue_candidate_disposition_counts"] = audit.get("disposition_counts") or {}
    acceptance["summary"] = summary

    if quality_path.exists():
        layout_report = read_json(standard_dir / "layout_report.json")
        visual_packets = read_json(standard_dir / "standard_visual_review_packets.json")
        print_qa = read_json(standard_dir / "print_qa_report.json")
        correction_log = read_json(standard_dir / "correction_log.json")
        issue_candidates = read_json(standard_dir / "standard_issue_candidates.json").get("items") or []
        quality = compute_quality_score(
            gates,
            layout_report,
            issue_candidates,
            visual_packets,
            print_qa,
            correction_log if isinstance(correction_log, list) else [],
            audit,
        )
        write_json(quality_path, quality)
        acceptance["quality_score"] = {"score": quality.get("score"), "status": quality.get("status")}

    write_json(acceptance_path, acceptance)
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        outputs = manifest.get("outputs") if isinstance(manifest.get("outputs"), dict) else {}
        outputs["issue_candidate_disposition_audit"] = "issue_candidate_disposition_audit.json"
        outputs["issue_candidate_disposition_audit_html"] = "issue_candidate_disposition_audit.html"
        manifest["outputs"] = outputs
        manifest["quality_score"] = acceptance.get("quality_score") or manifest.get("quality_score")
        manifest["acceptance"] = {
            "status": acceptance.get("status"),
            "gates": {name: gate.get("status") for name, gate in gates.items() if isinstance(gate, dict)},
        }
        write_json(manifest_path, manifest)
    return acceptance


def summarize_neighbor(block: dict[str, Any] | None) -> dict[str, Any]:
    if not block:
        return {}
    return {
        "id": block.get("id"),
        "type": block.get("type"),
        "subtype": block.get("subtype") or "",
        "line_start": block.get("line_start"),
        "text": re.sub(r"\s+", " ", str(block.get("markdown") or "")).strip()[:240],
    }


def classify_workbook_relation_audit_item(
    kind: str,
    block: dict[str, Any],
    relation_item: dict[str, Any],
    previous_block: dict[str, Any] | None,
    next_block: dict[str, Any] | None,
) -> tuple[str, str]:
    text = re.sub(r"\s+", " ", str(block.get("markdown") or "")).strip()
    previous_text = re.sub(r"\s+", " ", str((previous_block or {}).get("markdown") or "")).strip()
    next_text = re.sub(r"\s+", " ", str((next_block or {}).get("markdown") or "")).strip()
    context_text = "\n".join([previous_text, text, next_text])

    if kind == "ungrouped_question":
        heading_path = [str(item).lower() for item in block.get("heading_path") or []]
        if not block.get("heading_path") and previous_text.strip().upper() == "TOPICS":
            return "front_matter_artifact", "topic_list_misread_as_question"
        if not block.get("heading_path") and FRONT_MATTER_NUMBER_RUN_RE.match(text):
            return "front_matter_artifact", "publication_number_line_misread_as_question"
        if re.match(r"^\d+(?:\.\s*\d+\.?)+$", text):
            return "explanation_artifact", "number_sequence_artifact_not_exercise_item"
        if re.match(r"^24 hours a day,\s*7 days a week$", text, re.I):
            return "explanation_artifact", "time_expression_phrase_not_exercise_item"
        if any("editing advice" in item for item in heading_path):
            return "explanation_artifact", "numbered_editing_advice_not_exercise_item"
        if WORKBOOK_NUMBERED_EXPLANATION_RE.match(text):
            return "explanation_artifact", "numbered_grammar_explanation_not_exercise_item"
        if previous_text.rstrip(":").lower() in {"note", "notes", "pronunciation note"} and WORKBOOK_NUMBERED_EXPLANATION_RE.match(text):
            return "explanation_artifact", "numbered_grammar_note_not_exercise_item"
        if WORKBOOK_GRAMMAR_EQUIVALENCE_RE.match(text):
            return "explanation_artifact", "numbered_grammar_equivalence_not_exercise_item"
        if WORKBOOK_NUMBERED_QUESTION_INSTRUCTION_RE.match(text):
            return "real_profile_gap", "numbered_instruction_should_start_question_group"
        return "real_profile_gap", "question_without_exercise_group"

    if kind in {"orphan_table_question", "unparented_explanation_table"}:
        if block.get("subtype") == "explanation_table" or is_explanation_table_context(context_text):
            return "explanation_artifact", "grammar_explanation_table_not_exercise_table"
        return "real_profile_gap", "table_question_without_exercise_group"

    if kind == "orphan_figure_relation_candidate":
        category = str(relation_item.get("category") or "")
        if category == "helper_icon":
            return "helper_icon_artifact", "small_helper_icon_should_use_compact_nearby_rendering"
        if category == "explanation_key_figure":
            return "explanation_artifact", "explanation_figure_without_exercise_parent"
        if category == "exercise_key_figure":
            previous_type = str((previous_block or {}).get("type") or "")
            next_type = str((next_block or {}).get("type") or "")
            if previous_type in {"unit_opener", "section", "captioned_figure"} or next_type in {"section", "paragraph"}:
                return "explanation_artifact", "unit_or_explanation_figure_requires_visual_review_not_exercise_parent"
            return "real_profile_gap", "content_figure_without_exercise_or_explanation_parent"
        return "needs_review", "unclassified_orphan_figure"

    return "needs_review", "unclassified_relation_item"


def build_workbook_relation_audit(
    profile: str,
    blocks: list[dict[str, Any]],
    image_relation_report: dict[str, Any],
) -> dict[str, Any]:
    if profile not in WORKBOOK_PROFILES:
        return {
            "schema": "luceon-standard-workbook-relation-audit/v1",
            "profile": profile,
            "applicable": False,
            "items": [],
            "count": 0,
            "kind_counts": {},
            "disposition_counts": {},
            "real_profile_gap_count": 0,
        }

    relation_by_block = {
        str(item.get("block_id") or ""): item
        for item in image_relation_report.get("items") or []
        if isinstance(item, dict)
    }
    items: list[dict[str, Any]] = []
    for index, block in enumerate(blocks):
        kind = ""
        block_type = block.get("type")
        subtype = block.get("subtype")
        if block_type == "question" and not block.get("parent_id"):
            kind = "ungrouped_question"
        elif block_type == "table" and subtype == "table_question" and not block.get("parent_id"):
            kind = "orphan_table_question"
        elif block_type == "table" and subtype == "explanation_table" and not block.get("parent_id"):
            kind = "unparented_explanation_table"
        elif (
            block_type == "captioned_figure"
            and block.get("layout", {}).get("profile_intent") == "figure_relation_candidate"
            and not block.get("parent_id")
        ):
            kind = "orphan_figure_relation_candidate"
        if not kind:
            continue
        previous_block = blocks[index - 1] if index > 0 else None
        next_block = blocks[index + 1] if index + 1 < len(blocks) else None
        relation_item = relation_by_block.get(str(block.get("id") or ""), {})
        disposition, reason = classify_workbook_relation_audit_item(kind, block, relation_item, previous_block, next_block)
        items.append(
            {
                "kind": kind,
                "disposition": disposition,
                "reason": reason,
                "block_id": block.get("id"),
                "type": block_type,
                "subtype": subtype or "",
                "line_start": block.get("line_start"),
                "heading_path": block.get("heading_path") or [],
                "text": re.sub(r"\s+", " ", str(block.get("markdown") or "")).strip()[:500],
                "image_relation": {
                    "category": relation_item.get("category") or "",
                    "action": relation_item.get("action") or "",
                    "dimensions": relation_item.get("dimensions") or {},
                },
                "previous_block": summarize_neighbor(previous_block),
                "next_block": summarize_neighbor(next_block),
            }
        )
    disposition_counts = Counter(str(item["disposition"]) for item in items)
    kind_counts = Counter(str(item["kind"]) for item in items)
    return {
        "schema": "luceon-standard-workbook-relation-audit/v1",
        "profile": profile,
        "applicable": True,
        "items": items,
        "count": len(items),
        "kind_counts": dict(kind_counts),
        "disposition_counts": dict(disposition_counts),
        "real_profile_gap_count": int(disposition_counts.get("real_profile_gap") or 0),
        "review_item_count": int(disposition_counts.get("needs_review") or 0),
    }


def build_workbook_relation_audit_html(audit: dict[str, Any]) -> str:
    rows: list[str] = []
    for item in audit.get("items") or []:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('disposition') or ''))}</td>"
            f"<td>{html.escape(str(item.get('kind') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(str(item.get('line_start') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str((item.get('image_relation') or {}).get('category') or ''))}</td>"
            f"<td>{html.escape(str(item.get('reason') or ''))}</td>"
            f"<td>{html.escape(str(item.get('text') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Relation Audit</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Relation Audit</h1>
  <pre>{html.escape(json.dumps({key: audit.get(key) for key in ['count', 'kind_counts', 'disposition_counts', 'real_profile_gap_count', 'review_item_count']}, ensure_ascii=False, indent=2))}</pre>
  <table><thead><tr><th>Disposition</th><th>Kind</th><th>Block</th><th>Line</th><th>Heading</th><th>Image Category</th><th>Reason</th><th>Text</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</body>
</html>
"""


def count_open_review_outcomes(review_outcomes: dict[str, Any], packet_type: str) -> int:
    return sum(
        1
        for item in review_outcomes.get("items") or []
        if item.get("packet_type") == packet_type and item.get("status") == "open" and item.get("basic_print_blocking")
    )


def contract_status(blockers: list[str], review_reasons: list[str]) -> str:
    if blockers:
        return "fail"
    if review_reasons:
        return "review"
    return "pass"


def build_workbook_profile_report(
    profile: str,
    relation_summary: dict[str, Any],
    block_counts: Counter[str] | dict[str, int],
    image_relation_report: dict[str, Any],
    image_visual_confirmation_packets: dict[str, Any],
    review_outcomes: dict[str, Any],
    workbook_relation_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    applicable = profile in WORKBOOK_PROFILES
    metrics = {
        "question_groups": int(relation_summary.get("question_groups") or 0),
        "questions": int(relation_summary.get("questions") or 0),
        "grouped_questions": int(relation_summary.get("grouped_questions") or 0),
        "ungrouped_questions": int(relation_summary.get("ungrouped_questions") or 0),
        "fill_blank_questions": int(relation_summary.get("fill_blank_questions") or 0),
        "options": int(relation_summary.get("options") or 0),
        "parented_options": int(relation_summary.get("parented_options") or 0),
        "orphan_options": int(relation_summary.get("orphan_options") or 0),
        "answer_blanks": int(relation_summary.get("answer_blanks") or 0),
        "parented_answer_blanks": int(relation_summary.get("parented_answer_blanks") or 0),
        "orphan_answer_blanks": int(relation_summary.get("orphan_answer_blanks") or 0),
        "table_questions": int(relation_summary.get("table_questions") or 0),
        "parented_table_questions": int(relation_summary.get("parented_table_questions") or 0),
        "orphan_table_questions": int(relation_summary.get("orphan_table_questions") or 0),
        "figure_relation_candidates": int(relation_summary.get("figure_relation_candidates") or 0),
        "parented_figure_relation_candidates": int(relation_summary.get("parented_figure_relation_candidates") or 0),
        "orphan_figure_relation_candidates": int(relation_summary.get("orphan_figure_relation_candidates") or 0),
    }
    block_type_counts = {str(key): int(value) for key, value in dict(block_counts).items()}

    if profile in MATH_PROFILES:
        open_formula_outcomes = count_open_review_outcomes(review_outcomes, "formula_visual_review")
        open_table_outcomes = count_open_review_outcomes(review_outcomes, "table_visual_review")
        formula_blocks = int(block_type_counts.get("formula", 0))
        table_blocks = int(block_type_counts.get("table", 0))
        blockers: list[str] = []
        review_reasons: list[str] = []
        if not formula_blocks and not table_blocks:
            blockers.append("no_formula_or_table_blocks_detected")
        if open_formula_outcomes:
            review_reasons.append("formula_visual_review_outcomes_open")
        if open_table_outcomes:
            review_reasons.append("table_visual_review_outcomes_open")
        if not review_reasons and not blockers:
            review_reasons.append("math_profile_contract_requires_explicit_promotion_review")
        profile_status = contract_status(blockers, review_reasons)
        basic_print_blockers: list[str] = []
        if profile_status != "pass":
            basic_print_blockers.append("math_profile_contract_not_pass")
        return {
            "schema": "luceon-standard-workbook-profile-report/v1",
            "profile": profile,
            "applicable": True,
            "status": profile_status,
            "regression_verdict": "math_profile_blocked_review"
            if basic_print_blockers
            else "math_profile_ready_for_basic_print_review",
            "profile_contract": {
                "status": profile_status,
                "metrics": metrics,
                "block_type_counts": block_type_counts,
                "required": [
                    "math_profile_selector",
                    "formula_table_visual_review_closure",
                    "source_evidence_for_formula_table_packets",
                ],
                "blockers": blockers,
                "review_reasons": review_reasons,
            },
            "math_visual_contract": {
                "status": profile_status,
                "formula_blocks": formula_blocks,
                "table_blocks": table_blocks,
                "open_formula_visual_review_outcomes": open_formula_outcomes,
                "open_table_visual_review_outcomes": open_table_outcomes,
                "review_reasons": review_reasons,
                "blockers": blockers,
            },
            "exercise_relation_contract": {
                "status": "not_applicable",
                "metrics": metrics,
                "review_reasons": ["math_profile_uses_math_visual_contract"],
                "blockers": [],
            },
            "image_relation_contract": {"status": "pass", "review_reasons": [], "blockers": []},
            "basic_print_blockers": basic_print_blockers,
            "next_actions": [
                "close_formula_table_visual_outcomes_with_source_evidence",
                "define_math_table_figure_relation_contract_before_promotion",
            ],
        }

    if not applicable:
        return {
            "schema": "luceon-standard-workbook-profile-report/v1",
            "profile": profile,
            "applicable": False,
            "status": "pass",
            "regression_verdict": "not_applicable",
            "profile_contract": {"status": "pass", "metrics": metrics, "block_type_counts": block_type_counts},
            "exercise_relation_contract": {"status": "pass", "metrics": metrics, "review_reasons": [], "blockers": []},
            "image_relation_contract": {"status": "pass", "review_reasons": [], "blockers": []},
            "basic_print_blockers": [],
            "next_actions": [],
        }

    relation_audit = workbook_relation_audit or {}
    explanation_table_count = int((relation_audit.get("disposition_counts") or {}).get("explanation_artifact") or 0)
    profile_blockers: list[str] = []
    profile_review_reasons: list[str] = []
    if metrics["question_groups"] == 0:
        profile_blockers.append("no_question_groups_detected")
    if metrics["answer_blanks"] > 0 and metrics["questions"] == 0:
        profile_review_reasons.append("answer_blanks_without_question_items")
    if int(block_type_counts.get("table", 0)) > metrics["table_questions"] + explanation_table_count:
        profile_review_reasons.append("tables_not_classified_as_table_questions")

    relation_review_reasons: list[str] = []
    relation_blockers: list[str] = []
    real_profile_gap_count = int(relation_audit.get("real_profile_gap_count") or 0)
    relation_needs_review_count = int(relation_audit.get("review_item_count") or 0)
    if real_profile_gap_count:
        relation_review_reasons.append("real_profile_gaps_present")
    if relation_needs_review_count:
        relation_review_reasons.append("unclassified_relation_items_present")

    category_counts = image_relation_report.get("category_counts") or {}
    action_counts = image_relation_report.get("action_counts") or {}
    packet_count = int(image_visual_confirmation_packets.get("count") or 0)
    crop_summary = image_visual_confirmation_packets.get("source_crop_summary") or {}
    source_crop_count = int(crop_summary.get("source_crop_count") or 0)
    ready_crop_count = int((image_visual_confirmation_packets.get("crop_status_counts") or {}).get("ready_for_source_crop") or 0)
    source_visual_check_count = int(image_relation_report.get("source_visual_check_count") or 0)
    open_image_outcomes = count_open_review_outcomes(review_outcomes, "image_source_visual_confirmation")
    open_table_outcomes = count_open_review_outcomes(review_outcomes, "table_visual_review")

    image_blockers: list[str] = []
    image_review_reasons: list[str] = []
    if int(category_counts.get("needs_dimension_review") or 0):
        image_review_reasons.append("image_dimensions_unreadable")
    if source_visual_check_count and packet_count == 0:
        image_blockers.append("source_visual_check_without_packets")
    if open_image_outcomes:
        image_review_reasons.append("image_review_outcomes_open")
    if source_crop_count and source_crop_count < packet_count:
        image_review_reasons.append("source_crop_generation_incomplete")

    profile_status = contract_status(profile_blockers, profile_review_reasons)
    exercise_status = contract_status(relation_blockers, relation_review_reasons)
    image_status = contract_status(image_blockers, image_review_reasons)

    basic_print_blockers: list[str] = []
    if profile_status != "pass":
        basic_print_blockers.append("workbook_profile_contract_not_pass")
    if exercise_status != "pass":
        basic_print_blockers.append("exercise_relation_contract_not_pass")
    if image_status != "pass":
        basic_print_blockers.append("image_relation_contract_not_pass")
    if open_table_outcomes:
        basic_print_blockers.append("table_visual_review_outcomes_open")

    hard_fail = profile_status == "fail" or exercise_status == "fail" or image_status == "fail"
    if hard_fail:
        status = "fail"
        regression_verdict = "unexpected_fail"
    elif basic_print_blockers:
        status = "review"
        regression_verdict = "expected_negative_regression_review"
    else:
        status = "pass"
        regression_verdict = "workbook_profile_ready_for_basic_print_review"

    next_actions: list[str] = []
    if relation_review_reasons:
        next_actions.append("inspect_or_fix_unlinked_workbook_blocks_before_layout_promotion")
    if open_image_outcomes:
        next_actions.append("review_image_visual_confirmation_packets_against_source_crops")
    if open_table_outcomes:
        next_actions.append("close_table_visual_review_outcomes_with_source_evidence")

    return {
        "schema": "luceon-standard-workbook-profile-report/v1",
        "profile": profile,
        "applicable": True,
        "status": status,
        "regression_verdict": regression_verdict,
        "profile_contract": {
            "status": profile_status,
            "metrics": metrics,
            "block_type_counts": block_type_counts,
            "required": [
                "question_groups_detected",
                "questions_or_answer_structures_detected",
                "tables_classified_when_source_tables_exist",
            ],
            "blockers": profile_blockers,
            "review_reasons": profile_review_reasons,
        },
        "exercise_relation_contract": {
            "status": exercise_status,
            "metrics": metrics,
            "relation_audit": {
                "count": int(relation_audit.get("count") or 0),
                "kind_counts": relation_audit.get("kind_counts") or {},
                "disposition_counts": relation_audit.get("disposition_counts") or {},
                "real_profile_gap_count": real_profile_gap_count,
                "review_item_count": relation_needs_review_count,
            },
            "review_reasons": relation_review_reasons,
            "blockers": relation_blockers,
        },
        "image_relation_contract": {
            "status": image_status,
            "image_relation_count": int(image_relation_report.get("count") or 0),
            "category_counts": category_counts,
            "action_counts": action_counts,
            "source_visual_check_count": source_visual_check_count,
            "image_visual_confirmation_packet_count": packet_count,
            "ready_for_source_crop_count": ready_crop_count,
            "source_crop_count": source_crop_count,
            "excluded_category_counts": image_visual_confirmation_packets.get("excluded_category_counts") or {},
            "open_image_review_outcome_count": open_image_outcomes,
            "open_table_review_outcome_count": open_table_outcomes,
            "source_crop_summary": crop_summary,
            "blockers": image_blockers,
            "review_reasons": image_review_reasons,
        },
        "basic_print_blockers": basic_print_blockers,
        "next_actions": next_actions,
    }


def build_workbook_profile_html(report: dict[str, Any]) -> str:
    profile = report.get("profile") or ""
    metrics = ((report.get("profile_contract") or {}).get("metrics") or {})
    metric_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(key))}</td>"
        f"<td>{html.escape(str(value))}</td>"
        "</tr>"
        for key, value in metrics.items()
    )
    sections = {
        "profile_contract": report.get("profile_contract") or {},
        "exercise_relation_contract": report.get("exercise_relation_contract") or {},
        "image_relation_contract": report.get("image_relation_contract") or {},
    }
    section_rows = "".join(
        "<tr>"
        f"<td>{html.escape(name)}</td>"
        f"<td>{html.escape(str(section.get('status') or ''))}</td>"
        f"<td>{html.escape(', '.join(section.get('blockers') or []))}</td>"
        f"<td>{html.escape(', '.join(section.get('review_reasons') or []))}</td>"
        "</tr>"
        for name, section in sections.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Workbook Profile Report</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 14px 0 28px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Workbook Profile Report</h1>
  <p><strong>Profile:</strong> {html.escape(str(profile))}</p>
  <p><strong>Status:</strong> {html.escape(str(report.get("status") or ""))}</p>
  <p><strong>Regression Verdict:</strong> {html.escape(str(report.get("regression_verdict") or ""))}</p>
  <p><strong>Basic Print Blockers:</strong> {html.escape(", ".join(report.get("basic_print_blockers") or []))}</p>
  <h2>Contracts</h2>
  <table><thead><tr><th>Contract</th><th>Status</th><th>Blockers</th><th>Review Reasons</th></tr></thead><tbody>{section_rows}</tbody></table>
  <h2>Workbook Metrics</h2>
  <table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>{metric_rows}</tbody></table>
  <h2>Next Actions</h2>
  <pre>{html.escape(json.dumps(report.get("next_actions") or [], ensure_ascii=False, indent=2))}</pre>
</body>
</html>
"""


def refresh_workbook_profile_artifacts(standard_dir: Path) -> dict[str, Any]:
    layout_report = read_json(standard_dir / "layout_report.json")
    document = read_json(standard_dir / "standard_document.json")
    image_relation_report = read_json(standard_dir / "image_relation_report.json")
    image_visual_confirmation_packets = read_json(standard_dir / "image_visual_confirmation_packets.json")
    review_outcomes = read_json(standard_dir / "standard_review_outcomes.json")
    workbook_relation_audit = read_json(standard_dir / "workbook_relation_audit.json")
    profile = str(layout_report.get("profile") or document.get("profile") or "")
    relation_summary = layout_report.get("relation_summary") if isinstance(layout_report.get("relation_summary"), dict) else {}
    block_counts = layout_report.get("block_type_counts") if isinstance(layout_report.get("block_type_counts"), dict) else {}
    report = build_workbook_profile_report(
        profile,
        relation_summary,
        Counter({str(key): int(value) for key, value in block_counts.items()}),
        image_relation_report,
        image_visual_confirmation_packets,
        review_outcomes,
        workbook_relation_audit,
    )
    write_json(standard_dir / "workbook_profile_report.json", report)
    (standard_dir / "workbook_profile.html").write_text(build_workbook_profile_html(report), encoding="utf-8")
    return report


def build_review_outcomes_html(review_outcomes: dict[str, Any]) -> str:
    rows = []
    for item in (review_outcomes.get("items") or [])[:500]:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('status') or ''))}</td>"
            f"<td>{html.escape(str(item.get('decision') or ''))}</td>"
            f"<td>{html.escape(str(item.get('packet_type') or ''))}</td>"
            f"<td>{html.escape(str(item.get('block_id') or ''))}</td>"
            f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
            f"<td>{html.escape(str(item.get('source_page_number') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_bbox') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_crop_status') or ''))}</td>"
            f"<td>{html.escape(str(item.get('source_crop') or ''))}</td>"
            f"<td>{html.escape(str(item.get('next_action') or ''))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Standard Review Outcomes</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    pre {{ background: #f6f6f6; padding: 8px; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Standard Review Outcomes</h1>
  <pre>{html.escape(json.dumps({k: review_outcomes.get(k) for k in ['count', 'decision_counts', 'open_blocking_count', 'closed_count']}, ensure_ascii=False, indent=2))}</pre>
  <table><thead><tr><th>Status</th><th>Decision</th><th>Packet</th><th>Block</th><th>Heading</th><th>Page</th><th>BBox</th><th>Crop Status</th><th>Source Crop</th><th>Next Action</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
</body>
</html>
"""


def profile_coverage_gate(
    profile: str,
    relation_summary: dict[str, Any],
    block_counts: Counter[str],
    *,
    explanation_table_count: int = 0,
) -> dict[str, Any]:
    if profile in MATH_PROFILES:
        formula_blocks = int(block_counts.get("formula", 0))
        table_blocks = int(block_counts.get("table", 0))
        question_blocks = int(block_counts.get("question", 0))
        review_reasons: list[str] = []
        blockers: list[str] = []
        if not formula_blocks and not table_blocks:
            blockers.append("no_formula_or_table_blocks_detected")
        if question_blocks and not formula_blocks:
            review_reasons.append("math_questions_without_formula_blocks")
        status = "fail" if blockers else "review"
        return {
            "status": status,
            "profile": profile,
            "required": [
                "math_profile_selector",
                "formula_table_visual_review",
                "source_evidence_for_formula_table_packets",
            ],
            "formula_blocks": formula_blocks,
            "table_blocks": table_blocks,
            "question_blocks": question_blocks,
            "blockers": blockers,
            "review_reasons": review_reasons or ["math_profile_contract_requires_visual_outcome_closure"],
        }
    if profile not in WORKBOOK_PROFILES:
        return {
            "status": "pass",
            "profile": profile,
            "required": ["outline", "source_fidelity", "media_integrity"],
        }

    question_groups = int(relation_summary.get("question_groups") or 0)
    questions = int(relation_summary.get("questions") or 0)
    answer_blanks = int(relation_summary.get("answer_blanks") or 0)
    table_questions = int(relation_summary.get("table_questions") or 0)
    figures = int(relation_summary.get("figure_relation_candidates") or 0)
    blockers: list[str] = []
    review_reasons: list[str] = []
    if question_groups == 0:
        blockers.append("no_question_groups_detected")
    if answer_blanks > 0 and questions == 0:
        review_reasons.append("answer_blanks_without_question_items")
    if int(block_counts.get("table", 0)) > table_questions + explanation_table_count:
        review_reasons.append("tables_not_classified_as_table_questions")

    status = "fail" if blockers else "review" if review_reasons else "pass"
    return {
        "status": status,
        "profile": profile,
        "question_groups": question_groups,
        "questions": questions,
        "answer_blanks": answer_blanks,
        "table_questions": table_questions,
        "figure_relation_candidates": figures,
        "blockers": blockers,
        "review_reasons": review_reasons,
    }


def image_relation_gate(profile: str, image_relation_report: dict[str, Any]) -> dict[str, Any]:
    if profile not in WORKBOOK_PROFILES:
        return {
            "status": "pass",
            "profile": profile,
            "image_relation_count": 0,
        }
    category_counts = image_relation_report.get("category_counts") or {}
    source_visual_check_count = int(image_relation_report.get("source_visual_check_count") or 0)
    needs_dimension_review = int(category_counts.get("needs_dimension_review") or 0)
    blockers: list[str] = []
    review_reasons: list[str] = []
    if needs_dimension_review:
        review_reasons.append("image_dimensions_unreadable")
    if source_visual_check_count:
        review_reasons.append("source_visual_check_required")
    status = "fail" if blockers else "review" if review_reasons else "pass"
    return {
        "status": status,
        "profile": profile,
        "image_relation_count": int(image_relation_report.get("count") or 0),
        "category_counts": category_counts,
        "action_counts": image_relation_report.get("action_counts") or {},
        "source_visual_check_count": source_visual_check_count,
        "blockers": blockers,
        "review_reasons": review_reasons,
    }


def compute_quality_score(
    gates: dict[str, dict[str, Any]],
    layout_report: dict[str, Any],
    issue_candidates: list[dict[str, Any]],
    visual_packets: dict[str, Any],
    print_qa: dict[str, Any],
    correction_log: list[dict[str, Any]],
    issue_disposition_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hard_fail = any(gate.get("status") == "fail" for gate in gates.values())
    issue_count = len(issue_candidates)
    unresolved_issue_count = (
        int(issue_disposition_audit.get("unresolved_blocking_count") or 0)
        if isinstance(issue_disposition_audit, dict)
        else issue_count
    )
    unknown_blocks = int(layout_report.get("unknown_blocks") or 0)
    block_count = max(1, int(layout_report.get("block_count") or 1))
    unknown_ratio = unknown_blocks / block_count
    visual_packet_count = int(visual_packets.get("count") or 0)
    review_outcomes_gate = gates.get("review_outcomes") if isinstance(gates.get("review_outcomes"), dict) else {}
    open_visual_review_count = (
        int(review_outcomes_gate.get("open_blocking_count") or 0)
        if review_outcomes_gate
        else visual_packet_count
    )

    source_fidelity = 25
    if gates["source_fidelity"]["status"] != "pass":
        source_fidelity -= 8
    if gates["correction_evidence"]["status"] != "pass":
        source_fidelity -= 6
    if open_visual_review_count:
        source_fidelity -= 2
    if correction_log and any(not item.get("evidence") for item in correction_log):
        source_fidelity -= 5

    structure = 20
    if gates["outline_lock"]["status"] != "pass":
        structure -= 6
    if unknown_ratio > 0:
        structure -= min(5, int(round(unknown_ratio * 20)))
    if not layout_report.get("block_type_counts"):
        structure -= 4

    context = 20
    if unresolved_issue_count:
        context -= min(8, max(2, unresolved_issue_count // 4))
    if layout_report.get("status_counts", {}).get("needs_review", 0):
        context -= min(4, int(layout_report["status_counts"]["needs_review"]) // 10)

    media_visual = 15
    if gates["media_integrity"]["status"] != "pass":
        media_visual -= 7
    if open_visual_review_count:
        media_visual -= min(4, max(1, open_visual_review_count // 10))

    print_layout = 15
    if gates["print_render"]["status"] != "pass":
        print_layout -= 8
    if not print_qa.get("pdf_page_count"):
        print_layout -= 2
    if unresolved_issue_count:
        print_layout -= 1

    auditability = 5
    if gates["auditability"]["status"] != "pass":
        auditability -= 4

    sections = {
        "source_fidelity": max(0, source_fidelity),
        "structure_recovery": max(0, structure),
        "context_integrity": max(0, context),
        "media_visual_integrity": max(0, media_visual),
        "print_layout": max(0, print_layout),
        "auditability_iteration": max(0, auditability),
    }
    total = sum(sections.values())
    if hard_fail or total < 75:
        status = "fail"
    elif total >= 90 and not unresolved_issue_count and not open_visual_review_count:
        status = "pass"
    else:
        status = "review"
    return {
        "schema": "luceon-standard-quality-score/v1",
        "score": total,
        "status": status,
        "sections": sections,
        "deductions": {
            "issue_candidate_count": issue_count,
            "issue_candidate_unresolved_blocking_count": unresolved_issue_count,
            "visual_review_packet_count": visual_packet_count,
            "visual_review_open_blocking_count": open_visual_review_count,
            "unknown_ratio": round(unknown_ratio, 4),
            "pdf_page_count": print_qa.get("pdf_page_count"),
        },
    }


def build_standard_product_status(
    acceptance: dict[str, Any],
    document: dict[str, Any],
    workbook_profile_report: dict[str, Any],
    review_outcomes: dict[str, Any],
    visual_review_packets: dict[str, Any],
    image_visual_confirmation_packets: dict[str, Any],
    source_crop_summary: dict[str, Any],
) -> dict[str, Any]:
    gates = acceptance.get("gates") if isinstance(acceptance.get("gates"), dict) else {}
    hard_gate_failures = [
        name
        for name, gate in gates.items()
        if isinstance(gate, dict) and gate.get("status") == "fail"
    ]
    basic_print_blockers = [
        str(item)
        for item in (workbook_profile_report.get("basic_print_blockers") or [])
        if str(item)
    ]
    acceptance_status = str(acceptance.get("status") or "")
    quality_score = int(((acceptance.get("quality_score") or {}).get("score")) or 0)
    open_blocking_count = int(review_outcomes.get("open_blocking_count") or 0)

    if hard_gate_failures or basic_print_blockers:
        product_layer = "blocked_needs_reconstruction"
        deliverable_use = "review_only_blocked"
        failure_stop = "stop_before_basic_print_candidate_or_accepted_claim"
        reasons = hard_gate_failures + basic_print_blockers
    elif acceptance_status == "pass" and quality_score >= 90 and open_blocking_count == 0:
        product_layer = "profile_certified_output"
        deliverable_use = "profile_certified_standard_output"
        failure_stop = ""
        reasons = []
    else:
        product_layer = "standard_review_draft"
        deliverable_use = "conservative_fallback_review_draft"
        failure_stop = "review_outcomes_or_review_gates_must_close_before_profile_certified_output"
        reasons = [
            name
            for name, gate in gates.items()
            if isinstance(gate, dict) and gate.get("status") == "review"
        ]

    return {
        "schema": "luceon-standard-product-status/v1",
        "policy": "compiler_never_promotes_corpus_status",
        "decision_boundary": (
            "This report classifies the generated Standard package only. Basic Print Candidate "
            "and Basic Print Accepted require separate corpus/golden decision records."
        ),
        "profile": document.get("profile") or "",
        "product_layer": product_layer,
        "deliverable_use": deliverable_use,
        "failure_stop": failure_stop,
        "reasons": reasons,
        "corpus_promotion": {
            "status": "not_promoted_by_compiler",
            "basic_print_candidate": False,
            "basic_print_accepted": False,
            "required_for_candidate": [
                "corpus case/run record",
                "candidate record",
                "separate promotion decision",
            ],
            "required_for_accepted": [
                "accepted golden record",
                "separate accepted-golden promotion decision",
            ],
        },
        "acceptance": {
            "status": acceptance_status,
            "quality_score": quality_score,
            "hard_gate_failures": hard_gate_failures,
            "review_gates": [
                name
                for name, gate in gates.items()
                if isinstance(gate, dict) and gate.get("status") == "review"
            ],
        },
        "review_outcomes": {
            "count": int(review_outcomes.get("count") or 0),
            "open_blocking_count": open_blocking_count,
            "closed_count": int(review_outcomes.get("closed_count") or 0),
            "decision_counts": review_outcomes.get("decision_counts") or {},
        },
        "source_evidence": {
            "source_pdf": document.get("metadata", {}).get("source_pdf") or "",
            "visual_review_packet_count": int(visual_review_packets.get("count") or 0),
            "image_visual_confirmation_packet_count": int(image_visual_confirmation_packets.get("count") or 0),
            "source_crop_count": int(source_crop_summary.get("source_crop_count") or 0),
        },
        "profile_contract": {
            "status": workbook_profile_report.get("status") or "",
            "regression_verdict": workbook_profile_report.get("regression_verdict") or "",
            "basic_print_blockers": basic_print_blockers,
        },
    }


def build_review_html(
    document: dict[str, Any],
    reports: dict[str, Any],
    standard_html_name: str = "standard.html",
) -> str:
    block_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(block['id'])}</td>"
        f"<td>{html.escape(block['type'])}</td>"
        f"<td>{html.escape(block.get('subtype') or '')}</td>"
        f"<td>{block['line_start']}</td>"
        f"<td>{html.escape(block.get('status') or '')}</td>"
        f"<td>{html.escape((block.get('markdown') or '')[:180])}</td>"
        "</tr>"
        for block in document["blocks"][:500]
    )
    issue_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(item.get('severity', ''))}</td>"
        f"<td>{html.escape(item.get('type', ''))}</td>"
        f"<td>{html.escape(str(item.get('block_id', '')))}</td>"
        f"<td>{html.escape(str(item.get('line', '')))}</td>"
        f"<td>{html.escape(str(item.get('text') or item.get('image') or ''))}</td>"
        "</tr>"
        for item in reports["issues"][:300]
    )
    acceptance = reports["acceptance"]
    quality = reports.get("quality_score", {})
    product_status = reports.get("product_status", {})
    visual_packets = reports.get("visual_review_packets", {}).get("items", [])
    visual_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(item.get('type', ''))}</td>"
        f"<td>{html.escape(str(item.get('block_id', '')))}</td>"
        f"<td>{html.escape(str(item.get('clean_lines', '')))}</td>"
        f"<td>{html.escape(' > '.join(item.get('heading_path') or []))}</td>"
        f"<td>{html.escape((item.get('clean_text') or '')[:260])}</td>"
        f"<td>{html.escape(item.get('crop_status', ''))}</td>"
        "</tr>"
        for item in visual_packets[:300]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Standard Review</title>
  <style>
    body {{ margin: 24px; font-family: Arial, Helvetica, sans-serif; color: #111; }}
    iframe {{ width: 100%; height: 72vh; border: 1px solid #aaa; }}
    table {{ width: 100%; border-collapse: collapse; margin: 14px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; vertical-align: top; }}
    th {{ background: #f2f2f2; text-align: left; }}
    code, pre {{ background: #f6f6f6; padding: 2px 4px; }}
    .status {{ font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Standard Review</h1>
  <p class="status">Acceptance: {html.escape(acceptance["status"])}</p>
  <p class="status">Quality Score: {html.escape(str(quality.get("score", "not scored")))} / 100</p>
  <p class="status">Product Layer: {html.escape(str(product_status.get("product_layer", "")))}</p>
  <iframe src="{html.escape(standard_html_name)}"></iframe>
  <h2>Product Status</h2>
  <pre>{html.escape(json.dumps(product_status, ensure_ascii=False, indent=2))}</pre>
  <h2>Quality Score</h2>
  <pre>{html.escape(json.dumps(quality, ensure_ascii=False, indent=2))}</pre>
  <h2>Acceptance Gates</h2>
  <pre>{html.escape(json.dumps(acceptance["gates"], ensure_ascii=False, indent=2))}</pre>
  <h2>Visual Review Packets</h2>
  <table><thead><tr><th>Type</th><th>Block</th><th>Clean Lines</th><th>Heading</th><th>Clean Text</th><th>Crop Status</th></tr></thead><tbody>{visual_rows}</tbody></table>
  <h2>Issue Candidates</h2>
  <table><thead><tr><th>Severity</th><th>Type</th><th>Block</th><th>Line</th><th>Evidence</th></tr></thead><tbody>{issue_rows}</tbody></table>
  <h2>Blocks</h2>
  <table><thead><tr><th>ID</th><th>Type</th><th>Subtype</th><th>Line</th><th>Status</th><th>Markdown</th></tr></thead><tbody>{block_rows}</tbody></table>
</body>
</html>
"""


def build_package(
    clean_dir: Path,
    out_dir: Path,
    raw_dir: Path | None,
    chrome: str | None,
    source_pdf_path: Path | None = None,
    profile: str = "auto",
    generate_source_crops: bool = False,
    require_clean_standard: bool = False,
) -> dict[str, Any]:
    clean_md = clean_dir / "clean.md"
    if not clean_md.exists():
        raise FileNotFoundError(f"Missing clean.md: {clean_md}")

    out_dir.mkdir(parents=True, exist_ok=True)
    markdown = clean_md.read_text(encoding="utf-8")
    clean_standard_path = clean_dir / "clean_standard.json"
    if require_clean_standard and not clean_standard_path.exists():
        raise FileNotFoundError(f"Missing clean_standard.json: {clean_standard_path}")
    clean_standard = read_json(clean_standard_path)
    if clean_standard_path.exists():
        shutil.copy2(clean_standard_path, out_dir / "clean_standard.json")
    contract_report_path = clean_dir / "clean_contract_report.json"
    if contract_report_path.exists():
        shutil.copy2(contract_report_path, out_dir / "clean_contract_report.json")
    lines = coalesce_html_table_lines(coalesce_display_math_lines([Line(idx, text) for idx, text in enumerate(markdown.splitlines(), start=1)]))
    clean_manifest = read_json(clean_dir / "manifest.json")
    media_report = read_json(clean_dir / "media_report.json")
    acceptance_report = read_json(clean_dir / "acceptance_report.json")
    structure_report = read_json(clean_dir / "structure_report.json")
    image_semantics = load_image_semantics(raw_dir)
    content_image_evidence = load_content_image_evidence(raw_dir)
    content_table_evidence = load_content_table_evidence(raw_dir)
    content_text_evidence = load_content_text_evidence(raw_dir)
    source_pdf = find_source_pdf(raw_dir, source_pdf_path)
    selected_profile = clean_standard_profile(clean_standard, profile) if clean_standard else profile
    selected_profile = infer_standard_profile(markdown, clean_manifest, selected_profile)
    clean_standard_canonical = load_clean_standard_canonical(clean_standard, selected_profile) if clean_standard else {}
    if require_clean_standard and not clean_standard_canonical:
        raise ValueError(f"clean_standard.json does not include canonical blocks: {clean_standard_path}")

    if clean_standard_canonical:
        outline = clean_standard_canonical.get("outline") if isinstance(clean_standard_canonical.get("outline"), list) else extract_outline(lines)
        blocks = clean_standard_canonical.get("blocks") or []
        relations = clean_standard_canonical.get("relations") if isinstance(clean_standard_canonical.get("relations"), list) else []
        issue_candidates = clean_standard_canonical.get("issue_candidates") if isinstance(clean_standard_canonical.get("issue_candidates"), list) else []
        short_marker_transforms = []
        relation_summary = (
            clean_standard_canonical.get("relation_summary")
            if isinstance(clean_standard_canonical.get("relation_summary"), dict)
            else annotate_question_relations(blocks, relations)
        )
    else:
        outline = extract_outline(lines)
        blocks, relations, issue_candidates = build_blocks(lines, image_semantics, selected_profile)
        blocks, short_marker_transforms = merge_short_marker_blocks(blocks)
        relation_summary = annotate_question_relations(blocks, relations)
    paired_vocabulary_summary = (
        apply_paired_vocabulary_groups(blocks, relations)
        if selected_profile in WORKBOOK_PROFILES
        else {
            "schema": "luceon-standard-paired-vocabulary-rule/v1",
            "policy": "not_applicable",
            "group_count": 0,
            "patched_table_count": 0,
            "layout_counts": {},
            "groups": [],
        }
    )
    relation_summary = apply_paired_vocabulary_relation_delta(relation_summary, paired_vocabulary_summary)
    workbook_table_attachment_summary = (
        apply_workbook_table_attachment_groups(blocks, relations)
        if selected_profile == "exercise_workbook"
        else {
            "schema": "luceon-standard-workbook-table-attachment-rule/v1",
            "policy": "not_applicable",
            "group_count": 0,
            "patched_table_count": 0,
            "family_counts": {},
            "groups": [],
        }
    )
    relation_summary = apply_workbook_table_attachment_relation_delta(relation_summary, workbook_table_attachment_summary)
    workbook_virtual_question_group_summary = (
        apply_workbook_virtual_question_groups(blocks, relations)
        if selected_profile == "exercise_workbook"
        else {
            "schema": "luceon-standard-workbook-virtual-question-group-rule/v1",
            "policy": "not_applicable",
            "group_count": 0,
            "grouped_question_count": 0,
            "starter_counts": {},
            "stop_counts": {},
            "groups": [],
        }
    )
    relation_summary = apply_workbook_virtual_question_group_relation_delta(
        relation_summary,
        workbook_virtual_question_group_summary,
    )
    workbook_question_continuation_summary = (
        apply_workbook_question_continuation_groups(blocks, relations)
        if selected_profile == "exercise_workbook"
        else {
            "schema": "luceon-standard-workbook-question-continuation-rule/v1",
            "policy": "not_applicable",
            "group_count": 0,
            "grouped_question_count": 0,
            "trigger_counts": {},
            "groups": [],
        }
    )
    relation_summary = apply_workbook_question_continuation_relation_delta(
        relation_summary,
        workbook_question_continuation_summary,
    )
    add_remaining_short_marker_issues(blocks, issue_candidates)
    standard_md = build_standard_md(blocks)
    refs = image_refs(standard_md)
    missing_images = copy_referenced_images(clean_dir, out_dir, refs)
    image_relation_report = build_image_relation_report(selected_profile, blocks, clean_dir)
    workbook_relation_audit = build_workbook_relation_audit(selected_profile, blocks, image_relation_report)
    image_visual_confirmation_packets = build_image_visual_confirmation_packets(image_relation_report, content_image_evidence, source_pdf)
    if generate_source_crops:
        source_crop_summary = add_source_pdf_crops_to_packets(image_visual_confirmation_packets, out_dir)
    else:
        source_crop_summary = skip_source_pdf_crops_for_packets(image_visual_confirmation_packets)

    document = {
        "schema": "luceon-standard-document/v1",
        "material_id": clean_manifest.get("material_id"),
        "run_id": clean_manifest.get("run_id"),
        "title": clean_manifest.get("title") or clean_manifest.get("source_pdf_name") or "Standard Document",
        "source_clean_manifest": str((clean_dir / "manifest.json").resolve()),
        "source_raw_manifest": str((raw_dir / "manifest.json").resolve()) if raw_dir and (raw_dir / "manifest.json").exists() else "",
        "profile": selected_profile,
        "source_hashes": {
            "clean_md_sha256": sha256_text(markdown),
            "standard_md_sha256": sha256_text(standard_md),
            "clean_standard_sha256": sha256_text(clean_standard_path.read_text(encoding="utf-8")) if clean_standard_path.exists() else "",
        },
        "outline": outline,
        "blocks": blocks,
        "relations": relations,
        "metadata": {
            "compiler": "backend/scripts/standard_from_clean.py",
            "strategy": "canonical_clean_standard_compile" if clean_standard_canonical else "deterministic_mvp_no_text_corrections",
            "requested_profile": profile,
            "clean_standard_contract": {
                "available": bool(clean_standard),
                "consumed": bool(clean_standard_canonical),
                "consumed_fields": ["blocks", "relations", "assets", "source_map"] if clean_standard_canonical else [],
                "schema": clean_standard.get("schema") if clean_standard else "",
                "contract_status": (clean_standard.get("contract") or {}).get("status") if clean_standard else "",
            },
            "source_pdf": source_pdf,
            "source_clean_acceptance": acceptance_report.get("status") or acceptance_report.get("acceptance", {}).get("status"),
            "short_marker_transforms": short_marker_transforms,
            "relation_summary": relation_summary,
            "paired_vocabulary_summary": paired_vocabulary_summary,
            "workbook_table_attachment_summary": workbook_table_attachment_summary,
            "workbook_virtual_question_group_summary": workbook_virtual_question_group_summary,
            "workbook_question_continuation_summary": workbook_question_continuation_summary,
        },
    }

    correction_log: list[dict[str, Any]] = []
    block_counts = Counter(block["type"] for block in blocks)
    status_counts = Counter(block["status"] for block in blocks)
    layout_report = {
        "schema": "luceon-standard-layout-report/v1",
        "profile": selected_profile,
        "block_count": len(blocks),
        "block_type_counts": dict(block_counts),
        "status_counts": dict(status_counts),
        "two_column_blocks": sum(1 for block in blocks if block.get("layout", {}).get("layout_hint") == "two_column"),
        "keep_together_blocks": sum(1 for block in blocks if block.get("layout", {}).get("keep_together")),
        "unknown_blocks": block_counts.get("unknown", 0),
        "short_marker_merge_count": len(short_marker_transforms),
        "relation_summary": relation_summary,
        "image_relation_summary": {
            "count": image_relation_report["count"],
            "category_counts": image_relation_report["category_counts"],
            "action_counts": image_relation_report["action_counts"],
            "source_visual_check_count": image_relation_report["source_visual_check_count"],
        },
        "image_visual_confirmation_summary": {
            "count": image_visual_confirmation_packets["count"],
            "category_counts": image_visual_confirmation_packets["category_counts"],
            "crop_status_counts": image_visual_confirmation_packets["crop_status_counts"],
            "source_crop_summary": source_crop_summary,
            "excluded_category_counts": image_visual_confirmation_packets["excluded_category_counts"],
        },
        "paired_vocabulary_summary": {
            "group_count": paired_vocabulary_summary["group_count"],
            "patched_table_count": paired_vocabulary_summary["patched_table_count"],
            "layout_counts": paired_vocabulary_summary["layout_counts"],
        },
    }
    visual_review_packets = build_visual_review_packets(blocks, source_pdf, content_table_evidence, content_text_evidence)
    review_outcomes = build_standard_review_outcomes(visual_review_packets, image_visual_confirmation_packets)
    review_outcomes = sync_image_visual_crops_to_review_outcomes(image_visual_confirmation_packets, review_outcomes)
    visual_outcome_review = build_visual_outcome_review(
        review_outcomes,
        visual_review_packets,
        image_visual_confirmation_packets,
        document,
    )
    issue_disposition_audit = build_issue_candidate_disposition_audit(
        issue_candidates,
        image_relation_report,
        review_outcomes,
    )
    workbook_profile_report = build_workbook_profile_report(
        selected_profile,
        relation_summary,
        block_counts,
        image_relation_report,
        image_visual_confirmation_packets,
        review_outcomes,
        workbook_relation_audit,
    )
    layout_report["workbook_profile_summary"] = {
        "applicable": workbook_profile_report["applicable"],
        "status": workbook_profile_report["status"],
        "regression_verdict": workbook_profile_report["regression_verdict"],
        "basic_print_blockers": workbook_profile_report["basic_print_blockers"],
    }

    standard_html = render_html(document, document["title"])
    visible_artifacts = detect_visible_artifacts(standard_html)
    (out_dir / "standard.md").write_text(standard_md, encoding="utf-8")
    (out_dir / "standard.html").write_text(standard_html, encoding="utf-8")
    write_json(out_dir / "standard_document.json", document)
    write_json(out_dir / "correction_log.json", correction_log)
    write_json(out_dir / "standard_issue_candidates.json", {"items": issue_candidates, "count": len(issue_candidates)})
    write_json(out_dir / "issue_candidate_disposition_audit.json", issue_disposition_audit)
    (out_dir / "issue_candidate_disposition_audit.html").write_text(
        build_issue_candidate_disposition_audit_html(issue_disposition_audit),
        encoding="utf-8",
    )
    write_json(out_dir / "layout_report.json", layout_report)
    write_json(out_dir / "image_relation_report.json", image_relation_report)
    write_json(out_dir / "workbook_relation_audit.json", workbook_relation_audit)
    (out_dir / "workbook_relation_audit.html").write_text(build_workbook_relation_audit_html(workbook_relation_audit), encoding="utf-8")
    write_json(out_dir / "paired_vocabulary_report.json", paired_vocabulary_summary)
    write_json(out_dir / "workbook_table_attachment_report.json", workbook_table_attachment_summary)
    write_json(out_dir / "workbook_virtual_question_group_report.json", workbook_virtual_question_group_summary)
    write_json(out_dir / "workbook_question_continuation_report.json", workbook_question_continuation_summary)
    write_json(out_dir / "image_visual_confirmation_packets.json", image_visual_confirmation_packets)
    (out_dir / "image_visual_confirmation.html").write_text(build_image_visual_confirmation_html(image_visual_confirmation_packets), encoding="utf-8")
    write_json(out_dir / "standard_visual_review_packets.json", visual_review_packets)
    write_json(out_dir / "standard_review_outcomes.json", review_outcomes)
    (out_dir / "review_outcomes.html").write_text(build_review_outcomes_html(review_outcomes), encoding="utf-8")
    write_json(out_dir / "visual_outcome_review.json", visual_outcome_review)
    (out_dir / "visual_outcome_review.html").write_text(build_visual_outcome_review_html(visual_outcome_review), encoding="utf-8")
    write_json(out_dir / "workbook_profile_report.json", workbook_profile_report)
    (out_dir / "workbook_profile.html").write_text(build_workbook_profile_html(workbook_profile_report), encoding="utf-8")

    pdf_ok, pdf_message = render_pdf(out_dir / "standard.html", out_dir / "standard.pdf", chrome)
    print_qa = {
        "schema": "luceon-standard-print-qa/v1",
        "html": str((out_dir / "standard.html").resolve()),
        "pdf": str((out_dir / "standard.pdf").resolve()),
        "pdf_ok": pdf_ok,
        "pdf_message": pdf_message,
        "pdf_bytes": (out_dir / "standard.pdf").stat().st_size if (out_dir / "standard.pdf").exists() else 0,
        "pdf_page_count": pdf_page_count(out_dir / "standard.pdf") if pdf_ok else None,
        "image_refs": len(set(refs)),
        "missing_images": missing_images,
        "visible_artifacts": visible_artifacts,
    }
    write_json(out_dir / "print_qa_report.json", print_qa)

    clean_outline_titles = [item["title"] for item in extract_outline(lines)]
    standard_outline_titles = [item["title"] for item in document["outline"]]
    outline_drift = clean_outline_titles != standard_outline_titles
    text_changed = clean_text_for_compare(markdown) != clean_text_for_compare(standard_md)
    dropped_media = [
        item
        for item in media_report.get("items", [])
        if item.get("decision") == "drop" or item.get("vision_review", {}).get("verdict") == "drop"
    ]
    dropped_without_evidence = [
        item.get("path")
        for item in dropped_media
        if not (item.get("vision_review") or item.get("reasons") or item.get("raw_semantics"))
    ]
    unknown_ratio = block_counts.get("unknown", 0) / max(1, len(blocks))
    profile_gate = profile_coverage_gate(
        selected_profile,
        relation_summary,
        block_counts,
        explanation_table_count=sum(1 for block in blocks if block.get("subtype") == "explanation_table"),
    )
    image_gate = image_relation_gate(selected_profile, image_relation_report)
    outcomes_gate = review_outcome_gate(review_outcomes)
    context_gate, review_threshold_gate = issue_candidate_gate_payloads(issue_disposition_audit)
    image_visual_confirmation_gate = {
        "status": "review" if image_visual_confirmation_packets["count"] else "pass",
        "packet_count": image_visual_confirmation_packets["count"],
        "category_counts": image_visual_confirmation_packets["category_counts"],
        "crop_status_counts": image_visual_confirmation_packets["crop_status_counts"],
        "source_crop_summary": source_crop_summary,
        "excluded_category_counts": image_visual_confirmation_packets["excluded_category_counts"],
    }

    gates = {
        "outline_lock": {
            "status": "fail" if outline_drift else "pass",
            "clean_outline_count": len(clean_outline_titles),
            "standard_outline_count": len(standard_outline_titles),
            "outline_drift": outline_drift,
        },
        "source_fidelity": {
            "status": "fail" if text_changed else "pass",
            "unlogged_content_change": text_changed,
            "clean_text_hash": sha256_text(clean_text_for_compare(markdown)),
            "standard_text_hash": sha256_text(clean_text_for_compare(standard_md)),
        },
        "correction_evidence": {
            "status": "pass",
            "correction_count": len(correction_log),
            "corrections_without_evidence": 0,
        },
        "context_integrity": context_gate,
        "media_integrity": {
            "status": "fail" if missing_images or dropped_without_evidence else "pass",
            "image_refs": len(set(refs)),
            "missing_images": missing_images,
            "dropped_images": len(dropped_media),
            "dropped_without_evidence": dropped_without_evidence,
        },
        "formula_table_integrity": {
            "status": "review" if structure_report.get("clean", {}).get("html_tables", 0) else "pass",
            "tables_preserved_from_clean": structure_report.get("clean", {}).get("html_tables", 0),
            "inline_math_delimiters": structure_report.get("clean", {}).get("inline_math_delimiters", 0),
        },
        "visible_artifacts": {
            "status": "fail" if visible_artifacts["count"] else "pass",
            "count": visible_artifacts["count"],
            "items": visible_artifacts["items"],
        },
        "layout_sanity": {
            "status": "review" if unknown_ratio > 0.15 else "pass",
            "unknown_ratio": round(unknown_ratio, 4),
            "two_column_blocks": layout_report["two_column_blocks"],
            "keep_together_blocks": layout_report["keep_together_blocks"],
        },
        "profile_coverage": profile_gate,
        "image_relation_integrity": image_gate,
        "image_visual_confirmation": image_visual_confirmation_gate,
        "review_outcomes": outcomes_gate,
        "print_render": {
            "status": "pass" if pdf_ok and print_qa["pdf_page_count"] is not None else "fail",
            "pdf_ok": pdf_ok,
            "pdf_message": pdf_message,
            "pdf_bytes": print_qa["pdf_bytes"],
            "pdf_page_count": print_qa["pdf_page_count"],
        },
        "source_evidence": {
            "status": "review" if visual_review_packets["count"] and not source_pdf else "pass",
            "source_pdf": source_pdf,
            "source_pdf_available": bool(source_pdf),
            "visual_review_packet_count": visual_review_packets["count"],
        },
        "auditability": {
            "status": "pass",
            "required_outputs": [
                "standard.md",
                "standard.html",
                "standard.pdf",
                "clean_standard.json",
                "clean_contract_report.json",
                "images/",
                "manifest.json",
                "standard_document.json",
                "standard_issue_candidates.json",
                "issue_candidate_disposition_audit.json",
                "issue_candidate_disposition_audit.html",
                "correction_log.json",
                "layout_report.json",
                "image_relation_report.json",
                "workbook_relation_audit.json",
                "workbook_relation_audit.html",
                "paired_vocabulary_report.json",
                "workbook_table_attachment_report.json",
                "workbook_virtual_question_group_report.json",
                "workbook_question_continuation_report.json",
                "image_visual_confirmation_packets.json",
                "image_visual_confirmation.html",
                "print_qa_report.json",
                "standard_acceptance_report.json",
                "standard_quality_score.json",
                "standard_product_status.json",
                "standard_visual_review_packets.json",
                "standard_review_outcomes.json",
                "review_outcomes.html",
                "visual_outcome_review.json",
                "visual_outcome_review.html",
                "workbook_profile_report.json",
                "workbook_profile.html",
                "review.html",
            ],
        },
        "review_threshold": review_threshold_gate,
    }
    standard_acceptance = {
        "schema": "luceon-standard-acceptance/v1",
        "status": acceptance_status(gates),
        "gates": gates,
        "summary": {
            "block_count": len(blocks),
            "outline_count": len(outline),
            "image_refs": len(set(refs)),
            "missing_images": len(missing_images),
            "correction_count": len(correction_log),
            "issue_candidate_count": len(issue_candidates),
            "issue_candidate_unresolved_blocking_count": issue_disposition_audit["unresolved_blocking_count"],
            "issue_candidate_disposition_counts": issue_disposition_audit["disposition_counts"],
            "visual_review_packet_count": visual_review_packets["count"],
            "visible_artifact_count": visible_artifacts["count"],
            "profile": selected_profile,
            "image_relation_count": image_relation_report["count"],
            "image_relation_source_visual_check_count": image_relation_report["source_visual_check_count"],
            "image_visual_confirmation_packet_count": image_visual_confirmation_packets["count"],
            "image_visual_confirmation_ready_crop_count": image_visual_confirmation_packets["crop_status_counts"].get("ready_for_source_crop", 0),
            "image_visual_confirmation_source_crop_count": source_crop_summary.get("source_crop_count", 0),
            "review_outcome_open_blocking_count": review_outcomes["open_blocking_count"],
            "review_outcome_closed_count": review_outcomes["closed_count"],
            "paired_vocabulary_group_count": paired_vocabulary_summary["group_count"],
            "paired_vocabulary_patched_table_count": paired_vocabulary_summary["patched_table_count"],
            "workbook_table_attachment_group_count": workbook_table_attachment_summary["group_count"],
            "workbook_table_attachment_patched_table_count": workbook_table_attachment_summary["patched_table_count"],
            "workbook_virtual_question_group_count": workbook_virtual_question_group_summary["group_count"],
            "workbook_virtual_grouped_question_count": workbook_virtual_question_group_summary["grouped_question_count"],
            "workbook_question_continuation_group_count": workbook_question_continuation_summary["group_count"],
            "workbook_question_continuation_grouped_question_count": workbook_question_continuation_summary["grouped_question_count"],
        },
    }
    quality_score = compute_quality_score(
        gates,
        layout_report,
        issue_candidates,
        visual_review_packets,
        print_qa,
        correction_log,
        issue_disposition_audit,
    )
    standard_acceptance["quality_score"] = {"score": quality_score["score"], "status": quality_score["status"]}
    product_status = build_standard_product_status(
        standard_acceptance,
        document,
        workbook_profile_report,
        review_outcomes,
        visual_review_packets,
        image_visual_confirmation_packets,
        source_crop_summary,
    )
    write_json(out_dir / "standard_acceptance_report.json", standard_acceptance)
    write_json(out_dir / "standard_quality_score.json", quality_score)
    write_json(out_dir / "standard_product_status.json", product_status)

    outputs = {
        "standard_md": "standard.md",
        "standard_html": "standard.html",
        "standard_pdf": "standard.pdf",
        "standard_document": "standard_document.json",
        "clean_standard": "clean_standard.json" if (out_dir / "clean_standard.json").exists() else "",
        "clean_contract_report": "clean_contract_report.json" if (out_dir / "clean_contract_report.json").exists() else "",
        "standard_issue_candidates": "standard_issue_candidates.json",
        "issue_candidate_disposition_audit": "issue_candidate_disposition_audit.json",
        "issue_candidate_disposition_audit_html": "issue_candidate_disposition_audit.html",
        "correction_log": "correction_log.json",
        "layout_report": "layout_report.json",
        "image_relation_report": "image_relation_report.json",
        "workbook_relation_audit": "workbook_relation_audit.json",
        "workbook_relation_audit_html": "workbook_relation_audit.html",
        "paired_vocabulary_report": "paired_vocabulary_report.json",
        "workbook_table_attachment_report": "workbook_table_attachment_report.json",
        "workbook_virtual_question_group_report": "workbook_virtual_question_group_report.json",
        "workbook_question_continuation_report": "workbook_question_continuation_report.json",
        "image_visual_confirmation_packets": "image_visual_confirmation_packets.json",
        "image_visual_confirmation_html": "image_visual_confirmation.html",
        "workbook_profile_report": "workbook_profile_report.json",
        "workbook_profile_html": "workbook_profile.html",
        "print_qa_report": "print_qa_report.json",
        "standard_acceptance_report": "standard_acceptance_report.json",
        "standard_quality_score": "standard_quality_score.json",
        "standard_product_status": "standard_product_status.json",
        "standard_visual_review_packets": "standard_visual_review_packets.json",
        "standard_review_outcomes": "standard_review_outcomes.json",
        "review_outcomes_html": "review_outcomes.html",
        "visual_outcome_review": "visual_outcome_review.json",
        "visual_outcome_review_html": "visual_outcome_review.html",
        "review_html": "review.html",
        "image_refs": len(set(refs)),
        "block_count": len(blocks),
        "outline_count": len(outline),
    }
    if source_crop_summary.get("source_crop_count"):
        outputs["source_crops"] = "source_crops/"
    outputs = {key: value for key, value in outputs.items() if value}

    manifest = {
        "schema": "luceon-eduassets-standard/v1",
        "pipeline_node": "clean_to_standard_mvp",
        "material_id": clean_manifest.get("material_id"),
        "run_id": clean_manifest.get("run_id"),
        "title": document["title"],
        "source_clean_manifest": str((clean_dir / "manifest.json").resolve()),
        "source_clean_standard": str(clean_standard_path.resolve()) if clean_standard_path.exists() else "",
        "source_raw_manifest": str((raw_dir / "manifest.json").resolve()) if raw_dir and (raw_dir / "manifest.json").exists() else "",
        "source_pdf": source_pdf,
        "profile": selected_profile,
        "outputs": outputs,
        "quality_score": {"score": quality_score["score"], "status": quality_score["status"]},
        "product_status": {
            "product_layer": product_status["product_layer"],
            "deliverable_use": product_status["deliverable_use"],
            "corpus_promotion_status": product_status["corpus_promotion"]["status"],
        },
        "acceptance": {
            "status": standard_acceptance["status"],
            "gates": {name: gate["status"] for name, gate in gates.items()},
        },
    }
    write_json(out_dir / "manifest.json", manifest)

    review_reports = {
        "acceptance": standard_acceptance,
        "issues": issue_candidates,
        "issue_disposition_audit": issue_disposition_audit,
        "quality_score": quality_score,
        "visual_review_packets": visual_review_packets,
        "image_visual_confirmation_packets": image_visual_confirmation_packets,
        "review_outcomes": review_outcomes,
        "visual_outcome_review": visual_outcome_review,
        "product_status": product_status,
    }
    (out_dir / "review.html").write_text(build_review_html(document, review_reports), encoding="utf-8")
    return standard_acceptance


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Standard MVP package from Clean package.")
    parser.add_argument("--clean-dir", required=True, type=Path, help="Local clean package directory containing clean.md.")
    parser.add_argument("--raw-dir", type=Path, help="Optional local raw body-final directory for image_semantics.json.")
    parser.add_argument("--source-pdf", type=Path, help="Optional original source PDF for visual review evidence.")
    parser.add_argument("--profile", default="auto", choices=["auto", *sorted(PROFILE_CHOICES)], help="Standard profile to apply.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output standard-final directory.")
    parser.add_argument("--chrome", help="Chrome/Chromium executable for PDF rendering.")
    parser.add_argument("--generate-source-crops", action="store_true", help="Generate heavy source PDF crop review artifacts during this run.")
    parser.add_argument("--require-clean-standard", action="store_true", help="Fail unless clean_standard.json is present and consumed.")
    parser.add_argument("--force", action="store_true", help="Delete out-dir before writing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.force and args.out_dir.exists():
        shutil.rmtree(args.out_dir)
    try:
        acceptance = build_package(
            args.clean_dir,
            args.out_dir,
            args.raw_dir,
            args.chrome,
            source_pdf_path=args.source_pdf,
            profile=args.profile,
            generate_source_crops=args.generate_source_crops,
            require_clean_standard=args.require_clean_standard,
        )
    except Exception as exc:
        print(f"standard_from_clean failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"out_dir": str(args.out_dir), "status": acceptance["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
