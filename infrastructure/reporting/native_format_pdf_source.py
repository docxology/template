"""Source-only PDF manuscript reconstruction and real pre-citeproc AST custody."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import (
    SemanticContentContract,
    semantic_content_contract_from_ast,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


@dataclass(frozen=True)
class PDFSourceInputs:
    content: bytes
    sources: tuple[tuple[str, bytes], ...]
    config: tuple[str, bytes]
    preamble: tuple[str, bytes] | None
    bibliographies: tuple[tuple[str, bytes], ...]
    blockers: tuple[str, ...]
    auxiliary: tuple[tuple[str, bytes], ...] = ()


def pdf_source_inputs(
    root: Path, directory: Path, scope: str, artifact: NativeArtifact, reader: SnapshotReader
) -> PDFSourceInputs:
    """Freeze the selected original source tree before executing transforms."""
    from infrastructure.rendering._bibliography import resolve_bibliography
    from infrastructure.rendering._pdf_combined_markdown import preprocess_combined_markdown
    from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections
    from infrastructure.rendering._pdf_title_page_config import _rendering_options
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.validation.output.render_formats import render_config_manuscript_dir
    from infrastructure.validation.publication.rendered_provenance import validate_rendered_provenance

    if artifact.format != "pdf" or artifact.id != "manuscript:pdf":
        raise ValueError("scientific manuscript source plan requires manuscript:pdf")
    if not validate_rendered_provenance(root, scope).valid:
        raise ValueError("scientific source reconstruction requires current consumed hydration")
    reader.read(f"projects/{scope}/manuscript/config.yaml")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    snapshots = [reader.read(path.relative_to(root).as_posix()) for path in discover_manuscript_files(manuscript)]
    if not snapshots or sum(len(item.content) for item in snapshots) > 4 * 1024 * 1024:
        raise ValueError("scientific source collection is empty or exceeds its budget")
    config = reader.read((manuscript / "config.yaml").relative_to(root).as_posix())
    parsed_config = yaml.safe_load(config.content)
    if not isinstance(parsed_config, dict):
        raise ValueError("scientific source config is not a mapping")
    preamble = (
        reader.read((manuscript / "preamble.md").relative_to(root).as_posix())
        if (manuscript / "preamble.md").is_file()
        else None
    )
    bibliographies = tuple(reader.read(path.relative_to(root).as_posix()) for path in resolve_bibliography(manuscript))
    frozen = directory / "source-project" / "output" / "manuscript"
    paths = []
    for snapshot in (*snapshots, config, *bibliographies, *((preamble,) if preamble else ())):
        target = frozen / Path(snapshot.relative).name
        atomic_write_bytes_confined(root, target, snapshot.content, mode=0o600)
        if snapshot in snapshots:
            paths.append(target)
    auxiliary = []
    variables = manuscript / "manuscript_vars.yaml"
    if variables.is_file():
        snapshot = reader.read(variables.relative_to(root).as_posix())
        atomic_write_bytes_confined(root, frozen / variables.name, snapshot.content, mode=0o600)
        auxiliary.append((snapshot.relative, snapshot.content))
    content = combine_manuscript_markdown_sections(
        paths, section_breaks=_rendering_options(parsed_config)["section_breaks"]
    )
    blockers = []
    if re.search(r"(?m)^\s*```\s*mermaid\b", content):
        # Re-rendering a diagram without retained original tool/runtime custody
        # cannot silently redefine the source-owned figure contract.
        blockers.append("source Mermaid transformation requires independently retained diagram observations")
    else:
        content = preprocess_combined_markdown(content, manuscript_dir=frozen).content
    if not reader.unchanged():
        raise ValueError("scientific source changed during frozen reconstruction")
    return PDFSourceInputs(
        content.encode(),
        tuple((item.relative, item.content) for item in snapshots),
        (config.relative, config.content),
        (preamble.relative, preamble.content) if preamble else None,
        tuple((item.relative, item.content) for item in bibliographies),
        tuple(blockers),
        tuple(auxiliary),
    )


def observe_pdf_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[SemanticContentContract, dict[str, Any]]:
    """Parse frozen reconstructed source without citeproc or producer artifacts."""
    if deadline <= time.monotonic():
        raise TimeoutError("scientific PDF source admission deadline expired")
    inputs = pdf_source_inputs(root, directory, scope, artifact, reader)
    source = directory / "source-only.md"
    atomic_write_bytes_confined(root, source, inputs.content, mode=0o600)
    arguments = [str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"]
    tool = native_tool_record(
        root,
        directory,
        "pandoc",
        arguments,
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="pdf-source-original-ast",
    )
    process = json.loads(reader.read(tool["artifact"]["path"]).content)
    if process["original_exit_code"] != 0 or process["exit_code"] != 0:
        raise ValueError("actual original source parser failed")
    ast = process["stdout"].encode()
    ast_path = directory / "source-only.ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    contract = semantic_content_contract_from_ast(artifact.id, inputs.sources, ast)
    original_inputs = [
        {"role": role, "path": path, "sha256": hashlib.sha256(content).hexdigest()}
        for role, values in (
            ("manuscript", inputs.sources),
            ("config", (inputs.config,)),
            ("preamble", (inputs.preamble,) if inputs.preamble else ()),
            ("bibliography", inputs.bibliographies),
            ("auxiliary", inputs.auxiliary),
        )
        for path, content in values
    ]
    return contract, {
        "schema_version": "template-native-pdf-source-only-v1",
        "source_inputs": original_inputs,
        "markdown": {"path": source.relative_to(root).as_posix(), "sha256": hashlib.sha256(inputs.content).hexdigest()},
        "ast": {"path": ast_path.relative_to(root).as_posix(), "sha256": hashlib.sha256(ast).hexdigest()},
        "parser_artifact": tool["artifact"],
        "citation_engine": "natbib/plainnat (original AST has no citeproc)",
        "blockers": list(inputs.blockers),
        "contract": contract.to_dict(),
    }
