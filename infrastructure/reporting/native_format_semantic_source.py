"""Actual bounded source parsing for independent HTML semantic obligations."""

from __future__ import annotations

import time
import hashlib
import shutil
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_content_contracts import (
    SemanticContentContract,
    semantic_content_contract_from_ast,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.validation.output.render_formats import render_config_manuscript_dir
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance
from infrastructure.rendering._combined_exports import combined_source_files
from infrastructure.rendering._paper_frontmatter import admit_paper_layout
from infrastructure.rendering._web_source_context import compose_web_source_context, project_source_context_ast


def semantic_source_plan(
    root: Path, scope: str, artifact: NativeArtifact, reader: SnapshotReader
) -> tuple[bytes, tuple[tuple[str, bytes], ...], tuple[tuple[str, bytes], ...]]:
    """Rebuild exact source transforms and ordering from current consumed bytes."""
    from infrastructure.rendering._web_markdown_preprocess import html_safe_markdown
    from infrastructure.rendering._bibliography import resolve_bibliography

    if artifact.format != "html" or not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("HTML semantics requires actual current consumed hydration")
    reader.read(f"projects/{scope}/manuscript/config.yaml")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    config = manuscript / "config.yaml"
    if config.is_file():
        reader.read(config.relative_to(root).as_posix())
    layout = admit_paper_layout(manuscript, tuple(combined_source_files(discover_manuscript_files(manuscript))))
    paths = list(layout.complete)
    if not paths:
        raise ValueError("source-owned HTML artifact has no consumed source")
    sources = tuple(
        (item.relative, item.content) for item in (reader.read(path.relative_to(root).as_posix()) for path in paths)
    )
    content = html_safe_markdown(
        compose_web_source_context(tuple(data for _, data in sources), len(layout.frontmatter)),
        render_citations=False,
    )
    bibliographies = tuple(
        (item.relative, item.content)
        for item in (reader.read(path.relative_to(root).as_posix()) for path in resolve_bibliography(manuscript))
    )
    if not reader.unchanged():
        raise ValueError("consumed semantic sources changed during reconstruction")
    return content.encode(), sources, bibliographies


def semantic_source_index(
    root: Path, scope: str, artifact: NativeArtifact, sources: tuple[tuple[str, bytes], ...]
) -> int | None:
    """Bind a split artifact to one exact source in the complete context."""
    if not (artifact.id.startswith("section:") and artifact.id.endswith(":html")):
        return None
    name = artifact.id.removeprefix("section:").removesuffix(":html")
    expected = (render_config_manuscript_dir(root / "projects" / scope) / name).relative_to(root).as_posix()
    matches = [index for index, (path, _) in enumerate(sources) if path == expected]
    if len(matches) != 1:
        raise ValueError("section identity requires one exact source-relative manuscript")
    return matches[0]


def semantic_owned_sources(
    root: Path, scope: str, artifact: NativeArtifact, sources: tuple[tuple[str, bytes], ...]
) -> tuple[tuple[str, bytes], ...]:
    """Select original survival obligations, retaining full context elsewhere."""
    index = semantic_source_index(root, scope, artifact, sources)
    return sources if index is None else (sources[index],)


def semantic_contract_ast(
    root: Path, scope: str, artifact: NativeArtifact, sources: tuple[tuple[str, bytes], ...], ast: bytes
) -> bytes:
    """Project only owned blocks from the independently parsed complete AST."""
    return project_source_context_ast(
        ast, tuple(data for _, data in sources), semantic_source_index(root, scope, artifact, sources)
    )


def semantic_parser_options(root: Path, scope: str) -> list[str]:
    """Use the canonical HTML reader's section and configured metadata context."""
    from infrastructure.rendering.web_renderer import WebRenderer

    return [
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=json",
        "--number-sections",
        *WebRenderer._pandoc_metadata_args(render_config_manuscript_dir(root / "projects" / scope)),
    ]


def semantic_lua_filters() -> tuple[Path, ...]:
    """Select the same ordered Source filters as the canonical HTML writer."""
    from infrastructure.rendering._pandoc_filters import formalism_filter_args

    rendering = Path(__file__).absolute().parents[1] / "rendering"
    images = rendering / "convert_latex_images.lua"
    return (*((images,) if images.is_file() else ()), *(Path(path) for path in formalism_filter_args()[1::2]))


def observe_html_source(
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
    """Run real Pandoc on frozen rebuilt source and preserve all parse receipts."""
    if deadline <= time.monotonic():
        raise TimeoutError("semantic source admission expired")
    content, sources, bibliographies = semantic_source_plan(root, scope, artifact, reader)
    source = directory / "semantic-source.md"
    atomic_write_bytes_confined(root, source, content, mode=0o600)
    args = [str(source), *semantic_parser_options(root, scope)]
    copied = []
    sdk_root = Path(__file__).absolute().parents[2]
    sdk_reader = SnapshotReader(sdk_root)

    for index, original in enumerate(semantic_lua_filters()):
        snapshot = sdk_reader.read(Path(original).relative_to(sdk_root).as_posix())
        target = directory / f"semantic-filter-{index}.lua"
        atomic_write_bytes_confined(root, target, snapshot.content, mode=0o600)
        args.extend(["--lua-filter", str(target)])
        copied.append(
            {
                "source": {"path": snapshot.relative, "sha256": snapshot.sha256},
                "consumed": {"path": target.relative_to(root).as_posix(), "sha256": snapshot.sha256},
            }
        )
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
    if crossref:
        args.extend(["--filter", crossref])
    for index, (_, data) in enumerate(bibliographies):
        target = directory / f"semantic-bibliography-{index}.bib"
        atomic_write_bytes_confined(root, target, data, mode=0o600)
        args.append(f"--bibliography={target}")
    if bibliographies:
        args.extend(["--citeproc", "--metadata=link-citations:true"])
    crossref_filter = None
    if "--filter" in args:
        from infrastructure.reporting.native_crossref_pandoc import source_crossref_pandoc
        from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime

        runtime = CitationRuntime(
            root, directory / "semantic-crossref-owner", env=env, deadline=deadline, run_id=run_id
        )
        held_paths = [source, *(root / row["consumed"]["path"] for row in copied)]
        held_paths.extend(directory / f"semantic-bibliography-{index}.bib" for index, _ in enumerate(bibliographies))
        observed, crossref_filter = source_crossref_pandoc(
            runtime, scope, args, "semantic-pandoc", output_format="json", input_paths=tuple(held_paths)
        )
        tool = {
            "artifact": runtime.tools[-1],
            "exit_code": observed["exit_code"],
            "original_exit_code": observed["original_exit_code"],
        }
    else:
        tool = native_tool_record(
            root, directory, "pandoc", args, env=env, deadline=deadline, run_id=run_id, purpose="semantic-pandoc"
        )
    if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
        raise ValueError("actual source Pandoc parse failed")
    snapshot_reader = SnapshotReader(root)
    raw = snapshot_reader.read(tool["artifact"]["path"]).json_object()
    ast = raw["stdout"].encode()
    ast_path = directory / "semantic-ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    ast_snapshot = snapshot_reader.read(ast_path.relative_to(root).as_posix())
    consumed = snapshot_reader.read(source.relative_to(root).as_posix())
    contract = semantic_content_contract_from_ast(
        artifact.id, (*sources, *bibliographies), semantic_contract_ast(root, scope, artifact, sources, ast)
    )
    from infrastructure.reporting.native_format_semantic_original import observe_original_source

    contract, original_source = observe_original_source(
        root,
        directory,
        (*semantic_owned_sources(root, scope, artifact, sources), *bibliographies),
        contract,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    if artifact.id != "manuscript:html" and not (artifact.id.startswith("section:") and artifact.id.endswith(":html")):
        from dataclasses import replace

        contract = replace(
            contract,
            blockers=(*contract.blockers, f"{artifact.id}: domain projection is not a literal full manuscript"),
        )
    if not reader.unchanged() or not snapshot_reader.unchanged() or not sdk_reader.unchanged():
        raise ValueError("semantic consumed custody changed")
    return contract, {
        "schema_version": "template-native-semantic-source-observation-v3",
        "source": {"path": consumed.relative, "sha256": consumed.sha256},
        "ast": {"path": ast_snapshot.relative, "sha256": ast_snapshot.sha256},
        "tool": tool,
        "filters": copied,
        "bibliographies": [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in bibliographies],
        "contract": contract.to_dict(),
        "original_source": original_source,
        "crossref_filter": crossref_filter,
    }
