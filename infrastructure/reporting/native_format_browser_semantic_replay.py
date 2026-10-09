"""Independent source/producer/DOM/pixel replay of scientific browser controls."""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def replay_semantic_control(
    root: Path,
    directory: Path,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    deadline: float,
    env: dict[str, str],
) -> None:
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_browser_semantic_controls import (
        semantic_control_source,
        alpha_figure_bytes,
        BIBLIOGRAPHY,
        figure_bytes,
        mutate_html,
    )
    from infrastructure.reporting.native_format_content_contracts import semantic_content_contract_from_ast
    from infrastructure.reporting.native_format_observer_validation import replay_browser_observation
    from infrastructure.rendering._web_assets import harden_mathjax_script

    name = raw["name"]
    if raw.get("schema_version") != "template-native-browser-semantic-control-v1" or raw.get("run_id") != run_id:
        raise ValueError("semantic browser control identity differs")
    for filename, content in (
        ("source.md", semantic_control_source(name)),
        ("references.bib", BIBLIOGRAPHY),
        ("figure.png", figure_bytes()),
        ("wrong.png", figure_bytes(mutant=True)),
        ("alpha.png", alpha_figure_bytes()),
        ("wrong-alpha.png", alpha_figure_bytes(mutant=True)),
    ):
        snapshot = reader.read((directory / filename).relative_to(root).as_posix())
        if snapshot.content != content:
            raise ValueError("scientific browser control source is not independently reconstructed fixture")
    original = _file(raw["original"], reader)
    baseline = _file(raw["baseline"], reader)
    pandoc_html = _file(raw["pandoc_html"], reader)
    ast = _file(raw["ast"], reader)
    for snapshot, filename in (
        (original, "original.html"),
        (baseline, "baseline.html"),
        (pandoc_html, "pandoc.html"),
        (ast, "source-ast.json"),
    ):
        if snapshot.path != directory / filename:
            raise ValueError("semantic fixture bytes belong to another control")
    source = directory / "source.md"
    bib = directory / "references.bib"
    common = [
        str(producer_path(custody, root, source)),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        f"--bibliography={producer_path(custody, root, bib)}",
        "--citeproc",
        "--metadata=link-citations:true",
    ]
    tools = raw.get("producer_tools")
    if not isinstance(tools, list) or len(tools) != 2:
        raise ValueError("semantic fixture omitted actual producer receipts")
    parsed = _tool(tools[0]["artifact"], reader, run_id, "pandoc", "semantic-control-ast", [*common, "--to=json"])
    _tool(
        tools[1]["artifact"],
        reader,
        run_id,
        "pandoc",
        "semantic-control-html",
        [
            *common,
            "--standalone",
            "--mathjax=https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js",
            "-o",
            str(producer_path(custody, root, pandoc_html.path)),
        ],
    )
    if parsed.get("stdout", "").encode() != ast.content:
        raise ValueError("semantic fixture AST differs from original actual stdout")
    sources = (
        (source.relative_to(root).as_posix(), semantic_control_source(name)),
        (bib.relative_to(root).as_posix(), BIBLIOGRAPHY),
    )
    contract = semantic_content_contract_from_ast("semantic-browser-control", sources, ast.content)
    if raw.get("contract") != contract.to_dict():
        raise ValueError("semantic fixture source contract is not actual AST-derived")
    pandoc = shutil.which("pandoc", path=env.get("PATH"))
    if not pandoc:
        raise ValueError("reader requires actual source semantic parser")
    with tempfile.TemporaryDirectory(prefix="semantic-control-replay-") as private:
        work = Path(private).resolve()
        independent_source = work / "source.md"
        independent_bib = work / "references.bib"
        independent_source.write_bytes(semantic_control_source(name))
        independent_bib.write_bytes(BIBLIOGRAPHY)
        result = run_bounded_subprocess(
            [
                pandoc,
                str(independent_source),
                "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
                f"--bibliography={independent_bib}",
                "--citeproc",
                "--metadata=link-citations:true",
                "--to=json",
            ],
            cwd=work,
            env=env,
            timeout=min(60, deadline - time.monotonic()),
        )
        if result.returncode != 0 or result.original_returncode != 0 or result.timed_out or result.custody_refused:
            raise ValueError("independent actual scientific source parsing failed")
        independent = semantic_content_contract_from_ast(
            "semantic-browser-control", sources, result.stdout.encode()
        ).to_dict()
        expected = contract.to_dict()
        independent.pop("ast_sha256", None)
        expected.pop("ast_sha256", None)
        if independent != expected:
            raise ValueError("scientific source AST semantics differ on independent reader")
        transformed = work / "baseline.html"
        transformed.write_bytes(pandoc_html.content)
        harden_mathjax_script(transformed)
        if (
            transformed.read_bytes() != baseline.content
            or mutate_html(baseline.content.decode(), name).encode() != original.content
        ):
            raise ValueError("scientific control did not apply exact independently reconstructed source transformation")
    replay_browser_observation(
        root,
        directory / "observation",
        original,
        contract,
        raw["observation"],
        reader,
        run_id=run_id,
        custody=custody,
        runtime=runtime,
    )
