"""Real original parser, valid PDFs and native raster negative controls."""

from __future__ import annotations

import copy
import hashlib
import os
import shutil
import subprocess
import time
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from infrastructure.reporting.native_format_pdf_frontmatter import compile_pdf_frontmatter_contract
from infrastructure.reporting.native_format_pdf_positioned_math import inspect_pdf_positioned_math
from infrastructure.reporting.native_format_pdf_positions import instrument_source_math_positions
from infrastructure.reporting.native_format_pdf_raw_source import tex_command_census
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan, strict_ast
from infrastructure.reporting.native_format_pdf_source_replay import replay_pdf_source_witness
from infrastructure.reporting.native_format_pdf_source_witness import inspect_pdf_source_witness
from infrastructure.reporting.native_format_scientific_math import _math_body, scientific_math_from_ast

SOURCE = b"""# Scientific table

| Parameter | Value |
|---|---|
| Alpha | 3.25 |
| Beta | 9.50 |

![Source colour map](asset.png)
"""


def parsed(source: bytes) -> bytes:
    executable = shutil.which("pandoc")
    if executable is None:
        pytest.skip("the genuine original source parser is unavailable")
    return subprocess.run(
        [executable, "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"],
        input=source,
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout


def source_asset() -> bytes:
    image = Image.new("RGB", (80, 48), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 39, 47), fill=(20, 55, 130))
    draw.rectangle((40, 0, 79, 47), fill=(245, 125, 25))
    draw.line((0, 47, 79, 0), fill=(25, 25, 25), width=3)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def native_pdf(path: Path, control: str) -> tuple[bytes, tuple[bytes, ...]]:
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen.canvas import Canvas

    executable = shutil.which("pdftoppm")
    if executable is None:
        pytest.skip("the genuine native page rasterizer is unavailable")
    canvas = Canvas(str(path), pagesize=(360, 288), invariant=True, pageCompression=0)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(30, 260, "Scientific table")
    for index, (left, right) in enumerate((("Parameter", "Value"), ("Alpha", "3.25"), ("Beta", "9.50"))):
        y = 230 - index * 40
        canvas.drawString(30, y, left)
        value = "3.26" if control == "changed-table-number" and index == 1 else right
        value_y = y - 16 if control == "misaligned-table" and index == 1 else y
        canvas.drawString(170, value_y, value)
    caption_x = 200 if control == "moved-figure-and-caption" else 30
    canvas.drawString(caption_x, 115, "Source colour map")
    asset = source_asset()
    if control == "changed-source-figure":
        stream = BytesIO()
        Image.new("RGB", (80, 48), (210, 10, 90)).save(stream, format="PNG")
        asset = stream.getvalue()
    figure_x = 200 if control in {"moved-figure", "moved-figure-and-caption"} else 30
    canvas.drawImage(ImageReader(BytesIO(asset)), figure_x, 10, width=160, height=96)
    if control == "opaque-figure-overlay":
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(30, 10, 160, 96, stroke=0, fill=1)
    canvas.showPage()
    canvas.save()
    prefix = path.with_suffix("")
    subprocess.run(
        [executable, "-r", "150", "-png", str(path), str(prefix)], capture_output=True, check=True, timeout=10
    )
    rasters = tuple(item.read_bytes() for item in sorted(path.parent.glob(prefix.name + "-*.png")))
    return path.read_bytes(), rasters


def test_original_parser_accounts_for_nested_math_citation_note_raw_and_cells() -> None:
    source = b"""# Heading $x^2$

Body [@example] with a note.[^n]

[^n]: Footnote $z+1$.

| Field | Value |
|---|---|
| Math | $q/2$ |

\\newpage
"""
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", source),), parsed(source))
    assert sum(row["kind"] == "Math" for row in plan.occurrences) == 3
    assert {"Cite", "Note", "RawBlock", "Table"} <= {row["kind"] for row in plan.occurrences}
    assert len(plan.tables[0]["rows"]) == 2
    assert plan.tables[0]["rows"][1]["cells"][1]["occurrence_ids"]
    assert plan.notes
    assert not any("@example" in token for block in plan.text for token in block.tokens)


def test_source_json_duplicate_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="repeats"):
        strict_ast(b'{"pandoc-api-version":[1,23],"blocks":[],"blocks":[]}')


def test_unknown_tex_command_survives_even_if_reader_would_drop_it() -> None:
    census = tex_command_census(r"\unknownDrop{Scientific assertion}")
    assert census["blockers"] == ["offset 0: unknown original TeX command unknownDrop"]


def test_dynamic_tex_input_and_layout_commands_remain_blocked() -> None:
    census = tex_command_census(r"\input{outside}\vspace{99pt}")
    assert len(census["blockers"]) == 2
    assert "dynamic-input" in census["blockers"][0]
    assert "layout interpretation" in census["blockers"][1]


def test_tex_comments_and_verbatim_do_not_execute_embedded_commands() -> None:
    census = tex_command_census(
        "% \\input{ignored}\n" + r"\verb|\input{literal}|" + "\n" + r"\begin{verbatim}\unknownLiteral\end{verbatim}"
    )
    assert not census["blockers"]
    assert [row["command"] for row in census["commands"]] == ["verb", "begin"]


def test_frontmatter_is_bound_to_declared_literal_source() -> None:
    # Without a literal date the title page would print the TeX runtime clock,
    # which stays blocked; this source declares that no date is rendered.
    contract = compile_pdf_frontmatter_contract(
        "config.yaml",
        b"paper:\n  title: Source Title\nauthors:\n  - name: Ada\n    email: ada@example.invalid\n"
        b"rendering:\n  include_date: false\n",
        "manuscript:pdf",
    )
    assert [block.id for block in contract.blocks] == [
        "config/title",
        "config/authors/0/name",
        "config/authors/0/email",
    ]
    assert not contract.blockers


def test_duplicate_frontmatter_config_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="repeats"):
        compile_pdf_frontmatter_contract("config.yaml", b"paper:\n  title: First\n  title: Second\n", "manuscript:pdf")


def tex_pdf(path: Path, tex: str) -> tuple[bytes, tuple[bytes, ...]]:
    """Small real XeTeX fixture; no native process outcome is substituted."""
    compiler, rasterizer = shutil.which("xelatex"), shutil.which("pdftoppm")
    if compiler is None or rasterizer is None:
        pytest.skip("the real source equation engine/rasterizer is unavailable")
    path.write_text(tex)
    environment = dict(os.environ)
    for variable in ("TEXMFHOME", "TEXMFCONFIG", "TEXMFVAR"):
        private = path.parent / variable.lower()
        private.mkdir(exist_ok=True)
        environment[variable] = str(private)
    environment.update({"openin_any": "p", "openout_any": "p"})
    for _ in range(2):
        subprocess.run(
            [compiler, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", path.name],
            cwd=path.parent,
            env=environment,
            capture_output=True,
            check=True,
            timeout=10,
        )
    pdf = path.with_suffix(".pdf")
    subprocess.run(
        [rasterizer, "-r", "150", "-png", str(pdf), str(path.with_suffix(""))],
        capture_output=True,
        check=True,
        timeout=10,
    )
    rasters = tuple(item.read_bytes() for item in sorted(path.parent.glob(path.stem + "-*.png")))
    return pdf.read_bytes(), rasters


def test_actual_source_positioned_repeated_math_and_changed_equation(tmp_path: Path) -> None:
    source = b"First $x^2$. Second $x^2$.\n"
    ast = parsed(source)
    nodes = scientific_math_from_ast(ast)
    preamble = r"\documentclass[10pt]{article}" + "\n"
    tex = preamble + r"\begin{document}First \(x^2\). Second \(x^2\).\end{document}"
    marked, bindings, blockers = instrument_source_math_positions(tex, nodes)
    assert not blockers and len(bindings) == 2
    pdf, rasters = tex_pdf(tmp_path / "native.tex", tex)
    instrumented_pdf, _ = tex_pdf(tmp_path / "positioned.tex", marked)
    interpreted_pdf, interpreted_rasters = tex_pdf(
        tmp_path / "interpreted.tex", preamble + r"\begin{document}" + _math_body(nodes) + r"\end{document}"
    )
    actual = inspect_pdf_positioned_math(
        pdf,
        rasters,
        ast,
        source_tex=tex.encode(),
        instrumented_pdf=instrumented_pdf,
        interpreted_pdf=interpreted_pdf,
        interpreted_rasters=interpreted_rasters,
        deadline=time.monotonic() + 10,
    )
    assert actual["status"] == "pass", actual
    assert len(actual["observations"]) == 2
    changed_pdf, changed_rasters = tex_pdf(tmp_path / "changed.tex", tex.replace(r"\(x^2\)", r"\(x^3\)", 1))
    changed = inspect_pdf_positioned_math(
        changed_pdf,
        changed_rasters,
        ast,
        source_tex=tex.encode(),
        instrumented_pdf=instrumented_pdf,
        interpreted_pdf=interpreted_pdf,
        interpreted_rasters=interpreted_rasters,
        deadline=time.monotonic() + 10,
    )
    assert changed["status"] == "fail", changed
    assert "pdf.math.source.position" in {row["code"] for row in changed["findings"]}


@pytest.mark.parametrize(
    "control,code",
    [
        ("baseline", None),
        ("changed-table-number", "pdf.content.missing"),
        ("misaligned-table", "pdf.table.row.alignment"),
        ("changed-source-figure", "pdf.figure.source"),
        ("opaque-figure-overlay", "pdf.figure.visual"),
        ("moved-figure", "pdf.figure.caption.position"),
        ("moved-figure-and-caption", "pdf.reference.glyphs"),
    ],
)
def test_actual_valid_pdf_native_source_controls(tmp_path: Path, control: str, code: str | None) -> None:
    ast = parsed(SOURCE)
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", SOURCE),), ast)
    identity = next(row["identity"] for row in plan.occurrences if row["kind"] == "Image")
    pdf, rasters = native_pdf(tmp_path / "control.pdf", control)
    source_pdf, source_rasters = native_pdf(tmp_path / "original-source-reference.pdf", "baseline")
    observed = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets={identity: ("asset.png", source_asset())},
        full_source_reference={"pdf": source_pdf, "rasters": source_rasters, "source_plan_digest": plan.digest},
        deadline=time.monotonic() + 15,
    )
    if code is None:
        assert observed["status"] == "pass", observed
        assert len(observed["tables"]["rows"]) == 3
        assert len(observed["figures"]["figures"]) == 1
        assert observed["figures"]["figures"][0]["covered"]
    else:
        assert observed["status"] == "fail", observed
        assert code in {row["code"] for row in observed["findings"]}, observed


def test_portable_replay_rejects_removed_real_source_finding(tmp_path: Path) -> None:
    ast = parsed(SOURCE)
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", SOURCE),), ast)
    identity = next(row["identity"] for row in plan.occurrences if row["kind"] == "Image")
    pdf, rasters = native_pdf(tmp_path / "control.pdf", "changed-table-number")
    assets = {identity: ("asset.png", source_asset())}
    source_pdf, source_rasters = native_pdf(tmp_path / "original-source-reference.pdf", "baseline")
    actual = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets=assets,
        full_source_reference={"pdf": source_pdf, "rasters": source_rasters, "source_plan_digest": plan.digest},
        deadline=time.monotonic() + 15,
    )
    assert actual["findings"]
    payloads = {
        "native.pdf": pdf,
        "native-page.png": rasters[0],
        "asset.png": source_asset(),
        "original-source.pdf": source_pdf,
        "original-source-page.png": source_rasters[0],
    }
    bindings = {
        name: {"path": name, "sha256": hashlib.sha256(content).hexdigest()} for name, content in payloads.items()
    }
    tampered = copy.deepcopy(actual)
    tampered["findings"] = []
    tampered["status"] = "pass"

    def retained(binding: dict[str, str]) -> bytes:
        return payloads[binding["path"]]

    current = replay_pdf_source_witness(
        actual,
        artifact_id="manuscript:pdf",
        sources=(("original.md", SOURCE),),
        ast_bytes=ast,
        pdf=bindings["native.pdf"],
        rasters=(bindings["native-page.png"],),
        assets={identity: bindings["asset.png"]},
        read_artifact=retained,
        full_source_reference={
            "pdf": bindings["original-source.pdf"],
            "rasters": (bindings["original-source-page.png"],),
            "source_plan_digest": plan.digest,
        },
        deadline=time.monotonic() + 15,
    )
    assert current["status"] == "fail"
    with pytest.raises(ValueError, match="independent source/native replay"):
        replay_pdf_source_witness(
            tampered,
            artifact_id="manuscript:pdf",
            sources=(("original.md", SOURCE),),
            ast_bytes=ast,
            pdf=bindings["native.pdf"],
            rasters=(bindings["native-page.png"],),
            assets={identity: bindings["asset.png"]},
            read_artifact=retained,
            full_source_reference={
                "pdf": bindings["original-source.pdf"],
                "rasters": (bindings["original-source-page.png"],),
                "source_plan_digest": plan.digest,
            },
            deadline=time.monotonic() + 15,
        )


def test_source_pixels_without_original_caption_reference_remain_blocked(tmp_path: Path) -> None:
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", SOURCE),), parsed(SOURCE))
    identity = next(row["identity"] for row in plan.occurrences if row["kind"] == "Image")
    pdf, rasters = native_pdf(tmp_path / "control.pdf", "baseline")
    observed = inspect_pdf_source_witness(
        pdf, rasters, plan, assets={identity: ("asset.png", source_asset())}, deadline=time.monotonic() + 15
    )
    assert observed["status"] == "blocked", observed
    assert not observed["figures"]["figures"][0]["covered"]
    assert any("source figure/caption positions" in blocker for blocker in observed["blockers"])


def test_equal_reference_cannot_discharge_uninterpreted_raw_source(tmp_path: Path) -> None:
    source = SOURCE + b"\n\\vspace{10pt}\n"
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", source),), parsed(source))
    identity = next(row["identity"] for row in plan.occurrences if row["kind"] == "Image")
    pdf, rasters = native_pdf(tmp_path / "control.pdf", "baseline")
    source_pdf, source_rasters = native_pdf(tmp_path / "reference.pdf", "baseline")
    observed = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets={identity: ("asset.png", source_asset())},
        full_source_reference={"pdf": source_pdf, "rasters": source_rasters, "source_plan_digest": plan.digest},
        deadline=time.monotonic() + 15,
    )
    assert observed["whole_page_parity"]["status"] == "pass"
    assert observed["status"] == "blocked", observed
    assert any("RawBlock requires" in blocker for blocker in observed["blockers"])
