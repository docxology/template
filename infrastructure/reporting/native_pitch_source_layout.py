"""Complete current-source native Pitch package layout, theme and replay."""

from __future__ import annotations

import hashlib
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile
from xml.etree.ElementTree import canonicalize

from defusedxml.ElementTree import iterparse

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_pitch_source import compile_pitch_source_model
from infrastructure.reporting.native_pitch_source_parity import inspect_pitch_package
from infrastructure.reporting.native_projection_contracts import compile_projection_contract
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


LAYOUT_SCHEMA = "template-native-pitch-package-layout-v2"
LAYOUT_CANONICALIZATION = "xml-c14n2-with-comments-and-namespace-bindings-v1"


def pitch_package_layout(content: bytes) -> dict[str, str]:
    """Preserve every native PPTX semantic part, including styles and notes.

    Creation metadata outside the presentation does not affect source layout.
    All presentation XML, relationships and native media bytes remain exact.
    Hardened admission precedes C14N2 of the same immutable member bytes.
    Complete scoped namespace declarations remain bound, including prefixes
    used only in OOXML compatibility metadata. Media bytes stay exact.
    """

    result = {}
    with ZipFile(BytesIO(content)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > 10000:
            raise ValueError("Pitch native package layout has duplicate or excessive parts")
        for name in sorted(names):
            if not name.startswith("ppt/"):
                continue
            data = archive.read(name)
            if name.endswith((".xml", ".rels")):
                namespaces: list[tuple[int, tuple[tuple[str, str], ...]]] = []
                pending: list[tuple[str, str]] = []
                ordinal = 0
                for event, value in iterparse(
                    BytesIO(data),
                    events=("start-ns", "start"),
                    forbid_dtd=True,
                    forbid_entities=True,
                    forbid_external=True,
                ):
                    if event == "start-ns":
                        pending.append(value)
                    else:
                        if pending:
                            namespaces.append((ordinal, tuple(sorted(pending))))
                            pending.clear()
                        ordinal += 1
                result[name] = canonical_digest(
                    {
                        "xml_c14n2": canonicalize(data, with_comments=True),
                        "namespace_bindings": namespaces,
                    }
                )
            else:
                result[name] = hashlib.sha256(data).hexdigest()
    if not result:
        raise ValueError("Pitch native package has no complete presentation layout")
    return result


def observe_pitch_package_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: Any,
    content: bytes,
    reader: SnapshotReader,
    *,
    tracked_paths: tuple[str, ...],
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> dict[str, Any]:
    """Conjoin independent literal/native/QR witnesses with full source layout.

    The fresh SDK native package is only a layout/theme reference. It cannot
    grant acceptance without the source text/fonts/images/QR/link package
    witnesses and the enclosing actual all-page Office/PDF observations.
    """
    import yaml
    from infrastructure.rendering.pptx_deck import render_pptx
    from infrastructure.rendering.slide_deck import DeckTheme
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    if artifact.format != "pptx":
        raise ValueError("Pitch native package source adapter requires exact PPTX identity")
    create_private_native_directory(root, directory)
    model, source_base = compile_pitch_source_model(
        root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    pages = compile_projection_contract(model, source_base_url=source_base, reader=reader)
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    theme = DeckTheme(**config["project_config"]["deck"].get("theme", {}))
    reference = render_pptx(model, directory / "source-model.pptx", theme=theme, source_base_url=source_base)
    snapshot = reader.read(reference.relative_to(root).as_posix())
    observed = inspect_pitch_package(
        content,
        pages,
        deadline=deadline,
        native_context=(root, directory, env, run_id),
        source_model=model,
    )
    actual_layout = pitch_package_layout(content)
    source_layout = pitch_package_layout(snapshot.content)
    layout_findings = [
        {"code": "pitch.package.source.layout", "part": name}
        for name in sorted(actual_layout.keys() | source_layout.keys())
        if actual_layout.get(name) != source_layout.get(name)
    ]
    observed["findings"].extend(layout_findings)
    observed["source_layout"] = {
        "schema_version": LAYOUT_SCHEMA,
        "canonicalization": LAYOUT_CANONICALIZATION,
        "source_artifact": {"path": snapshot.relative, "sha256": snapshot.sha256},
        "source_layout_digest": canonical_digest(source_layout),
        "candidate_layout_digest": canonical_digest(actual_layout),
        "parts": len(source_layout),
        "findings": layout_findings,
        "status": "fail" if layout_findings else "pass",
    }
    observed["status"] = "fail" if observed["findings"] else "blocked" if observed["blockers"] else "pass"
    if time.monotonic() >= deadline or not reader.unchanged():
        raise ValueError("Pitch source/native layout custody changed or original deadline expired")
    return observed


def replay_pitch_source_layout(
    root: Path,
    scope: str,
    artifact: Any,
    candidate: bytes,
    reader: SnapshotReader,
    *,
    tracked_paths: tuple[str, ...],
    deadline: float,
) -> dict[str, Any]:
    """Independently rebuild all source-owned native layout parts from current DATA."""
    import yaml
    from infrastructure.rendering.pptx_deck import render_pptx
    from infrastructure.rendering.slide_deck import DeckTheme

    model, source_base = compile_pitch_source_model(
        root,
        scope,
        artifact,
        reader,
        tracked_paths=tracked_paths,
        deadline=deadline,
    )
    config = yaml.safe_load(reader.read(f"projects/{scope}/manuscript/config.yaml").content)
    theme = DeckTheme(**config["project_config"]["deck"].get("theme", {}))
    with tempfile.TemporaryDirectory(prefix="native-pitch-layout-replay-") as private:
        reference = render_pptx(model, Path(private) / "source.pptx", theme=theme, source_base_url=source_base)
        source_layout = pitch_package_layout(reference.read_bytes())
    candidate_layout = pitch_package_layout(candidate)
    findings = [
        {"code": "pitch.package.source.layout", "part": name}
        for name in sorted(source_layout.keys() | candidate_layout.keys())
        if source_layout.get(name) != candidate_layout.get(name)
    ]
    if time.monotonic() >= deadline or not reader.unchanged():
        raise ValueError("portable Pitch source layout DATA changed or original deadline expired")
    return {
        "schema_version": LAYOUT_SCHEMA,
        "canonicalization": LAYOUT_CANONICALIZATION,
        "source_layout_digest": canonical_digest(source_layout),
        "candidate_layout_digest": canonical_digest(candidate_layout),
        "parts": len(source_layout),
        "findings": findings,
        "status": "fail" if findings else "pass",
    }
