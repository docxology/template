"""Actual section compiler ToolAPI under the existing genuine native stage child.

The ordinary renderer keeps its original subprocess path. A native-origin
environment is a refusal guard and never creates a Source owner.
"""

from __future__ import annotations

import os
import secrets
import subprocess
from pathlib import Path

from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
from infrastructure.reporting.native_stage_child import current_native_stage_directory, retain_native_stage_artifact
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.validation.output.render_formats import render_config_manuscript_dir


def run_native_tex_section_pass(
    command: list[str], tex: Path, output: Path, *, environment: dict[str, str]
) -> subprocess.CompletedProcess[str] | None:
    """Run this actual Source-selected compiler pass, retaining real OS and output."""
    owner = current_native_producer_operation()
    if owner is None:
        if any(
            os.environ.get(key)
            for key in (
                "TEMPLATE_PUBLIC_REFERENCE_ROOT",
                "TEMPLATE_PUBLIC_REFERENCE_COMMIT",
                "TEMPLATE_PUBLIC_REFERENCE_FINGERPRINT",
            )
        ):
            raise ValueError("native-origin section rendering lacks its actual Source owner")
        return None
    from infrastructure.rendering.latex_utils import latex_compile_command

    root = owner.source.bindings.current_root
    tex, output = tex.absolute(), output.absolute()
    if not tex.is_relative_to(root) or tex.suffix != ".tex":
        return None
    parts = tex.relative_to(root).parts
    scope = "/".join(parts[1:3])
    if len(parts) < 5 or parts[0] != "projects" or scope not in PUBLIC_PROJECT_NAMES:
        return None
    project = root / "projects" / scope
    consumed = render_config_manuscript_dir(project)
    if not tex.is_relative_to(consumed):
        # Other Source-owned compiler callers have their own native adapters.
        # This hook supplies custody only for the declared section writer.
        return None
    directory = current_native_stage_directory()
    if directory is None:
        raise ValueError("native section compile requires its actual fixed Source-admitted stage child")
    if (
        tex.suffix != ".tex"
        or tex != tex.resolve(strict=True)
        or output != project / "output/pdf"
        or command != latex_compile_command(tex, output, command[0])
        or command[0] not in {"xelatex", "lualatex", "pdflatex"}
    ):
        raise ValueError("native section compiler differs from exact Source section argv/cwd/output")
    reader = SnapshotReader(root, native_producer_operation=owner)
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    source = resolve_source_manuscript_dir(project) / tex.relative_to(consumed)
    authored = reader.read(source.relative_to(root).as_posix())
    if authored.content != owner.source.reference.read(authored.relative):
        raise ValueError("native section compiler authored input differs from held Source")
    selected = reader.read(tex.relative_to(root).as_posix())
    runtime = CitationRuntime(
        root,
        directory / ("section-compile-" + secrets.token_hex(12)),
        env=environment,
        deadline=owner.deadline,
        run_id=owner.run_id,
    )
    actual = runtime.tool(
        command[0],
        command[1:],
        "source-section-compile",
        input_paths=(tex,),
        cwd=tex.parent,
        preserve_nominated_launcher=True,
    )
    pdf = reader.read((output / (tex.stem + ".pdf")).relative_to(root).as_posix())
    frozen = runtime.freeze("section-output.input", pdf.content)
    held = reader.read(frozen.relative_to(root).as_posix())
    from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot

    def binding(item: ArtifactSnapshot) -> dict[str, str]:
        return {"path": item.relative, "sha256": item.sha256}

    packet = write_json(
        root,
        runtime.directory / "renderer.json",
        {
            "schema_version": "template-source-native-renderer-command-v1",
            "run_id": owner.run_id,
            "scope": scope,
            "writer": "latex",
            "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
            "owner_pid": owner.owner_pid,
            "command": actual["command"],
            "cwd": str(tex.parent),
            "source_inputs": [binding(authored)],
            "render_inputs": [binding(selected)],
            "output": binding(held),
            "tool_artifacts": list(runtime.tools),
            "crossref_filter": None,
            "loader_qualification": None,
        },
    )
    retain_native_stage_artifact(reader.read(packet["path"]), tool_artifacts=runtime.tools)
    if not reader.unchanged():
        raise ValueError("native actual section compiler input/output changed before stage retention")
    owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
    remaining(owner.deadline)
    return subprocess.CompletedProcess(command, actual["original_exit_code"], actual["stdout"], actual["stderr"])
