"""Real natbib source engines and raw-node interpretation integration controls."""

from __future__ import annotations

import copy
import sys
import time
from pathlib import Path
from typing import Any

import infrastructure
import pytest

from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_format_pdf_raw_natbib import independent_raw_natbib_labels
from infrastructure.reporting.native_format_pdf_semantic_plan import compile_pdf_semantic_plan
from infrastructure.reporting.native_format_pdf_source_witness import inspect_pdf_source_witness
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, compile_reference
from infrastructure.reporting.native_pdf_citations import observe_natbib_reference

SOURCE = rb"""Before raw \citep{example} after raw.

Before reader [@example] after reader.
"""
BIB = rb"""@article{example, author={Alice Smith}, title={Original}, year={2000}, journal={Test}}
"""


@pytest.fixture(scope="module")
def original_natbib(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("original-raw-natbib")
    directory = root / "output/readiness/citations"
    canonical = Path(infrastructure.__file__).resolve().parent.parent
    env = native_environment(canonical, Path(sys.executable), directory)
    deadline = time.monotonic() + 60
    parser = CitationRuntime(root, directory / "parse", env=env, deadline=deadline, run_id="raw-natbib")
    source = parser.freeze("original.md", SOURCE)
    ast = parser.tool(
        "pandoc",
        [str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"],
        "original-source-ast",
    )["stdout"].encode()
    reference = observe_natbib_reference(
        root,
        directory / "independent-natbib",
        ast_bytes=ast,
        sources=(("original.md", SOURCE),),
        bibliographies=(("references.bib", BIB),),
        env=env,
        deadline=deadline,
        run_id="raw-natbib",
        artifact_id="manuscript:pdf",
    )
    assert not reference["blockers"], reference
    return {"root": root, "directory": directory, "env": env, "ast": ast, "reference": reference}


def _original_source_pdf(cohort: dict[str, Any], name: str, bibliography: bytes) -> tuple[bytes, tuple[bytes, ...]]:
    directory = cohort["directory"] / name
    runtime = CitationRuntime(
        cohort["root"], directory, env=cohort["env"], deadline=time.monotonic() + 30, run_id="raw-natbib"
    )
    source = runtime.freeze("original.md", SOURCE)
    runtime.freeze("references.bib", bibliography)
    tex = runtime.tool(
        "pandoc",
        [
            str(source),
            "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
            "--to=latex",
            "--standalone",
            "--natbib",
        ],
        "actual-whole-original-source",
    )["stdout"]
    tex = tex.replace(r"\end{document}", "\\bibliography{references}\n" + r"\end{document}")
    pdf, _ = compile_reference(runtime, tex.encode())
    raster = CitationRuntime(
        cohort["root"],
        cohort["directory"] / (name + "-raster"),
        env=cohort["env"],
        deadline=time.monotonic() + 10,
        run_id="raw-natbib",
    )
    raster.freeze("target.pdf", pdf)
    raster.tool("pdftoppm", ["-r", "150", "-png", "target.pdf", "page"], "actual-every-page-raster")
    pages = tuple(raster.read(path) for path in sorted(raster.directory.glob("page-*.png")))
    assert pages
    return pdf, pages


def test_genuine_raw_natbib_and_reader_citation_complete_source_positive(original_natbib: dict[str, Any]) -> None:
    cohort = original_natbib
    plan = compile_pdf_semantic_plan(
        "manuscript:pdf", (("original.md", SOURCE),), cohort["ast"], citation_reference=cohort["reference"]
    )
    raw = [row for row in plan.occurrences if row["kind"] == "RawInline"]
    assert len(raw) == 1 and raw[0]["raw_citation_reference_ids"]
    assert sum(row["kind"] == "Cite" for row in plan.occurrences) == 1
    pdf, rasters = _original_source_pdf(cohort, "candidate-original-source", BIB)
    reference_pdf, reference_rasters = _original_source_pdf(cohort, "source-only-original-reference", BIB)
    observed = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets={},
        citation_reference=cohort["reference"],
        full_source_reference={"pdf": reference_pdf, "rasters": reference_rasters, "source_plan_digest": plan.digest},
        deadline=time.monotonic() + 15,
    )
    assert observed["status"] == "pass", observed
    assert len(observed["citations"]["matches"]) == 2


def test_genuine_changed_bibliographic_year_cannot_clear_source_citation(original_natbib: dict[str, Any]) -> None:
    cohort = original_natbib
    plan = compile_pdf_semantic_plan(
        "manuscript:pdf", (("original.md", SOURCE),), cohort["ast"], citation_reference=cohort["reference"]
    )
    pdf, rasters = _original_source_pdf(cohort, "changed-year-candidate", BIB.replace(b"year={2000}", b"year={2001}"))
    reference_pdf, reference_rasters = _original_source_pdf(cohort, "source-only-year-control", BIB)
    observed = inspect_pdf_source_witness(
        pdf,
        rasters,
        plan,
        assets={},
        citation_reference=cohort["reference"],
        full_source_reference={"pdf": reference_pdf, "rasters": reference_rasters, "source_plan_digest": plan.digest},
        deadline=time.monotonic() + 15,
    )
    assert observed["status"] == "fail", observed
    assert "citation.glyph.missing" in {row["code"] for row in observed["findings"]}


def test_raw_reference_source_command_substitution_is_rejected(original_natbib: dict[str, Any]) -> None:
    cohort = original_natbib
    changed = copy.deepcopy(cohort["reference"])
    raw = next(row for row in changed["occurrences"] if row["source"]["kind"] == "raw-natbib")
    raw["source"]["original"]["command"] = "citeauthor"
    with pytest.raises(ValueError, match="exact parsed source command"):
        independent_raw_natbib_labels(cohort["ast"], changed)


def test_source_citation_looking_fragment_in_residual_raw_markup_stays_blocked(
    tmp_path: Path, original_natbib: dict[str, Any]
) -> None:
    cohort = original_natbib
    source = rb"Before \raisebox{1pt}{\citep{example}} after." + b"\n"
    parser = CitationRuntime(
        tmp_path, tmp_path / "parse", env=cohort["env"], deadline=time.monotonic() + 10, run_id="raw-residual"
    )
    path = parser.freeze("original.md", source)
    ast = parser.tool("pandoc", [str(path), "--from=markdown+raw_tex", "--to=json"], "original-source-ast")[
        "stdout"
    ].encode()
    reference = observe_natbib_reference(
        tmp_path,
        tmp_path / "reference",
        ast_bytes=ast,
        sources=(("original.md", source),),
        bibliographies=(("references.bib", BIB),),
        env=cohort["env"],
        deadline=time.monotonic() + 30,
        run_id="raw-residual",
        artifact_id="manuscript:pdf",
    )
    assert any("residual raw markup" in blocker for blocker in reference["blockers"]), reference
    assert independent_raw_natbib_labels(ast, reference) == {}
    plan = compile_pdf_semantic_plan("manuscript:pdf", (("original.md", source),), ast, citation_reference=reference)
    assert any(row["kind"] == "RawInline" for row in plan.occurrences)
    assert not any("raw_citation_reference_ids" in row for row in plan.occurrences)
