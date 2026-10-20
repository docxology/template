"""Pure Source command construction shared by actual combined writers/readers.

Paths are already selected roles. These functions do not select tools, open
files, create owners or authorize a native command from retained JSON.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

RENDERER_CROSSREF_SCHEMA = "template-source-native-renderer-crossref-parser-v1"


def pre_crossref_json_command(command: list[str], writer: str) -> list[str]:
    """Select the complete parser/Lua/metadata prefix of our fixed writers.

    JSON changes Pandoc's writer FORMAT. Actual complete AST comparison with
    every real Crossref stdin remains mandatory; this factory proves no parity.
    Bibliography and metadata options apply before filters even when their argv
    operands follow Crossref, so only the ordered post-Crossref citeproc is cut.
    """
    filters = [index for index, value in enumerate(command) if value == "--filter"]
    if writer not in {"latex", "html"} or len(filters) != 1 or command.count("-o") != 1:
        raise ValueError("pre-Crossref parser needs one exact combined writer/filter/output")
    selected_filter, output = filters[0], command.index("-o")
    if selected_filter + 1 >= len(command) or output + 1 >= len(command):
        raise ValueError("pre-Crossref parser lacks a complete selected operand")
    lua = [index for index, value in enumerate(command) if value == "--lua-filter"]
    citeproc = [index for index, value in enumerate(command) if value == "--citeproc"]
    if any(index >= selected_filter for index in lua) or (
        citeproc and (writer != "html" or len(citeproc) != 1 or citeproc[0] <= selected_filter)
    ):
        raise ValueError("pre-Crossref parser changed the actual ordered Source filters")
    removed = {output, output + 1, selected_filter, selected_filter + 1, *citeproc}
    result = [value for index, value in enumerate(command) if index not in removed]
    if writer == "latex":
        if result.count("--to=latex") != 1:
            raise ValueError("pre-Crossref PDF parser changed its exact selected writer")
        result[result.index("--to=latex")] = "--to=json"
    else:
        if result.count("-t") != 1 or result[result.index("-t") + 1] != "html5":
            raise ValueError("pre-Crossref HTML parser changed its exact selected writer")
        result[result.index("-t") + 1] = "json"
    return result


def pdf_combined_command(
    pandoc: str,
    combined: Path,
    output: Path,
    manuscript: Path,
    figures: Path,
    configuration: dict[str, Any] | None,
    formalism: list[str],
    crossref: str | None,
) -> list[str]:
    command = [
        pandoc,
        str(combined),
        "-o",
        str(output),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=latex",
        "--standalone",
        "--number-sections",
        "--natbib",
        "--metadata=linkReferences:true",
        "--resource-path=" + str(manuscript),
        "--resource-path=" + str(figures),
    ]
    if configuration:
        metadata = configuration.get("metadata", {})
        paper = configuration.get("paper", {})
        authors = configuration.get("authors", [])
        if isinstance(paper, dict) and paper.get("title"):
            command.append(f"--metadata=title:{paper['title']}")
        names = [str(author["name"]) for author in authors if isinstance(author, dict) and author.get("name")]
        if names:
            command.append(f"--metadata=author:{'; '.join(names)}")
        if isinstance(metadata, dict) and metadata.get("language"):
            command.append(f"--metadata=lang:{metadata['language']}")
        for key in ("geometry", "documentclass", "fontsize"):
            value = metadata.get(key)
            if value:
                command.extend(["-V", f"{key}:{value}"])
    command.extend(formalism)
    command.extend(
        [
            "--metadata=template-latex-table-headers:true",
            "--lua-filter",
            str(Path(__file__).with_name("_table_header_breaks.lua")),
        ]
    )
    if crossref:
        command.extend(["--filter", crossref])
    return command


def html_metadata_arguments(configuration: object) -> list[str]:
    if not isinstance(configuration, dict):
        return []
    paper = configuration.get("paper") or {}
    if not isinstance(paper, dict):
        return []
    arguments = ["--metadata=linkReferences:true"]
    title, subtitle = paper.get("title"), paper.get("subtitle")
    description = paper.get("description") or subtitle
    if title:
        arguments.extend([f"--metadata=title:{title}", f"--metadata=pagetitle:{title}"])
    if subtitle:
        arguments.append(f"--metadata=subtitle:{subtitle}")
    if description:
        arguments.append(f"--metadata=description:{description}")
    for entry in configuration.get("authors") or []:
        if isinstance(entry, dict) and entry.get("name"):
            arguments.append(f"--metadata=author:{entry['name']}")
        elif isinstance(entry, str) and entry:
            arguments.append(f"--metadata=author:{entry}")
    metadata = configuration.get("metadata")
    language = str(metadata.get("language") or "en") if isinstance(metadata, dict) else "en"
    if language:
        arguments.append(f"--metadata=lang:{language}")
    return arguments


def html_combined_command(
    pandoc: str,
    combined: Path,
    output: Path,
    mathjax: str,
    metadata: list[str],
    resource_paths: list[Path],
    lua_filters: list[Path],
    crossref: str | None,
    bibliographies: list[Path],
) -> list[str]:
    command = [
        pandoc,
        str(combined),
        "-t",
        "html5",
        "-o",
        str(output),
        "--standalone",
        f"--mathjax={mathjax}",
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        *metadata,
    ]
    for path in resource_paths:
        command.extend(["--resource-path", str(path)])
    for path in lua_filters:
        command.extend(["--lua-filter", str(path)])
    if crossref:
        command.extend(["--filter", crossref])
    if bibliographies:
        command.append("--citeproc")
        command.extend(f"--bibliography={path}" for path in bibliographies)
        command.append("--metadata=link-citations:true")
    return command
