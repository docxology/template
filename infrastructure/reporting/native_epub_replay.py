"""Portable replay of retained EPUB validator and reader execution custody."""

from __future__ import annotations

import hashlib
import re
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from collections.abc import Callable
from typing import Any

from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_acceptance_contracts import TOOL_SCHEMA
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation


def replay_epub_conversion(
    raw: dict[str, Any],
    input_bytes: bytes,
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    producer_path: Callable[[str], str],
    run_id: str,
) -> dict[str, Any]:
    """Validate frozen receipt bytes without reopening any producer engine path.

    The enclosing reader supplies confined artifact admission and the recorded
    original producer root mapping. External Java identity is original execution
    custody; only admitted private JAR bytes are reopened during portable replay.
    """

    def admitted(binding: dict[str, Any]) -> bytes:
        data = read_artifact(binding)
        if hashlib.sha256(data).hexdigest() != binding["sha256"]:
            raise ValueError("portable EPUB artifact differs from original admitted bytes")
        return data

    if raw["schema_version"] != "template-native-epub-reader-v2" or admitted(raw["input"]) != input_bytes:
        raise ValueError("portable EPUB conversion differs from exact original input")
    parse_native_bytes("epub", input_bytes)
    directory = str(PurePosixPath(raw["input"]["path"]).parent)
    from infrastructure.reporting.release_readiness_snapshot import json_object_from_bytes

    environment = json_object_from_bytes(admitted(raw["reader_environment_artifact"]))
    if environment != {
        "schema_version": "template-native-epub-reader-environment-v2",
        "run_id": run_id,
        "CALIBRE_CONFIG_DIRECTORY": producer_path(directory + "/calibre-profile"),
        "CALIBRE_CACHE_DIRECTORY": producer_path(directory + "/calibre-cache"),
        "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
        "QT_DEBUG_PLUGINS": "1",
        "QT_LOGGING_RULES": "qt.core.plugin.factoryloader.debug=false;qt.core.plugin.loader.debug=false",
    }:
        raise ValueError("portable EPUB reader environment differs from exact source-owned software rendering")
    engine = raw["engine"]
    if engine["schema_version"] != "template-native-epubcheck-engine-v1":
        raise ValueError("portable EPUB engine identity is invalid")
    rows = engine["files"]
    keys = [(row["category"], row["path"]) for row in rows]
    if not rows or len(rows) > 20_000 or len(set(keys)) != len(keys):
        raise ValueError("portable EPUB runtime/JAR inventory is incomplete or duplicated")
    for row in rows:
        path = PurePosixPath(row["path"])
        if (
            row["category"] not in {"java-runtime", "epubcheck-bundle"}
            or path.is_absolute()
            or ".." in path.parts
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            or type(row["bytes"]) is not int
            or not 0 <= row["bytes"] <= 512 * 1024 * 1024
        ):
            raise ValueError("portable EPUB engine inventory violates source-owned bounds")
    if sum(row["bytes"] for row in rows) > 2 * 1024 * 1024 * 1024:
        raise ValueError("portable EPUB engine exceeds source-owned byte budget")
    runtime = {row["path"]: row for row in rows if row["category"] == "java-runtime"}
    bundle = {row["path"]: row for row in rows if row["category"] == "epubcheck-bundle"}
    if "bin/java" not in runtime or "release" not in runtime:
        raise ValueError("portable EPUB lacks independently bound actual Java runtime")
    private_main = raw["consumed_jar"]
    private_base = PurePosixPath(private_main["path"]).parent
    consumed = raw["consumed_jars"]
    relative = [PurePosixPath(row["path"]).relative_to(private_base).as_posix() for row in consumed]
    if len(set(relative)) != len(relative) or set(relative) != set(bundle):
        raise ValueError("portable EPUB consumed JAR set differs from original admitted bundle")
    jars = {}
    for name, binding in zip(relative, consumed, strict=True):
        content = admitted(binding)
        if binding["sha256"] != bundle[name]["sha256"] or len(content) != bundle[name]["bytes"]:
            raise ValueError("portable EPUB consumed JAR differs from original engine identity")
        jars[name] = content
    main_name = PurePosixPath(engine["jar"]).name
    if private_main["path"] != str(private_base / main_name) or admitted(private_main) != jars[main_name]:
        raise ValueError("portable EPUB actual main JAR binding is invalid")
    with zipfile.ZipFile(BytesIO(jars[main_name])) as archive:
        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8").replace("\r\n ", "").replace("\n ", "")
    for line in manifest.splitlines():
        if line.startswith("Class-Path:") and any(name not in jars for name in line.partition(":")[2].split()):
            raise ValueError("portable EPUB manifest dependency is outside frozen consumed JARs")
    tools = [json_object_from_bytes(admitted(binding)) for binding in raw["tool_artifacts"]]
    purposes = (
        "java-runtime-version",
        "epubcheck-version",
        "epubcheck-validation",
        "epub-reader-version",
        "epub-reader-conversion",
    )
    if len(tools) != len(purposes):
        raise ValueError("portable EPUB requires all actual version/validation/reader commands")
    reader_exe = tools[3]["executable"]
    commands = (
        [engine["java"], "-version"],
        [engine["java"], "-jar", producer_path(private_main["path"]), "--version"],
        [engine["java"], "-jar", producer_path(private_main["path"]), producer_path(raw["input"]["path"])],
        [reader_exe, "--version"],
        [
            reader_exe,
            producer_path(raw["input"]["path"]),
            producer_path(raw["pdf"]["path"]),
            "--disable-font-rescaling",
        ],
    )
    tool_fields = {
        "schema_version",
        "run_id",
        "purpose",
        "tool",
        "command",
        "executable",
        "executable_sha256",
        "executable_observation_before",
        "executable_observation_after",
        "exit_code",
        "original_exit_code",
        "timed_out",
        "custody_refused",
        "diagnostic",
        "stdout",
        "stderr",
    }
    for index, (tool, purpose, command) in enumerate(zip(tools, purposes, commands, strict=True)):
        if set(tool) != tool_fields:
            raise ValueError("portable EPUB original tool fieldset differs")
        for name in ("executable_observation_before", "executable_observation_after"):
            validate_executable_observation(tool[name], tool["executable"], tool["executable_sha256"])
        if (
            tool["schema_version"] != TOOL_SCHEMA
            or tool["purpose"] != purpose
            or tool["run_id"] != run_id
            or tool["command"] != command
            or tool["executable"] != command[0]
            or tool["tool"] != (engine["java"] if index < 3 else "ebook-convert")
            or type(tool["exit_code"]) is not int
            or tool["exit_code"] != 0
            or type(tool["original_exit_code"]) is not int
            or tool["original_exit_code"] != 0
            or tool["timed_out"] is not False
            or tool["custody_refused"] is not False
            or tool["diagnostic"] != ""
            or not isinstance(tool["stdout"], str)
            or not isinstance(tool["stderr"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", tool["executable_sha256"])
        ):
            raise ValueError("portable EPUB actual original command custody differs")
        if index < 3 and (
            tool["executable"] != engine["java"] or tool["executable_sha256"] != runtime["bin/java"]["sha256"]
        ):
            raise ValueError("portable EPUB Java receipt differs from independently bound runtime bytes")
    if tools[3]["executable_sha256"] != tools[4]["executable_sha256"]:
        raise ValueError("portable EPUB reader executable changed between version and conversion")
    from infrastructure.project.native_reader_runtime_custody import (
        replay_retained_native_reader_runtime,
        require_native_reader_plugin_trace,
    )

    consumed_plugin = "Contents/Frameworks/plugins/headless.so"
    reader_runtime = replay_retained_native_reader_runtime(
        raw["reader_runtime_before"],
        raw["reader_runtime_after"],
        read_artifact=admitted,
        run_id=run_id,
        executable=reader_exe,
        executable_sha256=tools[4]["executable_sha256"],
        consumed_members=(consumed_plugin,),
    )
    require_native_reader_plugin_trace(reader_runtime, tools[4]["stderr"], consumed_plugin)
    pdf = admitted(raw["pdf"])
    parsed = parse_native_bytes("pdf", pdf)
    if parsed != raw["observation"]:
        raise ValueError("portable EPUB native reader PDF observation differs from actual bytes")
    return {
        "input": raw["input"],
        "pdf": raw["pdf"],
        "observation": parsed,
        "engine": engine,
        "consumed_jar": private_main,
        "consumed_jars": consumed,
        "tool_artifacts": raw["tool_artifacts"],
        "reader_environment_artifact": raw["reader_environment_artifact"],
        "reader_runtime_before": raw["reader_runtime_before"],
        "reader_runtime_after": raw["reader_runtime_after"],
    }
