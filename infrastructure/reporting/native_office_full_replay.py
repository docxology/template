"""Independent portable complete-source Office replay without producer tool paths."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from infrastructure.reporting.native_format_acceptance_contracts import NativeArtifact
from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.native_office_full_observer import (
    SCHEMA,
    office_full_outcome,
)
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)


from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
    OfficeMermaidReaderRuntime,
    office_original_mermaid_sources,
    original_office_mermaid_ast_occurrences,
    replay_office_original_mermaid_sources,
)

from infrastructure.reporting.native_office_diagram_binding import (
    admitted_office_diagram_sources,
    diagram_witness_budget,
    diagram_witness_runtime,
)

from infrastructure.reporting.native_office_diagram_visibility import (
    replay_office_diagram_visibility,
)


def _current_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    source: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    env: dict[str, str],
    deadline: float,
    mermaid_runtime: OfficeMermaidReaderRuntime | None = None,
) -> tuple[bytes, bytes, OfficeMermaidAdmission | None]:
    """Bind original parses and independently execute current admitted source."""
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _tool,
    )
    from infrastructure.reporting.native_office_semantic_source import (
        office_semantic_source_plan,
    )
    from infrastructure.reporting.native_office_source_coverage import (
        office_coverage_obligations,
    )
    from infrastructure.rendering.office_native_projection import (
        office_semantics_filter_path,
    )
    from infrastructure.rendering._pandoc_filters import formalism_filter_path

    required_fields = {
        "schema_version",
        "run_id",
        "format",
        "artifact_id",
        "source",
        "ast",
        "tool",
        "sources",
        "config",
        "variables",
        "filters",
        "bibliographies",
        "crossref_runtime",
        "source_coverage",
        "source_coverage_tool",
        "source_coverage_ast",
        "original_source",
        "original_source_ast",
        "original_source_tool",
        "original_mermaid_occurrences",
        "mermaid",
        "blockers",
    }
    if (
        set(source) != required_fields
        or source["schema_version"] != "template-native-office-semantic-source-v2"
        or source["run_id"] != run_id
        or source["format"] != artifact.format
        or source["artifact_id"] != artifact.id
    ):
        raise ValueError("portable Office original semantic source identity/fields differ")

    def original_path(path):
        return str(producer_path(custody, root, path))

    with tempfile.TemporaryDirectory(prefix="office-current-source-") as private:
        admission: OfficeMermaidAdmission | None = None
        work = Path(private).resolve()
        plan = office_semantic_source_plan(root, work, scope, artifact, reader, deadline=deadline)
        original_source_data = plan.original_content
        if source["mermaid"] is not None:
            if mermaid_runtime is None:
                raise ValueError("portable Office original Mermaid admission requires explicit reader runtime roots")
            admission = replay_office_original_mermaid_sources(
                root,
                original_source_data.decode(),
                scope,
                source["mermaid"],
                reader,
                mermaid_runtime,
                env=env,
                deadline=deadline,
                run_id=run_id,
            )
            plan = office_semantic_source_plan(
                root,
                work,
                scope,
                artifact,
                reader,
                deadline=deadline,
                mermaid_admission=admission,
            )
            if source["mermaid"] != plan.mermaid:
                raise ValueError("portable Office original Mermaid captions/alternatives/PNG projection differs")
        original_command = None
        if office_original_mermaid_sources(original_source_data.decode(), scope):
            original = _file(source["original_source"], reader)
            original_ast = _file(source["original_source_ast"], reader)
            if (
                original.path != directory / "office-original-source.md"
                or original.content != original_source_data
                or original_ast.path != directory / "office-original-source-ast.json"
            ):
                raise ValueError("portable original Office Mermaid source/AST custody differs")
            original_args = [
                original_path(original.path),
                "--from=markdown+yaml_metadata_block",
                "--to=json",
                "--standalone",
            ]
            original_parse = _tool(
                source["original_source_tool"]["artifact"],
                reader,
                run_id,
                "pandoc",
                "office-original-mermaid-source-pandoc",
                original_args,
            )
            if original_parse["stdout"].encode() != original_ast.content or source[
                "original_mermaid_occurrences"
            ] != original_office_mermaid_ast_occurrences(original_ast.content, original_source_data.decode(), scope):
                raise ValueError("portable actual original Office CodeBlocks differ from original source occurrences")
            current_original_source = work / "original-source.md"
            current_original_source.write_bytes(original_source_data)
            original_command = (str(current_original_source), original_ast.content)
        elif (
            any(
                source[name] is not None
                for name in (
                    "original_source",
                    "original_source_ast",
                    "original_source_tool",
                    "mermaid",
                )
            )
            or source["original_mermaid_occurrences"]
        ):
            raise ValueError("portable Office Mermaid evidence has no original source occurrence")

        def expected(rows):
            return [{"path": path, "sha256": hashlib.sha256(data).hexdigest()} for path, data in rows]

        if source.get("sources") != expected(plan.sources) or source.get("blockers") != list(plan.blockers):
            raise ValueError("portable Office complete source inventory/obligations differ")
        for name, binding in (("config", plan.config), ("variables", plan.variables)):
            value = (
                None
                if binding is None
                else {
                    "path": binding[0],
                    "sha256": hashlib.sha256(binding[1]).hexdigest(),
                }
            )
            if source.get(name) != value:
                raise ValueError("portable Office source config/variable custody differs")
        consumed = _file(source["source"], reader)
        inventory = _file(source["source_coverage_ast"], reader)
        filtered = _file(source["ast"], reader)
        if consumed.path != directory / "office-semantic-source.md" or consumed.content != plan.content:
            raise ValueError("portable Office original source bytes differ from current independent plan")
        if (
            inventory.path != directory / "office-source-coverage-ast.json"
            or filtered.path != directory / "office-semantic-ast.json"
        ):
            raise ValueError("portable Office original AST belongs to a different attempt")
        base = [
            original_path(consumed.path),
            "--from=markdown+yaml_metadata_block",
            "--to=json",
            "--standalone",
        ]
        observed_inventory = _tool(
            source["source_coverage_tool"]["artifact"],
            reader,
            run_id,
            "pandoc",
            "office-source-coverage-pandoc",
            base,
        )
        if observed_inventory["stdout"].encode() != inventory.content or source[
            "source_coverage"
        ] != office_coverage_obligations(inventory.content):
            raise ValueError("portable Office pre-filter census does not match original actual parser bytes")
        original_args = [*base, f"--metadata=office-native-target:{artifact.format}"]
        current_pandoc = shutil.which("pandoc", path=env.get("PATH"))
        if not current_pandoc:
            raise ValueError("portable Office source replay requires current actual Pandoc")
        local_source = work / "source.md"
        local_source.write_bytes(plan.content)
        current_args = [
            current_pandoc,
            str(local_source),
            *base[1:],
            f"--metadata=office-native-target:{artifact.format}",
        ]
        filters = source.get("filters")
        current_filters = (office_semantics_filter_path(), formalism_filter_path())
        if not isinstance(filters, list) or len(filters) != len(current_filters):
            raise ValueError("portable Office source omitted exact native semantic/formalism filters")
        sdk_root = Path(__file__).absolute().parents[2]
        sdk_reader = SnapshotReader(sdk_root)
        for index, (binding, path) in enumerate(zip(filters, current_filters, strict=True)):
            current = sdk_reader.read(path.relative_to(sdk_root).as_posix())
            copied = _file(binding["consumed"], reader)
            if (
                binding["source"] != {"path": current.relative, "sha256": current.sha256}
                or copied.path != directory / f"office-semantic-filter-{index}.lua"
                or copied.content != current.content
            ):
                raise ValueError("portable Office original filter differs from current admitted SDK")
            original_args.extend(["--lua-filter", original_path(copied.path)])
            current_filter = work / f"filter-{index}.lua"
            current_filter.write_bytes(current.content)
            current_args.extend(["--lua-filter", str(current_filter)])
        if source["crossref_runtime"]:
            current_crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
            if not current_crossref:
                raise ValueError("portable Office source replay requires declared current actual crossref")
            original_args.extend(["--filter", source["crossref_runtime"]["path"]])
            current_args.extend(["--filter", current_crossref])
        bibliographies = source.get("bibliographies")
        if not isinstance(bibliographies, list) or len(bibliographies) != len(plan.bibliographies):
            raise ValueError("portable Office source bibliography set differs")
        if bibliographies:
            original_args.append("--citeproc")
            current_args.append("--citeproc")
        for index, (binding, (bibliography_source_path, data)) in enumerate(
            zip(bibliographies, plan.bibliographies, strict=True)
        ):
            copied = _file(binding["consumed"], reader)
            if (
                binding["source"]
                != {
                    "path": bibliography_source_path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
                or copied.path != directory / f"office-semantic-bibliography-{index}.bib"
                or copied.content != data
            ):
                raise ValueError("portable Office source bibliography consumed bytes differ")
            original_args.append(f"--bibliography={original_path(copied.path)}")
            current_bib = work / f"bibliography-{index}.bib"
            current_bib.write_bytes(data)
            current_args.append(f"--bibliography={current_bib}")
        original_args.extend(["--lua-filter", original_path(directory / "office-semantic-filter-0.lua")])
        current_args.extend(["--lua-filter", str(work / "filter-0.lua")])
        observed_filtered = _tool(
            source["tool"]["artifact"],
            reader,
            run_id,
            "pandoc",
            "office-semantic-pandoc",
            original_args,
        )
        if observed_filtered["stdout"].encode() != filtered.content:
            raise ValueError("portable Office filtered source AST differs from original actual stdout")
        current_commands = [
            ([current_pandoc, str(local_source), *base[1:]], inventory.content),
            (current_args, filtered.content),
        ]
        if original_command is not None:
            current_commands.append(([current_pandoc, original_command[0], *base[1:]], original_command[1]))
        for command, retained in current_commands:
            result = run_bounded_subprocess(
                command,
                cwd=root,
                env=env,
                timeout=min(60.0, deadline - time.monotonic()),
            )
            if result.returncode != 0 or result.original_returncode != 0 or result.timed_out or result.custody_refused:
                raise ValueError("portable Office actual current source parse failed")
            if json.loads(result.stdout) != json.loads(retained):
                raise ValueError("portable Office current independent source interpretation differs")
        if not sdk_reader.unchanged():
            raise ValueError("portable Office current source filter SDK changed")
        return inventory.content, filtered.content, admission


def replay_office_full_source(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    snapshot: ArtifactSnapshot,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
    mermaid_runtime: OfficeMermaidReaderRuntime | None = None,
) -> None:
    """Recompute source/package/all-page witnesses and original command custody.

    Producer absolute executable paths are retained labels. New executions use
    current reader-local Pandoc/crossref and explicitly supplied Mermaid runtime
    roots on admitted original bytes.
    Existing portable Office/EPUB and raster/runtime/font replay stays active.
    """
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.reporting.native_format_acceptance_validation import (
        _file,
        _raster,
        _tool,
    )
    from infrastructure.reporting.native_format_observer_source_replay import (
        replay_office_conversion,
    )
    from infrastructure.reporting.native_epub_replay import replay_epub_conversion
    from infrastructure.reporting.native_office_content_witness import (
        inspect_office_source_survival,
    )
    from infrastructure.reporting.native_office_reference import (
        inspect_office_package_reference,
    )
    from infrastructure.reporting.native_office_reference_visual import (
        inspect_office_reference_projection,
    )
    from infrastructure.reporting.native_office_image_ink import (
        inspect_office_cover,
        inspect_office_native_images,
    )
    import yaml

    if (
        set(raw)
        != {
            "schema_version",
            "reference",
            "readbacks",
            "native",
            "diagram_visibility",
            "observation",
        }
        or raw.get("schema_version") != SCHEMA
    ):
        raise ValueError("invalid portable complete Office observer schema")
    reference = raw["reference"]
    if (
        set(reference)
        != {
            "schema_version",
            "source",
            "package",
            "writer",
            "ast",
            "metadata",
            "figures",
            "cover",
            "source_date_epoch",
            "status",
            "blockers",
            "assurance",
        }
        or reference["schema_version"] != "template-native-office-source-reference-v1"
    ):
        raise ValueError("portable Office original reference fields differ")
    if set(raw["readbacks"]) != {"reference", "candidate"} or set(raw["native"]) != {
        "reference",
        "candidate",
    }:
        raise ValueError("portable Office complete original native counterpart set differs")
    source = reference["source"]
    source_dir = directory / "source-reference"
    inventory, filtered, admission = _current_source(
        root,
        source_dir,
        scope,
        artifact,
        source,
        reader,
        run_id=run_id,
        custody=custody,
        env=env,
        deadline=deadline,
        mermaid_runtime=mermaid_runtime,
    )
    metadata = _file(reference["metadata"], reader)
    reference_ast = _file(reference["ast"], reader)
    reference_package = _file(reference["package"], reader)
    if artifact.format == "docx" and source["mermaid"] is not None:
        from infrastructure.rendering.office_diagram_layout import (
            project_docx_diagram_layout,
        )

        projected, _ = project_docx_diagram_layout(
            reference_package.content,
            tuple(row["png"]["sha256"] for row in source["mermaid"]["occurrences"]),
        )
        if projected != reference_package.content:
            raise ValueError("portable Office original source reference omitted its declared diagram height projection")
    if (
        metadata.path != source_dir / "source-reference-metadata.yaml"
        or reference_ast.path != source_dir / "source-reference-ast.json"
        or reference_package.path != source_dir / f"source-reference.{artifact.format}"
    ):
        raise ValueError("portable Office source reference artifact paths differ")
    from infrastructure.rendering.office_native_projection import office_pandoc_metadata

    settings = {} if source["config"] is None else yaml.safe_load(_file(source["config"], reader).content)
    expected_metadata = office_pandoc_metadata(settings)
    if artifact.format == "epub":
        authors = expected_metadata.get("author") or []
        author = "; ".join(map(str, authors)) if isinstance(authors, list) else str(authors)
        raw_metadata = settings.get("metadata") or {}
        language = raw_metadata.get("language", "en") if isinstance(raw_metadata, dict) else "en"
        expected_metadata = {
            key: value
            for key, value in {
                "title": expected_metadata.get("title"),
                "author": author,
                "lang": language,
            }.items()
            if value
        }
    if yaml.safe_load(metadata.content) != expected_metadata:
        raise ValueError("portable Office reference metadata is not derived from current source config")
    from infrastructure.validation.output.render_formats import (
        render_config_manuscript_dir,
    )

    project = root / "projects" / scope
    manuscript = render_config_manuscript_dir(project)
    document = json.loads(inventory)
    from infrastructure.reporting.native_office_reference import (
        office_reference_metadata,
    )

    document["meta"].update({key: office_reference_metadata(value) for key, value in expected_metadata.items()})
    pending = [document["blocks"]]
    image_index = 0
    figures = []
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if value.get("t") == "Image":
                binding = reference["figures"][image_index]
                original = _file(binding["source"], reader)
                frozen = _file(binding["consumed"], reader)
                if (
                    value["c"][2][0] != binding["target"]
                    or original.content != frozen.content
                    or frozen.path != source_dir / f"source-figure-{image_index}{original.path.suffix}"
                ):
                    raise ValueError("portable Office source/native frozen figure custody differs")
                target = binding["target"]
                roots = (
                    manuscript,
                    project / "output/figures",
                    project / "output",
                    project / "output/web",
                )
                target_path = next((base / target for base in roots if (base / target).is_file()), None)
                if (
                    target_path is None
                    or target_path.resolve(strict=True).relative_to(root).as_posix() != binding["original_target"]
                ):
                    raise ValueError(
                        "portable Office frozen figure does not resolve from current original source target"
                    )
                if target_path.suffix.lower() == ".pdf":
                    target_path = next(
                        (
                            target_path.with_suffix(suffix)
                            for suffix in (".png", ".jpg", ".jpeg")
                            if target_path.with_suffix(suffix).is_file()
                        ),
                        None,
                    )
                if target_path is None or target_path.resolve(strict=True) != original.path.resolve(strict=True):
                    raise ValueError("portable Office frozen asset is not the production-selected source figure")
                value["c"][2][0] = str(producer_path(custody, root, frozen.path))
                figures.append(frozen.content)
                image_index += 1
            pending.extend(reversed(list(value.values())))
        elif isinstance(value, list):
            pending.extend(reversed(value))
    if image_index != len(reference["figures"]) or document != json.loads(reference_ast.content):
        raise ValueError("portable Office source-only writer AST contains altered or dropped source")
    args = [
        str(producer_path(custody, root, reference_ast.path)),
        "--from=json",
        f"--to={artifact.format}",
        "--standalone",
        f"--metadata-file={producer_path(custody, root, metadata.path)}",
        "--output",
        str(producer_path(custody, root, reference_package.path)),
    ]
    for binding in source["filters"]:
        args.extend(
            [
                "--lua-filter",
                str(producer_path(custody, root, root / binding["consumed"]["path"])),
            ]
        )
    if source["crossref_runtime"]:
        args.extend(["--filter", source["crossref_runtime"]["path"]])
    if source["bibliographies"]:
        args.append("--citeproc")
        args.extend(
            f"--bibliography={producer_path(custody, root, root / binding['consumed']['path'])}"
            for binding in source["bibliographies"]
        )
    args.extend(
        [
            "--lua-filter",
            str(producer_path(custody, root, root / source["filters"][0]["consumed"]["path"])),
        ]
    )
    cover = None
    from infrastructure.rendering._pdf_title_page_images import (
        _cover_image_path,
        _cover_image_alt,
    )

    configured_cover = (
        _cover_image_path(settings, root / source["config"]["path"])
        if artifact.format == "epub" and source["config"]
        else None
    )
    if bool(reference["cover"]) != bool(configured_cover):
        raise ValueError("portable Office reference omitted or introduced configured cover")
    if reference["cover"]:
        original = _file(reference["cover"]["source"], reader)
        frozen = _file(reference["cover"]["consumed"], reader)
        if original.content != frozen.content or frozen.path != source_dir / f"source-cover{original.path.suffix}":
            raise ValueError("portable Office configured frozen cover differs")
        if (
            configured_cover is None
            or configured_cover.resolve(strict=True) != original.path.resolve(strict=True)
            or reference["cover"]["alt"] != _cover_image_alt(settings)
        ):
            raise ValueError("portable Office cover asset/alternative differs from current source declaration")
        cover = frozen.content
        args.append(f"--epub-cover-image={producer_path(custody, root, frozen.path)}")
    if artifact.format == "epub":
        from infrastructure.rendering.epub_renderer import _EPUB_IDENTIFIER_PLACEHOLDER

        args.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
    _tool(
        reference["writer"]["artifact"],
        reader,
        run_id,
        "pandoc",
        "office-source-reference-writer",
        args,
    )
    readbacks = {}
    current_pandoc = shutil.which("pandoc", path=env.get("PATH"))
    if not current_pandoc:
        raise ValueError("portable Office native package replay requires current actual Pandoc")
    for name, package in (("reference", reference_package), ("candidate", snapshot)):
        data = raw["readbacks"][name]
        leaf = directory / f"{name}-readback"
        frozen = reader.read((leaf / f"readback-input.{artifact.format}").relative_to(root).as_posix())
        parsed = _file(data["ast"], reader)
        if (
            frozen.content != package.content
            or parsed.path != leaf / "package-readback-ast.json"
            or data["input"] != {"path": package.relative, "sha256": package.sha256}
        ):
            raise ValueError("portable Office actual package reader consumed different original bytes")
        tool = _tool(
            data["tool"]["artifact"],
            reader,
            run_id,
            "pandoc",
            "office-package-readback",
            [
                str(producer_path(custody, root, frozen.path)),
                f"--from={artifact.format}",
                "--to=json",
                "--standalone",
            ],
        )
        if tool["stdout"].encode() != parsed.content:
            raise ValueError("portable Office native readback AST differs from actual stdout")
        with tempfile.TemporaryDirectory(prefix="office-package-replay-") as private:
            input_path = Path(private) / f"input.{artifact.format}"
            input_path.write_bytes(package.content)
            result = run_bounded_subprocess(
                [
                    current_pandoc,
                    str(input_path),
                    f"--from={artifact.format}",
                    "--to=json",
                    "--standalone",
                ],
                cwd=Path(private),
                env=env,
                timeout=min(60.0, deadline - time.monotonic()),
            )
            if (
                result.returncode != 0
                or result.original_returncode != 0
                or result.timed_out
                or result.custody_refused
                or json.loads(result.stdout) != json.loads(parsed.content)
            ):
                raise ValueError("portable Office independent current actual package interpretation differs")
        readbacks[name] = parsed.content
    pdfs, pixels = {}, {}
    for name, package in (("reference", reference_package), ("candidate", snapshot)):
        native = raw["native"][name]
        leaf = directory / f"{name}-native"
        if artifact.format == "docx":
            pdf = replay_office_conversion(
                root,
                leaf,
                package,
                native["conversion"],
                reader,
                run_id=run_id,
                custody=custody,
            )
        else:
            replay_epub_conversion(
                native["conversion"],
                package.content,
                read_artifact=lambda binding: _file(binding, reader).content,
                producer_path=lambda relative: str(producer_path(custody, root, root / relative)),
                run_id=run_id,
            )
            pdf = _file(native["conversion"]["pdf"], reader)
        _raster(native, pdf, 0, leaf, reader, run_id, versions, custody)
        pdfs[name] = pdf.content
        pixels[name] = tuple(
            _file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in native["raster"]["rasters"]
        )
    source_survival = inspect_office_source_survival(
        inventory,
        filtered,
        readbacks["candidate"],
        snapshot.content,
        artifact.format,
        tuple(figures),
        yaml.safe_load(metadata.content),
        cover,
    )
    reference_survival = inspect_office_source_survival(
        inventory,
        filtered,
        readbacks["reference"],
        reference_package.content,
        artifact.format,
        tuple(figures),
        yaml.safe_load(metadata.content),
        cover,
    )
    package_parity = inspect_office_package_reference(
        readbacks["reference"], readbacks["candidate"], source["source_coverage"]
    )
    package_parity.update(status="failed" if package_parity["findings"] else "observed", blockers=[])
    projection = inspect_office_reference_projection(
        pdfs["reference"],
        pixels["reference"],
        pdfs["candidate"],
        pixels["candidate"],
        deadline=deadline,
    )
    diagram_visibility = raw["diagram_visibility"]
    if source["mermaid"] is None:
        if diagram_visibility is not None:
            raise ValueError("portable Office diagram witness exists without admitted original diagram source")
    else:
        if not isinstance(diagram_visibility, dict) or set(diagram_visibility) != {
            "reference",
            "candidate",
        }:
            raise ValueError("portable Office omitted an original native diagram counterpart")
        if mermaid_runtime is None:
            raise ValueError("portable Office requires an explicit reader-local diagram source paint directory")
        diagram_sources = admitted_office_diagram_sources(source, scope, reader, admission)
        for name in ("reference", "candidate"):
            replay_office_diagram_visibility(
                root,
                directory / f"{name}-diagram-visibility",
                pdfs[name],
                pixels[name],
                diagram_sources,
                diagram_visibility[name],
                reader,
                budget=diagram_witness_budget(admission),
                pdfium_runtime=diagram_witness_runtime(admission, deadline),
                run_id=run_id,
                custody=custody,
                versions=versions,
                deadline=deadline,
                reader_directory=mermaid_runtime.directory / f"{artifact.format}-{name}-native-diagram-stencils",
                env=env,
            )
    outcome = office_full_outcome(
        source,
        source_survival,
        reference_survival,
        package_parity,
        projection,
        diagram_visibility,
    )
    assets = ((cover,) if cover else ()) + tuple(figures)
    image_ink = {name: inspect_office_native_images(data, assets, deadline=deadline) for name, data in pdfs.items()}
    covers = (
        None
        if cover is None
        else {
            name: inspect_office_cover(data, cover, reference["cover"]["alt"])
            for name, data in (
                ("reference", reference_package.content),
                ("candidate", snapshot.content),
            )
        }
    )
    outcome.update(native_source_images=image_ink, covers=covers)
    for extra in (*image_ink.values(), *(covers or {}).values()):
        outcome["findings"].extend(extra["findings"])
        outcome["blockers"].extend(extra["blockers"])
    outcome["status"] = "failed" if outcome["findings"] else "blocked" if outcome["blockers"] else "observed"
    if outcome != raw["observation"] or not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("portable Office independently reconstructed complete source/native evidence differs")
