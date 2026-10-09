"""Genuine source parsers, source occurrence contracts and native controls."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_slide_source import compile_slide_source_contract, instrument_slide_source
from infrastructure.reporting.native_slide_raw_source import raw_slide_segments
from infrastructure.reporting.native_slide_controls import CONTROL_SOURCE, SLIDE_CONTROL_CODES, run_slide_source_control


def _parse(source: bytes) -> bytes:
    binary = shutil.which("pandoc")
    if binary is None:
        pytest.skip("actual Pandoc source parser is unavailable")
    return subprocess.run(
        [binary, "--from=markdown", "--to=json"], input=source, capture_output=True, check=True, timeout=10
    ).stdout


def test_actual_source_duplicates_and_later_occurrences_are_complete() -> None:
    ast = _parse(CONTROL_SOURCE)
    contract = compile_slide_source_contract(
        "invented:slides", (("source.md", CONTROL_SOURCE),), ast, profile="archive"
    )
    marked, bindings = instrument_slide_source(ast, contract, target="beamer")
    assert len(bindings) == 8
    assert [row["source"] for row in bindings[:4]] == [row["source"] for row in bindings[4:]]
    assert len({row["identity"] for row in bindings}) == 8
    assert len({row["mcid"] for row in bindings}) == 8
    assert "pdf:code" in marked.decode()
    assert contract.blockers == ()


def test_actual_source_images_preserve_alt_metadata_without_fabricated_native_text() -> None:
    source = b"![Scientific result](../figures/result.png)\n\nAn actual [source](https://example.org/evidence).\n"
    ast = _parse(source)
    contract = compile_slide_source_contract("invented:slides", (("source.md", source),), ast, profile="archive")
    _, bindings = instrument_slide_source(ast, contract, target="beamer")
    images = [row for row in contract.occurrences if row.kind == "image"]
    assert len(images) == 1
    assert "Scientific" in images[0].source
    assert sum(row["kind"] == "image" for row in bindings) == 1
    assert any(row.kind == "link" and row.target == "https://example.org/evidence" for row in contract.occurrences)


def test_actual_source_unknown_raw_cannot_inherit_complete_projection_support() -> None:
    source = b"\\begin{unknownenvironment}\nA changed scientific claim.\n\\end{unknownenvironment}\n"
    ast = _parse(source)
    contract = compile_slide_source_contract("invented:slides", (("source.md", source),), ast, profile="archive")
    assert contract.blockers
    assert any(row.kind == "unsupported-raw" for row in contract.occurrences)


def test_raw_formalism_witnesses_cover_inner_numbers_code_math_and_references() -> None:
    raw = (
        r"\begin{hypothesis}[Measured outcome]Offset -3.25 mV; "
        r"\texttt{sample\_count=150}; $\alpha=0.05$; \cref{eq:outcome}.\end{hypothesis}"
    )
    segments, blockers = raw_slide_segments(raw, "raw-formalism", references={"eq:outcome": "Equation 2"})
    assert blockers == ()
    assert any(row.kind == "math" and row.source == r"\alpha=0.05" for row in segments)
    assert any(
        row.kind == "reference" and row.target == "eq:outcome" and row.tokens == ("Equation", "2") for row in segments
    )
    assert any("-" in row.tokens and "25" in row.tokens for row in segments if row.kind == "text")
    assert any(row.source == r"\_" and row.tokens == ("_",) for row in segments)
    assert all(raw[row.start : row.end] == row.source for row in segments)
    _, unresolved = raw_slide_segments(raw, "raw-formalism")
    assert any("eq:outcome" in item for item in unresolved)


def test_raw_source_unknown_command_and_external_expansion_remain_blocked() -> None:
    _, unknown = raw_slide_segments(r"\begin{theorem}A \unadmitted{claim}.\end{theorem}", "raw-formalism")
    assert any("unadmitted" in item for item in unknown)
    _, external = raw_slide_segments(r"\begin{theorem}\input{outside}\end{theorem}", "raw-formalism")
    assert external


def test_actual_source_cross_references_need_independent_original_numbers() -> None:
    source = b"The scientific result is shown in [@fig:measurement].\n"
    ast = _parse(source)
    missing = compile_slide_source_contract("invented:slides", (("source.md", source),), ast, profile="archive")
    assert any("fig:measurement" in item for item in missing.blockers)
    admitted = compile_slide_source_contract(
        "invented:slides", (("source.md", source),), ast, profile="archive", reference_displays={"fig:measurement": "2"}
    )
    _, bindings = instrument_slide_source(ast, admitted, target="beamer")
    assert admitted.blockers == ()
    assert any(row["kind"] == "reference" and row["tokens"] == ("2",) for row in bindings)
    assert not any("@fig" in row["source"] for row in bindings if row["kind"] == "text")


def test_actual_source_math_external_expansion_is_explicitly_blocked() -> None:
    source = rb"An equation $\input{outside}$ must never read another file."
    contract = compile_slide_source_contract(
        "invented:slides", (("source.md", source),), _parse(source), profile="archive"
    )
    assert any("mathematical source expands" in item for item in contract.blockers)


@pytest.mark.parametrize("name", tuple(SLIDE_CONTROL_CODES))
def test_actual_later_page_native_slide_controls(tmp_path: Path, name: str) -> None:
    if not all(shutil.which(tool) for tool in ("pandoc", "pdftoppm", "pdffonts")):
        pytest.skip("actual native slide control tools are unavailable")
    directory = tmp_path / "output/readiness/control"
    directory.parent.mkdir(parents=True)
    observed = run_slide_source_control(
        tmp_path, directory, name, env=dict(os.environ), deadline=time.monotonic() + 45, run_id="actual-slide-control"
    )
    assert observed["parser"]["pages"] == 2
    assert len(observed["raster"]["rasters"]) == 2
    expected = SLIDE_CONTROL_CODES[name]
    assert observed["oracle_exit_code"] == (0 if expected is None else 1)
    assert observed["observation"]["status"] == ("pass" if expected is None else "fail")
    # Retained source marker ledger is reconstructed from actual source parsing.
    source_tool = json.loads((tmp_path / observed["source_tools"][0]["path"]).read_bytes())
    assert source_tool["original_exit_code"] == source_tool["exit_code"] == 0
    assert "Measured" in source_tool["stdout"]
