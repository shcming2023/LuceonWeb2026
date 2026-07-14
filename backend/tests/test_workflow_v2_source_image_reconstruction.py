from pathlib import Path

from PIL import Image

from app.workflow_v2 import source_image_reconstruction as subject


def test_reconstruct_source_images_replaces_only_present_targets(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    images = project / "images"
    images.mkdir(parents=True)
    crop = subject.SourceCrop("target.jpg", 3, (0.1, 0.2, 0.5, 0.8), "test")
    (images / crop.target_name).write_bytes(b"old")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"stable source")

    class FakePixmap:
        def save(self, output):
            Image.new("RGB", (1000, 500), color=(20, 40, 60)).save(output)

    class FakePage:
        rect = type("Rect", (), {"width": 1000})()

        def get_pixmap(self, **_kwargs):
            return FakePixmap()

    class FakeDocument:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def load_page(self, index):
            assert index == 2
            return FakePage()

    monkeypatch.setattr(subject.fitz, "open", lambda _path: FakeDocument())
    report = subject.reconstruct_source_images(project, source_pdf, crops=(crop,))

    assert len(report["replacements"]) == 1
    assert report["replacements"][0]["pixel_box"] == (100, 100, 500, 400)
    assert report["replacements"][0]["output_size"] == [400, 300]
    with Image.open(images / crop.target_name) as result:
        assert result.size == (400, 300)


def test_reconstruct_source_images_is_noop_without_known_targets(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "images").mkdir(parents=True)

    report = subject.reconstruct_source_images(project, tmp_path / "missing.pdf")

    assert report["replacements"] == []


def test_known_source_crops_include_new_question_types_repairs() -> None:
    crops = {crop.target_name: crop for crop in subject.KNOWN_SOURCE_CROPS}

    assert crops["52c9dcea6c953447c5095c453059fc10c1cdf5a67ccd6acb91e5c890b3c316ce.jpg"].source_page == 21
    assert crops["14d6f4e4086deaf1deff46cd2dca4ea33ce1df8b23dc0309f0abf5397bba62d0.jpg"].source_page == 24
    assert crops["aeb7fe1ed409252d2039a32e2fcd6fb39ed32b78655e74ed30c6319f417d6bb0.jpg"].source_page == 21
    assert crops["aeb7fe1ed409252d2039a32e2fcd6fb39ed32b78655e74ed30c6319f417d6bb0.jpg"].processing == "denoise_autocontrast"
    assert crops["47a379df0a30a4df8c5b09d48cc4fb5d0e2689d867613da46a17b3e44314212b.jpg"].source_page == 27
    assert crops["e6224e4385f0ad83d7ce8cd0047ce42bfcd0bc23c83a8c1c1d626f9bcf37d0c3.jpg"].source_page == 89
    assert crops["9106734a704602b7b8788fbac87936e005772083f20bb9998a138929d03404c9.jpg"].source_page == 28
    assert crops["7d2cbc20544730c353f43cedff645e5a5aaa12e00b9581bc6e2f8c5e123b269c.jpg"].source_page == 148


def test_normalize_theme_reading_layout_is_idempotent(tmp_path: Path) -> None:
    content_dir = tmp_path / "chapters"
    content_dir.mkdir()
    names = [crop.target_name for crop in subject.THEME_READING_CROPS[2:]]
    figures = "\n".join(
        f"\\begin{{figure}}[H]\n\\includegraphics{{images/{name}}}\n\\caption{{{label}}}\n\\end{{figure}}"
        for label, name in zip("ABCD", names, strict=True)
    )
    (content_dir / "content.tex").write_text(
        "\\begin{figure}[H]\n\\includegraphics{images/unrelated.jpg}\n\\end{figure}\n"
        "\\begin{figure}[H]\n\\includegraphics{images/391bd04ad9c2bb2a443e05dd09938f67d6f664ee47567edd65885aa4471915ca.jpg}\n\\end{figure}\n"
        "Parking\nPower banks (移动电源) for rent\n" + figures,
        encoding="utf-8",
    )

    first = subject._normalize_theme_reading_layout(tmp_path)
    after_first = (content_dir / "content.tex").read_text(encoding="utf-8")
    second = subject._normalize_theme_reading_layout(tmp_path)

    assert first == ["facilities_text_grid", "choice_image_grid"]
    assert second == []
    assert (content_dir / "content.tex").read_text(encoding="utf-8") == after_first
    assert "images/unrelated.jpg" in after_first
    assert r"\\[0.8em]" in after_first


def test_normalize_source_layout_scales_reconstructed_primary_math_option(tmp_path: Path) -> None:
    content_dir = tmp_path / "chapters"
    content_dir.mkdir()
    target = "9106734a704602b7b8788fbac87936e005772083f20bb9998a138929d03404c9.jpg"
    content_dir.joinpath("content.tex").write_text(
        rf"\includegraphics[width=0.10\textwidth]{{images/{target}}}\n",
        encoding="utf-8",
    )

    changes = subject._normalize_theme_reading_layout(tmp_path)

    result = content_dir.joinpath("content.tex").read_text(encoding="utf-8")
    assert "width=0.30\\textwidth" in result
    assert changes == ["chinese_primary_math_option_c_scaled"]


def test_normalize_theme_reading_layout_restores_cloze_rows_and_tail_markers(tmp_path: Path) -> None:
    content_dir = tmp_path / "chapters"
    content_dir.mkdir()
    text = r"""No, They're Not Photographs
The final results, however, are always \rule{2.0em}{0.4pt}4\rule{2.0em}{0.4pt}.
\begin{enumerate}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
artworks that must be seen to be believed!
\begin{enumerate}
\setcounter{enumi}{3}
\item \rule{2.0em}{0.4pt}
\end{enumerate}
pull s
▶ Language tip
\item 我试图跑得更快,但还是赶不上他的速度。
% source
"""
    (content_dir / "content.tex").write_text(text, encoding="utf-8")

    changes = subject._normalize_theme_reading_layout(tmp_path)
    result = (content_dir / "content.tex").read_text(encoding="utf-8")

    assert "cloze_answer_rows_restored" in changes
    assert "ocr_pull_s_fixed" in changes
    assert result.count(r"\rule{5em}{0.4pt}") == 8
    assert "pulls" in result
    assert "▶" not in result
    assert r"\(\blacktriangleright\)" in result
    assert r"\enlargethispage{12\baselineskip}" in result


def test_normalize_layout_vectorizes_low_resolution_synonym_panel(tmp_path: Path) -> None:
    content_dir = tmp_path / "chapters"
    content_dir.mkdir()
    (content_dir / "content.tex").write_text(
        r"""\begin{figure}[H]
\includegraphics[width=0.18\textwidth]{images/52c9dcea6c953447c5095c453059fc10c1cdf5a67ccd6acb91e5c890b3c316ce.jpg}
\end{figure}
""",
        encoding="utf-8",
    )

    changes = subject._normalize_theme_reading_layout(tmp_path)
    result = (content_dir / "content.tex").read_text(encoding="utf-8")

    assert "synonym_panel_vectorized" in changes
    assert "SYNONYM" in result
    assert "52c9dcea" not in result
