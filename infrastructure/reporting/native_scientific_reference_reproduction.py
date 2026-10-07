"""Fresh reader-local source compilation; original XDV never substitutes for ink."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
from datetime import datetime
from io import BytesIO
import json
import re
import os
import stat
import struct
import zlib
from pathlib import Path
import time
from typing import Any

from infrastructure.reporting.native_format_acceptance_checks import native_tool_record
from infrastructure.reporting.native_format_pdf_source import PDFSourceInputs
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_format_scientific_math import observe_scientific_math_reference
from infrastructure.reporting.native_scientific_reference_replay import (
    TOOL_FIELDS,
    replay_scientific_math_reference,
    strict_json_object,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def canonical_xdv(content: bytes) -> bytes:
    """Compare every render byte; retain the original non-rendering date comment.

    DVI pre=247,id=7,num4,den4,mag4,k1,comment[k]. Only the exact
    source-owned XeTeX clock string is projected; header and entire instruction
    stream, offsets, fonts and padding remain byte-identical requirements.
    """
    if len(content) < 44 or content[:2] != bytes([247, 7]) or content[14] != 29:
        raise ValueError("reference XDV preamble differs from source engine")
    if re.fullmatch(rb" XeTeX output [0-9]{4}\.[0-9]{2}\.[0-9]{2}:[0-9]{4}", content[15:44]) is None:
        raise ValueError("reference XDV source comment is unrecognized")
    datetime.strptime(content[15:44].decode("ascii"), " XeTeX output %Y.%m.%d:%H%M")
    return content[:15] + bytes(29) + content[44:]


MAX_RASTER_PAGES = 500
MAX_RASTER_BYTES = 256 * 1024 * 1024
MAX_RASTER_FILE_BYTES = 64 * 1024 * 1024
MAX_RASTER_PIXELS = 60_000_000


def _png_dimensions(header: bytes) -> tuple[int, int]:
    if (
        len(header) != 33
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[8:16] != b"\x00\x00\x00\x0dIHDR"
        or zlib.crc32(header[12:29]) != int.from_bytes(header[29:33], "big")
    ):
        raise ValueError("original raster lacks exact PNG IHDR")
    width, height = struct.unpack(">II", header[16:24])
    if not width or not height or width * height > MAX_RASTER_PIXELS:
        raise ValueError("original raster exceeds native pixel dimensions")
    return width, height


def _raster_file(root: Path, binding: dict[str, Any], *, deadline: float, scan: bool) -> dict[str, Any]:
    """Hold no-follow lexical ancestors and one bounded file during each scan."""
    from infrastructure.core.files.secure_write import (
        _close_all,
        _directory_identity_matches,
        _open_parent,
        _relative_target,
    )

    if time.monotonic() >= deadline:
        raise TimeoutError("original raster admission deadline exhausted")
    reader = SnapshotReader(root)
    path = reader.public_path(binding["path"])
    lexical_root, parts, name = _relative_target(root, path)
    parent, opened = _open_parent(lexical_root, parts, create=False)
    descriptor = -1
    try:
        descriptor = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(descriptor)
        identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
        if not stat.S_ISREG(before.st_mode) or not 33 <= before.st_size <= MAX_RASTER_FILE_BYTES:
            raise ValueError("original raster exceeds its bounded regular-file size")
        digest = hashlib.sha256()
        header = b""
        size = 0
        if scan:
            while chunk := os.read(descriptor, 65536):
                if time.monotonic() >= deadline:
                    raise TimeoutError("original raster scan deadline exhausted")
                size += len(chunk)
                if size > MAX_RASTER_FILE_BYTES or size > before.st_size:
                    raise ValueError("original raster changed or exceeds its byte budget")
                digest.update(chunk)
                header += chunk[: max(0, 33 - len(header))]
            if size != before.st_size or (binding["sha256"] is not None and digest.hexdigest() != binding["sha256"]):
                raise ValueError("original raster streaming size/SHA differs from exact binding")
        observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
        after = os.fstat(descriptor)
        if (
            (observed.st_dev, observed.st_ino) != (after.st_dev, after.st_ino)
            or identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            or not _directory_identity_matches(lexical_root, parts, parent, None)
        ):
            raise ValueError("original raster changed during confined streaming read")
        return {
            "binding": binding,
            "identity": identity,
            "bytes": before.st_size,
            "dimensions": _png_dimensions(header) if scan else None,
            "sha256": digest.hexdigest() if scan else None,
        }
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        _close_all(opened)


def admit_original_rasters(
    root: Path, bindings: Any, *, read_artifact: Callable[[dict[str, Any]], bytes], deadline: float
) -> list[dict[str, Any]]:
    """Admit metadata budgets before hashing/authentication or image allocation."""
    if not isinstance(bindings, list) or not 0 < len(bindings) <= MAX_RASTER_PAGES:
        raise ValueError("original reference raster count exceeds its finite page budget")
    paths = set()
    ordered = [binding.get("path") if isinstance(binding, dict) else None for binding in bindings]
    if any(not isinstance(path, str) for path in ordered) or ordered != sorted(str(path) for path in ordered):
        raise ValueError("original reference raster bindings are not ordered")
    identities = []
    total = 0
    for binding in bindings:
        if (
            not isinstance(binding, dict)
            or set(binding) != {"path", "sha256"}
            or not isinstance(binding["path"], str)
            or not isinstance(binding["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", binding["sha256"]) is None
            or binding["path"] in paths
        ):
            raise ValueError("original raster binding is ambiguous or duplicated")
        paths.add(binding["path"])
        metadata = _raster_file(root, binding, deadline=deadline, scan=False)
        total += metadata["bytes"]
        if total > MAX_RASTER_BYTES:
            raise ValueError("original raster encoded closure exceeds 256 MiB")
        identities.append(metadata)
    for metadata in identities:
        actual = _raster_file(root, metadata["binding"], deadline=deadline, scan=True)
        if actual["identity"] != metadata["identity"]:
            raise ValueError("original raster changed after budget admission")
        # Preserve enclosing caller authentication in addition to exact no-follow
        # streaming digest admission. Only one already-bounded page is materialized.
        authenticated = read_artifact(metadata["binding"])
        if (
            len(authenticated) != actual["bytes"]
            or hashlib.sha256(authenticated).hexdigest() != metadata["binding"]["sha256"]
        ):
            raise ValueError("original raster differs from callback-authenticated bytes")
        metadata["dimensions"] = actual["dimensions"]
    return identities


def reproduce_scientific_reference(
    root: Path,
    directory: Path,
    raw: dict[str, Any],
    ast_bytes: bytes,
    inputs: PDFSourceInputs,
    raster: dict[str, Any],
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    producer_path: Callable[[str], str],
    original_run_id: str,
    env: dict[str, str],
    timeout: float = 180,
) -> dict[str, Any]:
    """Independently recompile unchanged source, compare original native observations.

    Caller supplies independently authenticated original source/parser/native SDK
    context. The fresh reader uses current prepared tools, observes their bytes
    twice, and retains its own finite receipts; it never opens origin tool paths.
    """
    if not 0 < timeout <= 3600:
        raise ValueError("reader-local source replay requires a finite budget")
    deadline = time.monotonic() + timeout
    from infrastructure.core.implementation_custody import capture_implementation_custody

    if not isinstance(raster, dict) or set(raster) != {"rasters", "tool_artifact"}:
        raise ValueError("original source reference requires complete raster custody")
    raster_inputs = admit_original_rasters(root, raster["rasters"], read_artifact=read_artifact, deadline=deadline)
    sdk_before = capture_implementation_custody()["files"]
    original = replay_scientific_math_reference(
        raw,
        ast_bytes,
        inputs,
        read_artifact=read_artifact,
        producer_path=producer_path,
        run_id=original_run_id,
        deadline=deadline,
    )
    if set(raster) != {"rasters", "tool_artifact"} or not raster["rasters"]:
        raise ValueError("original source reference requires complete raster custody")
    process_bytes = read_artifact(raster["tool_artifact"])
    if hashlib.sha256(process_bytes).hexdigest() != raster["tool_artifact"]["sha256"]:
        raise ValueError("original raster process changed")
    process = strict_json_object(process_bytes)
    validate_executable_observation(
        process["executable_observation_before"], process["executable"], process["executable_sha256"]
    )
    validate_executable_observation(
        process["executable_observation_after"], process["executable"], process["executable_sha256"]
    )
    original_directory = str(Path(raw["source"]["path"]).parent)
    if (
        set(process) != TOOL_FIELDS
        or process["schema_version"] != "template-native-tool-execution-v2"
        or process["run_id"] != original_run_id
        or process["tool"] != "pdftoppm"
        or process["purpose"] != "scientific-reference-raster"
        or process["command"]
        != [
            process["executable"],
            "-png",
            "-r",
            "150",
            producer_path(raw["pdf"]["path"]),
            producer_path(original_directory + "/page"),
        ]
        or type(process["exit_code"]) is not int
        or process["exit_code"] != 0
        or type(process["original_exit_code"]) is not int
        or process["original_exit_code"] != 0
        or process["timed_out"] is not False
        or process["custody_refused"] is not False
        or process["diagnostic"] != ""
    ):
        raise ValueError("original raster command/outcome/custody differs")
    directory.mkdir(parents=True, exist_ok=False)
    reader_run_id = "reader-" + original_run_id
    current = observe_scientific_math_reference(
        root, directory, ast_bytes, inputs, env=env, deadline=deadline, run_id=reader_run_id
    )
    reader = SnapshotReader(root)
    local = replay_scientific_math_reference(
        current,
        ast_bytes,
        inputs,
        read_artifact=lambda binding: reader.read(binding["path"]).content,
        producer_path=lambda path: str(root) if path == "." else str(root / path),
        run_id=reader_run_id,
        deadline=deadline,
    )

    # Compare actual consumed package/font bytes without reopening old distribution
    # paths. Names and SHA identify every independently consumed frozen dependency.
    def dependencies(reference: dict[str, Any]) -> list[tuple[str, str, int]]:
        return sorted(
            (Path(row["resolved_path"]).name, row["sha256"], row["size_bytes"])
            for row in reference["dependencies_before"]
        )

    if dependencies(current) != dependencies(raw):
        raise ValueError("reader-local actual TeX/font dependency bytes differ from original reference")

    def semantic_glyphs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # PDF subset labels are generated per file. Preserve original complete
        # observations and compare semantic names after actual font-byte parity.
        return [
            {
                **row,
                "glyphs": [
                    {**glyph, "fontname": re.sub(r"^[A-Z]{6}\+", "", glyph["fontname"])} for glyph in row["glyphs"]
                ],
            }
            for row in rows
        ]

    if (
        semantic_glyphs(local["reference_glyphs"]) != semantic_glyphs(original["reference_glyphs"])
        or local["reference_vectors"] != original["reference_vectors"]
    ):
        raise ValueError("original native glyph/vector observation differs from source recompilation")
    for label in ("discovery", "final"):
        original_xdv = read_artifact(raw["backend_inputs"][label])
        local_xdv = reader.read(current["backend_inputs"][label]["path"]).content
        if canonical_xdv(original_xdv) != canonical_xdv(local_xdv):
            raise ValueError("original retained XDV differs from independently compiled native source bytes")
    raster_record = native_tool_record(
        root,
        directory,
        "pdftoppm",
        ["-png", "-r", "150", str(root / current["pdf"]["path"]), str(directory / "page")],
        env=env,
        deadline=deadline,
        run_id=reader_run_id,
        purpose="scientific-reference-raster",
    )
    process = json.loads(reader.read(raster_record["artifact"]["path"]).content)
    if (
        process["exit_code"] != 0
        or process["original_exit_code"] != 0
        or process["timed_out"]
        or process["custody_refused"]
        or process["diagnostic"] != ""
    ):
        raise ValueError("reader-local source raster did not complete")
    paths = sorted(directory.glob("page-*.png"))
    if len(paths) != len(raster_inputs) or len(paths) != len(original["reference_vectors"]):
        raise ValueError("source reference raster pages are incomplete")
    from PIL import Image, ImageChops

    bindings = []
    for index, (path, original_input) in enumerate(zip(paths, raster_inputs, strict=True), 1):
        original_binding = original_input["binding"]
        if original_binding["path"] != original_directory + f"/page-{index:0{len(str(len(paths)))}d}.png":
            raise ValueError("original raster role/page identity differs from exact command")
        fresh = _raster_file(root, original_binding, deadline=deadline, scan=True)
        if fresh["identity"] != original_input["identity"]:
            raise ValueError("original raster changed before complete ink comparison")
        original_pixels = read_artifact(original_binding)
        if (
            len(original_pixels) != original_input["bytes"]
            or hashlib.sha256(original_pixels).hexdigest() != original_binding["sha256"]
        ):
            raise ValueError("original callback-authenticated raster changed")
        if path.name != f"page-{index:0{len(str(len(paths)))}d}.png":
            raise ValueError("source reference raster page order differs")
        actual_binding = {"path": path.relative_to(root).as_posix(), "sha256": None}
        actual_input = _raster_file(root, actual_binding, deadline=deadline, scan=True)
        actual_binding["sha256"] = actual_input["sha256"]
        snapshot = reader.read(path.relative_to(root).as_posix())
        with Image.open(BytesIO(snapshot.content)) as actual, Image.open(BytesIO(original_pixels)) as expected:
            if (
                actual.format != "PNG"
                or expected.format != "PNG"
                or actual.size != actual_input["dimensions"]
                or expected.size != original_input["dimensions"]
                or actual.size != expected.size
                or actual.width * actual.height > 60_000_000
                or ImageChops.difference(actual.convert("RGB"), expected.convert("RGB")).getbbox() is not None
            ):
                raise ValueError("original native reference ink differs from independent source pixels")
        bindings.append({"path": snapshot.relative, "sha256": snapshot.sha256})
    for original_input in raster_inputs:
        if (
            _raster_file(root, original_input["binding"], deadline=deadline, scan=False)["identity"]
            != original_input["identity"]
        ):
            raise ValueError("original raster path changed during independent replay")
    sdk_after = capture_implementation_custody()["files"]
    if sdk_before != sdk_after or not reader.unchanged() or time.monotonic() >= deadline:
        raise ValueError("reader-local source replay changed or exhausted its finite budget")
    return {
        "schema_version": "template-native-scientific-reference-reproduction-v1",
        "original_observation": original,
        "reader_reference": current,
        "reader_raster": {"rasters": bindings, "tool_artifact": raster_record["artifact"]},
        "reader_budget_seconds": timeout,
        "reader_sdk_before": sdk_before,
        "reader_sdk_after": sdk_after,
        "blockers": original["blockers"],
        "status": "blocked" if original["blockers"] else "pass",
    }
