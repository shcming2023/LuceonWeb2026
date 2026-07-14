from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class SourceCrop:
    target_name: str
    source_page: int
    box: tuple[float, float, float, float]
    rationale: str
    processing: str = "none"


THEME_READING_CROPS = (
    SourceCrop(
        "a4d4006a611cf804e538be095226512078381a68c3e0543a2c18750618435348.jpg",
        12,
        (0.230, 0.575, 0.490, 0.825),
        "Replace the contaminated MinerU collage with the source-faithful visual region.",
    ),
    SourceCrop(
        "4e1bd2ad416ef017ddcd229951008fbce1aa77636a6a6f1ad4b3f0dec7cc5c5a.jpg",
        15,
        (0.280, 0.670, 0.442, 0.812),
        "Restore the Guangfulin museum photograph from the source scan.",
    ),
    SourceCrop(
        "4298beb076a629e9c03c88766e859e3204375e77ef906b22736eb988f80ee01e.jpg",
        15,
        (0.490, 0.805, 0.575, 0.865),
        "Restore answer image A at printable resolution.",
    ),
    SourceCrop(
        "a3f617cefb83852c14ab7d6d2178a429e76016c53e6d188f27733219c9fd7506.jpg",
        15,
        (0.580, 0.805, 0.665, 0.865),
        "Restore answer image B at printable resolution.",
    ),
    SourceCrop(
        "cef38b2d8e4409d6aa73fb5b3c8a8fab27e2942b3c0f38a37580370e56f68f9d.jpg",
        15,
        (0.490, 0.900, 0.575, 0.960),
        "Restore answer image C at printable resolution.",
    ),
    SourceCrop(
        "cd624c2bcf12a21ab531bcc79d763273798ad23fb72808ae1bf008e314e32d87.jpg",
        15,
        (0.580, 0.900, 0.665, 0.960),
        "Restore answer image D at printable resolution.",
    ),
)

NEW_QUESTION_TYPES_CROPS = (
    SourceCrop(
        "aeb7fe1ed409252d2039a32e2fcd6fb39ed32b78655e74ed30c6319f417d6bb0.jpg",
        21,
        (0.205, 0.245, 0.450, 0.515),
        "Restore the Pelé photograph from the source page at printable resolution.",
        "denoise_autocontrast",
    ),
    SourceCrop(
        "52c9dcea6c953447c5095c453059fc10c1cdf5a67ccd6acb91e5c890b3c316ce.jpg",
        21,
        (0.470, 0.645, 0.570, 0.742),
        "Restore the synonym panel from the source page at printable resolution.",
    ),
    SourceCrop(
        "14d6f4e4086deaf1deff46cd2dca4ea33ce1df8b23dc0309f0abf5397bba62d0.jpg",
        24,
        (0.145, 0.735, 0.460, 0.975),
        "Restore only the teamwork illustration and exclude adjacent sentence text.",
    ),
    SourceCrop(
        "47a379df0a30a4df8c5b09d48cc4fb5d0e2689d867613da46a17b3e44314212b.jpg",
        27,
        (0.800, 0.490, 0.935, 0.610),
        "Restore the film still from the source page at printable resolution.",
    ),
)

GREAT_WRITING_3_CROPS = (
    SourceCrop(
        "e6224e4385f0ad83d7ce8cd0047ce42bfcd0bc23c83a8c1c1d626f9bcf37d0c3.jpg",
        89,
        (0.0, 0.0, 1.0, 0.41),
        "Restore the complete Oksana Masters photograph and its source caption instead of the clipped MinerU extract.",
    ),
)

CHINESE_PRIMARY_MATH_CROPS = (
    SourceCrop(
        "9106734a704602b7b8788fbac87936e005772083f20bb9998a138929d03404c9.jpg",
        28,
        (0.49, 0.603, 0.67, 0.645),
        "Restore option C in the rectangle-area question from the full-resolution source page.",
    ),
    SourceCrop(
        "7d2cbc20544730c353f43cedff645e5a5aaa12e00b9581bc6e2f8c5e123b269c.jpg",
        148,
        (0.24, 0.76, 0.82, 0.93),
        "Restore the complete angle-size speech illustration instead of the clipped character-only extract.",
    ),
)

KNOWN_SOURCE_CROPS = (
    THEME_READING_CROPS
    + NEW_QUESTION_TYPES_CROPS
    + GREAT_WRITING_3_CROPS
    + CHINESE_PRIMARY_MATH_CROPS
)


def reconstruct_source_images(
    project_dir: Path,
    source_pdf: Path,
    *,
    crops: tuple[SourceCrop, ...] = KNOWN_SOURCE_CROPS,
) -> dict:
    """Replace known degraded extracts with deterministic crops from the source PDF."""
    existing = [crop for crop in crops if (project_dir / "images" / crop.target_name).exists()]
    if not existing:
        return {"schema": "luceon.source-image-reconstruction/v1", "replacements": []}

    render_dir = project_dir.parent / ".source-image-pages"
    render_dir.mkdir(parents=True, exist_ok=True)
    rendered: dict[int, Path] = {}
    replacements = []
    with fitz.open(source_pdf) as document:
        for crop in existing:
            page_image = rendered.get(crop.source_page)
            if page_image is None:
                page = document.load_page(crop.source_page - 1)
                scale = 3000 / page.rect.width
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                page_image = render_dir / f"page-{crop.source_page}.png"
                pixmap.save(page_image)
                rendered[crop.source_page] = page_image

            with Image.open(page_image) as page:
                width, height = page.size
                left, top, right, bottom = crop.box
                pixels = (
                    round(left * width),
                    round(top * height),
                    round(right * width),
                    round(bottom * height),
                )
                replacement = page.crop(pixels).convert("RGB")
                if crop.processing == "denoise_autocontrast":
                    replacement = ImageOps.autocontrast(replacement.filter(ImageFilter.MedianFilter(size=3)), cutoff=1)
                target = project_dir / "images" / crop.target_name
                replacement.save(target, format="JPEG", quality=95, subsampling=0)
            replacements.append(
                {
                    **asdict(crop),
                    "pixel_box": pixels,
                    "output_size": list(replacement.size),
                    "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )

    layout_changes = _normalize_theme_reading_layout(project_dir)
    report = {
        "schema": "luceon.source-image-reconstruction/v1",
        "source_pdf_sha256": hashlib.sha256(source_pdf.read_bytes()).hexdigest(),
        "render_width": 3000,
        "replacements": replacements,
        "layout_changes": layout_changes,
    }
    (project_dir.parent / "source-image-reconstruction.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def _normalize_theme_reading_layout(project_dir: Path) -> list[str]:
    content_path = project_dir / "chapters" / "content.tex"
    if not content_path.exists():
        return []
    content = content_path.read_text(encoding="utf-8")
    changes = []

    option_c = (
        r"\includegraphics[width=0.10\textwidth]"
        r"{images/9106734a704602b7b8788fbac87936e005772083f20bb9998a138929d03404c9.jpg}"
    )
    if option_c in content:
        content = content.replace(option_c, option_c.replace("0.10", "0.30"), 1)
        changes.append("chinese_primary_math_option_c_scaled")

    synonym_panel = re.compile(
        r"\\begin\{figure\}\[H\](?:(?!\\end\{figure\}).)*"
        r"52c9dcea6c953447c5095c453059fc10c1cdf5a67ccd6acb91e5c890b3c316ce\.jpg"
        r"(?:(?!\\end\{figure\}).)*\\end\{figure\}",
        re.DOTALL,
    )
    synonym_replacement = (
        r"\begin{center}\fbox{\begin{tabular}{c}"
        r"\rule{3.2em}{0.4pt}\,2\,\rule{3.2em}{0.4pt}\\"
        r"\textbf{SYNONYM}\\"
        r"\rule{3.2em}{0.4pt}\,4\,\rule{3.2em}{0.4pt}"
        r"\end{tabular}}\end{center}"
    )
    content, count = synonym_panel.subn(lambda _match: synonym_replacement, content, count=1)
    if count:
        changes.append("synonym_panel_vectorized")

    facility_pattern = re.compile(
        r"\\begin\{figure\}\[H\](?:(?!\\end\{figure\}).)*391bd04ad9c2bb2a443e05dd09938f67d6f664ee47567edd65885aa4471915ca\.jpg"
        r"(?:(?!\\end\{figure\}).)*\\end\{figure\}.*?"
        r"Power banks \(移动电源\) for rent",
        re.DOTALL,
    )
    facility_replacement = r"""\begin{multicols}{2}
\begin{itemize}[leftmargin=1.5em]
\item Parking
\item Guided tours
\item Strollers (婴儿车) for rent
\item Vending machines (自动售货机)
\item Toilets
\item Luggage storage
\item Wheelchairs for rent
\item Power banks (移动电源) for rent
\end{itemize}
\end{multicols}"""
    content, count = facility_pattern.subn(lambda _match: facility_replacement, content, count=1)
    if count:
        changes.append("facilities_text_grid")

    names = [crop.target_name for crop in THEME_READING_CROPS[2:]]
    def figure_block(name: str) -> str:
        return (
            r"\\begin\{figure\}\[H\](?:(?!\\end\{figure\}).)*"
            + re.escape(name)
            + r"(?:(?!\\end\{figure\}).)*\\end\{figure\}\s*"
        )

    figures_pattern = re.compile("".join(figure_block(name) for name in names), re.DOTALL)
    cells = []
    for label, name in zip("ABCD", names, strict=True):
        cells.append(
            rf"\begin{{minipage}}[t]{{0.46\textwidth}}\centering"
            rf"\includegraphics[width=0.88\linewidth,height=0.12\textheight,keepaspectratio]{{images/{name}}}\\"
            rf"\textbf{{{label}}}\end{{minipage}}"
        )
    figures_replacement = (
        "\\begin{center}\n"
        + cells[0] + "\\hfill\n" + cells[1] + r"\\[0.8em]" + "\n"
        + cells[2] + "\\hfill\n" + cells[3]
        + "\n\\end{center}\n\n"
    )
    content, count = figures_pattern.subn(lambda _match: figures_replacement, content, count=1)
    if count:
        changes.append("choice_image_grid")

    cloze_start = content.find("No, They're Not Photographs")
    cloze_end = content.find("% source", cloze_start + 1) if cloze_start >= 0 else -1
    if cloze_start >= 0 and cloze_end > cloze_start:
        chapter = content[cloze_start:cloze_end]
        blank_block = re.compile(
            r"\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{\d+\}\s*)?"
            r"\\item\s*\\rule\{2\.0em\}\{0\.4pt\}\s*\\end\{enumerate\}|"
            r"\d+\.\\rule\{2\.0em\}\{0\.4pt\}",
            re.DOTALL,
        )
        cleaned, removed = blank_block.subn("", chapter)
        if removed:
            first_anchor = "The final results, however, are always \\rule{2.0em}{0.4pt}4\\rule{2.0em}{0.4pt}."
            second_anchor = "artworks that must be seen to be believed!"
            first_answers = "\n\n\\noindent " + r"\textbf{1.} \rule{5em}{0.4pt}\quad \textbf{2.} \rule{5em}{0.4pt}\quad \textbf{3.} \rule{5em}{0.4pt}\quad \textbf{4.} \rule{5em}{0.4pt}"
            second_answers = "\n\n\\noindent " + r"\textbf{5.} \rule{5em}{0.4pt}\quad \textbf{6.} \rule{5em}{0.4pt}\quad \textbf{7.} \rule{5em}{0.4pt}\quad \textbf{8.} \rule{5em}{0.4pt}"
            cleaned = cleaned.replace(first_anchor, first_anchor + first_answers, 1)
            cleaned = cleaned.replace(second_anchor, second_anchor + second_answers, 1)
            content = content[:cloze_start] + cleaned + content[cloze_end:]
            changes.append("cloze_answer_rows_restored")

    fairy_start = content.find('Doors for "Fairies"')
    fairy_end = content.find("% source", fairy_start + 1) if fairy_start >= 0 else -1
    if fairy_start >= 0 and fairy_end > fairy_start:
        chapter = content[fairy_start:fairy_end]
        chapter = chapter.replace('Doors for "Fairies"', r"\chapter{Doors for ``Fairies''}", 1)
        blank_block = re.compile(
            r"\\begin\{enumerate\}\s*(?:\\setcounter\{enumi\}\{\d+\}\s*)?"
            r"\\item\s*\\rule\{2\.0em\}\{0\.4pt\}\s*\\end\{enumerate\}",
            re.DOTALL,
        )
        chapter, removed = blank_block.subn("", chapter)
        if removed:
            row_one = "\n\n\\noindent " + r"\textbf{1.} \rule{5em}{0.4pt}\quad \textbf{2.} \rule{5em}{0.4pt}\quad \textbf{3.} \rule{5em}{0.4pt}\quad \textbf{4.} \rule{5em}{0.4pt}"
            row_two = "\n\n\\noindent " + r"\textbf{5.} \rule{5em}{0.4pt}\quad \textbf{6.} \rule{5em}{0.4pt}\quad \textbf{7.} \rule{5em}{0.4pt}\quad \textbf{8.} \rule{5em}{0.4pt}"
            chapter = chapter.replace("exactly how many there are.", "exactly how many there are." + row_one, 1)
            chapter = chapter.replace("see more fairy doors in the future!", "see more fairy doors in the future!" + row_two, 1)
        content = content[:fairy_start] + chapter + content[fairy_end:]
        changes.append("fairy_doors_chapter_restored")

    if "pull s" in content:
        content = content.replace("pull s", "pulls", 1)
        changes.append("ocr_pull_s_fixed")

    arrow_count = content.count("▶")
    if arrow_count:
        content = content.replace("▶", r"\(\blacktriangleright\)")
        changes.extend(["unsupported_arrow_glyph_replaced"] * arrow_count)

    orphan_targets = (
        r"\item 新规定让许多学生感到困惑。(confused)",
        r"\item 我试图跑得更快,但还是赶不上他的速度。",
        r"\item 我的祖母对我的童年有着深远的影响。(influence n.)",
    )
    for target in orphan_targets:
        marker = r"\enlargethispage{12\baselineskip}" + "\n"
        if target in content and marker + target not in content:
            content = content.replace(target, marker + target, 1)
            changes.append("prechapter_tail_compacted")

    overextended = (
        r"\enlargethispage{12\baselineskip}" + "\n"
        + r"\item 如果我们不仔细规划这次旅行, 可能会遇到麻烦。"
    )
    if overextended in content:
        content = content.replace(overextended, r"\item 如果我们不仔细规划这次旅行, 可能会遇到麻烦。", 1)
        changes.append("overextended_tail_reverted")

    final_chatgpt_item = r"\item 没有任何在线视频能够与观看现场演唱会的体验相媲美。(match v.)"
    old_chatgpt_marker = r"\enlargethispage{5\baselineskip}" + "\n"
    final_chatgpt_marker = r"\enlargethispage{8\baselineskip}" + "\n"
    content = content.replace(old_chatgpt_marker + final_chatgpt_item, final_chatgpt_item, 1)
    if final_chatgpt_item in content and final_chatgpt_marker + final_chatgpt_item not in content:
        content = content.replace(final_chatgpt_item, final_chatgpt_marker + final_chatgpt_item, 1)
        changes.append("final_chatgpt_item_compacted")
    late_marker = (
        r"\printshortanswer" + "\n" + r"\begin{enumerate}" + "\n"
        + r"\setcounter{enumi}{4}" + "\n" + final_chatgpt_marker + final_chatgpt_item
    )
    early_marker = (
        final_chatgpt_marker + r"\printshortanswer" + "\n" + r"\begin{enumerate}" + "\n"
        + r"\setcounter{enumi}{4}" + "\n" + final_chatgpt_item
    )
    if late_marker in content:
        content = content.replace(late_marker, early_marker, 1)
        changes.append("final_chatgpt_marker_moved_before_break")

    chatgpt_start = content.find("ChatGPT Has Taken Their Jobs")
    chatgpt_end = content.find("% source", chatgpt_start + 1) if chatgpt_start >= 0 else -1
    if chatgpt_start >= 0 and chatgpt_end > chatgpt_start:
        chapter = content[chatgpt_start:chatgpt_end]
        if r"\begingroup\small" not in chapter and "Quiz\n\n" in chapter:
            chapter = chapter.replace("Quiz\n\n", "Quiz\n\n" + r"\begingroup\small" + "\n", 1)
            chapter = chapter.rstrip() + "\n" + r"\endgroup" + "\n\n"
            content = content[:chatgpt_start] + chapter + content[chatgpt_end:]
            changes.append("chatgpt_quiz_compacted")

    task_heading = r"\exerciseheading{II. Answer the questions.}" + "\n\n" + r"\exerciseheading{Task 1:}"
    guarded_task_heading = r"\Needspace{12\baselineskip}" + "\n" + task_heading
    unguarded_count = content.count(task_heading) - content.count(guarded_task_heading)
    if unguarded_count:
        content = content.replace(task_heading, guarded_task_heading)
        changes.extend(["answer_task_heading_guarded"] * unguarded_count)

    fairy_translation = (
        r"\exerciseheading{IV. Translate the sentences according to the Chinese.}" + "\n\n"
        + r"\begin{enumerate}" + "\n" + r"\item 看起来这周展览不会开放。(sign n.)"
    )
    guarded_fairy_translation = r"\Needspace{18\baselineskip}" + "\n" + fairy_translation
    if fairy_translation in content and guarded_fairy_translation not in content:
        content = content.replace(fairy_translation, guarded_fairy_translation, 1)
        changes.append("fairy_translation_heading_guarded")

    if changes:
        content_path.write_text(content, encoding="utf-8")
    return changes
