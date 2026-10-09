"""Actual Pandoc/Chromium table, note and alpha-source coverage and replay."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import time
from pathlib import Path

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.reporting.native_format_browser_oracles import audit_browser_html
from infrastructure.reporting.native_format_browser_replay import replay_browser_observation
from infrastructure.reporting.native_format_browser_semantic_controls import alpha_figure_bytes, mutate_html
from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
from infrastructure.reporting.native_format_observer_dispatch import _chrome
from infrastructure.reporting.native_format_semantic_original import (
    inspect_original_source,
    observe_original_source,
    replay_original_source,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


SOURCE = (
    b"# Invented scientific structure\n\n"
    b"| Invented channel | Invented value |\n|---|---:|\n| A | -9.25 |\n| B | 2.75 |\n\n"
    b"Invented footer reference.[^invented-note]\n\n"
    b"[^invented-note]: Invented footer offset -6.25 mV.\n\n"
    b"![Invented alpha pixels](alpha.png)\n\n![Repeated alpha pixels](alpha.png)\n"
)


def _parse(source: Path, *, html: Path | None = None) -> bytes:
    pandoc = shutil.which("pandoc")
    assert pandoc, "actual source parser is required"
    args = [pandoc, str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes"]
    args.extend(["--standalone", "--to=html5", "-o", str(html)] if html else ["--to=json"])
    result = run_bounded_subprocess(args, cwd=source.parent, env=build_bounded_env(), timeout=30)
    assert result.returncode == result.original_returncode == 0
    assert not result.timed_out and not result.custody_refused
    return result.stdout.encode()


def test_actual_source_census_retains_unknown_descendants_and_footnotes(tmp_path: Path) -> None:
    fixture = tmp_path / "output/readiness/fixture"
    fixture.mkdir(mode=0o700, parents=True)
    source = fixture / "source.md"
    source.write_bytes(SOURCE)
    ast = _parse(source)
    contract = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), SOURCE),), ast
    )
    assert not contract.blockers
    assert len(contract.table_sources) == len(contract.footnote_sources) == 1
    assert len(contract.image_sources) == 2
    note = contract.footnote_sources[0]
    assert [token for block in note["blocks"] for token in block["tokens"]] == [
        "Invented",
        "footer",
        "offset",
        "-",
        "6",
        ".",
        "25",
        "mV",
        ".",
    ]
    document = json.loads(ast)
    original = document["blocks"][0]
    document["blocks"][0] = {"t": "UnknownScientificContainer", "c": [original]}
    unknown = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), SOURCE),), json.dumps(document).encode()
    )
    assert any("unsupported block UnknownScientificContainer" in item for item in unknown.blockers)
    assert any(item["tag"] == "UnknownScientificContainer" for item in unknown.source_occurrences)
    assert any(item["tag"] == "Header" for item in unknown.source_occurrences)
    assert contract.blocks[0].tokens == unknown.blocks[0].tokens


def test_actual_original_source_receipts_and_portable_replay(tmp_path: Path) -> None:
    fixture = tmp_path / "output/readiness/fixture"
    fixture.mkdir(mode=0o700, parents=True)
    source = fixture / "source.md"
    source.write_bytes(SOURCE)
    ast = _parse(source)
    sources = ((source.relative_to(tmp_path).as_posix(), SOURCE),)
    projected = semantic_content_contract_from_ast("invented:html", sources, ast)
    evidence = tmp_path / "output/readiness/original-observation"
    evidence.mkdir(mode=0o700)
    deadline = time.monotonic() + 60
    bound, raw = observe_original_source(
        tmp_path,
        evidence,
        sources,
        projected,
        env=build_bounded_env(),
        deadline=deadline,
        run_id="d" * 32,
    )
    assert bound.original_source_occurrences and not bound.blockers
    independently_bound = replay_original_source(
        tmp_path,
        evidence,
        sources,
        projected,
        raw,
        SnapshotReader(tmp_path),
        run_id="d" * 32,
        custody={
            "root": str(tmp_path),
            "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
        },
        env=build_bounded_env(),
        deadline=deadline,
    )
    assert independently_bound.to_dict() == bound.to_dict()
    mutated = semantic_content_contract_from_ast("invented:html", sources, ast.replace(b"-9.25", b"-8.25"))
    assert any(
        item["code"] == "html.original.content"
        for item in inspect_original_source(
            "invented:html",
            sources,
            ast,
            mutated,
        )["findings"]
    )
    forged = copy.deepcopy(raw)
    forged["survival"]["contract"]["source_occurrences"].pop()
    with pytest.raises(ValueError, match="occurrence/survival"):
        replay_original_source(
            tmp_path,
            evidence,
            sources,
            projected,
            forged,
            SnapshotReader(tmp_path),
            run_id="d" * 32,
            custody={
                "root": str(tmp_path),
                "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
            },
            env=build_bounded_env(),
            deadline=deadline,
        )


@pytest.mark.timeout(240)
@pytest.mark.parametrize(
    "name,expected",
    [
        ("baseline-structure", None),
        ("changed-table-cell", "html.table.content"),
        ("changed-table-span", "html.table.span"),
        ("reordered-table-cell", "html.table.content"),
        ("hidden-table-cell", "html.table.visibility"),
        ("changed-footnote", "html.footnote.content"),
        ("hidden-footnote", "html.footnote.visibility"),
        ("wrong-footnote-target", "html.footnote.target"),
        ("opaque-footnote", "html.visual.invisible"),
        ("changed-alpha-pixel", "html.figure.pixels"),
        ("opaque-alpha-figure", "html.figure.visual"),
    ],
)
def test_actual_structure_and_alpha_browser_controls(tmp_path: Path, name: str, expected: str | None) -> None:
    fixture = tmp_path / "output/readiness/fixture"
    fixture.mkdir(mode=0o700, parents=True)
    source = fixture / "source.md"
    source.write_bytes(SOURCE)
    ast = _parse(source)
    contract = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), SOURCE),), ast
    )
    original = fixture / "original.html"
    _parse(source, html=original)
    for filename, mutant in (("alpha.png", False), ("wrong-alpha.png", True)):
        (fixture / filename).write_bytes(alpha_figure_bytes(mutant=mutant))
    original.write_text(mutate_html(original.read_text(), name))
    env = build_bounded_env()
    snapshot = SnapshotReader(tmp_path).read(original.relative_to(tmp_path).as_posix())
    evidence = tmp_path / "output/readiness/observation"
    evidence.mkdir(mode=0o700)
    raw = audit_browser_html(
        tmp_path,
        evidence,
        snapshot.content,
        contract,
        chrome=_chrome(env),
        env=env,
        deadline=time.monotonic() + 120,
        run_id="d" * 32,
        artifact=snapshot,
    )
    # Preserve only retained observation custody; retired browser caches are not
    # inputs to replay and can be removed from this disposable test root.
    for width in (390, 1280):
        shutil.rmtree(evidence / f"profile-{width}")
    assert not raw["blockers"]
    for viewport in raw["viewports"]:
        codes = {finding["code"] for finding in viewport["findings"]}
        assert not codes if expected is None else expected in codes, codes
        assert len(viewport["figures"]["figures"]) == 2
        assert len(viewport["structure"]["tables"]) == len(viewport["structure"]["footnotes"]) == 1
    # Independent parsing and native replay use the current implementation and
    # retained bytes, not producer outcomes or an equal-writer assertion.
    independent = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), SOURCE),), _parse(source)
    )
    assert independent.to_dict() == contract.to_dict()
    replay_browser_observation(
        tmp_path,
        evidence,
        snapshot,
        independent,
        raw,
        SnapshotReader(tmp_path),
        run_id="d" * 32,
        custody={
            "root": str(tmp_path),
            "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
        },
        runtime={"executable": sys.executable},
    )
    # Removing a source cell or forging a structure witness cannot reuse a
    # valid native screenshot/driver receipt to obtain portable admission.
    forged = copy.deepcopy(raw)
    forged["viewports"][0]["structure"]["tables"][0]["cells"].pop()
    with pytest.raises(ValueError, match="independently recomputed"):
        replay_browser_observation(
            tmp_path,
            evidence,
            snapshot,
            independent,
            forged,
            SnapshotReader(tmp_path),
            run_id="d" * 32,
            custody={
                "root": str(tmp_path),
                "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
            },
            runtime={"executable": sys.executable},
        )
