"""Actual package and independent source semantics controls for native Office."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from infrastructure.reporting.native_office_math_semantics import office_math_expression
from infrastructure.reporting.native_office_raw_roles import office_raw_source_roles
from infrastructure.reporting.native_office_scientific_controls import (
    CONTROL_BIBLIOGRAPHY,
    CONTROL_SOURCE,
    mutate_office_scientific_package,
)
from infrastructure.reporting.native_office_content_witness import docx_bookmark_names, inspect_office_source_survival
from infrastructure.rendering.office_native_projection import (
    office_semantics_filter_path,
    project_docx_transmission_layout,
)
from infrastructure.rendering._pandoc_filters import formalism_filter_path


def test_independent_expression_tree_preserves_signs_scripts_fractions_and_array_cells() -> None:
    equivalent = (
        (r"\frac{1}{2}x^{2}", r"\dfrac{1}{2} {x}^{2}"),
        (r"\sqrt5", r"\sqrt{5}"),
        (r"\alpha \geq 2", r"\alpha\ge 2"),
    )
    for left, right in equivalent:
        assert office_math_expression(left) == office_math_expression(right)
    changed = (
        (r"\frac{1}{2}", r"\frac{2}{1}"),
        (r"x_{k+1}", r"x^{k+1}"),
        (r"1-\alpha", r"1+\alpha"),
        (r"\begin{bmatrix}1&2\\3&4\end{bmatrix}", r"\begin{bmatrix}1&3\\2&4\end{bmatrix}"),
    )
    for left, right in changed:
        assert office_math_expression(left) != office_math_expression(right)
    with pytest.raises(ValueError, match="command unsupported"):
        office_math_expression(r"\invented{visible}")
    with pytest.raises(ValueError, match="finite expression budget"):
        office_math_expression("x" * (64 * 1024 + 1))


@pytest.mark.parametrize(
    ("label", "pinned", "current"),
    [
        # Bookmark names observed from actual Pandoc 3.11 and 3.12 DOCX writers.
        ("eq:control", "eq:control", "_d17530b69e3a78bc022e0ff92c94249180367d5"),
        ("refs", "refs", "_refs"),
        ("_x", "Xa532fea85b26fa6eea03db6aa3984579acd0189", "__x"),
        ("1abc", "X1ad43d75ba33f5f8a8956ad2118d0b62f840fa2", "_1abc"),
        ("a" * 39, "a" * 39, "_" + "a" * 39),
        ("b" * 40, "b" * 40, "_6e892b750b146f39a486af8c31d555e9c771b3e"),
        ("c" * 45, "X14c3280596694af2d9c25b194b62cfae2a23a55", "_14c3280596694af2d9c25b194b62cfae2a23a55"),
    ],
)
def test_docx_bookmark_names_match_both_pinned_pandoc_writers(label: str, pinned: str, current: str) -> None:
    assert docx_bookmark_names(label) == (pinned, current)


def test_raw_source_roles_cannot_excuse_visible_content_as_nonvisible_metadata() -> None:
    blocks = [
        {"t": "RawBlock", "c": ["tex", "\\begin{equation}\n\\label{eq:truth}\n\\frac{1}{2}\n\\end{equation}"]},
        {"t": "RawBlock", "c": ["latex", "\\section*{Visible heading}\\label{heading}"]},
        {"t": "RawBlock", "c": ["latex", "\\newpage"]},
        {"t": "RawBlock", "c": ["html", "<!-- alt: Source image description. -->"]},
        {"t": "RawBlock", "c": ["html", "<p>Visible source prose.</p>"]},
        {"t": "RawBlock", "c": ["tex", "\\textbf{Visible source prose.}"]},
    ]
    roles = office_raw_source_roles(
        json.dumps({"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": blocks}).encode()
    )
    assert [row["kind"] for row in roles] == [
        "equation",
        "heading",
        "page-break",
        "image-alternative",
        "unsupported",
        "unsupported",
    ]
    assert roles[0]["label"] == "eq:truth" and roles[0]["expression"] == r"\frac{1}{2}"


@pytest.mark.parametrize("kind", ("docx", "epub"))
def test_actual_source_writer_and_reader_reject_independent_scientific_mutants(tmp_path: Path, kind: str) -> None:
    from io import BytesIO
    from PIL import Image
    from infrastructure.rendering._epub_xhtml_sanitizer import sanitize_epub_xhtml
    from infrastructure.rendering.epub_renderer import _normalize_epub_archive, _EPUB_IDENTIFIER_PLACEHOLDER

    pandoc, crossref = shutil.which("pandoc"), shutil.which("pandoc-crossref")
    if not pandoc or not crossref:
        pytest.skip("actual configured Pandoc/crossref source providers unavailable")
    source = tmp_path / "source.md"
    source.write_text(CONTROL_SOURCE)
    bib = tmp_path / "references.bib"
    bib.write_text(CONTROL_BIBLIOGRAPHY)
    image = Image.new("RGB", (20, 20), (40, 80, 160))
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")
    (tmp_path / "control.png").write_bytes(image_buffer.getvalue())
    filters = [
        "--lua-filter",
        str(office_semantics_filter_path()),
        "--lua-filter",
        str(formalism_filter_path()),
        "--filter",
        crossref,
        "--citeproc",
        f"--bibliography={bib}",
        f"--resource-path={tmp_path}",
        "--metadata=title:Scientific control",
        "--lua-filter",
        str(office_semantics_filter_path()),
    ]
    if kind == "epub":
        filters.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")

    def actual(args: list[str]) -> bytes:
        completed = subprocess.run([pandoc, *args], cwd=tmp_path, capture_output=True, timeout=30, check=False)
        assert completed.returncode == 0, completed.stderr.decode()
        return completed.stdout

    source_ast = actual([str(source), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"])
    filtered_ast = actual(
        [
            str(source),
            "--from=markdown+yaml_metadata_block",
            "--to=json",
            "--standalone",
            f"--metadata=office-native-target:{kind}",
            *filters,
        ]
    )
    package = tmp_path / f"baseline.{kind}"
    actual(
        [
            str(source),
            "--from=markdown+yaml_metadata_block",
            f"--to={kind}",
            "--standalone",
            *filters,
            "--output",
            str(package),
        ]
    )
    if kind == "docx":
        project_docx_transmission_layout(package)
    else:
        sanitize_epub_xhtml(package)
    original = package.read_bytes()
    required = {
        "baseline": None,
        "changed-equation": "office.source.math",
        "changed-citation": "office.source.citation_rendering",
        "changed-table": "office.source.table_cells",
        "changed-figure": "office.source.image_content",
        "wrong-alternative": "office.source.image_alternative",
        "lost-pagebreak": "office.source.page_breaks",
        "lost-label": "office.source.label",
    }
    for name, code in required.items():
        candidate = tmp_path / f"{name}.{kind}"
        candidate.write_bytes(mutate_office_scientific_package(original, kind, name))
        if kind == "epub":
            _normalize_epub_archive(candidate, source_date_epoch=946684800)
        native_ast = actual([str(candidate), f"--from={kind}", "--to=json", "--standalone"])
        observed = inspect_office_source_survival(
            source_ast,
            filtered_ast,
            native_ast,
            candidate.read_bytes(),
            kind,
            (image_buffer.getvalue(),),
            {"title": "Scientific control"},
        )
        assert not observed["blockers"], observed
        codes = {row["code"] for row in observed["findings"]}
        if code is None:
            assert observed["status"] == "observed", observed
        else:
            assert code in codes, observed
