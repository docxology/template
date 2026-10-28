"""Independent portable replay of genuine scientific Office control processes."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from infrastructure.reporting.native_format_portable_custody import producer_path
from infrastructure.reporting.native_office_scientific_controls import (
    CONTROL_BIBLIOGRAPHY,
    CONTROL_CODES,
    CONTROL_SOURCE,
    SCHEMA,
    office_scientific_epub_arguments,
    mutate_office_scientific_package,
)
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def _exact(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("portable scientific native control fields differ")
    return value


def replay_office_scientific_controls(
    root: Path,
    directory: Path,
    kind: str,
    records: list[dict[str, Any]],
    reader: SnapshotReader,
    *,
    run_id: str,
    scope: str,
    source: NativeSourceContext,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    original_deadline: float,
    deadline: float,
    env: dict[str, str],
    original_epub_arguments: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Retain original zero/negative exits and recompute source/native findings.

    ``original_epub_arguments`` comes from the admitted original supervision
    specification, including its original validator/Java/frozen-engine labels.
    Those labels are never opened as reader-side executable paths. Existing
    EPUB replay binds actual engine/JAR receipts to archived bytes.
    """
    from PIL import Image
    from infrastructure.reporting.native_format_current_pandoc import current_pandoc_reader
    from infrastructure.reporting.native_print_child_custody import OfficeScientificControlReaderOperation
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _raster, _tool
    from infrastructure.reporting.native_format_observer_source_replay import replay_office_conversion
    from infrastructure.reporting.native_epub_replay import replay_epub_conversion
    from infrastructure.reporting.native_office_content_witness import inspect_office_source_survival
    from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection
    from infrastructure.rendering.office_native_projection import office_semantics_filter_path
    from infrastructure.rendering._pandoc_filters import formalism_filter_path
    from infrastructure.rendering.epub_renderer import _EPUB_IDENTIFIER_PLACEHOLDER, _normalize_epub_archive

    if kind not in {"docx", "epub"} or not isinstance(records, list) or len(records) != len(CONTROL_CODES):
        raise ValueError("portable scientific native suite omitted a required original control")
    if tuple(item.get("name") for item in records) != tuple(CONTROL_CODES):
        raise ValueError("portable scientific native suite missing, duplicated or reordered a required control")
    epub_arguments = office_scientific_epub_arguments(kind, original_epub_arguments)
    parent_reader = reader
    context = OfficeScientificControlReaderOperation(
        source, parent_reader, records, scope=scope, run_id=run_id, deadline=deadline
    )
    reader = SnapshotReader(root, native_control_operation=context)
    image = Image.new("RGB", (64, 48), (255, 255, 255))
    for x in range(8, 56):
        for y in range(8, 40):
            image.putpixel((x, y), (40, 80, 160))
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()

    def original_path(path):
        return str(producer_path(custody, root, path))

    outcomes: list[dict[str, Any]] = []
    for ordinal, (item, (name, required)) in enumerate(zip(records, CONTROL_CODES.items(), strict=True)):
        _exact(
            item,
            {
                "name",
                "process_artifact",
                "artifact",
                "specification_artifact",
                "closure_artifact",
                "original_exit_code",
            },
        )
        leaf = directory / f"{kind}-scientific-control-{ordinal:04d}"
        expected_exit = int(required is not None)
        authority = context.child(item, reader)
        specification = authority["specification"]
        if (
            specification["kind"] != kind
            or specification["epub_arguments"] != list(epub_arguments)
            or specification["caller_deadline_monotonic"] != original_deadline
            or specification["directory"] != leaf.relative_to(root).as_posix()
            or item["name"] != name
            or type(item["original_exit_code"]) is not int
            or item["original_exit_code"] != expected_exit
        ):
            raise ValueError("portable scientific native actual child scope/kind/engine/clock differs")
        observation = _file(item["artifact"], reader)
        fixture = leaf / "fixture"
        raw = _exact(
            observation.json_object(),
            {
                "schema_version",
                "run_id",
                "scope",
                "worker_pid",
                "worker_platform",
                "kind",
                "source",
                "source_package",
                "source_tools",
                "crossref_runtime",
                "source_date_epoch",
                "control",
                "controls",
                "oracle_exit_code",
            },
        )
        if (
            raw["schema_version"] != SCHEMA
            or raw["run_id"] != run_id
            or raw["kind"] != kind
            or raw["scope"] != scope
            or raw["worker_pid"] != authority["process"]["pid"]
            or raw["worker_platform"] != specification["parent_platform"]
            or raw["control"] != name
            or type(raw["oracle_exit_code"]) is not int
            or raw["oracle_exit_code"] != expected_exit
        ):
            raise ValueError("portable scientific native source oracle differs")
        source_dir = fixture / "source"
        source_file = _file(raw["source"], reader)
        baseline = _file(raw["source_package"], reader)
        bibliography = reader.read((source_dir / "references.bib").relative_to(root).as_posix())
        figure = reader.read((source_dir / "control.png").relative_to(root).as_posix())
        if (
            source_file.path != source_dir / "source.md"
            or source_file.content != CONTROL_SOURCE.encode()
            or baseline.path != source_dir / f"baseline.{kind}"
            or bibliography.content != CONTROL_BIBLIOGRAPHY.encode()
            or figure.content != image_bytes
        ):
            raise ValueError("portable scientific native source fixture bytes differ")
        crossref_runtime = _exact(raw["crossref_runtime"], {"path", "sha256", "bytes"})
        if (
            not isinstance(crossref_runtime["path"], str)
            or not Path(crossref_runtime["path"]).is_absolute()
            or not isinstance(crossref_runtime["sha256"], str)
            or len(crossref_runtime["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in crossref_runtime["sha256"])
            or type(crossref_runtime["bytes"]) is not int
            or not 0 < crossref_runtime["bytes"] <= 512 * 1024 * 1024
        ):
            raise ValueError("portable scientific native original crossref inventory differs")
        filters = []
        current_filters = []
        for index, path in enumerate((office_semantics_filter_path(), formalism_filter_path())):
            frozen = reader.read((source_dir / f"filter-{index}.lua").relative_to(root).as_posix())
            if frozen.content != path.read_bytes():
                raise ValueError("portable scientific native source filter differs from current SDK")
            filters.extend(["--lua-filter", original_path(frozen.path)])
            current_filters.append(frozen.content)
        common = [
            *filters,
            "--filter",
            crossref_runtime["path"],
            "--citeproc",
            f"--bibliography={original_path(bibliography.path)}",
            f"--resource-path={original_path(source_dir)}",
            "--metadata=title:Scientific control",
            "--lua-filter",
            original_path(source_dir / "filter-0.lua"),
        ]
        if kind == "epub":
            common.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
            if type(raw["source_date_epoch"]) is not int:
                raise ValueError("portable scientific EPUB original archive epoch differs")
        elif raw["source_date_epoch"] is not None:
            raise ValueError("portable scientific DOCX introduced an EPUB epoch")
        base = [original_path(source_file.path), "--from=markdown+yaml_metadata_block"]
        if not isinstance(raw["source_tools"], list) or len(raw["source_tools"]) != 3:
            raise ValueError("portable scientific native source tool evidence omitted")
        specifications = (
            ("office-scientific-control-source", [*base, "--to=json", "--standalone"]),
            (
                "office-scientific-control-filtered",
                [*base, "--to=json", "--standalone", f"--metadata=office-native-target:{kind}", *common],
            ),
            (
                "office-scientific-control-writer",
                [*base, f"--to={kind}", "--standalone", *common, "--output", original_path(baseline.path)],
            ),
        )
        tools = [
            _tool(record["artifact"], reader, run_id, "pandoc", purpose, args)
            for record, (purpose, args) in zip(raw["source_tools"], specifications, strict=True)
        ]
        source_ast, filtered_ast = (tools[index]["stdout"].encode() for index in (0, 1))
        names = ("baseline",) if name == "baseline" else ("baseline", name)
        if not isinstance(raw["controls"], list) or len(raw["controls"]) != len(names):
            raise ValueError("portable scientific native control omitted positive counterpart")
        checked_rows: list[dict[str, Any]] = []
        with current_pandoc_reader(
            root, parent_reader, env=env, deadline=deadline, purpose=f"office-scientific-{kind}-{name}", crossref=True
        ) as current:
            work = current.runtime.directory
            local_source = current.runtime.freeze("source.md", source_file.content)
            local_bib = current.runtime.freeze("references.bib", bibliography.content)
            current.runtime.freeze("control.png", image_bytes)

            def actual(arguments: list[str], retained: bytes, purpose: str) -> None:
                original = current.tool("pandoc", arguments, purpose)
                if json.loads(original["stdout"]) != json.loads(retained):
                    raise ValueError("portable scientific native actual current Source-owned reader differs")

            local_filters = []
            for index, data in enumerate(current_filters):
                path = current.runtime.freeze(f"filter-{index}.lua", data)
                local_filters.extend(["--lua-filter", str(path)])
            current_common = [
                *local_filters,
                "--filter",
                str(current.crossref),
                "--citeproc",
                f"--bibliography={local_bib}",
                f"--resource-path={work}",
                "--metadata=title:Scientific control",
                "--lua-filter",
                str(work / "filter-0.lua"),
            ]
            if kind == "epub":
                current_common.append(f"--metadata=identifier:{_EPUB_IDENTIFIER_PLACEHOLDER}")
            actual(
                [str(local_source), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"],
                source_ast,
                "current-office-scientific-source",
            )
            actual(
                [
                    str(local_source),
                    "--from=markdown+yaml_metadata_block",
                    "--to=json",
                    "--standalone",
                    f"--metadata=office-native-target:{kind}",
                    *current_common,
                ],
                filtered_ast,
                "current-office-scientific-filtered",
            )
            positive = None
            for row, control in zip(raw["controls"], names, strict=True):
                _exact(
                    row, {"name", "package", "readback", "native", "source_survival", "projection", "required_finding"}
                )
                if row["name"] != control or row["required_finding"] != CONTROL_CODES[control]:
                    raise ValueError("portable scientific native control source requirement differs")
                package = _file(row["package"], reader)
                control_leaf = fixture / control
                if package.path != control_leaf / f"control.{kind}":
                    raise ValueError("portable scientific native control package belongs to another attempt")
                candidate = mutate_office_scientific_package(baseline.content, kind, control)
                if kind == "epub":
                    from infrastructure.core.files.secure_write import atomic_write_bytes_confined

                    normalization = work / f"normalize-{control}.epub"
                    atomic_write_bytes_confined(root, normalization, candidate, mode=0o600)
                    _normalize_epub_archive(normalization, source_date_epoch=cast(int, raw["source_date_epoch"]))
                    candidate = normalization.read_bytes()
                mutated = current.runtime.freeze(f"mutated-{control}.{kind}", candidate)
                if mutated.read_bytes() != package.content:
                    raise ValueError("portable scientific native candidate differs from actual source-defined mutation")
                readback = row["readback"]
                frozen = reader.read((control_leaf / f"readback/readback-input.{kind}").relative_to(root).as_posix())
                parsed = _file(readback["ast"], reader)
                if (
                    frozen.content != package.content
                    or parsed.path != control_leaf / "readback/package-readback-ast.json"
                    or readback["input"] != {"path": package.relative, "sha256": package.sha256}
                ):
                    raise ValueError("portable scientific native actual reader input differs")
                tool = _tool(
                    readback["tool"]["artifact"],
                    reader,
                    run_id,
                    "pandoc",
                    "office-package-readback",
                    [original_path(frozen.path), f"--from={kind}", "--to=json", "--standalone"],
                )
                if tool["stdout"].encode() != parsed.content:
                    raise ValueError("portable scientific native original reader stdout differs")
                actual(
                    [str(mutated), f"--from={kind}", "--to=json", "--standalone"],
                    parsed.content,
                    f"current-office-scientific-readback-{control}",
                )
                survival = inspect_office_source_survival(
                    source_ast,
                    filtered_ast,
                    parsed.content,
                    package.content,
                    kind,
                    (image_bytes,),
                    {"title": "Scientific control"},
                )
                native = row["native"]
                native_leaf = control_leaf / "native"
                if kind == "docx":
                    pdf = replay_office_conversion(
                        root, native_leaf, package, native["conversion"], reader, run_id=run_id, custody=custody
                    )
                else:
                    replay_epub_conversion(
                        native["conversion"],
                        package.content,
                        read_artifact=lambda binding: _file(binding, reader).content,
                        producer_path=lambda relative: original_path(root / relative),
                        run_id=run_id,
                        authenticate_tool=lambda binding, raw: validate_original_native_tool(
                            binding,
                            raw,
                            reader,
                            run_id=run_id,
                        ),
                    )
                    pdf = _file(native["conversion"]["pdf"], reader)
                _raster(native, pdf, 0, native_leaf, reader, run_id, versions, custody)
                observed = (
                    pdf.content,
                    tuple(
                        _file({"path": raster["path"], "sha256": raster["sha256"]}, reader).content
                        for raster in native["raster"]["rasters"]
                    ),
                )
                if control == "baseline":
                    positive = observed
                if positive is None:
                    raise ValueError("portable scientific native positive baseline omitted")
                projection = inspect_office_reference_projection(*positive, *observed, deadline=deadline)
                codes = {finding["code"] for result in (survival, projection) for finding in result["findings"]}
                required_code = CONTROL_CODES[control]
                if (
                    survival != row["source_survival"]
                    or projection != row["projection"]
                    or survival["blockers"]
                    or (required_code is None and codes)
                    or (required_code is not None and required_code not in codes)
                    or (control in {"tiny-math", "invisible-math"} and survival["status"] != "observed")
                ):
                    raise ValueError("portable scientific native independently reconstructed original finding differs")
                checked_rows.append(
                    {
                        "control": control,
                        "source_survival": survival,
                        "projection": projection,
                        "diagnostics": sorted(codes),
                    }
                )
        outcomes.append(
            {
                "name": name,
                "original_exit_code": item["original_exit_code"],
                "reconstructed_exit_code": 0 if required is None else 1,
                "intended_diagnostic": required,
                "targets": [{"fixture": "scientific-" + kind, "control": row["control"]} for row in checked_rows],
                "rows": checked_rows,
                "artifact": item["artifact"],
            }
        )
    context.verify(reader)
    if not reader.unchanged() or not parent_reader.unchanged():
        raise ValueError("portable scientific native admitted custody changed")
    return {"suite_id": kind + "_scientific", "scope": scope, "original_run_id": run_id, "outcomes": outcomes}
