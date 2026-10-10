"""Retained pre-transform source semantics and independent survival obligations."""

from __future__ import annotations

import copy
import json
import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_content_contracts import (
    SemanticContentContract,
    semantic_content_contract_from_ast,
    text_tokens,
)


def original_source_bytes(sources: tuple[tuple[str, bytes], ...]) -> bytes:
    """Assemble frozen original manuscripts before any HTML transformation."""
    parts = []
    manuscripts = [(name, data) for name, data in sources if not name.endswith(".bib")]
    for index, (_, data) in enumerate(manuscripts):
        parts.append(data.decode("utf-8").rstrip() + "\n")
        if index < len(manuscripts) - 1:
            parts.append("\n---\n\n")
    return "\n\n".join(parts).lstrip("\n\r").removeprefix("\ufeff").encode()


def inspect_original_source(
    artifact_id: str,
    sources: tuple[tuple[str, bytes], ...],
    original_ast: bytes,
    projected: SemanticContentContract,
) -> dict[str, Any]:
    """Keep all original occurrences; check recognized semantic survival.

    Bibliographic display syntax has a separate identity obligation. It is
    omitted only from this comparison text view; the unmodified original AST
    ledger and citation records are retained and independently reconstructed.
    Raw and unknown source nodes always retain their unsupported obligations.
    """
    original = semantic_content_contract_from_ast(artifact_id, sources, original_ast)
    document = copy.deepcopy(json.loads(original_ast))

    def separate_citation_display(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("t") == "Cite":
                value["c"][1] = []
            for child in value.values():
                separate_citation_display(child)
        elif isinstance(value, list):
            for child in value:
                separate_citation_display(child)

    separate_citation_display(document)
    comparison = semantic_content_contract_from_ast(artifact_id, sources, json.dumps(document).encode())
    findings = []
    projected_blocks = [
        *[list(block.tokens) for block in projected.blocks],
        *[block["tokens"] for note in projected.footnote_sources for block in note["blocks"]],
    ]
    projected_tokens = [token for block in projected_blocks for token in block]
    cursor = 0
    original_blocks = [
        *[list(block.tokens) for block in comparison.blocks],
        *[block["tokens"] for note in comparison.footnote_sources for block in note["blocks"]],
    ]
    for index, tokens in enumerate(original_blocks):
        position = next(
            (
                i
                for i in range(cursor, len(projected_tokens) - len(tokens) + 1)
                if projected_tokens[i : i + len(tokens)] == tokens
            ),
            None,
        )
        if position is None:
            findings.append({"code": "html.original.content", "block_index": index})
        else:
            cursor = position + len(tokens)
    projected_math = [tex for _, tex in projected.mathematical_sources]
    cursor = 0
    for source_id, tex in original.mathematical_sources:
        position = next((i for i in range(cursor, len(projected_math)) if projected_math[i] == tex), None)
        if position is None:
            findings.append({"code": "html.original.math", "source_id": source_id})
        else:
            cursor = position + 1
    projected_images = [target for _, target, _ in projected.image_sources]
    cursor = 0
    for source_id, target, _ in original.image_sources:
        # These three explicit source-path rewrites preserve the complete tail;
        # matching by basename or arbitrary path equivalence is never admitted.
        mapped = (
            target.replace("../../output/figures/", "../figures/")
            .replace("../output/figures/", "../figures/")
            .replace("output/figures/", "../figures/")
        )
        position = next((i for i in range(cursor, len(projected_images)) if projected_images[i] == mapped), None)
        if position is None:
            findings.append({"code": "html.original.figure", "source_id": source_id})
        else:
            cursor = position + 1
    projected_citations = [keys for _, keys in projected.citation_sources]
    citation_cursor = 0
    text_cursor = 0
    for source_id, keys in original.citation_sources:
        position = next(
            (i for i in range(citation_cursor, len(projected_citations)) if projected_citations[i] == keys), None
        )
        if position is not None:
            citation_cursor = position + 1
            continue
        visible = list(text_tokens("[" + "; ".join(keys) + "]"))
        position = next(
            (
                i
                for i in range(text_cursor, len(projected_tokens) - len(visible) + 1)
                if projected_tokens[i : i + len(visible)] == visible
            ),
            None,
        )
        if position is None:
            findings.append({"code": "html.original.citation", "source_id": source_id})
        else:
            text_cursor = position + len(visible)
    if len(original.table_sources) != len(projected.table_sources):
        findings.append({"code": "html.original.table"})
    if len(original.footnote_sources) != len(projected.footnote_sources):
        findings.append({"code": "html.original.footnote"})
    link_cursor = 0
    projected_links = [target for _, target in projected.link_sources]
    for source_id, target in original.link_sources:
        position = next((i for i in range(link_cursor, len(projected_links)) if projected_links[i] == target), None)
        if position is None:
            findings.append({"code": "html.original.link", "source_id": source_id})
        else:
            link_cursor = position + 1
    blockers = [f"original-source: {blocker}" for blocker in original.blockers]
    return {
        "schema_version": "template-html-original-source-survival-v1",
        "contract": original.to_dict(),
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def _bind_original(projected: SemanticContentContract, ast: bytes, survival: dict[str, Any]) -> SemanticContentContract:
    if survival["findings"]:
        raise ValueError(
            "source transformation lost original scientific obligations: " + json.dumps(survival["findings"])
        )
    return replace(
        projected,
        blockers=(*projected.blockers, *survival["blockers"]),
        original_ast_sha256=hashlib.sha256(ast).hexdigest(),
        original_source_occurrences=tuple(survival["contract"]["source_occurrences"]),
    )


def observe_original_source(
    root: Path,
    directory: Path,
    sources: tuple[tuple[str, bytes], ...],
    projected: SemanticContentContract,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[SemanticContentContract, dict[str, Any]]:
    """Obtain an actual unfiltered pre-transform AST under the original deadline."""
    from infrastructure.core.files.secure_write import atomic_write_bytes_confined
    from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
    from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

    source = directory / "semantic-original-source.md"
    atomic_write_bytes_confined(root, source, original_source_bytes(sources), mode=0o600)
    args = [str(source), "--from=markdown+tex_math_dollars+raw_tex+header_attributes", "--to=json"]
    tool = native_tool_record(
        root, directory, "pandoc", args, env=env, deadline=deadline, run_id=run_id, purpose="semantic-original-pandoc"
    )
    if tool["exit_code"] != 0 or tool["original_exit_code"] != 0:
        raise ValueError("actual original source Pandoc parse failed")
    reader = SnapshotReader(root)
    ast = reader.read(tool["artifact"]["path"]).json_object()["stdout"].encode()
    ast_path = directory / "semantic-original-ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    ast_snapshot = reader.read(ast_path.relative_to(root).as_posix())
    source_snapshot = reader.read(source.relative_to(root).as_posix())
    survival = inspect_original_source(projected.artifact_id, sources, ast, projected)
    bound = _bind_original(projected, ast, survival)
    if not reader.unchanged():
        raise ValueError("original source parse custody changed")
    return bound, {
        "schema_version": "template-html-original-source-observation-v1",
        "source": {"path": source_snapshot.relative, "sha256": source_snapshot.sha256},
        "ast": {"path": ast_snapshot.relative, "sha256": ast_snapshot.sha256},
        "tool": tool,
        "survival": survival,
    }


def replay_original_source(
    root: Path,
    directory: Path,
    sources: tuple[tuple[str, bytes], ...],
    projected: SemanticContentContract,
    raw: dict[str, Any],
    reader: Any,
    *,
    run_id: str,
    custody: dict[str, str],
    env: dict[str, str],
    deadline: float,
) -> SemanticContentContract:
    """Independently reparse original sources and all unsupported occurrences."""
    from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
    from infrastructure.reporting.native_format_acceptance_validation import _file, _tool
    from infrastructure.reporting.native_format_portable_custody import producer_path

    if raw.get("schema_version") != "template-html-original-source-observation-v1":
        raise ValueError("original source occurrence custody is required")
    source, ast = _file(raw["source"], reader), _file(raw["ast"], reader)
    content = original_source_bytes(sources)
    if (
        source.path != directory / "semantic-original-source.md"
        or source.content != content
        or ast.path != directory / "semantic-original-ast.json"
    ):
        raise ValueError("original source/AST belongs to another source projection")
    args = [
        str(producer_path(custody, root, source.path)),
        "--from=markdown+tex_math_dollars+raw_tex+header_attributes",
        "--to=json",
    ]
    transcript = _tool(raw["tool"]["artifact"], reader, run_id, "pandoc", "semantic-original-pandoc", args)
    if transcript.get("stdout", "").encode() != ast.content:
        raise ValueError("original source AST differs from actual original parse stdout")
    survival = inspect_original_source(projected.artifact_id, sources, ast.content, projected)
    if raw.get("survival") != survival:
        raise ValueError("original source occurrence/survival obligations changed")
    with current_pandoc_reader(root, reader, env=env, deadline=deadline, purpose="html-original-ast") as current:
        local_source = current.runtime.freeze("source.md", content)
        process = current.tool("pandoc", [str(local_source), *args[1:]], "current-html-original-ast")
        independent = inspect_original_source(projected.artifact_id, sources, process["stdout"].encode(), projected)
        expected = copy.deepcopy(survival)
        actual = copy.deepcopy(independent)
        expected["contract"].pop("ast_sha256", None)
        actual["contract"].pop("ast_sha256", None)
        if expected != actual:
            raise ValueError("independent original source occurrences or unsupported obligations differ")
    return _bind_original(projected, ast.content, survival)
