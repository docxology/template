"""Genuine original Note reader/XeTeX anchor and body controls, never mocks."""

from __future__ import annotations

import shutil
import subprocess
import time
import hashlib
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_pdf_note_paint import (
    inspect_pdf_original_note_paint,
    instrument_original_source_notes,
    replay_pdf_original_note_paint,
)
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from tests.infra_tests.reporting.test_native_pdf_source_witness import parsed, tex_pdf

SOURCE = b"Body before marker.[^n]\n\n[^n]: Literal original footnote body.\n"


@pytest.fixture(scope="module")
def original_note(tmp_path_factory: pytest.TempPathFactory) -> dict:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("genuine original Note writer is unavailable")
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", SOURCE),), parsed(SOURCE))
    body = subprocess.run(
        [pandoc, "--from=markdown", "--to=latex"], input=SOURCE, capture_output=True, check=True, timeout=10
    ).stdout.decode()
    tex = r"\documentclass{article}\begin{document}" + "\n" + body + "\n" + r"\end{document}" + "\n"
    directory = tmp_path_factory.mktemp("original-source-note")
    pdf, rasters = tex_pdf(directory / "original.tex", tex)
    marked, _ = instrument_original_source_notes(tex, plan)
    marked_pdf, marked_rasters = tex_pdf(directory / "marked.tex", marked)
    return {
        "plan": plan,
        "source_tex": tex.encode(),
        "source_marked_tex": marked.encode(),
        "source_marked_pdf": marked_pdf,
        "source_marked_rasters": marked_rasters,
        "source_marked_aux": (directory / "marked.aux").read_bytes(),
        "original_reference_pdf": pdf,
        "original_reference_rasters": rasters,
    }


def inspect(original: dict, pdf: bytes, rasters: tuple[bytes, ...]) -> dict:
    return inspect_pdf_original_note_paint(pdf, rasters, deadline=time.monotonic() + 10, **original)


def test_actual_original_note_anchor_and_body_have_source_semantics_and_paint(original_note: dict) -> None:
    actual = inspect(
        original_note, original_note["original_reference_pdf"], original_note["original_reference_rasters"]
    )
    assert actual["status"] == "pass", actual
    assert {row["kind"] for row in actual["observations"]} == {"anchor", "body"}
    assert {row["source_counter"] for row in actual["observations"]} == {"1"}


@pytest.mark.parametrize("control", ["changed-body", "changed-anchor-counter"])
def test_actual_note_body_or_anchor_changes_refuse_original_source(
    tmp_path: Path,
    original_note: dict,
    control: str,
) -> None:
    tex = original_note["source_tex"].decode()
    if control == "changed-body":
        changed = tex.replace("Literal original footnote body.", "Literal altered footnote body.")
    else:
        changed = tex.replace(r"\begin{document}", r"\begin{document}\setcounter{footnote}{8}")
    assert changed != tex
    pdf, rasters = tex_pdf(tmp_path / "candidate.tex", changed)
    actual = inspect(original_note, pdf, rasters)
    assert actual["status"] == "fail", actual
    assert actual["findings"]


def test_actual_source_note_counter_cannot_be_duplicated_or_replaced(original_note: dict) -> None:
    original_aux = original_note["source_marked_aux"]
    line = next(line for line in original_aux.splitlines(keepends=True) if line.startswith(b"\\NativeSourceNoteNumber"))
    changed = original_aux + line
    assert changed != original_aux
    with pytest.raises(ValueError, match="duplicate/nonliteral"):
        inspect(
            dict(original_note, source_marked_aux=changed),
            original_note["original_reference_pdf"],
            original_note["original_reference_rasters"],
        )


def test_portable_note_rebuilds_original_native_glyph_ledger_and_refuses_missing_claims(original_note: dict) -> None:
    pdf, rasters = original_note["original_reference_pdf"], original_note["original_reference_rasters"]
    observed = inspect(original_note, pdf, rasters)
    payload = dict(original_note, pdf=pdf, rasters=rasters)
    payload.pop("plan")
    artifacts = {}
    bindings = {}
    for name, value in payload.items():
        if isinstance(value, bytes):
            artifacts[name] = value
            bindings[name] = {"path": name, "sha256": hashlib.sha256(value).hexdigest()}
        else:
            bindings[name] = []
            for index, content in enumerate(value):
                path = f"{name}/{index}.png"
                artifacts[path] = content
                bindings[name].append({"path": path, "sha256": hashlib.sha256(content).hexdigest()})

    def retained(binding: dict) -> bytes:
        return artifacts[binding["path"]]

    assert (
        replay_pdf_original_note_paint(
            observed, original_note["plan"], bindings, read_artifact=retained, deadline=time.monotonic() + 10
        )
        == observed
    )
    with pytest.raises(ValueError, match="predicates differ"):
        replay_pdf_original_note_paint(
            dict(observed, observations=[]),
            original_note["plan"],
            bindings,
            read_artifact=retained,
            deadline=time.monotonic() + 10,
        )
