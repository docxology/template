"""Fresh source-only glyph native launches and portable byte/command custody."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import (
    atomic_write_bytes_confined,
    read_bytes_confined,
)
from infrastructure.core.execution_boundary import run_bounded_subprocess
from infrastructure.project.public_acceptance_evidence import bootstrap_command
from infrastructure.reporting.native_format_acceptance_checks import (
    native_tool_record,
    parse_native_bytes,
)
from infrastructure.reporting.native_format_browser_runtime import validate_runtime
from infrastructure.reporting.native_format_html_child_custody import (
    html_child_custodian,
    prepare_html_child_launch,
    validate_retained_html_child,
)
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.native_format_html_font_provider import HTMLFontProvider
from infrastructure.reporting.native_format_html_font_driver_adapter import (
    bind_html_font_driver,
    replay_html_font_driver,
)
from infrastructure.reporting.native_format_html_glyph_reference import (
    GLYPH_REFERENCE_SCRIPT,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    binding,
    remaining_seconds,
)
from infrastructure.reporting.native_format_portable_custody import (
    producer_path,
    validate_executable_observation,
)
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import (
    SnapshotReader,
    json_object_from_bytes,
)

PROBE_MODULE = "infrastructure.reporting.native_format_html_platform_font_probe"


def _sdk() -> tuple[Path, SnapshotReader]:
    root = Path(__file__).absolute().parents[2]
    return root, SnapshotReader(root, native_producer_operation=current_native_producer_operation())


def _reference_result(result: dict[str, Any], pixels: bytes, programs: dict[str, str], width: int) -> None:
    """Actual application/executable exits and complete pixel bytes, no JSON authority."""
    executable = result["browser_command"][0]
    if (
        result.get("browser_original_exit") != 0
        or result.get("screenshot_sha256") != hashlib.sha256(pixels).hexdigest()
    ):
        raise ValueError("source-only reference lost genuine browser exit0 or exact screenshot bytes")
    if (
        result.get("runtime_observer_sha256") != programs["native_format_browser_runtime.py"]
        or result.get("platform_font_observer_sha256") != programs["native_format_html_platform_font_dom.py"]
    ):
        raise ValueError("source-only reference used different admitted SDK runtime/font observers")
    before, after = (
        result["runtime_observation_before"],
        result["runtime_observation_after"],
    )
    if before != after:
        raise ValueError("source-only browser application bytes changed during real rendering")
    validate_runtime(before, executable, result["browser_sha256"])
    for key in ("executable_observation_before", "executable_observation_after"):
        validate_executable_observation(result[key], executable, result["browser_sha256"])
    if not isinstance(result.get("asset_origin"), str) or not re.fullmatch(
        r"http://127\.0\.0\.1:[1-9][0-9]{0,4}", result["asset_origin"]
    ):
        raise ValueError("source-only reference lacks its fresh bounded loopback origin")
    size = parse_native_bytes("png", pixels)
    if size["width_px"] != width or size["height_px"] < result["dom"]["height"]:
        raise ValueError("source-only reference omitted complete original native geometry")


def _browser_args(directory: Path, chrome: str, width: int, deadline: float) -> list[str]:
    return [
        str(directory / "browser-driver.py"),
        "--chrome",
        chrome,
        "--source",
        str(directory / "source.html"),
        "--profile",
        str(directory / "profile"),
        "--width",
        str(width),
        "--output",
        str(directory / "reference.json"),
        "--deadline",
        str(deadline),
        "--observer-script",
        str(directory / "observer.js"),
        "--asset-root",
        str(directory),
        "--platform-font-observer",
        str(directory / "native_format_html_platform_font_dom.py"),
    ]


def observe_font_probe(
    root: Path,
    directory: Path,
    request: dict[str, Any],
    reader: SnapshotReader,
    *,
    provider: HTMLFontProvider,
    env: dict[str, str],
    deadline: float,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    remaining_seconds(deadline)
    provider.validate_request(request, deadline=deadline)
    sdk_root, sdk_reader = _sdk()
    sdk_source = sdk_reader.read(PROBE_MODULE.replace(".", "/") + ".py")
    path = directory / "font-request.json"
    atomic_write_bytes_confined(
        root,
        path,
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode(),
        mode=0o600,
    )
    consumed = reader.read(path.relative_to(root).as_posix())
    command = bootstrap_command(
        Path(sys.executable),
        sdk_root,
        PROBE_MODULE,
        "--request",
        str(path),
        "--deadline",
        str(deadline),
    )
    tool = native_tool_record(
        root,
        directory,
        sys.executable,
        list(command[1:]),
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose="html-source-font-probe",
    )
    from infrastructure.reporting.native_format_acceptance_evidence import _tool

    transcript = _tool(
        tool["artifact"],
        reader,
        run_id,
        sys.executable,
        "html-source-font-probe",
        list(command[1:]),
    )
    probe = json_object_from_bytes(transcript["stdout"].encode())
    provider.validate_probe(request, probe, deadline=deadline)
    if not reader.unchanged() or not sdk_reader.unchanged():
        raise ValueError("source font probe SDK/request/native evidence changed")
    evidence = {
        "request": binding(consumed),
        "source": binding(sdk_source),
        "tool": tool,
        "probe": probe,
        "deadline_monotonic": deadline,
    }
    remaining_seconds(deadline)
    return probe, evidence


def replay_font_probe(
    root: Path,
    directory: Path,
    request: dict[str, Any],
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    provider: HTMLFontProvider,
    env: dict[str, str],
    deadline: float,
    work: Path,
) -> dict[str, Any]:
    """Authenticate original probe, then execute the reader's own actual probe."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool

    remaining_seconds(deadline)
    sdk_root, sdk_reader = _sdk()
    source = sdk_reader.read(PROBE_MODULE.replace(".", "/") + ".py")
    consumed = _file(raw["request"], reader)
    content = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    if (
        consumed.path != directory / "font-request.json"
        or consumed.content != content
        or raw["source"] != binding(source)
    ):
        raise ValueError("original source font probe request/SDK byte binding differs")
    original_deadline = raw["deadline_monotonic"]
    if type(original_deadline) not in {int, float} or not math.isfinite(original_deadline):
        raise ValueError("source font probe omitted original deadline")
    # Only labels are projected. No producer font path or program is read.
    implementation = Path(custody["implementation_root"])
    command = bootstrap_command(
        Path(runtime["executable"]),
        sdk_root,
        PROBE_MODULE,
        "--request",
        str(producer_path(custody, root, consumed.path)),
        "--deadline",
        str(original_deadline),
        command_root=implementation.parent,
        implementation_root=implementation,
    )
    transcript = _tool(
        raw["tool"]["artifact"],
        reader,
        run_id,
        runtime["executable"],
        "html-source-font-probe",
        list(command[1:]),
    )
    if json_object_from_bytes(transcript["stdout"].encode()) != raw["probe"]:
        raise ValueError("retained platform probe differs from genuine original stdout")
    local = work / "font-request.json"
    local.write_bytes(content)
    command = bootstrap_command(
        Path(sys.executable),
        sdk_root,
        PROBE_MODULE,
        "--request",
        str(local),
        "--deadline",
        str(deadline),
    )
    process = run_bounded_subprocess(command, cwd=work, env=env, timeout=remaining_seconds(deadline))
    if process.returncode != 0 or process.original_returncode != 0 or process.timed_out or process.custody_refused:
        raise ValueError("independent local source font probe did not preserve original exit0")
    independent = json_object_from_bytes(process.stdout.encode())
    provider.validate_probe(request, independent, deadline=deadline)
    original_fonts = [
        (
            row["postscript_name"],
            row["characters"],
            row["font_sha256"],
            row["glyph_ids"],
        )
        for row in raw["probe"]["fonts"]
    ]
    local_fonts = [
        (
            row["postscript_name"],
            row["characters"],
            row["font_sha256"],
            row["glyph_ids"],
        )
        for row in independent["fonts"]
    ]
    if original_fonts != local_fonts or independent["request_sha256"] != raw["probe"]["request_sha256"]:
        raise ValueError(
            "independent local font bytes/source codepoint glyphs differ from original native font evidence"
        )
    if not reader.unchanged() or not sdk_reader.unchanged():
        raise ValueError("source font reader SDK/original evidence changed during replay")
    remaining_seconds(deadline)
    return independent


def observe_glyph_reference(
    root: Path,
    directory: Path,
    page: bytes,
    width: int,
    reader: SnapshotReader,
    *,
    chrome: str,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    observer_script: str = GLYPH_REFERENCE_SCRIPT,
) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    remaining_seconds(deadline)
    _, sdk_reader = _sdk()
    programs = {}
    for name, target_name in (
        ("native_format_browser_driver.py", "browser-driver.py"),
        ("native_format_browser_runtime.py", "native_format_browser_runtime.py"),
    ):
        source = sdk_reader.read("infrastructure/reporting/" + name)
        atomic_write_bytes_confined(root, directory / target_name, source.content, mode=0o600)
        programs[name] = source.sha256
        reader.read((directory / target_name).relative_to(root).as_posix())
    font = bind_html_font_driver(root, directory, reader, deadline=deadline)
    programs["native_format_html_platform_font_dom.py"] = font["source"]["sha256"]
    source_path, script_path = directory / "source.html", directory / "observer.js"
    atomic_write_bytes_confined(root, source_path, page, mode=0o600)
    atomic_write_bytes_confined(root, script_path, observer_script.encode(), mode=0o600)
    source, script = (
        reader.read(source_path.relative_to(root).as_posix()),
        reader.read(script_path.relative_to(root).as_posix()),
    )
    args = _browser_args(directory, chrome, width, deadline)
    with html_child_custodian(directory, directory, deadline=deadline, artifact_root=root):
        tool = native_tool_record(
            root,
            directory,
            sys.executable,
            args,
            env=env,
            deadline=deadline,
            run_id=run_id,
            purpose="html-source-glyph-reference",
        )
    from infrastructure.reporting.native_format_acceptance_evidence import _tool

    _tool(
        tool["artifact"],
        reader,
        run_id,
        sys.executable,
        "html-source-glyph-reference",
        args,
    )
    native = reader.read((directory / "reference.json").relative_to(root).as_posix())
    pixels = reader.read((directory / "reference.png").relative_to(root).as_posix())
    result = native.json_object()
    _reference_result(result, pixels.content, programs, width)
    replay_html_font_driver(root, directory, reader, font, result, deadline=deadline)
    if not reader.unchanged() or not sdk_reader.unchanged():
        raise ValueError("source-only reference original Source/SDK/native evidence changed")
    evidence = {
        "source": binding(source),
        "script": binding(script),
        "programs": programs,
        "font_observer": font,
        "native": binding(native),
        "pixels": binding(pixels),
        "tool": tool,
        "deadline_monotonic": deadline,
    }
    remaining_seconds(deadline)
    return result["dom"], pixels.content, evidence


def replay_glyph_reference(
    root: Path,
    directory: Path,
    page: bytes,
    width: int,
    raw: dict[str, Any],
    reader: SnapshotReader,
    *,
    run_id: str,
    custody: dict[str, str],
    runtime: dict[str, Any],
    env: dict[str, str],
    deadline: float,
    work: Path,
    chrome: str,
    observer_script: str = GLYPH_REFERENCE_SCRIPT,
) -> tuple[dict[str, Any], bytes]:
    """Retained producer pixels are authenticated, never used as expected ink."""
    from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool

    remaining_seconds(deadline)
    _, sdk_reader = _sdk()
    programs = {}
    for name, target_name in (
        ("native_format_browser_driver.py", "browser-driver.py"),
        ("native_format_browser_runtime.py", "native_format_browser_runtime.py"),
        (
            "native_format_html_platform_font_dom.py",
            "native_format_html_platform_font_dom.py",
        ),
    ):
        source = sdk_reader.read("infrastructure/reporting/" + name)
        copy = reader.read((directory / target_name).relative_to(root).as_posix())
        if copy.content != source.content:
            raise ValueError("retained source-only reference SDK copy differs")
        programs[name] = source.sha256
        (work / target_name).write_bytes(source.content)
    source, script = _file(raw["source"], reader), _file(raw["script"], reader)
    native, pixels = _file(raw["native"], reader), _file(raw["pixels"], reader)
    if (
        source.path != directory / "source.html"
        or source.content != page
        or script.path != directory / "observer.js"
        or script.content != observer_script.encode()
        or native.path != directory / "reference.json"
        or pixels.path != directory / "reference.png"
        or raw["programs"] != programs
    ):
        raise ValueError("source-only reference original scene/script/output/SDK differs")
    original = native.json_object()
    _reference_result(original, pixels.content, programs, width)
    replay_html_font_driver(root, directory, reader, raw["font_observer"], original, deadline=deadline)
    args = _browser_args(
        producer_path(custody, root, directory),
        original["browser_command"][0],
        width,
        raw["deadline_monotonic"],
    )
    _tool(
        raw["tool"]["artifact"],
        reader,
        run_id,
        runtime["executable"],
        "html-source-glyph-reference",
        args,
    )
    validate_retained_html_child(
        raw["tool"]["artifact"],
        original,
        programs,
        reader,
        custody=custody,
        deadline=deadline,
    )
    (work / "source.html").write_bytes(page)
    (work / "observer.js").write_bytes(observer_script.encode())
    args = _browser_args(work, chrome, width, deadline)
    operation_deadline = min(deadline, time.monotonic() + 120)
    with html_child_custodian(work, work, deadline=deadline):
        prepared = prepare_html_child_launch([sys.executable, *args], env, operation_deadline)
        if prepared is None:
            raise ValueError("Source-only replay driver did not select its actual HTML child custodian")
        process = run_native_tool_process(
            work,
            sys.executable,
            args,
            cwd=work,
            env=prepared.environment,
            deadline=operation_deadline,
            purpose="reader-html-source-glyph-reference",
            preserve_nominated_launcher=True,
        )
        prepared.authenticate(process, caller_deadline=deadline)
        if process["original_exit_code"] != 0 or not process["accepted"] or process["timed_out"]:
            raise ValueError("independent Source-only browser reference did not preserve original signed OS exit0")
    actual = json_object_from_bytes(read_bytes_confined(work, work / "reference.json", max_bytes=32 * 1024 * 1024))
    local_pixels = read_bytes_confined(work, work / "reference.png", max_bytes=64 * 1024 * 1024)
    _reference_result(actual, local_pixels, programs, width)
    for name, target_name in (
        ("native_format_browser_driver.py", "browser-driver.py"),
        ("native_format_browser_runtime.py", "native_format_browser_runtime.py"),
        (
            "native_format_html_platform_font_dom.py",
            "native_format_html_platform_font_dom.py",
        ),
    ):
        copy_bytes = read_bytes_confined(work, work / target_name, max_bytes=1024 * 1024)
        if hashlib.sha256(copy_bytes).hexdigest() != programs[name]:
            raise ValueError("independent source-only reference consumed SDK copies changed")
    if not sdk_reader.unchanged() or not reader.unchanged():
        raise ValueError("independent source-only reference SDK/original evidence changed")
    remaining_seconds(deadline)
    return actual["dom"], local_pixels
