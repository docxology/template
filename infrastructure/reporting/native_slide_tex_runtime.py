"""Actual source-only TeX discovery and fresh admitted slide compilation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_pdf_citation_runtime import (
    CitationRuntime,
    _backend_dependencies,
    file_observation,
    tex_dependencies,
)


def prepare_source_beamer_writer(
    runtime: CitationRuntime,
    plan: Any,
    config: Any,
    document: bytes,
    level: int,
    numbers: dict[str, str] | None,
) -> dict[str, Any]:
    """Use only the selected SDK writer and declared source DATA consumers."""
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.rendering._slides_beamer import beamer_command, transform_beamer_latex
    from infrastructure.rendering._slides_tex_figures import fix_slides_figure_paths
    from infrastructure.reporting.native_slide_tex_source import resolve_source_slide_references

    ast = runtime.freeze("source.json", document)
    tex = runtime.directory / "oracle.tex"
    command = beamer_command(
        config,
        ast,
        tex,
        plan.manuscript_directory,
        plan.figures_directory,
        slide_level=level,
        accessible_resource_roots=(plan.manuscript_directory, plan.figures_directory),
    )
    command = [part for part in command if part != "--citeproc"]
    if plan.profile == "archive":
        command.extend(["--from", "json"])
    dependencies = tuple(
        Path(command[i + 1]) for i, value in enumerate(command[:-1]) if value in {"--filter", "--lua-filter", "-H"}
    )
    before = [file_observation(path) for path in dependencies]
    runtime.tool("pandoc", command[1:], "source-beamer-writer", input_paths=(ast,))
    after = [file_observation(path) for path in dependencies]
    if before != after:
        raise ValueError("source-owned Beamer writer/filter/header dependencies changed during original execution")
    writer = runtime.freeze("original-source-writer.tex", runtime.read(tex))
    content = fix_slides_figure_paths(runtime.read(writer).decode(), runtime.directory, plan.figures_directory)
    content = resolve_source_slide_references(content, config, numbers)

    def seqsplit() -> None:
        if not runtime.tool("kpsewhich", ["seqsplit.sty"], "source-seqsplit")["stdout"].strip():
            raise ValueError("accessible slide source requires actual seqsplit capability")

    content = transform_beamer_latex(content, config, require_seqsplit=seqsplit)
    if "^^" in content or re.search(r"\\(?:write18|openin|openout|catcode)\b", content):
        raise ValueError("source Beamer reference contains unadmitted expansion or lexical translation")
    atomic_write_bytes_confined(runtime.root, tex, content.encode(), mode=0o600)
    runtime.unchanged()
    return {"ast": ast, "tex": tex, "writer_tex": writer, "dependencies_before": before, "dependencies_after": after}


def compile_source_slide_tex(runtime: CitationRuntime, tex: Path) -> dict[str, Any]:
    """Discover actual styles/fonts, then freshly compile under unchanged hashes.

    The discovery pass never grants reference acceptance. Only the later fresh
    actual compilation has all discovered external inputs held before/after.
    Native binaries/fonts stay installed; all processes use the original clock.
    """

    def chain(phase: str) -> str:
        for number in range(1, 3):
            runtime.tool(
                "xelatex",
                [
                    "-fmt=xelatex",
                    "-progname=xelatex",
                    "-no-pdf",
                    "-recorder",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-no-shell-escape",
                    "oracle.tex",
                ],
                f"source-{phase}-xelatex-{number}",
                input_paths=(tex,),
            )
        backend = runtime.tool(
            "xdvipdfmx",
            [
                "--kpathsea-debug=4",
                "-vv",
                "-o",
                "oracle.pdf",
                "oracle.xdv",
            ],
            f"source-{phase}-native-backend",
            input_paths=(runtime.directory / "oracle.xdv",),
        )
        return str(backend["stdout"]) + "\n" + str(backend["stderr"])

    def inputs(transcript: str) -> list[dict[str, Any]]:
        rows = {
            row["path"]: row
            for row in (
                *tex_dependencies(runtime, runtime.directory / "oracle.fls"),
                *_backend_dependencies(runtime, transcript, "source"),
            )
        }
        return [rows[key] for key in sorted(rows) if not Path(key).is_relative_to(runtime.directory)]

    discovery = inputs(chain("discovery"))
    before = [file_observation(Path(row["path"])) for row in discovery]
    if before != discovery:
        raise ValueError("source-only slide discovery inputs changed before fresh native admission")
    admitted = inputs(chain("admitted"))
    after = [file_observation(Path(row["path"])) for row in discovery]
    if admitted != before or after != before:
        raise ValueError("source-only slide dependencies changed during original fresh native compilation")
    runtime.unchanged()
    return {"discovery": discovery, "before": before, "after": after}
