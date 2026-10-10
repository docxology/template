"""Source-owned combined manuscript reconstruction for native DOCX and EPUB.

This planner preserves the combined edition's actual preprocessing and citation
filter order. Its parse is evidence, not proof of mathematical or image layout.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
    office_original_mermaid_sources,
    original_office_mermaid_ast_occurrences,
    project_admitted_office_mermaid_sources,
)


@dataclass(frozen=True)
class OfficeSemanticPlan:
    """Exact ordered source inputs and independently rebuilt combined bytes."""

    content: bytes
    sources: tuple[tuple[str, bytes], ...]
    bibliographies: tuple[tuple[str, bytes], ...]
    config: tuple[str, bytes] | None
    variables: tuple[str, bytes] | None
    blockers: tuple[str, ...]
    original_content: bytes
    mermaid: dict[str, Any] | None


def office_semantic_source_plan(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    deadline: float,
    mermaid_admission: OfficeMermaidAdmission | None = None,
) -> OfficeSemanticPlan:
    """Rebuild shared source without reading the producer's combined derivative."""
    from infrastructure.rendering._combined_exports import combined_source_files
    from infrastructure.rendering._pdf_markdown_combine import (
        combine_manuscript_markdown_sections,
    )
    from infrastructure.rendering._pdf_combined_markdown import (
        preprocess_combined_markdown,
    )
    from infrastructure.rendering._pdf_title_page_config import (
        _resolve_config_yaml,
        _rendering_options,
    )
    from infrastructure.rendering._bibliography import resolve_bibliography
    from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
    from infrastructure.validation.output.render_formats import (
        render_config_manuscript_dir,
    )
    from infrastructure.validation.publication.rendered_provenance import (
        validate_current_rendered_provenance,
    )
    import yaml

    if time.monotonic() >= deadline:
        raise TimeoutError("Office semantic source admission expired")
    if artifact.format not in {"docx", "epub"} or artifact.id != f"manuscript:{artifact.format}":
        raise ValueError("Office semantics requires a literal combined manuscript artifact")
    if not validate_current_rendered_provenance(root, scope).valid:
        raise ValueError("Office semantics requires current consumed hydration")
    reader.read(f"projects/{scope}/manuscript/config.yaml")
    manuscript = render_config_manuscript_dir(root / "projects" / scope)
    paths = combined_source_files(discover_manuscript_files(manuscript))
    if not paths:
        raise ValueError("Office semantic manuscript has no source inputs")
    sources = tuple(
        (item.relative, item.content) for item in (reader.read(path.relative_to(root).as_posix()) for path in paths)
    )
    config_path = _resolve_config_yaml(manuscript)
    config = None
    settings: Any = None
    if config_path is not None:
        item = reader.read(config_path.relative_to(root).as_posix())
        config = (item.relative, item.content)
        settings = yaml.safe_load(item.content)
    variables = None
    vars_path = manuscript / "manuscript_vars.yaml"
    if vars_path.is_file():
        item = reader.read(vars_path.relative_to(root).as_posix())
        variables = (item.relative, item.content)
    content = combine_manuscript_markdown_sections(paths, section_breaks=_rendering_options(settings)["section_breaks"])
    original_content = content.encode()
    original_diagrams = office_original_mermaid_sources(content, scope)
    mermaid = None
    blockers: tuple[str, ...] = ()
    if original_diagrams:
        if mermaid_admission is None:
            blockers = ("combined Mermaid asset production requires independent native source binding",)
        else:
            content, mermaid = project_admitted_office_mermaid_sources(
                root, manuscript, content, scope, reader, mermaid_admission
            )
    elif mermaid_admission is not None:
        raise ValueError("Office source has no Mermaid occurrences for the supplied native reference")
    if not blockers:
        scratch = directory / "preprocess-manuscript"
        scratch.mkdir(mode=0o700)
        if variables:
            atomic_write_bytes_confined(directory, scratch / "manuscript_vars.yaml", variables[1], mode=0o600)
        content = preprocess_combined_markdown(content, manuscript_dir=scratch).content
        if mermaid:
            # The shared preprocessor can rewrite figure paths. Every admitted
            # portable target must remain literal, never silently retargeted.
            if any(f"(<{row['image_target']}>)" not in content for row in mermaid["occurrences"]):
                raise ValueError("Office preprocessing changed an admitted original Mermaid image target")
    bibliographies = tuple(
        (item.relative, item.content)
        for item in (reader.read(path.relative_to(root).as_posix()) for path in resolve_bibliography(manuscript))
    )
    if (
        not reader.unchanged()
        or time.monotonic() >= deadline
        or not validate_current_rendered_provenance(root, scope).valid
    ):
        raise ValueError("Office semantic hydration/source custody changed")
    return OfficeSemanticPlan(
        content.encode(),
        sources,
        bibliographies,
        config,
        variables,
        blockers,
        original_content,
        mermaid,
    )


def observe_office_semantic_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    mermaid_admission: OfficeMermaidAdmission | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Run real Pandoc JSON with the actual combined writer's ordered filters."""
    from infrastructure.rendering._pandoc_filters import formalism_filter_args
    from infrastructure.project.public_acceptance_evidence import write_json
    from infrastructure.rendering.office_native_projection import (
        office_semantics_filter_path,
    )

    plan = office_semantic_source_plan(
        root,
        directory,
        scope,
        artifact,
        reader,
        deadline=deadline,
        mermaid_admission=mermaid_admission,
    )
    source = directory / "office-semantic-source.md"
    atomic_write_bytes_confined(root, source, plan.content, mode=0o600)
    args = [
        str(source),
        "--from=markdown+yaml_metadata_block",
        "--to=json",
        "--standalone",
    ]
    # Inventory before any writer filters: a filter cannot erase an obligation
    # merely because the candidate and reference both consume its result.
    from infrastructure.reporting.native_office_source_coverage import (
        office_coverage_obligations,
    )

    inventory_tool = native_tool_record(
        root,
        directory,
        "pandoc",
        list(args),
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-source-coverage-pandoc",
    )
    if inventory_tool["original_exit_code"] != 0 or inventory_tool["exit_code"] != 0:
        raise ValueError("actual unfiltered Office source Pandoc parse failed")
    inventory_reader = SnapshotReader(root)
    inventory_ast = inventory_reader.read(inventory_tool["artifact"]["path"]).json_object()["stdout"].encode()
    coverage = office_coverage_obligations(inventory_ast)
    atomic_write_bytes_confined(root, directory / "office-source-coverage-ast.json", inventory_ast, mode=0o600)
    original_source = original_ast = original_tool = None
    original_occurrences = []
    if office_original_mermaid_sources(plan.original_content.decode(), scope):
        original_path = directory / "office-original-source.md"
        original_ast_path = directory / "office-original-source-ast.json"
        atomic_write_bytes_confined(root, original_path, plan.original_content, mode=0o600)
        original_tool = native_tool_record(
            root,
            directory,
            "pandoc",
            [
                str(original_path),
                "--from=markdown+yaml_metadata_block",
                "--to=json",
                "--standalone",
            ],
            env=env,
            deadline=deadline,
            run_id=run_id,
            purpose="office-original-mermaid-source-pandoc",
        )
        if original_tool["original_exit_code"] != 0 or original_tool["exit_code"] != 0:
            raise ValueError("actual original Mermaid Office source Pandoc parse failed")
        original_data = inventory_reader.read(original_tool["artifact"]["path"]).json_object()["stdout"].encode()
        original_occurrences = original_office_mermaid_ast_occurrences(
            original_data, plan.original_content.decode(), scope
        )
        atomic_write_bytes_confined(root, original_ast_path, original_data, mode=0o600)
        original_source = {
            "path": original_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(plan.original_content).hexdigest(),
        }
        original_ast = {
            "path": original_ast_path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(original_data).hexdigest(),
        }
    filters = []
    sdk_root = Path(__file__).absolute().parents[2]
    sdk_reader = SnapshotReader(sdk_root)
    filter_paths = [str(office_semantics_filter_path()), *formalism_filter_args()[1::2]]
    # JSON parsing is evidence for this declared native target. Pandoc's native
    # writer applies the same first filter before crossref and citeproc.
    args.append(f"--metadata=office-native-target:{artifact.format}")
    for ordinal, path in enumerate(filter_paths):
        original = sdk_reader.read(Path(path).relative_to(sdk_root).as_posix())
        copied = directory / f"office-semantic-filter-{ordinal}.lua"
        atomic_write_bytes_confined(root, copied, original.content, mode=0o600)
        args.extend(["--lua-filter", str(copied)])
        filters.append(
            {
                "source": {"path": original.relative, "sha256": original.sha256},
                "consumed": {
                    "path": copied.relative_to(root).as_posix(),
                    "sha256": original.sha256,
                },
            }
        )
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
    crossref_before: dict[str, Any] | None = None
    if crossref:
        runtime_path = Path(crossref).resolve(strict=True)
        size = runtime_path.stat().st_size
        if size > 512 * 1024 * 1024:
            raise ValueError("Office crossref runtime exceeds finite file budget")
        with runtime_path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        crossref_before = {"path": str(runtime_path), "sha256": digest, "bytes": size}
        crossref = str(runtime_path)
        args.extend(["--filter", crossref])
    bibliographies = []
    if plan.bibliographies:
        args.append("--citeproc")
        for ordinal, (path, data) in enumerate(plan.bibliographies):
            copied = directory / f"office-semantic-bibliography-{ordinal}.bib"
            atomic_write_bytes_confined(root, copied, data, mode=0o600)
            args.append(f"--bibliography={copied}")
            digest = hashlib.sha256(data).hexdigest()
            bibliographies.append(
                {
                    "source": {"path": path, "sha256": digest},
                    "consumed": {
                        "path": copied.relative_to(root).as_posix(),
                        "sha256": digest,
                    },
                }
            )
    # Crossref rebuilds Figure nodes and can discard their nonvisible Image
    # alt attributes. Reapply the same source-bound projection after filters.
    args.extend(["--lua-filter", str(directory / "office-semantic-filter-0.lua")])
    tool = native_tool_record(
        root,
        directory,
        "pandoc",
        args,
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="office-semantic-pandoc",
    )
    if tool["original_exit_code"] != 0 or tool["exit_code"] != 0:
        raise ValueError("actual Office source Pandoc parse failed")
    if crossref_before:
        current_path = Path(crossref_before["path"])
        with current_path.open("rb") as handle:
            current_digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if (
            Path(str(crossref)).resolve(strict=True) != current_path
            or current_digest != crossref_before["sha256"]
            or current_path.stat().st_size != crossref_before["bytes"]
        ):
            raise ValueError("original Office crossref runtime changed during actual parse")
    local = SnapshotReader(root)
    ast = local.read(tool["artifact"]["path"]).json_object()["stdout"].encode()
    document = json.loads(ast)
    if not isinstance(document.get("blocks"), list) or not document.get("pandoc-api-version"):
        raise ValueError("actual Office parser returned no Pandoc document")
    ast_path = directory / "office-semantic-ast.json"
    atomic_write_bytes_confined(root, ast_path, ast, mode=0o600)
    consumed = local.read(source.relative_to(root).as_posix())
    parsed = local.read(ast_path.relative_to(root).as_posix())
    evidence = {
        "schema_version": "template-native-office-semantic-source-v2",
        "run_id": run_id,
        "format": artifact.format,
        "artifact_id": artifact.id,
        "source": {"path": consumed.relative, "sha256": consumed.sha256},
        "ast": {"path": parsed.relative, "sha256": parsed.sha256},
        "tool": tool,
        "sources": [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in plan.sources],
        "config": None
        if not plan.config
        else {
            "path": plan.config[0],
            "sha256": hashlib.sha256(plan.config[1]).hexdigest(),
        },
        "variables": None
        if not plan.variables
        else {
            "path": plan.variables[0],
            "sha256": hashlib.sha256(plan.variables[1]).hexdigest(),
        },
        "filters": filters,
        "bibliographies": bibliographies,
        "crossref_runtime": crossref_before,
        "source_coverage": coverage,
        "source_coverage_tool": inventory_tool,
        "source_coverage_ast": {
            "path": (directory / "office-source-coverage-ast.json").relative_to(root).as_posix(),
            "sha256": hashlib.sha256(inventory_ast).hexdigest(),
        },
        "original_source": original_source,
        "original_source_ast": original_ast,
        "original_source_tool": original_tool,
        "original_mermaid_occurrences": original_occurrences,
        "mermaid": plan.mermaid,
        "blockers": list(plan.blockers),
    }
    if (
        not reader.unchanged()
        or not local.unchanged()
        or not sdk_reader.unchanged()
        or not inventory_reader.unchanged()
        or time.monotonic() >= deadline
    ):
        raise ValueError("Office semantic consumed/source custody changed")
    write_json(root, directory / "office-semantic-source-observation.json", evidence)
    return ast, evidence
