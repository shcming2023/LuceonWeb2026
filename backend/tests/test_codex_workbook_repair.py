from __future__ import annotations

import json
from pathlib import Path

import fitz

from app.services.codex_workbook_repair import repair_staging_candidate, repair_workbook_project


def _image(path: Path, width: int, height: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
    pixmap.clear_with(255)
    pixmap.save(path)


def _project(root: Path, content: str) -> Path:
    project = root / "project"
    (project / "chapters").mkdir(parents=True)
    (project / "main.tex").write_text("\\documentclass{book}\n", encoding="utf-8")
    (project / "chapters" / "content.tex").write_text(content, encoding="utf-8")
    return project


def test_repair_regroups_strict_choice_matrix_without_losing_workbook_content(tmp_path):
    content = """\\chapter{Complete lesson}
\\exerciseheading{Choose the best answer.}
\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{1.} A. one\\par

\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{2.} A. two\\par

\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{3.} A. three\\par

\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{4.} A. four\\par

B. first

B. second

B. third

B. fourth

C. alpha

C. beta

C. gamma

C. delta

Final substantive source sentence remains here.
\\printshortanswer
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["status"] == "changed"
    assert report["choice_matrices_regrouped"] == 1
    assert report["before"] == report["after"] == {
        "chapters": 1,
        "exercise_headings": 1,
        "answer_surfaces": 1,
    }
    assert r"\item A. one\quad B. first\quad C. alpha" in repaired
    assert r"\usepackage{needspace}" in (project / "main.tex").read_text(encoding="utf-8")
    assert "Final substantive source sentence remains here." in repaired
    assert r"\printshortanswer" in repaired

    second = repair_workbook_project(project)
    assert second["status"] == "unchanged"
    assert second["choice_matrices_regrouped"] == 0


def test_repair_caps_only_targeted_low_resolution_images(tmp_path):
    content = """\\chapter{Images}
\\includegraphics[width=0.78\\textwidth]{images/portrait.png}
Some teaching text between figures.
\\includegraphics[width=0.78\\textwidth]{images/pair-a.png}

\\includegraphics[width=0.78\\textwidth]{images/pair-b.png}
\\includegraphics[width=0.78\\textwidth]{images/high-resolution.png}
"""
    project = _project(tmp_path, content)
    _image(project / "images" / "portrait.png", 395, 470)
    _image(project / "images" / "pair-a.png", 470, 376)
    _image(project / "images" / "pair-b.png", 344, 385)
    _image(project / "images" / "high-resolution.png", 1200, 800)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["low_resolution_images_capped"] == 3
    assert r"width=0.52\textwidth,height=0.22\textheight,keepaspectratio]{images/portrait.png}" in repaired
    assert r"width=0.54\textwidth,height=0.22\textheight,keepaspectratio]{images/pair-a.png}" in repaired
    assert r"width=0.50\textwidth,height=0.22\textheight,keepaspectratio]{images/pair-b.png}" in repaired
    assert r"width=0.78\textwidth]{images/high-resolution.png}" in repaired


def test_repair_recovers_one_ocr_shifted_a_option_number(tmp_path):
    content = """\\chapter{OCR shifted options}
\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{1.} A. one\\par

\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{2.} A. two\\par

2.A.three

\\par\\Needspace{2\\baselineskip}\\noindent\\textbf{3.} A. four\\par

B. first
B. second
B. third
B. fourth
C. alpha
C. beta
C. gamma
C. delta
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    matrix = report["choice_matrices"][0]
    assert matrix["source_numbers"] == [1, 2, 2, 3]
    assert matrix["renumbered_from_source"] is True
    assert r"\item A. three\quad B. third\quad C. gamma" in repaired
    assert "2.A.three" not in repaired


def test_repair_removes_duplicate_image_labels_and_adds_local_writing_space(tmp_path):
    labels = (
        "Window Washing machine Bedside table Bed Shelf Front Bedroom Bed Shelf Wardrobe Shelf "
        "Wardrobe Bedside table Bed Back Bedroom Chair Desk Shoe shelf TV cabinet Bookcase Coffee "
        "table Living Room Dining table Chairs Arm-chair Arm-chair Shower room Toilet Bathroom Kitchen "
        "Fridge Cooker Cupboard Sink Window Window South North"
    )
    content = f"""\\chapter{{Furniture}}
\\exerciseheading{{Complete the table according to the article.}}
What can be done to improve the arrangement? Give Sam at least four pieces of advice.
\\begin{{figure}}[H]
\\includegraphics[width=0.70\\textwidth]{{images/plan.png}}
\\end{{figure}}
\\emph{{{labels}}}
\\chapter{{Next lesson}}
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["duplicate_image_ocr_labels_removed"] == 1
    assert report["before"]["answer_surfaces"] == 0
    assert report["after"]["answer_surfaces"] == 1
    assert labels not in repaired
    assert r"\printlonganswer" in repaired


def test_repair_normalizes_profile_restores_cloze_numbers_and_adds_translation_space(tmp_path):
    content = r"""\chapter{Enjoy Being a Teenager}
\begin{infobox}
\begin{itemize}
\item[\textbf{语篇类型}] 随笔
\item[\textbf{词数}] 353
\item[\textbf{难度}] 3级
\end{itemize}
\end{infobox}
范畴: 人与自我 (生活与学习)
教材链接: 新教材 8AU4 (Then and now)
\exerciseheading{I. Choose the best words or phrases to complete the passage.}
First \rule{2.0em}{0.4pt} second sentence fragment
\begin{figure}[H]
\includegraphics[width=0.78\textwidth]{images/class.png}
\end{figure}
continues here before \rule{2.0em}{0.4pt}2\rule{2.0em}{0.4pt}
third \rule{2.0em}{0.4pt}3\rule{2.0em}{0.4pt} fourth \rule{2.0em}{0.4pt}
fifth \rule{2.0em}{0.4pt}5\rule{2.0em}{0.4pt}.
\begin{vocabbox}
words
\end{vocabbox}
\exerciseheading{II. Translate the following expressions from English to Chinese.}
\par\Needspace{2\baselineskip}\noindent\textbf{1.} nine out of ten\par

\par\Needspace{2\baselineskip}\noindent\textbf{2.} consist of\par
\exerciseheading{III. Complete the sentences with the words below. Each word can be used twice.}
catch escape matter present
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["metadata_infoboxes_normalized"] == 1
    assert report["cloze_blank_numbers_restored"] == 2
    assert report["translation_answer_spaces_added"] == 2
    assert r"\begin{description}[leftmargin=0pt,labelindent=0pt]" in repaired
    assert r"\item[\textbf{范围}] 人与自我 (生活与学习)" in repaired
    assert r"\item[\textbf{教材链接}] 新教材 8AU4 (Then and now)" in repaired
    assert report["sentence_split_figures_repaired"] == 1
    assert r"\includegraphics[width=0.50\textwidth]{images/class.png}" in repaired
    assert "second sentence fragment continues here before" in repaired
    assert r"\rule{2.0em}{0.4pt}1\rule{2.0em}{0.4pt}" in repaired
    assert r"\rule{2.0em}{0.4pt}4\rule{2.0em}{0.4pt}" in repaired
    assert repaired.count(r"\printshortanswer") == 2
    assert report["word_banks_formatted"] == 1
    assert r"\fbox{\begin{tabular}{cccc}" in repaired


def test_staging_repair_uses_reported_project_and_worker_blockers(tmp_path):
    project = _project(tmp_path, "\\chapter{Lesson}\n\\printshortanswer\n")
    (tmp_path / "latex_polish_report.json").write_text(
        json.dumps({"project_dir": str(project)}),
        encoding="utf-8",
    )
    (tmp_path / "worker_quality_report.json").write_text(
        json.dumps({"hard_blockers": [{"code": "source_tail_anchor_missing"}]}),
        encoding="utf-8",
    )

    report = repair_staging_candidate(tmp_path)

    assert report["status"] == "unchanged"
    assert report["worker_blockers"] == ["source_tail_anchor_missing"]
    assert (tmp_path / "deterministic_repair_report.json").is_file()


def test_repair_regroups_column_major_options_wrapped_in_isolated_enumerates(tmp_path):
    content = r"""\chapter{Choices}
\exerciseheading{Choose.}
\begin{enumerate}
\item A. one
\end{enumerate}
\printshortanswer
\begin{enumerate}
\item A two
\end{enumerate}
\printshortanswer
\begin{enumerate}
\item A. three
\end{enumerate}
\printshortanswer
\begin{enumerate}
\item A. four
\end{enumerate}
\printshortanswer
B. first
B. second
B. third
B. fourth
C. alpha
C. beta
C. gamma
C. delta
D. red
D. blue
D. green
D. gold
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["choice_matrices_regrouped"] == 1
    assert report["misplaced_option_answer_spaces_removed"] == 4
    assert report["source_before"]["answer_surfaces"] == 4
    assert report["after"]["answer_surfaces"] == 0
    assert r"\item A. two\quad B. second\quad C. beta\quad D. blue" in repaired
    assert repaired.count(r"\begin{enumerate}") == 1


def test_repair_removes_qr_marketing_figure_and_generic_caption(tmp_path):
    content = r"""\chapter{Figures}
\begin{figure}[H]
\includegraphics[width=0.54\textwidth]{images/qr.png}
\caption{扫描上方二维码获取语音及习题答案}
\end{figure}
日直上万二目同 订购多目程展展展
日星上方二道可仅置 遥目自望及之直百富
\begin{figure}[H]
\includegraphics[width=0.50\textwidth]{images/lesson.png}
\caption{image}
\end{figure}
Lesson text remains.
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["qr_marketing_figures_removed"] == 1
    assert report["qr_ocr_residue_lines_removed"] == 2
    assert "qr.png" not in repaired
    assert "订购" not in repaired
    assert "lesson.png" in repaired
    assert r"\caption{image}" not in repaired
    assert "Lesson text remains." in repaired


def test_repair_removes_marketing_outer_figure_but_preserves_nested_teaching_figure(tmp_path):
    content = r"""\chapter{Nested figure}
\begin{figure}[H]
\includegraphics[width=0.50\textwidth]{images/uncaptioned.png}
\end{figure}
Sentence begins
\begin{figure}[H]
\includegraphics[width=0.18\textwidth]{images/qr.png}
\caption{日用上方二维码获取语音}
\begin{figure}[H]
\includegraphics[width=0.50\textwidth]{images/lesson.png}
\caption{image}
\end{figure}
\end{figure} and continues.
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["qr_marketing_figures_removed"] == 1
    assert "qr.png" not in repaired
    assert "lesson.png" in repaired
    assert "uncaptioned.png" in repaired
    assert repaired.count(r"\begin{figure}[H]") == repaired.count(r"\end{figure}") == 2
    assert "Sentence begins and continues." in repaired


def test_repair_continues_split_enumerates_and_adds_translation_lines(tmp_path):
    content = r"""\chapter{Practice}
\exerciseheading{III. Translate the sentences according to the Chinese.}
\begin{enumerate}
\item First sentence.
\end{enumerate}
English continuation for the first sentence.
\begin{enumerate}
\item Second sentence.
\end{enumerate}
\begin{enumerate}
\item Third sentence.
\end{enumerate}
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["exercise_numbering_blocks_fixed"] == 2
    assert r"\setcounter{enumi}{1}" in repaired
    assert r"\setcounter{enumi}{2}" in repaired
    assert report["translation_answer_spaces_added"] == 3
    assert repaired.count(r"\printshortanswer") == 3
    assert repaired.index("English continuation for the first sentence.") < repaired.index(r"\printshortanswer")

    second_report = repair_workbook_project(project)
    repaired_again = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert second_report["translation_answer_spaces_added"] == 0
    assert repaired_again == repaired


def test_repair_corrects_stale_existing_enumerate_counters(tmp_path):
    content = r"""\chapter{Practice}
\exerciseheading{IV. Translate the sentences according to the Chinese.}
\begin{enumerate}
\item First.
\end{enumerate}
\begin{enumerate}
\setcounter{enumi}{9}
\item Second.
\item Third.
\end{enumerate}
\begin{enumerate}
\setcounter{enumi}{12}
\item Fourth.
\end{enumerate}
"""
    project = _project(tmp_path, content)
    repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert r"\setcounter{enumi}{1}" in repaired
    assert r"\setcounter{enumi}{3}" in repaired
    assert r"\setcounter{enumi}{9}" not in repaired
    assert r"\setcounter{enumi}{12}" not in repaired


def test_repair_restores_escaped_ocr_blank_and_option_placeholders(tmp_path):
    content = r"""\chapter{OCR}
Sentence \_4 \{\{\{\{\{\ensuremath{{}_and} frequency.
4. \{\{\{\{\{\ensuremath{{}_A} . available
B. forms
C. further
D. final
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["ocr_placeholder_runs_repaired"] == 2
    assert r"\rule{2.0em}{0.4pt}4\rule{2.0em}{0.4pt} and frequency." in repaired
    assert "4. A. available" in repaired
    assert r"\{\{\{\{" not in repaired


def test_repair_promotes_heading_embedded_at_end_of_previous_enumerate(tmp_path):
    content = r"""\chapter{Embedded heading}
\begin{enumerate}
\item Previous exercise.
IV. Translate the sentences according to the Chinese.
\end{enumerate}
\begin{enumerate}
\setcounter{enumi}{8}
\item 中文题干。
\end{enumerate}
English answer fragment.
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["embedded_exercise_headings_promoted"] == 1
    assert r"\exerciseheading{IV. Translate the sentences according to the Chinese.}" in repaired
    assert r"\setcounter{enumi}{8}" not in repaired
    assert r"\Needspace{6\baselineskip}" not in repaired
    assert repaired.index("English answer fragment.") < repaired.index(r"\printshortanswer")


def test_repair_removes_source_evidence_debug_block_and_technical_cover_metadata(tmp_path):
    content = r"""\chapter{Lesson}
{\scriptsize
\setlength{\tabcolsep}{2pt}
\renewcommand{\arraystretch}{1.15}
\par\begingroup\small\ttfamily
((( source table evidence 1. A. alpha B. beta source table evidence\par
\endgroup
}
Student-facing lesson text.
"""
    project = _project(tmp_path, content)
    (project / "main.tex").write_text(
        r"""\documentclass{book}
\title{Lesson.pdf}
\subtitle{Worker V2 candidate}
\author{Luceon}
\date{\today}
\version{Reviewed}
{\normalsize\color{gray}
\begin{tabular}{l}
Luceon\\
\today\\
Reviewed\\
\end{tabular}}
\begin{document}
\end{document}
""",
        encoding="utf-8",
    )
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    main = (project / "main.tex").read_text(encoding="utf-8")
    assert report["source_table_evidence_blocks_removed"] == 1
    assert "source table evidence" not in repaired
    assert "Student-facing lesson text." in repaired
    assert "Worker V2" not in main
    assert "Luceon" not in main
    assert "Reviewed" not in main
    assert r"\title{Lesson}" in main


def test_repair_detects_wide_double_qr_image(tmp_path):
    content = r"""\chapter{Lesson}
\begin{figure}[H]
\includegraphics[width=0.54\textwidth]{images/double-qr.png}
\end{figure}
Student-facing lesson text.
"""
    project = _project(tmp_path, content)
    image_path = project / "images" / "double-qr.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 220, 100), False)
    samples = bytearray([255] * (220 * 100 * 3))
    for y in range(10, 90):
        for x in list(range(10, 100)) + list(range(120, 210)):
            if ((x // 5) + (y // 5)) % 2 == 0:
                offset = (y * 220 + x) * 3
                samples[offset : offset + 3] = b"\x00\x00\x00"
    pix = fitz.Pixmap(fitz.csRGB, 220, 100, bytes(samples), False)
    pix.save(str(image_path))

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["qr_marketing_figures_removed"] == 1
    assert "double-qr.png" not in repaired
    assert "Student-facing lesson text." in repaired


def test_repair_cleans_ocr_debug_blocks_math_prose_and_duplicate_caption(tmp_path):
    prose = "Push-ups are actually a human movement. " * 4
    duplicate = "Imagine an underwater camera that could take photos anywhere in the sea. " * 6
    content = rf"""\chapter{{Lesson}}
${prose}$
\par\begingroup\small\ttfamily\raggedright
(((6.)))\par
\endgroup
\par\begingroup\small\ttfamily\raggedright
We are really \_3 ()()()()()()\_that they live so long.\par
\endgroup
\begin{{figure}}[H]
\includegraphics[width=0.5\textwidth]{{images/lesson.png}}
\caption{{{duplicate}}}
\end{{figure}}
*{duplicate}*
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["debug_number_markers_removed"] == 1
    assert report["accidental_math_prose_unwrapped"] == 1
    assert report["ocr_parenthesis_blanks_repaired"] == 1
    assert report["duplicate_long_captions_removed"] == 1
    assert "(((6.)))" not in repaired
    assert f"${prose}$" not in repaired
    assert r"\rule{2.0em}{0.4pt}3\rule{2.0em}{0.4pt}" in repaired
    assert r"\ttfamily" not in repaired
    assert r"\caption{" not in repaired
    assert duplicate in repaired


def test_repair_regroups_inline_column_options_and_private_use_cloze(tmp_path):
    content = """\\chapter{Lesson}
Sentence \ue0004\\rule{2.0em}{0.4pt}5\ue000 continues.
\\begin{enumerate}
\\item A. alpha
\\item A. beta
\\end{enumerate}
B. bravo B. bicycle
C. cat C. circle
D. dog D. diamond
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["private_use_cloze_blanks_repaired"] == 1
    assert r"\rule{2.0em}{0.4pt}5\rule{2.0em}{0.4pt}" in repaired
    assert r"\item A. alpha\quad B. bravo\quad C. cat\quad D. dog" in repaired
    assert r"\item A. beta\quad B. bicycle\quad C. circle\quad D. diamond" in repaired


def test_repair_cleans_escaped_placeholder_names_and_adds_written_response_space(tmp_path):
    content = r"""\chapter{Lesson}
\_3 \{\{\{\{\{\ensuremath{{}_water-loving} trees.
- 2 \{\{\{\{\{\ensuremath{{}_Kevin} wants to join.
\item 4 \{\{\{\{\{\ensuremath{{}_Chloe} wants to join.
Give Sam at least four pieces of advice.
\begin{figure}[H]
\includegraphics[width=0.5\textwidth]{images/room.jpg}
\end{figure}
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["ocr_placeholder_runs_repaired"] == 3
    assert report["written_response_spaces_added"] == 1
    assert "water-loving" in repaired
    assert "- 2. Kevin wants to join." in repaired
    assert r"\item 4. Chloe wants to join." in repaired
    assert repaired.index(r"\end{figure}") < repaired.index(r"\printlonganswer")


def test_repair_compacts_sequential_single_answer_blocks_before_chapter(tmp_path):
    content = r"""\chapter{One}
Passage.
\begin{enumerate}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
\begin{enumerate}
\setcounter{enumi}{1}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
3.
\begin{enumerate}
\setcounter{enumi}{3}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
\chapter{Two}
"""
    project = _project(tmp_path, content)
    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    assert report["answer_index_runs_compacted"] == 1
    assert r"\textbf{1.}" in repaired
    assert r"\textbf{4.}" in repaired
    assert repaired.count(r"\begin{enumerate}") == 0


def test_repair_restores_naked_rule_and_detached_translation_completion(tmp_path):
    content = r"""\chapter{One}
She likes to explore 2.0em 0.4pt outdoors.
\begin{enumerate}
\setcounter{enumi}{4}
\item 随着比赛越来越激烈,选手们变得更加紧张。
(heat up)
\end{enumerate}
the players become more nervous.
% source_page_idx: 8
\chapter{Two}
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["known_ocr_tokens_repaired"] == 1
    assert report["detached_translation_completions_repaired"] == 1
    assert r"explore \rule{2.0em}{0.4pt} outdoors" in repaired
    assert r"(heat up)\\" in repaired
    assert repaired.index("the players become more nervous.") < repaired.index(r"\end{enumerate}")


def test_repair_compacts_answer_index_run_at_end_of_document(tmp_path):
    content = r"""\chapter{One}
\begin{enumerate}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
\begin{enumerate}
\setcounter{enumi}{1}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
3.
\begin{enumerate}
\setcounter{enumi}{3}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
5.
"""
    project = _project(tmp_path, content)

    report = repair_workbook_project(project)
    repaired = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert report["answer_index_runs_compacted"] == 1
    assert r"\textbf{5.}" in repaired


def test_prechapter_answer_compaction_is_idempotent(tmp_path):
    content = r"""\chapter{One}
Question.
\printshortanswer
\chapter{Two}
"""
    project = _project(tmp_path, content)

    repair_workbook_project(project)
    after_first = (project / "chapters" / "content.tex").read_text(encoding="utf-8")
    repair_workbook_project(project)
    after_second = (project / "chapters" / "content.tex").read_text(encoding="utf-8")

    assert after_second == after_first
    assert after_second.count(r"\enlargethispage{12\baselineskip}") == 1
