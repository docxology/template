"""Separate, source-owned config custody for genuine HTML metadata observation."""

from __future__ import annotations

import copy
import hashlib
import math
import time
from pathlib import Path
from typing import Any

import yaml

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_html_metadata import bind_html_metadata_ast, compile_html_config_metadata
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader, json_object_from_bytes
from infrastructure.validation.output.render_formats import render_config_manuscript_dir
from infrastructure.validation.publication.rendered_provenance import (
    RECEIPT_RELATIVE_PATH,
    build_rendered_provenance_receipt,
    validate_rendered_provenance,
)

METADATA_OBSERVATION_SCHEMA = "template-native-html-source-metadata-observation-v1"
HTML_WITNESS_SCHEMA = "template-native-html-complete-source-observation-v2"
METADATA_PURPOSE = "semantic-config-metadata-pandoc"


def binding(snapshot: ArtifactSnapshot) -> dict[str, str]:
    """Bind one admitted artifact without re-reading its content."""
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def require_unambiguous_yaml(content: bytes) -> None:
    """Reject duplicate YAML keys and cyclic aliases before renderer coercion."""
    if len(content) > 1024 * 1024:
        raise ValueError("HTML config exceeds the unchanged finite metadata source budget")
    document = yaml.compose(content.decode("utf-8", errors="strict"))
    count = 0

    def visit(node: yaml.Node, ancestors: frozenset[int], depth: int) -> None:
        nonlocal count
        count += 1
        if count > 100000 or depth > 64 or id(node) in ancestors:
            raise ValueError("HTML config alias/nesting occurrences need specific supported source custody")
        ancestors = ancestors | {id(node)}
        if isinstance(node, yaml.MappingNode):
            keys: set[tuple[str, str]] = set()
            for key, value in node.value:
                if not isinstance(key, yaml.ScalarNode) or key.tag != "tag:yaml.org,2002:str":
                    raise ValueError("HTML config has unsupported non-string or merged YAML keys")
                identity = (key.tag, key.value)
                if identity in keys:
                    raise ValueError("HTML config repeats a source key; no occurrence may be silently dropped")
                keys.add(identity)
                visit(value, ancestors, depth + 1)
        elif isinstance(node, yaml.SequenceNode):
            for value in node.value:
                visit(value, ancestors, depth + 1)

    if document is not None:
        visit(document, frozenset(), 0)


def html_metadata_plan(
    root: Path, scope: str, artifact: NativeArtifact, reader: SnapshotReader
) -> tuple[ArtifactSnapshot, dict[str, Any], dict[str, Any]] | None:
    """Bind original and selected config, plus the actual current hydration bridge.

    YAML is deliberately absent from the body source plan and its occurrence
    compiler. Section renders receive no config CLI metadata in WebRenderer.
    """
    if artifact.format != "html":
        raise ValueError("HTML config metadata cannot belong to another format")
    if artifact.id != "manuscript:html":
        return None
    from infrastructure.rendering.web_renderer import WebRenderer

    project = root / "projects" / scope
    original = reader.read((project / "manuscript/config.yaml").relative_to(root).as_posix())
    require_unambiguous_yaml(original.content)
    selected = render_config_manuscript_dir(project)
    config = reader.read((selected / "config.yaml").relative_to(root).as_posix())
    require_unambiguous_yaml(config.content)
    receipt = reader.read((project / RECEIPT_RELATIVE_PATH).relative_to(root).as_posix())
    current: Any = build_rendered_provenance_receipt(root, scope).to_dict()
    if receipt.json_object() != current or not validate_rendered_provenance(root, scope).valid:
        raise ValueError("HTML config metadata requires the exact current validated hydration receipt")
    evidence: list[dict[str, str]] = []
    for row in current["evidence_files"].values():
        snapshot = reader.read((project / row["path"]).relative_to(root).as_posix())
        if snapshot.sha256 != row["sha256"] or len(snapshot.content) != row["size_bytes"]:
            raise ValueError("HTML metadata hydration evidence changed")
        evidence.append(binding(snapshot))
    consumption: list[dict[str, Any]] = []
    for row in current["consumed_manuscript"]:
        rendered = reader.read((project / row["rendered_path"]).relative_to(root).as_posix())
        if rendered.sha256 != row["rendered_sha256"]:
            raise ValueError("HTML metadata consumed manuscript drifted")
        source = None
        if row["source_path"] is not None:
            snapshot = reader.read((project / row["source_path"]).relative_to(root).as_posix())
            if snapshot.sha256 != row["source_sha256"]:
                raise ValueError("HTML metadata pre-hydration source drifted")
            source = binding(snapshot)
        consumption.append({"rendered": binding(rendered), "source": source})
    metadata = compile_html_config_metadata(config.relative, config.content)
    if metadata["pandoc_args"] != WebRenderer._pandoc_metadata_args(selected):
        raise ValueError("HTML metadata compiler differs from the current renderer's consumed argv")
    custody = {
        "source_config": binding(original),
        "consumed_config": binding(config),
        "selected_manuscript": selected.relative_to(root).as_posix(),
        "receipt": binding(receipt),
        "hydration": current,
        "evidence": evidence,
        "consumption": consumption,
        "metadata_arguments": list(metadata["pandoc_args"]),
    }
    if not reader.unchanged():
        raise ValueError("HTML config/hydration changed during source reconstruction")
    return config, metadata, custody


def portable_metadata_document(ast_bytes: bytes, bibliography_paths: tuple[tuple[str, bytes], ...]) -> dict[str, Any]:
    """Normalize only authenticated CLI bibliography filenames, preserving the AST.

    The exact unmodified AST and command remain independently bound artifacts.
    Each filename must occur literally inside the bibliography metadata field;
    no basename, substring, arbitrary path, or other metadata is normalized.
    """
    if len(ast_bytes) > 32 * 1024 * 1024:
        raise ValueError("metadata AST exceeds the existing finite source budget")
    document = json_object_from_bytes(ast_bytes)
    if not document.get("pandoc-api-version") or not isinstance(document.get("meta"), dict):
        raise ValueError("HTML config metadata omitted actual native AST metadata")
    if not isinstance(document.get("blocks"), list):
        raise ValueError("HTML config metadata omitted native body occurrences")
    document = copy.deepcopy(document)
    for filename, content in bibliography_paths:
        found = 0

        def normalize(value: Any) -> Any:
            nonlocal found
            if isinstance(value, str) and value == filename:
                found += 1
                return "source-sha256:" + hashlib.sha256(content).hexdigest()
            if isinstance(value, list):
                return [normalize(child) for child in value]
            if isinstance(value, dict):
                return {key: normalize(child) for key, child in value.items()}
            return value

        document["meta"]["bibliography"] = normalize(document["meta"].get("bibliography"))
        if found != 1:
            raise ValueError("CLI bibliography metadata requires one exact native filename occurrence")
    return document


def metadata_contract(
    source: dict[str, Any], ast: bytes, body_ast: bytes, bibliography_paths: tuple[tuple[str, bytes], ...]
) -> dict[str, Any]:
    """Preserve every native metadata node and retain unsupported placement forms."""
    bound = bind_html_metadata_ast(source, ast)
    document = portable_metadata_document(ast, bibliography_paths)
    body = json_object_from_bytes(body_ast)
    blockers = list(bound["blockers"])
    if document["blocks"] != body.get("blocks"):
        blockers.append(
            "config metadata changes native body semantics: complete combined source integration unsupported"
        )
    records: list[dict[str, Any]] = []
    configured = {row["key"] for row in source["records"]}
    writer_keys = {"bibliography", "references", "link-citations", "linkReferences"}
    for key in document["meta"]:
        if key not in configured | writer_keys:
            blockers.append(f"native metadata {key}: source-specific page placement unsupported")

    def census(value: Any, path: str, depth: int = 0) -> None:
        if depth > 64 or len(records) > 100000:
            raise ValueError("metadata source occurrences exceed the unchanged finite budget")
        if isinstance(value, dict):
            if "t" in value:
                records.append({"source_id": "metadata-ast:" + path, "tag": value["t"], "payload": value})
                if value["t"] in {"Emph", "Strong", "Underline", "SmallCaps", "Span"}:
                    blockers.append(f"metadata-ast:{path}: decorated metadata requires native style/geometry proof")
            for key, child in value.items():
                if key != "t":
                    census(child, path + "/" + key, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                census(child, path + "/" + str(index), depth + 1)

    census(document["meta"], "meta")
    result = {
        **bound,
        "blockers": blockers,
        "native_metadata_occurrences": records,
        "portable_native_ast_sha256": canonical_digest(document),
    }
    result.pop("digest")
    return {**result, "digest": canonical_digest(result)}


def remaining_seconds(deadline: float) -> float:
    """Keep every parse inside its original enclosing deadline and source cap."""
    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ValueError("HTML metadata requires the original finite deadline")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("HTML metadata replay exhausted the original source deadline")
    return min(60.0, remaining)
