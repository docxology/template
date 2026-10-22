"""Real TeX proves both shared wrapping-header branches compile without tolerance."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

from infrastructure.rendering.latex_texttt import make_long_texttt_breakable
from infrastructure.rendering.latex_utils import compile_latex
from infrastructure.core.exceptions import CompilationError
from infrastructure.rendering._slides_math_header import write_slides_math_header

pytestmark = [pytest.mark.requires_latex, pytest.mark.timeout(90)]


@pytest.mark.parametrize("writer", ("article", "beamer"))
@pytest.mark.parametrize("fallback", (False, True), ids=("selected-package", "missing-package-fallback"))
def test_real_wrapping_header_compiles_without_nested_parameter_errors(
    tmp_path: Path, fallback: bool, writer: str
) -> None:
    compiler = shutil.which("xelatex")
    assert compiler is not None, "prepare the declared actual XeLaTeX provider"
    if not fallback:
        package = subprocess.run(
            ["kpsewhich", "seqsplit.sty"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert package.returncode == 0 and package.stdout.strip(), "prepare the actual seqsplit package"
    token = "MeaningfulLongIdentifier0123456789"
    if writer == "article":
        source, replacements = make_long_texttt_breakable(
            r"\documentclass{article}" + "\n" + r"\begin{document}\texttt{" + token + r"}\end{document}" + "\n"
        )
        assert replacements == 1
    else:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        header = write_slides_math_header(manuscript, tmp_path)
        assert header is not None
        source = (
            r"\documentclass{beamer}"
            + "\n"
            + header.read_text()
            + "\n"
            + r"\begin{document}\begin{frame}\breaktt{"
            + token
            + r"}\end{frame}\end{document}"
            + "\n"
        )
    if fallback:
        # Change only document input DATA to select a genuinely absent file.
        # No compiler, dependency implementation, or filesystem lookup is replaced.
        source = source.replace("seqsplit.sty", "template-absent-seqsplit-regression.sty")
    document = tmp_path / "wrapping.tex"
    document.write_text(source)
    result = subprocess.run(
        [
            compiler,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            document.name,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    log = document.with_suffix(".log").read_text(errors="replace")
    assert "Illegal parameter number" not in log
    pdf = PdfReader(document.with_suffix(".pdf"))
    assert token in "".join("".join(page.extract_text().split()) for page in pdf.pages)


@pytest.mark.parametrize(
    "failure",
    ("nested-parameter", "nested-and-undefined", "undefined-only", "missing-input"),
)
def test_nonzero_real_tex_exit_cannot_promote_even_a_valid_pdf(tmp_path: Path, failure: str) -> None:
    compiler = shutil.which("xelatex")
    assert compiler is not None, "prepare the declared actual XeLaTeX provider"
    # This genuine erroneous document recreates the old generated-header defect.
    # The compiler must refuse it even when nonstop recovery leaves a valid PDF.
    broken_header = (
        r"\IfFileExists{template-absent-seqsplit-regression.sty}{}"
        r"{\newcommand{\seqsplit}[1]{#1}}"
    )
    if failure == "undefined-only":
        broken_header = ""
    if failure == "missing-input":
        broken_header = r"\input{template-absent-fatal-input.tex}"
    body = r"Actual output."
    if failure in {"nested-and-undefined", "undefined-only"}:
        body += r"\TemplateUndefinedCommand"
    document = tmp_path / "refused.tex"
    document.write_text(
        r"\documentclass{article}" + "\n" + broken_header + "\n" + r"\begin{document}" + body + r"\end{document}" + "\n"
    )
    with pytest.raises(CompilationError) as caught:
        compile_latex(document, tmp_path / "compiled", compiler=compiler, passes=1)
    assert caught.value.context["exit_code"] != 0
    if failure != "missing-input":
        assert caught.value.context["pdf_exists"] is True
        assert caught.value.context["pdf_structure_valid"] is True
        log = (tmp_path / "compiled/refused.log").read_text(errors="replace")
        if failure == "undefined-only":
            assert "Undefined control sequence" in log
        else:
            assert "Illegal parameter number" in log


@pytest.mark.parametrize("writer", ("article", "beamer"))
def test_real_pandoc_code_wrap_preserves_literal_bodies_and_fits(tmp_path: Path, writer: str) -> None:
    """Actual highlighted tokens and plain verbatim wrap at unchanged font sizes."""
    from infrastructure.rendering._pdf_combined_preamble import inject_latex_preamble

    pandoc = shutil.which("pandoc")
    compiler = shutil.which("xelatex")
    assert pandoc is not None and compiler is not None, "prepare actual Pandoc and XeLaTeX providers"
    token = "LiteralCode0123456789" * 12
    literal = r"\example{literal} $x_1$ {braces} µ"
    markdown = (
        '## Literal code controls\n\n```yaml\ndescription: "' + token + '"\n```\n\n'
        "```\n" + token + "\n" + literal + "\n```\n\nNeighboring real math: $x_1 + 1 = 2$.\n"
    )
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "control.md"
    source.write_text(markdown)
    generated = subprocess.run(
        [
            pandoc,
            str(source),
            "--standalone",
            "--to=" + ("beamer" if writer == "beamer" else "latex"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    original = generated.stdout
    body = original.split(r"\begin{document}", 1)[1]
    assert r"\begin{Highlighting}" in body and r"\begin{verbatim}" in body
    if writer == "article":
        wrapped = inject_latex_preamble(original, manuscript)
    else:
        header = write_slides_math_header(manuscript, tmp_path)
        assert header is not None
        wrapped = original.replace(r"\begin{document}", header.read_text() + "\n" + r"\begin{document}", 1)
    # A preamble-only fix may not alter any character of the authored code or
    # neighboring mathematics, including TeX syntax inside literal environments.
    assert wrapped.split(r"\begin{document}", 1)[1] == original.split(r"\begin{document}", 1)[1]
    for name, content in (("unwrapped", original), ("wrapped", wrapped)):
        directory = tmp_path / name
        directory.mkdir()
        document = directory / "control.tex"
        document.write_text(content)
        result = subprocess.run(
            [
                compiler,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-no-shell-escape",
                document.name,
            ],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        log = document.with_suffix(".log").read_text(errors="replace")
        assert "Missing character" not in log
        if name == "unwrapped":
            assert "Overfull \\hbox" in log, "control must reproduce the actual clipping defect"
        else:
            assert "Overfull \\hbox" not in log, log
            assert "Overfull \\vbox" not in log, log
            pdf = PdfReader(document.with_suffix(".pdf"))
            text = "".join("".join(page.extract_text().split()) for page in pdf.pages)
            assert text.count(token) == 2
            assert "".join(literal.split()) in text


@pytest.mark.parametrize("row_count", (17, 31))
def test_real_archive_tables_keep_every_row_counter_and_nonempty_frame(tmp_path: Path, row_count: int) -> None:
    """Whole-row AST chunks survive the real Pandoc/crossref/Beamer path."""
    import re

    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    assert all(shutil.which(tool) for tool in ("pandoc", "pandoc-crossref", "xelatex"))
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "inventory.md"
    source.write_text(
        "## Complete inventory {#sec:inventory}\n\n"
        "| Module | Python Files | AGENTS | README | Export |\n"
        "|---|---:|---|---|---|\n"
        + "".join(f"| module{index:02d} | {index} | yes | yes | capability |\n" for index in range(row_count))
        + "\n: Complete module inventory {#tbl:inventory}\n\n"
        "## Following numbered table\n\n| Key | Value |\n|---|---|\n| FinalRowEvidence | 1 |\n\n"
        ": Following table {#tbl:following}\n\n"
        "## References\n\nSee [@tbl:inventory] and [@tbl:following].\n"
    )
    pdf = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(tmp_path / "output/slides"),
            latex_compiler="xelatex",
            slides_profile="archive",
        )
    ).render(source, output_format="beamer", manuscript_dir=manuscript)
    tex = pdf.with_suffix(".tex").read_text()
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log and "Overfull \\vbox" not in log, log
    assert tex.count(r"\label{tbl:inventory}") == tex.count(r"\label{tbl:following}") == 1
    pages = [page.extract_text() for page in PdfReader(pdf).pages]
    text = "".join("".join(pages).split())
    for index in range(row_count):
        assert text.count(f"module{index:02d}") == 1
    assert "Table1:Completemoduleinventory" in text
    assert "Table2:Followingtable" in text
    references = pages[-1]
    assert re.search(r"(?<![0-9])1(?![0-9])", references)
    assert re.search(r"(?<![0-9])2(?![0-9])", references)
    assert "tbl:inventory" not in references and "tbl:following" not in references and "??" not in references
    for page in pages:
        assert re.search(r"module\d{2}|FinalRowEvidence|See", page), page


@pytest.mark.parametrize("shape", ("portrait", "wide", "tiny"))
def test_real_archive_generated_image_bounds_shrink_without_upscaling(tmp_path: Path, shape: str) -> None:
    """Dedicated image frames use the title-safe area and retain the caption once."""
    import pdfplumber
    from PIL import Image

    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    assert all(shutil.which(tool) for tool in ("pandoc", "pandoc-crossref", "xelatex"))
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    figures = tmp_path / "output/figures"
    figures.mkdir(parents=True)
    size = {"portrait": (200, 800), "wide": (800, 200), "tiny": (12, 12)}[shape]
    image = figures / "geometry.png"
    Image.new("RGB", size, "#12628c").save(image, dpi=(72, 72))
    source = manuscript / "geometry.md"
    source.write_text(
        "## UniqueImageTitle\n\n![CompleteCaptionEvidence: every authored caption word remains visible. "
        "CaptionEndEvidence.](../output/figures/geometry.png){#fig:geometry}\n\n"
        "## ExplicitImageTitle\n\n![](../output/figures/geometry.png){width=20pt}\n\n"
        "## ExplicitHeightTitle\n\n![](../output/figures/geometry.png){height=20pt}\n\n"
        "## ExplicitBothTitle\n\n![](../output/figures/geometry.png){width=20pt height=20pt}\n"
    )
    stale_pdf = tmp_path / "obsolete-pdf"
    stale_pdf.mkdir()
    # Historical AUX is controlled DATA, not authority in standalone/PDF-off mode.
    (stale_pdf / "_combined_manuscript.aux").write_text(r"\newlabel{fig:geometry}{{99}{1}}" + "\n")
    pdf = SlidesRenderer(
        RenderingConfig(
            pdf_dir=str(stale_pdf),
            output_dir=str(tmp_path / "output"),
            slides_dir=str(tmp_path / "output/slides"),
            figures_dir=str(figures),
            latex_compiler="xelatex",
            slides_profile="archive",
        )
    ).render(source, output_format="beamer", manuscript_dir=manuscript, figures_dir=figures)
    tex = pdf.with_suffix(".tex").read_text()
    assert r"\pandocbounded{\includegraphics" in tex
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log and "Overfull \\vbox" not in log, log
    with pdfplumber.open(pdf) as document:
        first, caption_page, explicit, explicit_height, explicit_both = document.pages
        assert len(first.images) == len(explicit.images) == 1
        projected = first.images[0]
        title = first.search("UniqueImageTitle")[0]
        caption = caption_page.search("CompleteCaptionEvidence")[0]
        assert title["bottom"] < projected["top"]
        assert not first.search("CompleteCaptionEvidence")
        assert "CaptionEndEvidence" in caption_page.extract_text()
        assert "Figure 1:" in caption_page.extract_text()
        assert caption["top"] > caption_page.search("UniqueImageTitle")[0]["bottom"]
        assert 4 < projected["x0"] < projected["x1"] < first.width - 4
        assert 4 < projected["top"] < projected["bottom"] < first.height - 4
        assert explicit.images[0]["width"] == pytest.approx(20, abs=0.1)
        assert explicit_height.images[0]["height"] == pytest.approx(20, abs=0.1)
        assert explicit_both.images[0]["width"] == pytest.approx(20, abs=0.1)
        assert explicit_both.images[0]["height"] == pytest.approx(20, abs=0.1)
        if shape == "portrait":
            assert projected["height"] > first.height * 0.55
        if shape == "wide":
            assert projected["width"] > first.width * 0.75
        if shape == "tiny":
            assert projected["width"] == pytest.approx(12, abs=0.1)
            assert projected["height"] == pytest.approx(12, abs=0.1)


@pytest.mark.parametrize("shape", ("rowspan", "footer", "nested"))
def test_real_archive_table_paginator_leaves_unrecognized_shapes_intact(tmp_path: Path, shape: str) -> None:
    """Real Pandoc AST inputs prove the flat-table gate abstains conservatively."""
    import copy
    import json

    pandoc = shutil.which("pandoc")
    assert pandoc is not None
    markdown = "## Boundary\n\n| Key | Value |\n|---|---|\n" + "".join(
        f"| BoundRow{index:02d} | {index} |\n" for index in range(17)
    )
    parsed = subprocess.run(
        [pandoc, "--from=markdown", "--to=json"],
        input=markdown,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert parsed.returncode == 0, parsed.stderr
    ast = json.loads(parsed.stdout)
    table = next(block for block in ast["blocks"] if block["t"] == "Table")
    rows = table["c"][4][0][3]
    if shape == "rowspan":
        rows[0][1][1][2] = 2
        rows[1][1].pop(1)
    elif shape == "footer":
        footer = copy.deepcopy(rows[0])
        footer[1][0][4] = [{"t": "Plain", "c": [{"t": "Str", "c": "FooterBoundaryEvidence"}]}]
        table["c"][5][1].append(footer)
    else:
        ast["blocks"] = [ast["blocks"][0], {"t": "BlockQuote", "c": [table]}]
    from infrastructure.rendering import _slides_beamer

    lua = Path(_slides_beamer.__file__).with_name("_beamer_allowframebreaks.lua")
    result = subprocess.run(
        [pandoc, "--from=json", "--to=beamer", "--lua-filter", str(lua)],
        input=json.dumps(ast),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count(r"\begin{longtable}") == 1
    assert r"\framebreak" not in result.stdout
    for index in range(17):
        assert result.stdout.count(f"BoundRow{index:02d}") == 1


@pytest.mark.parametrize("writer", ("article", "beamer"))
def test_real_header_breaks_preserve_all_matrix_cells_and_fit_columns(tmp_path: Path, writer: str) -> None:
    """All ten real-style tool names wrap within their own native cell."""
    import pdfplumber

    from infrastructure.rendering.combined_native_commands import pdf_combined_command, pre_crossref_json_command
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    headers = [
        "Capability",
        "template/",
        "Snakemake",
        "Nextflow",
        "CWL",
        "Quarto",
        "Jupyter Book",
        "R Markdown",
        "DVC",
        "Overleaf",
        "OpenAI Prism",
    ]
    source_headers = [headers[0], "`template/`", *headers[2:]]
    rows = ["| " + " | ".join(source_headers) + " |", "|" + "---|" * 11]
    for row in range(14):
        rows.append("| " + " | ".join([f"R{row:02d}", *[f"{chr(97 + col)}{row:02d}" for col in range(10)]]) + " |")
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "matrix.md"
    source.write_text("## Whole Matrix Evidence\n\n" + "\n".join(rows) + "\n\n: Whole matrix {#tbl:matrix}\n")
    if writer == "beamer":
        pdf = SlidesRenderer(RenderingConfig(slides_dir=str(tmp_path), slides_profile="archive")).render(
            source,
            "beamer",
            manuscript_dir=manuscript,
        )
    else:
        tex = tmp_path / "matrix.tex"
        command = pdf_combined_command(
            shutil.which("pandoc"),
            source,
            tex,
            manuscript,
            tmp_path,
            None,
            [],
            shutil.which("pandoc-crossref"),
        )
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, result.stderr
        # Source's genuine cold parser changes FORMAT to JSON. The factory's
        # explicit projection metadata must retain the same header pass there.
        replay = subprocess.run(pre_crossref_json_command(command, "latex"), capture_output=True, text=True, timeout=20)
        assert replay.returncode == 0, replay.stderr
        assert r"\\allowbreak{}" in replay.stdout
        assert all(f"{chr(97 + col)}{row:02d}" in replay.stdout for row in range(14) for col in range(10))
        pdf = compile_latex(tex, tmp_path, compiler="xelatex", passes=2)
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log, log
    assert "Overfull \\vbox" not in log, log
    with pdfplumber.open(pdf) as rendered:
        if writer == "beamer":
            assert len(rendered.pages) == 2
        all_text = "".join("".join(page.extract_text().split()) for page in rendered.pages)
        for row in range(14):
            assert all_text.count(f"R{row:02d}") == 1
            for col in range(10):
                assert all_text.count(f"{chr(97 + col)}{row:02d}") == 1
        for page_index, page in enumerate(rendered.pages):
            first_row = 8 if writer == "beamer" and page_index else 0
            anchors = [
                page.search(f"R{first_row:02d}")[0],
                *[page.search(f"{chr(97 + col)}{first_row:02d}")[0] for col in range(10)],
            ]
            starts = [anchor["x0"] for anchor in anchors]
            rules = sorted(
                edge["top"]
                for edge in page.edges
                if abs(edge["top"] - edge["bottom"]) < 0.1
                and starts[0] - 2 <= edge["x0"] <= starts[0]
                and edge["x1"] >= starts[-1]
                and edge["top"] < anchors[0]["top"]
            )
            assert len(rules) == 2
            top, bottom = rules
            for col, expected in enumerate(headers):
                right = starts[col + 1] - 1 if col < 10 else starts[col] + (starts[col] - starts[col - 1]) - 1
                cell = page.crop((starts[col] - 1, top - 1, right, bottom))
                assert "".join(cell.extract_text().split()) == "".join(expected.split())
                assert {round(char["size"], 2) for char in cell.chars} == {round(anchors[col]["chars"][0]["size"], 2)}
                if col == 1:
                    assert all("Mono" in char["fontname"] for char in cell.chars)
    # A real negative control removes only the optional header penalties from
    # the successful native TeX. Same cells, widths and fonts must reproduce
    # the collision; compilation remains a genuine process with its own log.
    negative = tmp_path / "no-header-breaks"
    negative.mkdir()
    tex = negative / "matrix.tex"
    tex.write_text(pdf.with_suffix(".tex").read_text().replace(r"\allowbreak{}", ""))
    failed_geometry_pdf = compile_latex(tex, negative, compiler="xelatex", passes=1)
    assert "Overfull \\hbox" in failed_geometry_pdf.with_suffix(".log").read_text(errors="replace")


@pytest.mark.parametrize("shape", ("raw", "nested", "span", "nested-table"))
def test_real_header_filter_preserves_body_and_unsupported_shapes(tmp_path: Path, shape: str) -> None:
    """Real ASTs prove narrow header edits never descend into scientific bodies."""
    import json

    source = tmp_path / "table.md"
    source.write_text("| Snakemake | `template/` |\n|---|---|\n| BodyScientificToken | `BodyCodeToken` |\n")
    parsed = subprocess.run(
        [shutil.which("pandoc"), str(source), "-t", "json"], capture_output=True, text=True, timeout=20
    )
    assert parsed.returncode == 0, parsed.stderr
    document = json.loads(parsed.stdout)
    table = document["blocks"][0]
    head = table["c"][3][1][0][1][0][4][0]["c"]
    if shape == "raw":
        head[:] = [{"t": "RawInline", "c": ["latex", "\\textbf{RawHeader}"]}]
    elif shape == "nested":
        head[:] = [{"t": "Strong", "c": head.copy()}]
    elif shape == "span":
        table["c"][3][1][0][1][0][2] = 2
    else:
        document["blocks"] = [{"t": "BlockQuote", "c": [table]}]
    ast = tmp_path / "table.json"
    ast.write_text(json.dumps(document))
    filter_path = Path(__file__).parents[3] / "infrastructure/rendering/_table_header_breaks.lua"
    # The requested writer activates the real header pass; a second native
    # writer round-trip exposes the resulting body/unsupported header bytes.
    result = subprocess.run(
        [shutil.which("pandoc"), str(ast), "-f", "json", "-t", "latex", "--lua-filter", str(filter_path)],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "BodyScientificToken" in result.stdout and "BodyCodeToken" in result.stdout
    assert "Body\\allowbreak" not in result.stdout
    assert "Snakemake" in result.stdout if shape != "raw" else "\\textbf{RawHeader}" in result.stdout
    if shape == "nested-table":
        assert r"\allowbreak" not in result.stdout


@pytest.mark.parametrize("small_labels", (False, True), ids=("readable-panels", "unreadable-panels-refused"))
def test_real_archive_panels_keep_global_caption_once_and_enforce_embedded_scale(
    tmp_path: Path,
    small_labels: bool,
) -> None:
    """Actual article AUX, ordered native panels and long full caption agree."""
    import hashlib
    import json

    import pdfplumber
    from PIL import Image, ImageDraw, ImageFont

    from infrastructure.core.exceptions import RenderingError
    from infrastructure.rendering.combined_native_commands import pdf_combined_command
    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.new("RGB", (1000, 1800), "#206090").save(figures / "canonical.png", dpi=(72, 72))
    panels = []
    for index in range(2):
        raster = Image.new("RGB", (1000, 600), "white")
        draw = ImageDraw.Draw(raster)
        font = ImageFont.load_default(size=90)
        text = f"Panel {index + 1} Evidence"
        draw.text((30, 230), text, font=font, fill="black")
        bounds = draw.textbbox((30, 230), text, font=font)
        target = figures / f"panel-{index}.png"
        raster.save(target, dpi=(72, 72))
        panels.append(
            {
                "src": f"../figures/{target.name}",
                "alt": text,
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "minimum_label_px": 1 if small_labels else bounds[3] - bounds[1],
            }
        )
    (figures / "panels.json").write_text(json.dumps({"schema_version": "1.0", "panels": panels}))
    caption_words = [f"CaptionWord{index:03d}" for index in range(90)]
    caption = " ".join(caption_words) + "."
    source = manuscript / "panels.md"
    source.write_text(
        "## Wrapped archive evidence title with several words to exercise the actual title safe area\n\n"
        + "!["
        + caption
        + "](../figures/canonical.png)"
        + '{#fig:control width=2in data-slide-manifest="../figures/panels.json"}\n\n'
        + "See [@fig:control].\n\n```\n"
        + r"\archivefigurecaptionnumber{fig:missing-literal}{\thefigure}"
        + "\n```\n"
    )
    combined = manuscript / "combined.md"
    combined.write_text(
        "![Leading one](../figures/canonical.png){#fig:leading-one width=1in}\n\n"
        "![Leading two](../figures/canonical.png){#fig:leading-two width=1in}\n\n" + source.read_text()
    )
    main_dir = tmp_path / "pdf"
    main_dir.mkdir()
    main_tex = main_dir / "_combined_manuscript.tex"
    command = pdf_combined_command(
        shutil.which("pandoc"), combined, main_tex, manuscript, figures, None, [], shutil.which("pandoc-crossref")
    )
    produced = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert produced.returncode == 0, produced.stderr
    compile_latex(main_tex, main_dir, compiler="xelatex", passes=2)
    output = tmp_path / "slides"
    renderer = SlidesRenderer(RenderingConfig(slides_dir=str(output), pdf_dir=str(main_dir), slides_profile="archive"))
    if small_labels:
        with pytest.raises(RenderingError, match="slides.density.figure-label-scale"):
            renderer.render(
                source, "beamer", manuscript_dir=manuscript, figures_dir=figures, strict_cross_deck_refs=True
            )
        assert not (output / "panels_slides.pdf").exists()
        return
    pdf = renderer.render(source, "beamer", manuscript_dir=manuscript, figures_dir=figures, strict_cross_deck_refs=True)
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log and "Overfull \\vbox" not in log, log
    assert r"\archivefigurecaptionnumber{fig:missing-literal}{\thefigure}" in pdf.with_suffix(".tex").read_text()
    with pdfplumber.open(pdf) as rendered:
        image_pages = [page for page in rendered.pages if page.images]
        assert len(image_pages) == 2
        assert [page.images[0]["srcsize"] for page in image_pages] == [(1000, 600), (1000, 600)]
        assert all(page.images[0]["width"] > 280 for page in image_pages)
        text = " ".join(page.extract_text() for page in rendered.pages)
        assert text.count("Figure 3:") == 1
        assert "fig. 3" in text.replace("\u00a0", " ")
        for word in caption_words:
            assert text.count(word) == 1
        assert all("CaptionWord" not in page.extract_text() for page in image_pages)
        for page in rendered.pages:
            assert page.extract_text().strip()
            assert all(0 <= char["top"] < char["bottom"] <= page.height for char in page.chars)


@pytest.mark.parametrize("shape", ("proper", "nested", "mixed", "literal"))
def test_real_archive_figure_filter_preserves_nonfigure_and_unsupported_content(tmp_path: Path, shape: str) -> None:
    """Actual Pandoc distinguishes a proper image frame from raw/mixed examples."""
    import json

    source = tmp_path / "figure.md"
    source.write_text("## Evidence\n\n![Full authored caption](native-data.png){#fig:proper}\n")
    parsed = subprocess.run(
        [shutil.which("pandoc"), str(source), "-t", "json"], capture_output=True, text=True, timeout=20
    )
    assert parsed.returncode == 0, parsed.stderr
    document = json.loads(parsed.stdout)
    figure = document["blocks"][1]
    literal = r"\framebreak \refstepcounter{figure}\label{fig:raw}"
    if shape == "nested":
        document["blocks"][1] = {"t": "BlockQuote", "c": [figure]}
    elif shape == "mixed":
        figure["c"][2][0]["c"].extend([{"t": "Space"}, {"t": "Str", "c": "PeerProseMustRemain"}])
    elif shape == "literal":
        document["blocks"][1] = {"t": "CodeBlock", "c": [["", [], []], literal]}
    ast = tmp_path / "figure.json"
    ast.write_text(json.dumps(document))
    filter_path = Path(__file__).parents[3] / "infrastructure/rendering/_archive_figure_frames.lua"
    result = subprocess.run(
        [shutil.which("pandoc"), str(ast), "-f", "json", "-t", "beamer", "--lua-filter", str(filter_path)],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    if shape == "proper":
        assert result.stdout.count(r"\begin{archiveimageframe}") == 1
        assert result.stdout.count(r"\begin{archivecaptionframe}") == 1
        assert "".join(result.stdout.split()).count("Fullauthoredcaption") == 2  # image alt plus caption
    else:
        assert r"\begin{archiveimageframe}" not in result.stdout
        if shape == "literal":
            assert literal in result.stdout and r"\begin{verbatim}" in result.stdout
        else:
            assert r"\begin{figure}" in result.stdout
            assert "Full authored caption" in result.stdout
            if shape == "mixed":
                assert "PeerProseMustRemain" in result.stdout


@pytest.mark.parametrize("kind", ("reference-image", "inline-code", "raw-comment", "plain"))
def test_real_archive_image_candidate_guard_preserves_literal_and_reference_inputs(tmp_path: Path, kind: str) -> None:
    """Candidate detection saves image-free work without interpreting examples."""
    import pdfplumber
    from PIL import Image

    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    figures = tmp_path / "figures"
    figures.mkdir()
    Image.new("RGB", (100, 100), "#246080").save(figures / "real.png", dpi=(72, 72))
    bodies = {
        "reference-image": "![Actual reference caption][actual]\n\n[actual]: ../figures/real.png\n",
        "inline-code": "`![literal](missing.png)`\n",
        "raw-comment": "\\begin{center}\n% ![literal](missing.png)\nRaw example body.\n\\end{center}\n",
        "plain": "An ordinary image-free paragraph.\n",
    }
    source = manuscript / "guard.md"
    source.write_text("## Candidate detection\n\nZeroImageEvidence.\n\n" + bodies[kind])
    commands = []

    def genuine_native_process(command, *args, **kwargs):
        # Observe the actual calls, forwarding every command/option to the real
        # provider. No subprocess output, implementation or dependency is replaced.
        commands.append(list(command))
        return subprocess.run(command, *args, **kwargs)

    pdf = SlidesRenderer(
        RenderingConfig(slides_dir=str(tmp_path / "slides")), process_runner=genuine_native_process
    ).render(
        source,
        "beamer",
        manuscript_dir=manuscript,
        figures_dir=figures,
    )
    parses = [command for command in commands if "-t" in command and command[command.index("-t") + 1] == "json"]
    assert len(parses) == (0 if kind == "plain" else 1)
    with pdfplumber.open(pdf) as document:
        assert sum(len(page.images) for page in document.pages) == (1 if kind == "reference-image" else 0)
        text = " ".join(page.extract_text() for page in document.pages)
        assert text.count("ZeroImageEvidence") == 1
        if kind == "reference-image":
            assert text.count("Actual reference caption") == 1
        elif kind == "inline-code":
            assert "![literal](missing.png)" in text
        elif kind == "raw-comment":
            assert "Raw example body." in text
