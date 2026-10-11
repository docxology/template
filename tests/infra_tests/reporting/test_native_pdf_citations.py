"""Actual source-only natbib references and valid changed/hidden PDF controls."""

from __future__ import annotations

import json
import base64
import shutil
import sys
import time
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_evidence import bootstrap_command, write_json
from infrastructure.reporting.native_format_acceptance_contracts import native_environment
from infrastructure.reporting.native_pdf_citation_replay import inspect_natbib_citations
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, compile_reference
from infrastructure.reporting.native_pdf_citations import citation_occurrences, observe_natbib_reference, raw_citations
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

pytestmark = [pytest.mark.requires_latex, pytest.mark.timeout(60)]
SOURCE = rb"""# Native citation proof

[@smithA; @smithB; @corp; @editor; @old; @three].

Following @smithA is narrative.

[-@old].

[see @smithA, pp. 2-3; @corp].

\citep[compare][chap. 2]{editor} and \citet{corp}.

\citeyearpar{old}.

\citetext{\citealp[see][pp. 2--3]{smithA}; \citealp{smithB}}.

\cite{three}; \citep{corp}; \citet*{three}; \citealt{editor}; \citeauthor{corp}; \citeyear{old}.
"""
BIB = rb"""@article{smithA, author={Alice Smith and Bob Jones}, title={Alpha}, year={2000}, journal={Test}}
@article{smithB, author={Alice Smith and Bob Jones}, title={Beta}, year={2000}, journal={Test}}
@book{corp, author={{World Health Organization}}, title={Guide}, year={2020}, publisher={Test}}
@book{editor, editor={Emily Brown and John Green}, title={Collected}, year={1999}, publisher={Test}}
@book{old, author={{Pliny the Elder}}, title={Nature}, year={c. 77 CE}, publisher={Test}}
@article{three, author={Alice Aster and Bob Birch and Carol Cedar}, title={Many}, year={2011}, journal={Test}}
"""


@pytest.fixture(scope="module")
def cohort(tmp_path_factory):
    for name in ("pandoc", "xelatex", "bibtex", "xdvipdfmx", "kpsewhich", "pdffonts", "pdftotext", "pdftoppm"):
        if not shutil.which(name):
            pytest.skip(f"actual native citation control requires installed {name}")
    root = tmp_path_factory.mktemp("source-natbib")
    base = root / "output/readiness/citations"
    base.mkdir(parents=True)
    env = native_environment(Path(__file__).resolve().parents[3], Path(sys.executable), base)
    deadline = time.monotonic() + 60
    parse = CitationRuntime(root, base / "parse", env=env, deadline=deadline, run_id="native-citations")
    source = parse.freeze("source.md", SOURCE)
    ast = parse.tool("pandoc", [str(source), "--from=markdown+raw_tex", "--to=json"], "original-source-ast")[
        "stdout"
    ].encode()
    arguments = {
        "ast_bytes": ast,
        "sources": (("source.md", SOURCE),),
        "bibliographies": (("references.bib", BIB),),
        "env": env,
        "deadline": deadline,
        "run_id": "native-citations",
        "artifact_id": "control:pdf",
    }
    reference = observe_natbib_reference(root, base / "reference", **arguments)
    write_json(root, base / "reference.json", reference)
    portable = tmp_path_factory.mktemp("natbib-reader")
    shutil.copytree(root / "output", portable / "output")
    shutil.rmtree(root)
    assert not root.exists()
    base = portable / "output/readiness/citations"
    arguments["env"] = native_environment(Path(__file__).resolve().parents[3], Path(sys.executable), base)
    return portable, base, arguments, reference


def _raster(root, directory, pdf, env):
    runtime = CitationRuntime(root, directory, env=env, deadline=time.monotonic() + 60, run_id="native-citations")
    runtime.freeze("target.pdf", pdf)
    runtime.tool(
        "pdftoppm",
        ["-r", "150", "-png", "target.pdf", "page"],
        "actual-native-raster",
        input_paths=(directory / "target.pdf",),
    )
    paths = sorted(directory.glob("page-*.png"))
    assert paths
    return tuple(runtime.read(path) for path in paths)


def _valid_control(reference, variant):
    from reportlab.lib.colors import black, white
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen.canvas import Canvas

    labels = [row["native_text"] for row in reference["occurrences"]]
    if variant == "changed":
        labels[0] = labels[0].replace("2000a", "9999a")
    elif variant == "omitted":
        labels.pop(0)
    elif variant == "reordered":
        labels[:2] = reversed(labels[:2])
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612, 792), pageCompression=0)
    top = 738
    canvas.setFont("Helvetica", 11)
    for number, label in enumerate(labels):
        canvas.setFillColor(white if variant == "hidden" and number == 0 else black)
        for line in simpleSplit(label, "Helvetica", 11, 500):
            canvas.drawString(54, top, line)
            top -= 16
        top -= 8
    canvas.save()
    return output.getvalue()


def test_real_plainnat_modes_notes_names_and_year_suffix(cohort):
    root, _, _, raw = cohort
    labels = [row["native_text"] for row in raw["occurrences"]]
    assert len(labels) == 14
    assert "Smith and Jones, 2000a,b" in labels[0]
    assert "World Health Organization, 2020" in labels[0]
    assert "Brown and Green, 1999" in labels[0]
    assert "Pliny the Elder, c. 77 CE" in labels[0]
    assert "Aster et al., 2011" in labels[0]
    assert labels[1] == "Smith and Jones [2000a]"
    assert labels[2] == "[c. 77 CE]"
    assert "pp. 2-3; World Health Organization" in labels[3]
    assert labels[4] == "[compare Brown and Green, 1999, chap. 2]"
    assert labels[7] == "[see Smith and Jones, 2000a, pp. 2–3; Smith and Jones, 2000b]"
    assert "Aster, Birch, and Cedar [2011]" in labels
    assert raw["blockers"] == []
    assert len(raw["tool_artifacts"]) == 14
    custody = raw["dependency_custody"]
    assert custody["before"] == custody["after"]
    assert custody["style_before"] == custody["style_after"]
    assert any(row["name"].endswith(".otf") for row in custody["before"])
    for binding in raw["tool_artifacts"]:
        process = SnapshotReader(root).read(binding["path"]).json_object()
        assert process["exit_code"] == process["original_exit_code"] == 0
        assert process["timed_out"] is False and process["custody_refused"] is False
        assert process["input_observations_before"] == process["input_observations_after"]


@pytest.mark.parametrize(
    "variant,code",
    [
        ("baseline", None),
        ("changed", "citation.glyph.missing"),
        ("omitted", "citation.glyph.missing"),
        ("hidden", "citation.visual.invisible"),
        ("reordered", "citation.glyph.order"),
    ],
)
def test_valid_actual_native_citation_controls(cohort, variant, code):
    root, base, arguments, reference = cohort
    pdf = _valid_control(reference, variant)
    rasters = _raster(root, base / f"control-{variant}", pdf, arguments["env"])
    observation = inspect_natbib_citations(pdf, rasters, reference, deadline=time.monotonic() + 60)
    assert observation["blockers"] == []
    if code is None:
        assert observation["status"] == "pass", observation["findings"]
        assert len(observation["matches"]) == len(reference["occurrences"])
    else:
        assert observation["status"] == "fail"
        assert code in {row["code"] for row in observation["findings"]}


def test_independent_complete_source_pdf_against_reference(cohort):
    root, base, arguments, reference = cohort
    deadline = time.monotonic() + 60
    target = CitationRuntime(
        root, base / "source-target", env=arguments["env"], deadline=deadline, run_id="native-citations"
    )
    source = target.freeze("source.md", SOURCE)
    target.freeze("references.bib", BIB)
    tex = target.tool(
        "pandoc",
        [str(source), "--from=markdown+raw_tex", "--to=latex", "--standalone", "--natbib"],
        "actual-complete-source-pdf",
    )["stdout"]
    tex = tex.replace(r"\end{document}", r"\bibliography{references}" + "\n" + r"\end{document}")
    pdf, _ = compile_reference(target, tex.encode())
    rasters = _raster(root, base / "source-target-raster", pdf, arguments["env"])
    observation = inspect_natbib_citations(pdf, rasters, reference, deadline=deadline)
    assert observation["status"] == "pass", observation


def test_current_reader_rebuild_after_destroyed_producer(cohort, tmp_path):
    root, _, arguments, reference = cohort
    portable = tmp_path / "reader"
    portable.mkdir()
    shutil.copytree(root / "output", portable / "output")
    process = SnapshotReader(root).read(reference["tool_artifacts"][0]["path"]).json_object()
    producer = Path(process["cwd"]).parents[3]
    assert not producer.exists()

    def encode(data):
        return base64.b64encode(data).decode("ascii")

    source_inputs = {
        "ast": encode(arguments["ast_bytes"]),
        "run_id": arguments["run_id"],
        "artifact_id": arguments["artifact_id"],
    }
    for name in ("sources", "bibliographies"):
        source_inputs[name] = [[name, encode(data)] for name, data in arguments[name]]
    request = portable / "output/readiness/reader-request.json"
    write_json(portable, request, {"reference": "output/readiness/citations/reference.json", "inputs": source_inputs})
    deadline = time.monotonic() + 60
    directory = portable / "output/readiness/replay"
    command = bootstrap_command(
        Path(sys.executable),
        Path(__file__).resolve().parents[3],
        "infrastructure.reporting.native_pdf_citation_replay",
        "--root",
        str(portable),
        "--request",
        str(request),
        "--directory",
        str(directory),
        "--deadline",
        str(deadline),
    )
    result = run_bounded_subprocess(
        command, cwd=portable, env=arguments["env"], timeout=deadline - time.monotonic(), capture_output=True
    )
    assert result.returncode == result.original_returncode == 0, result.stderr or result.command_error
    assert not result.timed_out and not result.custody_refused
    fresh = SnapshotReader(portable).read("output/readiness/replay/reader-reference.json").json_object()
    assert fresh["occurrences"] == reference["occurrences"]
    assert not producer.exists()


def test_raw_citation_parser_keeps_balanced_modes_notes_and_unknowns():
    rows, residual = raw_citations(r"\citetext{\citealp[see][pp. {2--3}]{a}; \citealp{b}}")
    assert residual == ""
    assert rows[0]["keys"] == ["a", "b"]
    assert rows[0]["children"][0]["notes"] == ["see", "pp. {2--3}"]
    with pytest.raises(ValueError, match="outside"):
        raw_citations(r"\autocite{a}")
    with pytest.raises(ValueError, match="unterminated"):
        raw_citations(r"\citep[see]{a")


def test_source_ast_raw_macro_and_mixed_crossref_blockers_are_preserved():
    cite = {
        "t": "Cite",
        "c": [
            [
                {"citationId": key, "citationPrefix": [], "citationSuffix": [], "citationMode": {"t": "NormalCitation"}}
                for key in ("def:truth", "smithA")
            ],
            [],
        ],
    }
    ast = {
        "pandoc-api-version": [1, 23],
        "meta": {},
        "blocks": [
            {
                "t": "Para",
                "c": [
                    cite,
                    {"t": "RawInline", "c": ["tex", r"\newcommand{\mycite}{\citep{smithA}}"]},
                    {"t": "RawBlock", "c": ["tex", r"\bibliographystyle{abbrvnat}"]},
                    {"t": "Code", "c": [["", [], []], r"\citep{not-a-visible-citation}"]},
                ],
            }
        ],
    }
    _, occurrences, excluded, blockers = citation_occurrences(
        json.dumps(ast).encode(), deadline=time.monotonic() + 60, crossref_keys=("def:truth",)
    )
    assert occurrences == () and len(excluded) == 1
    assert any("mixed" in row for row in blockers)
    assert any("macro" in row for row in blockers)
    assert len(blockers) == 3


def test_nocite_metadata_is_a_nonvisible_style_input():
    nocite = {"t": "MetaInlines", "c": [{"t": "Cite", "c": [[{"citationId": "*"}], []]}]}
    ast = {"pandoc-api-version": [1, 23], "meta": {"nocite": nocite}, "blocks": []}
    _, occurrences, nonvisible, blockers = citation_occurrences(
        json.dumps(ast).encode(), deadline=time.monotonic() + 60
    )
    assert not occurrences and not blockers
    assert nonvisible == ({"kind": "metadata-nocite", "original": nocite},)
