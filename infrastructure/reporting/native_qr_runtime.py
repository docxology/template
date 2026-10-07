"""Observe the actual linked QR core; portable receipts retain hashes, never binaries."""

from __future__ import annotations

import hashlib
import stat
import re
import sys
from pathlib import Path, PurePosixPath
from collections.abc import Callable
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.public_acceptance_evidence import write_json
from infrastructure.reporting.native_format_acceptance_checks import native_tool_record, NativeToolUnavailable
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes
from infrastructure.reporting.native_format_acceptance_contracts import TOOL_SCHEMA
from infrastructure.reporting.native_format_portable_custody import EXECUTABLE_SCHEMA


def bind_qr_core(
    root: Path, directory: Path, *, env: dict[str, str], deadline: float, run_id: str, ordinal: int
) -> tuple[dict[str, Any], Path, bytes]:
    """Observe native loader metadata and retain original linked-core file observations without binary redistribution."""
    version = native_tool_record(
        root,
        directory,
        "zbarimg",
        ["--version"],
        env=env,
        deadline=deadline,
        run_id=run_id,
        purpose=f"qr-version-{ordinal}",
    )
    if version["exit_code"] != 0 or version["original_exit_code"] != 0:
        raise ValueError("actual QR engine version probe failed")
    reader = SnapshotReader(root)
    observed = json_object_from_bytes(reader.read(version["artifact"]["path"]).content)
    executable = observed["executable"]
    if sys.platform == "darwin":
        loader, arguments = "otool", ["-L", executable]
    elif sys.platform.startswith("linux"):
        loader, arguments = "ldd", [executable]
    else:
        raise NativeToolUnavailable("QR scanner core loader observation requires macOS or Linux")
    linked = native_tool_record(
        root, directory, loader, arguments, env=env, deadline=deadline, run_id=run_id, purpose=f"qr-loader-{ordinal}"
    )
    if linked["exit_code"] != 0 or linked["original_exit_code"] != 0:
        raise ValueError("actual QR engine loader observation failed")
    output = json_object_from_bytes(reader.read(linked["artifact"]["path"]).content)["stdout"]
    candidates = []
    for line in output.splitlines():
        value = line.strip().split(" (", 1)[0]
        if "=>" in value:
            value = value.split("=>", 1)[1].strip()
        if value.startswith("/") and re.match(r"libzbar(?:[.\-]|$)", Path(value).name):
            candidates.append(Path(value))
    if len(set(candidates)) != 1:
        raise NativeToolUnavailable("actual linked QR scanner core was not independently identified")
    linked_core = candidates[0]
    core = linked_core.resolve(strict=True)
    content = read_bytes_confined(core.parent, core, max_bytes=16 * 1024 * 1024)
    observation = _core_observation(core)
    return (
        {
            "schema_version": "template-native-qr-core-v2",
            "ordinal": ordinal,
            "executable": executable,
            "executable_sha256": observed["executable_sha256"],
            "core_path": str(core),
            "linked_core_path": str(linked_core),
            "core_sha256": hashlib.sha256(content).hexdigest(),
            "core_bytes": len(content),
            "core_observation_before": observation,
            "version_artifact": version["artifact"],
            "loader_artifact": linked["artifact"],
        },
        core,
        content,
    )


def finish_qr_core(
    root: Path, directory: Path, binding: dict[str, Any], core: Path, content: bytes, *, ordinal: int
) -> dict[str, Any]:
    """Retain custody only after the actual linked core stayed unchanged."""
    current = read_bytes_confined(core.parent, core, max_bytes=16 * 1024 * 1024)
    if (
        Path(binding["linked_core_path"]).resolve(strict=True) != core
        or current != content
        or hashlib.sha256(current).hexdigest() != binding["core_sha256"]
    ):
        raise ValueError("actual linked QR scanner core changed during pixel decoding")
    after = _core_observation(core)
    if after != binding["core_observation_before"]:
        raise ValueError("actual linked QR core file metadata changed during decode")
    binding = {**binding, "core_observation_after": after}
    return write_json(root, directory / f"qr-runtime-{ordinal}.json", binding)


def replay_projection_qr_runtime(
    row: dict[str, Any],
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    producer_path: Callable[[str], str],
    run_id: str,
) -> dict[str, Any]:
    """Validate original scanner execution and retained core, without host reads."""

    def admitted(binding: dict[str, Any]) -> bytes:
        if (
            set(binding) != {"path", "sha256"}
            or type(binding["path"]) is not str
            or PurePosixPath(binding["path"]).is_absolute()
            or ".." in PurePosixPath(binding["path"]).parts
            or str(PurePosixPath(binding["path"])) != binding["path"]
            or not re.fullmatch(r"[0-9a-f]{64}", binding["sha256"])
        ):
            raise ValueError("portable QR artifact binding is malformed")
        content = read_artifact(binding)
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("portable QR runtime artifact differs from original custody")
        return content

    if set(row) != {
        "raster_sha256",
        "target",
        "decoded",
        "tool_artifact",
        "runtime_artifact",
        "original_exit_code",
        "findings",
        "status",
    }:
        raise ValueError("portable QR original row fieldset differs")
    runtime: dict[str, Any] = json_object_from_bytes(admitted(row["runtime_artifact"]))
    ordinal = runtime["ordinal"]
    if (
        runtime["schema_version"] != "template-native-qr-core-v2"
        or type(ordinal) is not int
        or not 1 <= ordinal <= 10_000
    ):
        raise ValueError("portable QR core identity is outside source-owned bounds")
    directory = PurePosixPath(row["runtime_artifact"]["path"]).parent
    if row["runtime_artifact"]["path"] != str(directory / f"qr-runtime-{ordinal}.json"):
        raise ValueError("portable QR runtime path differs from original native page")
    expected_fields = {
        "schema_version",
        "ordinal",
        "executable",
        "executable_sha256",
        "core_path",
        "linked_core_path",
        "core_sha256",
        "core_bytes",
        "core_observation_before",
        "core_observation_after",
        "version_artifact",
        "loader_artifact",
    }
    if set(runtime) != expected_fields or runtime["core_observation_before"] != runtime["core_observation_after"]:
        raise ValueError("portable QR original before/after core observation differs")
    core = runtime["core_observation_before"]
    if (
        set(core) != {"schema_version", "path", "sha256", "bytes", "metadata"}
        or core["schema_version"] != "template-native-linked-qr-core-observation-v1"
        or core["path"] != runtime["core_path"]
        or core["sha256"] != runtime["core_sha256"]
        or core["bytes"] != runtime["core_bytes"]
        or type(core["bytes"]) is not int
        or not 0 < core["bytes"] <= 16 * 1024 * 1024
        or not re.fullmatch(r"[0-9a-f]{64}", core["sha256"])
    ):
        raise ValueError("portable QR original core byte observations malformed")
    facts = core["metadata"]
    if (
        set(facts) != {"size", "mode", "inode", "device", "mtime_ns", "ctime_ns"}
        or any(type(v) is not int for v in facts.values())
        or facts["size"] != core["bytes"]
        or not stat.S_ISREG(facts["mode"])
    ):
        raise ValueError("portable QR original core metadata malformed")
    if (
        type(row["original_exit_code"]) is not int
        or row["original_exit_code"] not in {0, 4}
        or not isinstance(row["decoded"], list)
        or any(type(value) is not str for value in row["decoded"])
    ):
        raise ValueError("portable QR original decode outcome malformed")
    for label in (runtime["executable"], runtime["core_path"], runtime["linked_core_path"]):
        _canonical_path(label)
    version = json_object_from_bytes(admitted(runtime["version_artifact"]))
    loader = json_object_from_bytes(admitted(runtime["loader_artifact"]))
    decoded = json_object_from_bytes(admitted(row["tool_artifact"]))
    scanner = runtime["executable"]
    loader_args = ["-L", scanner] if loader["tool"] == "otool" else [scanner]
    commands = (
        [scanner, "--version"],
        [loader["executable"], *loader_args],
        [
            scanner,
            "--quiet",
            "--raw",
            "--set",
            "disable",
            "--set",
            "qrcode.enable",
            producer_path(str(directory / f"qr-page-{ordinal}.png")),
        ],
    )
    purposes = (f"qr-version-{ordinal}", f"qr-loader-{ordinal}", f"qr-decode-{ordinal}")
    for index, (tool, command, purpose) in enumerate(zip((version, loader, decoded), commands, purposes, strict=True)):
        expected = row["original_exit_code"] if index == 2 else 0
        binding = (runtime["version_artifact"], runtime["loader_artifact"], row["tool_artifact"])[index]
        if binding["path"] != str(directory / f"{purpose}.json"):
            raise ValueError("portable QR original tool artifact path differs")
        if (
            set(tool) != _TOOL_FIELDS
            or tool["schema_version"] != TOOL_SCHEMA
            or tool["run_id"] != run_id
            or tool["purpose"] != purpose
            or tool["command"] != command
            or type(tool["exit_code"]) is not int
            or type(tool["original_exit_code"]) is not int
            or tool["exit_code"] != expected
            or tool["original_exit_code"] != expected
            or tool["timed_out"] is not False
            or tool["custody_refused"] is not False
            or tool["diagnostic"] != ""
            or not re.fullmatch(r"[0-9a-f]{64}", tool["executable_sha256"])
        ):
            raise ValueError("portable QR original command differs from source-owned execution")
        _canonical_path(tool["executable"])
        observation = {
            "schema_version": EXECUTABLE_SCHEMA,
            "path": tool["executable"],
            "sha256": tool["executable_sha256"],
        }
        if (
            tool["executable_observation_before"] != observation
            or tool["executable_observation_after"] != observation
            or tool["tool"] != (loader["tool"] if index == 1 else "zbarimg")
            or type(tool["stdout"]) is not str
            or type(tool["stderr"]) is not str
        ):
            raise ValueError("portable QR original executable observations differ")
        if index != 1 and (tool["executable"] != scanner or tool["executable_sha256"] != runtime["executable_sha256"]):
            raise ValueError("portable QR scanner binary changed between actual observations")
    if loader["tool"] not in {"otool", "ldd"} or row["original_exit_code"] not in {0, 4}:
        raise ValueError("portable QR loader or original decoder outcome is unsupported")
    linked = runtime["linked_core_path"]
    if (
        not PurePosixPath(linked).is_absolute()
        or not PurePosixPath(runtime["core_path"]).is_absolute()
        or not re.match(r"libzbar(?:[.\-]|$)", PurePosixPath(linked).name)
        or _linked_paths(loader["stdout"]) != [linked]
        or decoded["stdout"].splitlines() != row["decoded"]
    ):
        raise ValueError("portable QR original linked core or actual decoded values differ")
    return runtime


_TOOL_FIELDS = {
    "schema_version",
    "executable_observation_before",
    "executable_observation_after",
    "run_id",
    "tool",
    "purpose",
    "executable",
    "executable_sha256",
    "command",
    "exit_code",
    "original_exit_code",
    "timed_out",
    "custody_refused",
    "diagnostic",
    "stdout",
    "stderr",
}


def _canonical_path(label: str) -> None:
    if type(label) is not str or "\\" in label or "\0" in label:
        raise ValueError("portable QR original path is not canonical")
    path = PurePosixPath(label)
    if not path.is_absolute() or ".." in path.parts or str(path) != label:
        raise ValueError("portable QR original path is not canonical")


def _core_observation(core: Path) -> dict[str, Any]:
    before = core.lstat()
    content = read_bytes_confined(core.parent, core, max_bytes=16 * 1024 * 1024)
    after = core.lstat()

    def facts(value: Any) -> dict[str, int]:
        return {
            "size": value.st_size,
            "mode": value.st_mode,
            "inode": value.st_ino,
            "device": value.st_dev,
            "mtime_ns": value.st_mtime_ns,
            "ctime_ns": value.st_ctime_ns,
        }

    if facts(before) != facts(after) or not stat.S_ISREG(before.st_mode):
        raise ValueError("linked QR core changed during byte observation")
    return {
        "schema_version": "template-native-linked-qr-core-observation-v1",
        "path": str(core),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "metadata": facts(before),
    }


def _linked_paths(output: str) -> list[str]:
    candidates = set()
    for line in output.splitlines():
        value = line.strip().split(" (", 1)[0]
        if "=>" in value:
            value = value.split("=>", 1)[1].strip()
        if value.startswith("/") and re.match(r"libzbar(?:[.\-]|$)", PurePosixPath(value).name):
            candidates.add(value)
    return sorted(candidates)
