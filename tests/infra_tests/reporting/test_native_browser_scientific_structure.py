"""Actual Pandoc/Chromium table, note and alpha-source coverage and replay."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.reporting.native_format_browser_oracles import inspect_browser_dom
from infrastructure.reporting.native_format_browser_replay import replay_browser_observation
from infrastructure.reporting.native_format_browser_semantic_controls import alpha_figure_bytes, mutate_html
from infrastructure.reporting.native_format_content_contracts import (
    NativeContentContract,
    semantic_content_contract_from_ast,
)
from infrastructure.reporting.native_format_semantic_original import (
    inspect_original_source,
    observe_original_source,
    replay_original_source,
)
from infrastructure.reporting.native_projection_contracts import ProjectionSourceUnsupported
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from tests.infra_tests.reporting._audited_browser_child import audited_browser_artifact

# Portable replay of a retained native receipt needs the externally admitted
# Source and the original launch custodian. Receipt DATA and a bare relocated
# SnapshotReader never hold either, so replay refuses at the first native tool
# receipt. Checks before that point are asserted for their own reason; checks
# after it are listed as explicit custody-gated skips.
UNADMITTED = "externally admitted source and original launch custody"
CUSTODY_GATED = (
    "requires original launch custody, which unit tests cannot construct; reachable only "
    "under the platform-required-acceptance native-original/complete jobs"
)


SOURCE = (
    b"# Invented scientific structure\n\n"
    b"| Invented channel | Invented value |\n|---|---:|\n| A | -9.25 |\n| B | 2.75 |\n\n"
    b"Invented footer reference.[^invented-note]\n\n"
    b"[^invented-note]: Invented footer offset -6.25 mV.\n\n"
    b"![Invented alpha pixels](alpha.png)\n\n![Repeated alpha pixels](alpha.png)\n"
)


def _refused_before_custody(reason: str, replay: Callable[[], object]) -> None:
    """Tampered DATA is refused for its own reason, not for absent custody."""
    with pytest.raises(ValueError, match=reason) as refused:
        replay()
    assert not isinstance(refused.value, ProjectionSourceUnsupported)


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
    # The retained survival obligation is recomputed from the retained AST bytes
    # with the current implementation, independently of the producer's write.
    retained_ast = SnapshotReader(tmp_path).read(raw["ast"]["path"]).content
    assert inspect_original_source("invented:html", sources, retained_ast, projected) == raw["survival"]

    def replay(receipt: dict[str, Any], *, replay_sources: tuple[tuple[str, bytes], ...] = sources) -> object:
        return replay_original_source(
            tmp_path,
            evidence,
            replay_sources,
            projected,
            receipt,
            SnapshotReader(tmp_path),
            run_id="d" * 32,
            custody={
                "root": str(tmp_path),
                "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
            },
            env=build_bounded_env(),
            deadline=deadline,
        )

    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        replay(raw)
    # Receipt bindings and source identity are checked before custody.
    forged_ast = copy.deepcopy(raw)
    forged_ast["ast"]["sha256"] = "0" * 64
    _refused_before_custody("bytes differ from their binding", lambda: replay(forged_ast))
    changed = ((sources[0][0], SOURCE.replace(b"-9.25", b"-8.25")),)
    _refused_before_custody("belongs to another source projection", lambda: replay(raw, replay_sources=changed))
    # A forged survival witness is compared only after the Pandoc receipt is
    # admitted; here it fails closed at the custody gate (see explicit skip).
    forged = copy.deepcopy(raw)
    forged["survival"]["contract"]["source_occurrences"].pop()
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        replay(forged)
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
    snapshot = SnapshotReader(tmp_path).read(original.relative_to(tmp_path).as_posix())
    evidence = tmp_path / "output/readiness/observation"
    evidence.mkdir(mode=0o700)
    # The HTML parent custodian requires an interpreter that installed the
    # executed-bytecode audit before importing the SDK, as trusted launchers do.
    raw = audited_browser_artifact(
        tmp_path,
        evidence,
        snapshot.relative,
        sources=(source.relative_to(tmp_path).as_posix(),),
        artifact_id="invented:html",
        ast=ast,
        workspace=tmp_path / "audited-child",
        deadline=time.monotonic() + 120,
        run_id="d" * 32,
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
    # Independent parsing uses the current implementation and retained bytes,
    # not producer outcomes or an equal-writer assertion. Each retained DOM
    # independently recomputes the exact structure witness it was bound to.
    independent = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), SOURCE),), _parse(source)
    )
    assert independent.to_dict() == contract.to_dict()
    for viewport in raw["viewports"]:
        assert inspect_browser_dom(viewport["dom"], independent, None)["structure"] == viewport["structure"]

    def replay(observation: dict[str, Any], replay_contract: NativeContentContract = independent) -> object:
        return replay_browser_observation(
            tmp_path,
            evidence,
            snapshot,
            replay_contract,
            observation,
            SnapshotReader(tmp_path),
            run_id="d" * 32,
            custody={
                "root": str(tmp_path),
                "implementation_root": str(Path(__file__).resolve().parents[3] / "infrastructure"),
            },
            runtime={"executable": sys.executable},
        )

    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        replay(raw)
    # Removing a source cell changes the source contract, which is compared
    # before custody: the retained native receipt cannot be reused for it.
    removed = tmp_path / "removed-cell/source.md"
    removed.parent.mkdir()
    removed_bytes = SOURCE.replace(b"| B | 2.75 |\n", b"")
    removed.write_bytes(removed_bytes)
    without_cell = semantic_content_contract_from_ast(
        "invented:html", ((source.relative_to(tmp_path).as_posix(), removed_bytes),), _parse(removed)
    )
    assert without_cell.digest != independent.digest
    _refused_before_custody("source/policy identity changed", lambda: replay(raw, without_cell))
    # A forged structure witness is compared only after the native browser
    # receipt is admitted; here it fails closed at the custody gate (see skip).
    forged = copy.deepcopy(raw)
    forged["viewports"][0]["structure"]["tables"][0]["cells"].pop()
    with pytest.raises(ProjectionSourceUnsupported, match=UNADMITTED):
        replay(forged)


@pytest.mark.parametrize("obligation", ["forged-original-survival-witness", "forged-browser-structure-witness"])
def test_forged_semantic_witness_rejection_needs_original_launch_custody(obligation: str) -> None:
    """Uncovered here: replay_original_source compares the survival witness, and
    replay_browser_observation the per-viewport structure witness, only after the
    retained native tool receipt is admitted against original launch custody."""
    pytest.skip(f"{obligation}: {CUSTODY_GATED}")
