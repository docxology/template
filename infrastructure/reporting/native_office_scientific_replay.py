"""Independent portable replay of genuine scientific Office control processes."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from infrastructure.reporting.native_format_portable_custody import producer_bootstrap, producer_path
from infrastructure.reporting.native_office_scientific_controls import (
    CONTROL_BIBLIOGRAPHY,
    CONTROL_CODES,
    CONTROL_SOURCE,
    mutate_office_scientific_package,
)
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
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    original_deadline: float,
    deadline: float,
    env: dict[str, str],
    original_epub_arguments: tuple[str, ...] = (),
) -> None:
    """Retain original zero/negative exits and recompute source/native findings.

    ``original_epub_arguments`` comes from the admitted original supervision
    specification, including its original validator/Java/frozen-engine labels.
    Those labels are never opened as reader-side executable paths. Existing
    EPUB replay binds actual engine/JAR receipts to archived bytes.
    """
    from PIL import Image
    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
    from infrastructure.reporting.native_format_observer_source_replay import replay_office_conversion
    from infrastructure.reporting.native_epub_replay import replay_epub_conversion
    from infrastructure.reporting.native_office_content_witness import inspect_office_source_survival
    from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection
    from infrastructure.rendering.office_native_projection import office_semantics_filter_path
    from infrastructure.rendering._pandoc_filters import formalism_filter_path
    from infrastructure.rendering.epub_renderer import _EPUB_IDENTIFIER_PLACEHOLDER, _normalize_epub_archive

    if kind not in {"docx", "epub"} or not isinstance(records, list) or len(records) != len(CONTROL_CODES):
        raise ValueError("portable scientific native suite omitted a required original control")
    if kind == "docx" and original_epub_arguments:
        raise ValueError("portable DOCX suite introduced unrelated original engine arguments")
    options = list(original_epub_arguments[::2])
    if (
        len(original_epub_arguments) % 2
        or len(set(options)) != len(options)
        or any(option not in {"--epubcheck-jar", "--java-executable", "--frozen-epub-engine"} for option in options)
    ):
        raise ValueError("portable scientific EPUB original supervision arguments differ")
    pandoc = shutil.which("pandoc", path=env.get("PATH"))
    crossref = shutil.which("pandoc-crossref", path=env.get("PATH"))
    if not pandoc or not crossref:
        raise ValueError("portable scientific native replay requires actual current Pandoc/crossref")
    image = Image.new("RGB", (64, 48), (255, 255, 255))
    for x in range(8, 56):
        for y in range(8, 40):
            image.putpixel((x, y), (40, 80, 160))
    image_buffer = BytesIO()
    image.save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()

    def original_path(path):
        return str(producer_path(custody, root, path))

    def actual(command: list[str], cwd: Path, retained: bytes) -> None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("portable scientific native control replay expired")
        outcome = run_bounded_subprocess(command, cwd=cwd, env=env, timeout=min(60.0, remaining))
        if (
            outcome.returncode != 0
            or outcome.original_returncode != 0
            or outcome.timed_out
            or outcome.custody_refused
            or json.loads(outcome.stdout) != json.loads(retained)
        ):
            raise ValueError("portable scientific native actual current reader differs")

    for ordinal, (item, (name, required)) in enumerate(zip(records, CONTROL_CODES.items(), strict=True)):
        _exact(item, {"kind", "name", "process_artifact", "artifact", "original_exit_code"})
        leaf = directory / f"{kind}-scientific-control-{ordinal}"
        expected_exit = int(required is not None)
        process = _file(item["process_artifact"], reader)
        observation = _file(item["artifact"], reader)
        if (
            item["kind"] != kind
            or item["name"] != name
            or type(item["original_exit_code"]) is not int
            or item["original_exit_code"] != expected_exit
            or process.path != directory / f"{kind}-scientific-control-{ordinal}-process.json"
            or observation.path != leaf / "observation.json"
        ):
            raise ValueError("portable scientific native control original attempt differs")
        original = _exact(
            process.json_object(),
            {
                "schema_version",
                "run_id",
                "command",
                "exit_code",
                "original_exit_code",
                "timed_out",
                "custody_refused",
                "stdout",
                "stderr",
                "diagnostic",
            },
        )
        arguments = [
            "--kind",
            kind,
            "--control",
            name,
            "--root",
            custody["root"],
            "--directory",
            original_path(leaf),
            "--deadline",
            str(original_deadline),
            "--run-id",
            run_id,
            *original_epub_arguments,
        ]
        wanted = producer_bootstrap(
            custody, root, runtime, "infrastructure.reporting.native_office_scientific_controls", *arguments
        )
        if (
            original["schema_version"] != "template-native-office-scientific-control-process-v1"
            or original["run_id"] != run_id
            or original["command"] != wanted
            or original["diagnostic"] != ""
            or original["timed_out"] is not False
            or original["custody_refused"] is not False
            or any(
                type(original[key]) is not int or original[key] != expected_exit
                for key in ("exit_code", "original_exit_code")
            )
        ):
            raise ValueError("portable scientific native control original supervised exit differs")
        raw = _exact(
            observation.json_object(),
            {
                "schema_version",
                "run_id",
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
            raw["schema_version"] != "template-native-office-scientific-controls-v1"
            or raw["run_id"] != run_id
            or raw["kind"] != kind
            or raw["control"] != name
            or type(raw["oracle_exit_code"]) is not int
            or raw["oracle_exit_code"] != expected_exit
        ):
            raise ValueError("portable scientific native source oracle differs")
        source_dir = leaf / "source"
        source = _file(raw["source"], reader)
        baseline = _file(raw["source_package"], reader)
        bibliography = reader.read((source_dir / "references.bib").relative_to(root).as_posix())
        figure = reader.read((source_dir / "control.png").relative_to(root).as_posix())
        if (
            source.path != source_dir / "source.md"
            or source.content != CONTROL_SOURCE.encode()
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
        base = [original_path(source.path), "--from=markdown+yaml_metadata_block"]
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
        with tempfile.TemporaryDirectory(prefix="office-scientific-replay-") as private:
            work = Path(private)
            local_source = work / "source.md"
            local_source.write_bytes(source.content)
            local_bib = work / "references.bib"
            local_bib.write_bytes(bibliography.content)
            (work / "control.png").write_bytes(image_bytes)
            local_filters = []
            for index, data in enumerate(current_filters):
                path = work / f"filter-{index}.lua"
                path.write_bytes(data)
                local_filters.extend(["--lua-filter", str(path)])
            current_common = [
                *local_filters,
                "--filter",
                crossref,
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
                [pandoc, str(local_source), "--from=markdown+yaml_metadata_block", "--to=json", "--standalone"],
                work,
                source_ast,
            )
            actual(
                [
                    pandoc,
                    str(local_source),
                    "--from=markdown+yaml_metadata_block",
                    "--to=json",
                    "--standalone",
                    f"--metadata=office-native-target:{kind}",
                    *current_common,
                ],
                work,
                filtered_ast,
            )
            positive = None
            for row, control in zip(raw["controls"], names, strict=True):
                _exact(
                    row, {"name", "package", "readback", "native", "source_survival", "projection", "required_finding"}
                )
                if row["name"] != control or row["required_finding"] != CONTROL_CODES[control]:
                    raise ValueError("portable scientific native control source requirement differs")
                package = _file(row["package"], reader)
                control_leaf = leaf / control
                if package.path != control_leaf / f"control.{kind}":
                    raise ValueError("portable scientific native control package belongs to another attempt")
                mutated = work / f"mutated.{kind}"
                mutated.write_bytes(mutate_office_scientific_package(baseline.content, kind, control))
                if kind == "epub":
                    _normalize_epub_archive(mutated, source_date_epoch=cast(int, raw["source_date_epoch"]))
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
                actual([pandoc, str(mutated), f"--from={kind}", "--to=json", "--standalone"], work, parsed.content)
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
    if not reader.unchanged():
        raise ValueError("portable scientific native admitted custody changed")
