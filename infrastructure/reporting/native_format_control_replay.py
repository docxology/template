"""Independent source-owned control replay retaining original supervised exits."""

from __future__ import annotations

import copy
import math
import stat
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

from defusedxml.ElementTree import fromstring

from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_portable_custody import producer_bootstrap, producer_path
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-native-observer-controls-v2"


def _keys(raw: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != keys:
        raise ValueError("unknown, missing or malformed native control fields")
    return raw


def _supervision(
    item: dict[str, Any],
    leaf: Path,
    kind: str,
    name: str,
    expected: int,
    reader: SnapshotReader,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    original_deadline: float,
    extra: list[str] | None = None,
) -> None:
    from infrastructure.reporting.native_format_acceptance_validation import _file

    projection = kind == "projection"
    binding = item["tool_artifact" if projection else "process_artifact"]
    process_file = _file(binding, reader)
    ordinal = leaf.name.rsplit("-", 1)[1]
    if process_file.path != leaf.parent / f"{kind}-control-{ordinal}-process.json":
        raise ValueError("control process belongs to another attempt")
    process = process_file.json_object()
    fields = {
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
    }
    if projection:
        fields.add("elapsed_seconds")
    _keys(process, fields)
    command = process["command"]
    if not isinstance(command, list) or command.count("--deadline") != 1:
        raise ValueError("control omitted its original finite deadline")
    if command[command.index("--deadline") + 1] != str(original_deadline):
        raise ValueError("control deadline differs from admitted original supervision specification")
    module = {
        "docx": "native_office_observer",
        "pptx": "native_office_observer",
        "epub": "native_epub_observer",
        "projection": "native_projection_checks",
    }[kind]
    arguments = (["--kind", kind] if kind in {"docx", "pptx"} else []) + [
        "--control",
        name,
        "--root",
        custody["root"],
        "--directory",
        str(producer_path(custody, reader.root, leaf)),
        "--deadline",
        str(original_deadline),
        "--run-id",
        run_id,
        *(extra or []),
    ]
    wanted = producer_bootstrap(custody, reader.root, runtime, f"infrastructure.reporting.{module}", *arguments)
    if (
        process["schema_version"]
        != f"template-native-{'office' if kind in {'docx', 'pptx'} else kind}-control-process-v1"
        or process["run_id"] != run_id
        or command != wanted
        or process["diagnostic"] != ""
        or process["timed_out"] is not False
        or process["custody_refused"] is not False
        or type(process["exit_code"]) is not int
        or process["exit_code"] != expected
        or type(process["original_exit_code"]) is not int
        or process["original_exit_code"] != expected
        or type(item["original_exit_code"]) is not int
        or item["original_exit_code"] != expected
    ):
        raise ValueError("native control lost its original bound process outcome")
    if projection and (
        type(process["elapsed_seconds"]) not in {int, float}
        or not math.isfinite(process["elapsed_seconds"])
        or process["elapsed_seconds"] < 0
    ):
        raise ValueError("invalid original control duration")


def _outcome(raw: dict[str, Any], observations: list[dict[str, Any]], code: str | None) -> None:
    expected = 0 if code is None else 1
    if type(raw.get("oracle_exit_code")) is not int or raw["oracle_exit_code"] != expected:
        raise ValueError("control oracle result identity changed")
    findings = {finding["code"] for observation in observations for finding in observation["findings"]}
    if any(observation["blockers"] for observation in observations):
        raise ValueError("unsupported control cannot substitute for an actual negative result")
    if code is None:
        if findings or any(observation["status"] != "pass" for observation in observations):
            raise ValueError("source-owned baseline did not pass")
    elif code not in findings or not any(observation["status"] == "fail" for observation in observations):
        raise ValueError("actual mutant omitted its source-defined diagnostic")


def _projection_pixels(
    pdf: bytes,
    pixels: tuple[bytes, ...],
    pages: tuple[Any, ...],
    recorded: dict[str, Any],
    reader: SnapshotReader,
    leaf: Path,
    *,
    run_id: str,
    custody: dict[str, str],
    deadline: float,
    env: dict[str, str],
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_validation import _file
    from infrastructure.reporting.native_projection_checks import inspect_projection
    from infrastructure.reporting.native_qr_runtime import replay_projection_qr_runtime

    if not isinstance(recorded.get("pages"), list) or len(recorded["pages"]) != len(pixels):
        raise ValueError("projected control omitted its complete native pages")
    for ordinal, page in enumerate(recorded["pages"], 1):
        if "qr" in page:
            qr = _keys(
                page["qr"],
                {
                    "raster_sha256",
                    "target",
                    "decoded",
                    "tool_artifact",
                    "runtime_artifact",
                    "original_exit_code",
                    "findings",
                    "status",
                },
            )
            runtime_file = _file(qr["runtime_artifact"], reader)
            decoded_file = _file(qr["tool_artifact"], reader)
            if (
                runtime_file.path != leaf / f"qr-runtime-{ordinal}.json"
                or decoded_file.path != leaf / f"qr-decode-{ordinal}.json"
            ):
                raise ValueError("QR control runtime belongs to another original attempt/page")
            consumed = reader.read((leaf / f"qr-page-{ordinal}.png").relative_to(reader.root).as_posix())
            if consumed.content != pixels[ordinal - 1] or qr["raster_sha256"] != consumed.sha256:
                raise ValueError("original QR decoder consumed different native raster bytes")
            replay_projection_qr_runtime(
                page["qr"],
                read_artifact=lambda binding: _file(binding, reader).content,
                producer_path=lambda relative: str(producer_path(custody, reader.root, reader.root / relative)),
                run_id=run_id,
            )
    with tempfile.TemporaryDirectory(prefix="native-control-pixels-") as temporary:
        root = Path(temporary).resolve()
        directory = root / "output/readiness/qr"
        directory.mkdir(parents=True)
        independent = inspect_projection(
            pdf, pixels, pages, deadline=deadline, native_context=(root, directory, env, run_id)
        )
    left, right = copy.deepcopy(recorded), copy.deepcopy(independent)
    for observation in (left, right):
        for page in observation["pages"]:
            if "qr" in page:
                page["qr"].pop("tool_artifact", None)
                page["qr"].pop("runtime_artifact", None)
    if left != right:
        raise ValueError("independent projected control geometry/decoded pixels differ")
    return independent


def _validate_control_candidate_run_diagnostic(raw: dict[str, Any], run_id: str) -> None:
    """Check candidate DATA only, after the caller's unchanged custody gate."""
    if raw["run_id"] != run_id or raw["diagnostic"] != "":
        raise ValueError("native control tool run or custody diagnostic changed")


def _closure(
    raw: object,
    reader: SnapshotReader,
    directory: Path,
    run_id: str,
    seen: set[str] | None = None,
    tool_binding: dict[str, str] | None = None,
) -> None:
    """Admit every retained binding, including nested tools and frozen engines."""
    from infrastructure.reporting.native_format_acceptance_contracts import (
        TOOL_SCHEMA,
        TOOL_FIELDS,
        CITATION_TOOL_FIELDS,
        HTML_TOOL_FIELDS,
    )
    from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
    from infrastructure.reporting.native_format_acceptance_validation import _file

    seen = set() if seen is None else seen
    if isinstance(raw, list):
        for item in raw:
            _closure(item, reader, directory, run_id, seen)
    elif isinstance(raw, dict):
        strict = {
            "template-native-qr-core-v1": set(
                "schema_version ordinal executable executable_sha256 core_path "
                "linked_core_path core_sha256 core_bytes core_artifact version_artifact loader_artifact".split()
            ),
            "template-native-epubcheck-engine-v1": {"schema_version", "java", "jar", "files"},
            "template-native-epub-reader-v2": set(
                "schema_version input pdf observation engine consumed_jar "
                "consumed_jars tool_artifacts reader_environment_artifact "
                "reader_runtime_before reader_runtime_after status blockers".split()
            ),
            "template-native-epub-reader-v3": set(
                "schema_version input pdf observation engine consumed_jar "
                "consumed_jars tool_artifacts reader_environment_artifact "
                "reader_runtime_before reader_runtime_after status blockers linux_calibre_selection".split()
            ),
        }
        if raw.get("schema_version") in strict:
            _keys(raw, strict[raw["schema_version"]])
        if raw.get("schema_version") == "template-native-epubcheck-engine-v1":
            for row in raw["files"]:
                _keys(row, {"category", "path", "sha256", "bytes"})
        if raw.get("schema_version") == TOOL_SCHEMA:
            if frozenset(raw) not in {TOOL_FIELDS, CITATION_TOOL_FIELDS, HTML_TOOL_FIELDS} or tool_binding is None:
                raise ValueError("native control tool lacks its exact shared original receipt fields/binding")
            from infrastructure.reporting.native_format_acceptance_validation import _tool

            _tool(
                tool_binding, reader, run_id, raw["tool"], raw["purpose"], raw["command"][1:], raw["original_exit_code"]
            )
            _validate_control_candidate_run_diagnostic(raw, run_id)
            for field in ("executable_observation_before", "executable_observation_after"):
                validate_executable_observation(raw[field], raw["executable"], raw["executable_sha256"])
            # The existing native tool reader authenticates the original OS
            # process, raw streams, source/SDK closure and nested custody. The
            # enclosing specialized reader still reconstructs required argv.
            return
        if set(raw) == {"path", "sha256"}:
            snapshot = _file(raw, reader)
            if not snapshot.path.is_relative_to(directory):
                shared = reader.root / "output/readiness/native-reader-runtimes" / run_id
                manifest = snapshot.json_object()
                if (
                    snapshot.path != shared / f"{manifest.get('digest')}.json"
                    or manifest.get("schema_version") != "template-native-reader-runtime-v1"
                ):
                    raise ValueError("native control binding escaped original confined control closure")
            if snapshot.relative not in seen and snapshot.path.suffix == ".json":
                seen.add(snapshot.relative)
                _closure(snapshot.json_object(), reader, directory, run_id, seen, raw)
        else:
            for item in raw.values():
                _closure(item, reader, directory, run_id, seen)


def _pixels(raster: dict[str, Any], reader: SnapshotReader) -> tuple[bytes, ...]:
    from infrastructure.reporting.native_format_acceptance_validation import _file

    _keys(raster, {"dpi", "input_artifact", "rasters", "tool_artifacts"})
    for row in raster["rasters"]:
        _keys(row, {"path", "sha256", "width_px", "height_px", "variance"})
    return tuple(_file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in raster["rasters"])


def _office_members(content: bytes) -> dict[str, bytes]:
    """Exact uncompressed member bytes; ZIP envelope time/compression are transport."""
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = archive.namelist()
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if (
                not item.filename
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in item.filename
                or "\0" in item.filename
                or str(path) != item.filename.rstrip("/")
                or stat.S_ISLNK(item.external_attr >> 16)
            ):
                raise ValueError("unsafe Office fixture member")
        if len(names) != len(set(names)) or sum(row.file_size for row in archive.infolist()) > 64 * 1024 * 1024:
            raise ValueError("ambiguous or oversized Office fixture")
        return {name: archive.read(name) for name in names}


def _office(
    kind: str,
    name: str,
    leaf: Path,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
) -> dict[str, Any]:
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster, _tool
    from infrastructure.reporting.native_format_observer_source_replay import replay_office_conversion
    from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
    from infrastructure.reporting.native_office_observer import reconstruct_office_control_fixture

    _keys(raw, {"schema_version", "kind", "name", "expected_code", "parser", "layout", "oracle_exit_code"})
    layout = _keys(raw["layout"], {"conversion", "raster", "observation", "status"})
    _keys(
        layout["conversion"],
        {
            "schema_version",
            "kind",
            "input",
            "pdf",
            "observation",
            "tool_artifacts",
            "reader_runtime_before",
            "reader_runtime_after",
            "status",
            "blockers",
        },
    )
    if layout["conversion"]["status"] != "blocked" or layout["conversion"]["blockers"] != [
        "complete source/layout and valid visual controls required"
    ]:
        raise ValueError("Office conversion-only result was improperly promoted")
    consumed = _file(layout["conversion"]["input"], reader)
    fixture = reader.read((leaf / f"fixture.{kind}").relative_to(reader.root).as_posix())
    if fixture.content != consumed.content or raw["parser"] != parse_native_bytes(kind, fixture.content):
        raise ValueError("Office control consumed another fixture or parser result")
    fixture_env = dict(env)
    if kind == "docx":
        # Pandoc's source-defined clock fields are reconstructed at the retained
        # original instant; every XML/media/relationship byte is still compared.
        core = fromstring(_office_members(fixture.content)["docProps/core.xml"])
        if core.tag != "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}coreProperties":
            raise ValueError("DOCX core clock namespace differs")
        for node in core:
            if node.tag in {"{http://purl.org/dc/terms/}created", "{http://purl.org/dc/terms/}modified"}:
                if node.attrib != {"{http://www.w3.org/2001/XMLSchema-instance}type": "dcterms:W3CDTF"}:
                    raise ValueError("DOCX source clock attributes differ")
        times = [
            node.text
            for node in core
            if node.tag in {"{http://purl.org/dc/terms/}created", "{http://purl.org/dc/terms/}modified"}
        ]
        if len(times) != 2 or times[0] != times[1] or not isinstance(times[0], str):
            raise ValueError("invalid original Pandoc clock metadata")
        instant = datetime.strptime(times[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if instant.strftime("%Y-%m-%dT%H:%M:%SZ") != times[0]:
            raise ValueError("DOCX source clock timestamp is not canonical UTC")
        fixture_env["SOURCE_DATE_EPOCH"] = str(int(instant.timestamp()))
    with tempfile.TemporaryDirectory(prefix="native-office-fixture-") as temporary:
        root = Path(temporary).resolve()
        directory = root / "output/readiness/fixture"
        directory.mkdir(parents=True)
        regenerated, contract, pages, producer = reconstruct_office_control_fixture(
            root, directory, kind, name, env=fixture_env, deadline=deadline, run_id=run_id
        )
        if _office_members(regenerated) != _office_members(fixture.content):
            raise ValueError("Office mutant package differs from exact source-owned fixture members")
        if kind == "docx":
            if producer is None:
                raise ValueError("reader did not actually reconstruct source DOCX")
            # Source text includes only the original producer overlay path.
            original_source = reader.read((leaf / "fixture.md").relative_to(reader.root).as_posix())
            source = (directory / "fixture.md").read_bytes()
            local_overlay = str(directory / "native-overlay.png").encode()
            original_overlay = str(producer_path(custody, reader.root, leaf / "native-overlay.png")).encode()
            if source.replace(local_overlay, original_overlay) != original_source.content:
                raise ValueError("DOCX fixture source differs from original source-defined input")
            if name == "opaque-overlay":
                retained = reader.read((leaf / "native-overlay.png").relative_to(reader.root).as_posix())
                if retained.content != (directory / "native-overlay.png").read_bytes():
                    raise ValueError("DOCX producer overlay input differs from source-owned exact pixels")
            tool_path = leaf / "docx-control-producer.json"
            # native_tool_record's stable source-owned purpose filename.
            _closure(
                {
                    "path": str(tool_path.relative_to(reader.root)),
                    "sha256": reader.read(str(tool_path.relative_to(reader.root))).sha256,
                },
                reader,
                leaf.parent,
                run_id,
            )
            _tool(
                {
                    "path": str(tool_path.relative_to(reader.root)),
                    "sha256": reader.read(str(tool_path.relative_to(reader.root))).sha256,
                },
                reader,
                run_id,
                "pandoc",
                "docx-control-producer",
                [
                    str(producer_path(custody, reader.root, original_source.path)),
                    "--standalone",
                    "-o",
                    str(producer_path(custody, reader.root, fixture.path)),
                ],
            )
    pdf = replay_office_conversion(
        reader.root, leaf, fixture, layout["conversion"], reader, run_id=run_id, custody=custody
    )
    _raster(
        {"raster": layout["raster"], "observation": layout["conversion"]["observation"]},
        pdf,
        0,
        leaf,
        reader,
        run_id,
        versions,
        custody,
    )
    pixels = _pixels(layout["raster"], reader)
    if kind == "docx":
        if contract is None or layout["observation"] != (
            fresh_observation := inspect_pdf_content(pdf.content, pixels, contract, deadline=deadline)
        ):
            raise ValueError("independent DOCX source/glyph/layout/pixel control differs")
    else:
        fresh_observation = _projection_pixels(
            pdf.content,
            pixels,
            pages,
            layout["observation"],
            reader,
            leaf,
            run_id=run_id,
            custody=custody,
            deadline=deadline,
            env=env,
        )
    if layout["status"] != layout["observation"]["status"]:
        raise ValueError("Office control layout summary differs")
    return fresh_observation


def validate_format_controls(
    rawcontrols: dict[str, Any],
    formats: tuple[str, ...],
    reader: SnapshotReader,
    directory: Path,
    *,
    run_id: str,
    scope: str | None = None,
    custody: dict[str, str],
    runtime: dict[str, Any],
    versions: dict[str, dict[str, Any]],
    deadline: float,
    env: dict[str, str],
    original_deadline: float,
) -> dict[str, Any]:
    """Replay complete ordered source suites, independently from original process exits."""
    from infrastructure.reporting.native_format_acceptance_validation import _file, _raster
    from infrastructure.reporting.native_epub_observer import (
        EPUB_CONTROL_CODES,
        epub_control_bytes,
        inspect_epub_spine,
        inspect_epub_reader_layout,
    )
    from infrastructure.reporting.native_epub_replay import replay_epub_conversion
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool
    from infrastructure.reporting.native_office_observer import OFFICE_CONTROL_CODES, PPTX_CONTROL_CODES
    from infrastructure.reporting.native_projection_checks import PROJECTION_CONTROL_CODES, projection_control_fixture

    if type(original_deadline) not in {int, float} or not math.isfinite(original_deadline) or original_deadline <= 0:
        raise ValueError("original native control deadline lacks admitted specification custody")
    if (
        not formats
        or len(set(formats)) != len(formats)
        or set(formats) - {"pdf", "html", "docx", "epub", "pptx", "slides"}
    ):
        raise ValueError("unknown or duplicate native format selection")
    selected = {"schema_version"}
    if "html" in formats:
        selected.update({"html", "html_semantic"})
    for kind in ("docx", "epub"):
        if kind in formats:
            selected.add(kind)
    if "slides" in formats or "pptx" in formats:
        selected.update({"projection", "pptx"})
    if "slides" in formats:
        selected.add("slide_source")
    _keys(rawcontrols, selected)
    if rawcontrols["schema_version"] != SCHEMA or not math.isfinite(deadline) or deadline <= time.monotonic():
        raise ValueError("invalid or exhausted native control replay contract")
    # HTML control replay is independently owned and invoked by the enclosing
    # reader; this module owns Office, EPUB and projected native controls.
    results: dict[str, Any] = {}
    if "slide_source" in selected:
        if scope is None:
            raise ValueError("slide control replay requires the exact enclosing public Source scope")
        from infrastructure.reporting.native_slide_control_adapter import replay_slide_source_controls

        results["manuscript_slides"] = replay_slide_source_controls(
            rawcontrols["slide_source"],
            reader,
            directory,
            scope=scope,
            run_id=run_id,
            custody=custody,
            runtime=runtime,
            versions=versions,
            original_deadline=original_deadline,
            deadline=deadline,
            env=env,
        )
    suites = {
        "docx": OFFICE_CONTROL_CODES,
        "epub": EPUB_CONTROL_CODES,
        "projection": PROJECTION_CONTROL_CODES,
        "pptx": PPTX_CONTROL_CODES,
    }
    for kind, codes in suites.items():
        if kind not in selected:
            continue
        records = rawcontrols[kind]
        if not isinstance(records, list) or [row.get("name") for row in records if isinstance(row, dict)] != list(
            codes
        ):
            raise ValueError("incomplete, duplicated, unknown or reordered native control suite")
        checked: list[dict[str, Any]] = []
        for ordinal, (item, (name, code)) in enumerate(zip(records, codes.items(), strict=True)):
            projection = kind == "projection"
            fields = (
                {"name", "original_exit_code", "tool_artifact", "result"}
                if projection
                else {"name", "original_exit_code", "process_artifact", "artifact"}
            )
            if kind in {"docx", "pptx"}:
                fields.add("kind")
            _keys(item, fields)
            leaf = directory / (f"control-{ordinal}" if projection else f"{kind}-control-{ordinal}")
            result = _file(item["result" if projection else "artifact"], reader)
            if result.path != leaf / "observation.json":
                raise ValueError("native control result belongs to another original attempt")
            raw = result.json_object()
            _closure(raw, reader, directory, run_id)
            schema_kind = "office" if kind in {"docx", "pptx"} else kind
            if (
                raw.get("schema_version") != f"template-native-{schema_kind}-valid-control-v1"
                or raw.get("name") != name
                or raw.get("expected_code") != code
                or kind in {"docx", "pptx"}
                and (raw.get("kind") != kind or item["kind"] != kind)
            ):
                raise ValueError("native control source contract identity differs")
            extra = None
            if kind == "epub":
                conversion = raw["conversion"]
                engine = conversion["engine"]
                private = Path(conversion["consumed_jar"]["path"]).parent
                extra = [
                    "--epubcheck-jar",
                    engine["jar"],
                    "--java-executable",
                    engine["java"],
                    "--frozen-engine",
                    str(producer_path(custody, reader.root, reader.root / private)),
                ]
            _supervision(
                item,
                leaf,
                kind,
                name,
                0 if code is None else 1,
                reader,
                run_id,
                custody,
                runtime,
                original_deadline,
                extra,
            )
            if kind in {"docx", "pptx"}:
                fresh_observation = _office(
                    kind,
                    name,
                    leaf,
                    raw,
                    reader,
                    run_id=run_id,
                    custody=custody,
                    versions=versions,
                    deadline=deadline,
                    env=env,
                )
                _outcome(raw, [raw["layout"]["observation"]], code)
            elif projection:
                _keys(
                    raw,
                    {
                        "schema_version",
                        "name",
                        "expected_code",
                        "input",
                        "parser",
                        "raster",
                        "observation",
                        "oracle_exit_code",
                    },
                )
                source = _file(raw["input"], reader)
                fixture, pages = projection_control_fixture(name)
                if (
                    source.path != leaf / "control.pdf"
                    or source.content != fixture
                    or raw["parser"] != parse_native_bytes("pdf", fixture)
                ):
                    raise ValueError("projection mutant differs from exact source fixture/parser")
                _raster(
                    {"raster": raw["raster"], "observation": raw["parser"]},
                    source,
                    0,
                    leaf,
                    reader,
                    run_id,
                    versions,
                    custody,
                )
                pixels = _pixels(raw["raster"], reader)
                fresh_observation = _projection_pixels(
                    fixture,
                    pixels,
                    pages,
                    raw["observation"],
                    reader,
                    leaf,
                    run_id=run_id,
                    custody=custody,
                    deadline=deadline,
                    env=env,
                )
                _outcome(raw, [raw["observation"]], code)
            else:
                _keys(
                    raw,
                    {
                        "schema_version",
                        "name",
                        "expected_code",
                        "conversion",
                        "raster",
                        "spine",
                        "layout",
                        "oracle_exit_code",
                    },
                )
                fixture, chapters = epub_control_bytes(name)
                conversion = raw["conversion"]
                if conversion["status"] != "blocked" or conversion["blockers"] != [
                    "complete spine/source/layout and valid reader visual controls required"
                ]:
                    raise ValueError("EPUB conversion-only result was improperly promoted")
                source = _file(conversion["input"], reader)
                if source.path != leaf / "input.epub" or source.content != fixture:
                    raise ValueError("EPUB mutant differs from exact source fixture")
                replay_epub_conversion(
                    conversion,
                    fixture,
                    read_artifact=lambda binding: _file(binding, reader).content,
                    authenticate_tool=lambda binding, tool: validate_original_native_tool(
                        binding, tool, reader, run_id=run_id
                    ),
                    producer_path=lambda relative: str(producer_path(custody, reader.root, reader.root / relative)),
                    run_id=run_id,
                )
                pdf = _file(conversion["pdf"], reader)
                _raster(
                    {"raster": raw["raster"], "observation": conversion["observation"]},
                    pdf,
                    0,
                    leaf,
                    reader,
                    run_id,
                    versions,
                    custody,
                )
                pixels = _pixels(raw["raster"], reader)
                fresh_spine = inspect_epub_spine(fixture, chapters)
                fresh_layout = inspect_epub_reader_layout(pdf.content, pixels, chapters, deadline=deadline)
                if raw["spine"] != fresh_spine or raw["layout"] != fresh_layout:
                    raise ValueError("independent EPUB ordered spine/layout/pixel control differs")
                _outcome(raw, [raw["spine"], raw["layout"]], code)
                fresh_observation = {"spine": fresh_spine, "layout": fresh_layout}
            checked.append(
                {
                    "name": name,
                    "original_exit_code": item["original_exit_code"],
                    "reconstructed_exit_code": 0 if code is None else 1,
                    "intended_diagnostic": code,
                    "targets": [{"fixture": kind, "name": name}],
                    "artifact": item["result" if projection else "artifact"],
                    "observation": fresh_observation,
                }
            )
        results[kind] = {"suite_id": kind, "scope": scope, "original_run_id": run_id, "outcomes": checked}
    if not reader.unchanged():
        raise ValueError("native control closure changed during independent replay")
    return results
