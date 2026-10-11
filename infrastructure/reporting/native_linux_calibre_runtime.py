"""Actual Source-selected Linux Calibre package/embedded-Qt observations.

Discovery always uses the existing live Source ToolAPI and original deadline.
Portable replay authenticates every retained command without opening producer
paths. These observations grant neither loaded-memory nor descendant coverage.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.project.native_linux_calibre_custody import (
    POLICY,
    SCHEMA,
    canonical_linux_member,
    observe_linux_calibre_packages,
    validate_linux_calibre_packages,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import NativeToolUnavailable, native_tool_record
from infrastructure.reporting.native_format_acceptance_contracts import (
    TOOL_FIELDS,
    TOOL_SCHEMA,
    create_private_native_directory,
)
from infrastructure.reporting.native_format_portable_custody import validate_executable_observation
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader, json_object_from_bytes

SELECTION_SCHEMA = "template-native-linux-calibre-selection-v1"
PLATFORM = "offscreen"
ENVIRONMENT = {"QT_QPA_PLATFORM": PLATFORM}
DISCOVERY = """import json, sys
from pathlib import Path
import calibre
from qt.core import QLibraryInfo
module = sys.modules[QLibraryInfo.__module__]
print(json.dumps({"schema_version":"template-calibre-embedded-layout-v1",
"platform":sys.platform,
"interpreter":str(Path(sys.executable).resolve(strict=True)),
"calibre_module":str(Path(calibre.__file__).resolve(strict=True)),
"qt_module":str(Path(module.__file__).resolve(strict=True)),
"qt_libraries":str(Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.LibrariesPath)).resolve(strict=True)),
"qt_plugins":str(Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)).resolve(strict=True))},sort_keys=True))"""
PLUGIN_DISCOVERY = """import json
from pathlib import Path
from qt.core import QPluginLoader
paths = json.loads(%s)
selected = []
for name in paths:
    metadata = QPluginLoader(name).metaData()
    if (metadata.get("IID") == "org.qt-project.Qt.QPA.QPlatformIntegrationFactoryInterface.5.3"
        and "offscreen" in metadata.get("MetaData", {}).get("Keys", [])):
        selected.append(str(Path(name).resolve(strict=True)))
print(json.dumps({"schema_version":"template-calibre-qt-platform-selection-v1","platform":"offscreen","plugins":sorted(set(selected))},sort_keys=True))"""
PACKAGE_FORMAT = "${binary:Package}\\t${Version}\\t${Architecture}\\t${Status}\\n"


def _owner(output: str, label: str) -> str:
    rows = output.splitlines()
    if len(rows) != 1 or ": " not in rows[0]:
        raise ValueError("Calibre runtime role requires one exact installed-package owner")
    name, actual = rows[0].split(": ", 1)
    if actual != label or re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9][a-z0-9-]*)?", name) is None:
        raise ValueError("Calibre package ownership query differs from selected actual role")
    return name


def _plugin_owners(output: str, prefix: str) -> list[str]:
    """Read actual package ownership below Qt's own discovered plugin prefix."""
    result: set[str] = set()
    directory = canonical_linux_member(prefix)
    for row in output.splitlines():
        if ": " not in row:
            raise ValueError("Calibre Qt plugin ownership output malformed")
        owners, label = row.split(": ", 1)
        member = canonical_linux_member(label)
        if not member.is_relative_to(directory):
            raise ValueError("Calibre Qt package query escaped actual discovered plugin directory")
        for name in owners.split(", "):
            if re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?::[a-z0-9][a-z0-9-]*)?", name) is None:
                raise ValueError("Calibre Qt plugin package owner malformed")
            result.add(name)
    if not result or len(result) > 256:
        raise ValueError("Calibre Qt plugin owning-package roster absent/unbounded")
    return sorted(result)


def _package(status: str, members: str, name: str) -> dict[str, Any]:
    rows = status.splitlines()
    fields = rows[0].split("\t") if len(rows) == 1 else []
    if len(fields) != 4 or fields[0] != name:
        raise ValueError("Calibre package status query differs from exact selected owner")
    labels = sorted(set("/" if label == "/." else label for label in members.splitlines()))
    for label in labels:
        canonical_linux_member(label)
    return {"package": name, "version": fields[1], "architecture": fields[2], "status": fields[3], "members": labels}


def _layout(output: str) -> dict[str, str]:
    value = json_object_from_bytes(output.encode())
    fields = {"platform", "interpreter", "calibre_module", "qt_module", "qt_libraries", "qt_plugins"}
    if set(value) != {"schema_version", *fields} or value["schema_version"] != "template-calibre-embedded-layout-v1":
        raise ValueError("Calibre embedded Python/Qt discovery schema differs")
    if value["platform"] != "linux":
        raise ValueError("Calibre embedded discovery requires genuine Linux execution")
    for name in fields - {"platform"}:
        canonical_linux_member(value[name])
    return value


def _plugin_command(packages: list[dict[str, Any]], layout: dict[str, str]) -> tuple[str, list[str]]:
    directory = Path(layout["qt_plugins"])
    candidates = sorted(
        {
            path
            for package in packages
            for path in package["members"]
            if Path(path).is_relative_to(directory) and Path(path).suffix == ".so"
        }
    )
    if not candidates or len(candidates) > 4096:
        raise ValueError("Calibre Qt metadata discovery requires a bounded package-owned candidate roster")
    encoded = json.dumps(candidates, separators=(",", ":"))
    if len(encoded.encode()) > 128 * 1024:
        raise ValueError("Calibre Qt candidate command exceeds finite source-owned bound")
    return PLUGIN_DISCOVERY % repr(encoded), candidates


def _plugin(output: str, candidates: list[str]) -> str:
    value = json_object_from_bytes(output.encode())
    if (
        set(value) != {"schema_version", "platform", "plugins"}
        or value["schema_version"] != "template-calibre-qt-platform-selection-v1"
        or value["platform"] != PLATFORM
        or not isinstance(value["plugins"], list)
        or len(value["plugins"]) != 1
        or value["plugins"][0] not in candidates
    ):
        raise ValueError("Calibre requires one actual package-owned Qt offscreen plugin")
    plugin = value["plugins"][0]
    if not isinstance(plugin, str):
        raise ValueError("Calibre selected package-owned Qt plugin must be a canonical string label")
    canonical_linux_member(plugin)
    return plugin


def observe_linux_calibre_runtime(
    root: Path, directory: Path, *, selected: Path, env: dict[str, str], deadline: float, run_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Discover real selected runtime roles; no package/module metadata pass."""
    owner = current_native_producer_operation()
    reader = SnapshotReader(root)
    if (
        sys.platform != "linux"
        or owner is None
        or owner.source.bindings.current_root != root
        or env.get("QT_QPA_PLATFORM") != PLATFORM
    ):
        raise NativeToolUnavailable(
            "Linux Calibre discovery requires actual Linux and its live Source owner/offscreen selection"
        )
    owner.verify(reader, run_id=run_id, deadline=deadline)
    if directory.exists() or directory.is_symlink():
        raise ValueError("Linux Calibre discovery requires one fresh owned evidence directory")
    create_private_native_directory(root, directory)
    chosen = shutil.which("ebook-convert", path=env.get("PATH"))
    debug, query = (shutil.which(name, path=env.get("PATH")) for name in ("calibre-debug", "dpkg-query"))
    if chosen is None or selected != Path(chosen).absolute() or debug is None or query is None:
        raise NativeToolUnavailable("Linux Calibre requires the actual selected reader/debug/package tools")
    launchers = {
        "launcher": str(selected.resolve(strict=True)),
        "debug_launcher": str(Path(debug).resolve(strict=True)),
        "package_query": str(Path(query).resolve(strict=True)),
    }
    nominations = {
        "ebook-convert": str(selected),
        "calibre-debug": str(Path(debug).absolute()),
        "dpkg-query": str(Path(query).absolute()),
    }
    tools: list[dict[str, str]] = []
    executed: list[dict[str, Any]] = []

    def execute(name: str, arguments: list[str], purpose: str) -> dict[str, Any]:
        remaining(deadline)
        owner.verify(reader, run_id=run_id, deadline=deadline)
        result = native_tool_record(
            root, directory, name, arguments, env=env, deadline=deadline, run_id=run_id, purpose=purpose
        )
        binding = result["artifact"]
        tool = reader.read(binding["path"]).json_object()
        owner.validate_tool(binding, tool, reader, run_id=run_id)
        if type(tool["original_exit_code"]) is int and tool["original_exit_code"] in (130, -2, 124):
            source_code = 130 if tool["original_exit_code"] in (130, -2) else 124
            failure = SystemExit(source_code)
            setattr(
                failure,
                "native_linux_calibre_attempt",
                {
                    "actual_tool": binding,
                    "original_exit_code": tool["original_exit_code"],
                    "source_exit_code": source_code,
                    "timed_out": tool["timed_out"],
                    "observer_complete": False,
                },
            )
            raise failure
        _checked_tool(tool, name, arguments, purpose, run_id)
        tools.append(binding)
        executed.append(tool)
        return tool

    layout = _layout(execute("calibre-debug", ["-c", DISCOVERY], "linux-calibre-embedded-layout")["stdout"])
    roles = {**launchers, **{name: layout[name] for name in ("interpreter", "calibre_module", "qt_module")}}
    # Query every exact selected role and the real Qt plugin directory. Its
    # owning package supplies candidates; no guessed filesystem plugin name.
    labels = sorted({*roles.values(), *nominations.values()})
    owners = sorted(
        {
            _owner(execute("dpkg-query", ["--search", label], f"linux-calibre-owner-{index:02d}")["stdout"], label)
            for index, label in enumerate(labels)
        }
    )
    plugin_owners = _plugin_owners(
        execute("dpkg-query", ["--search", layout["qt_plugins"] + "/*"], "linux-calibre-plugin-owners")["stdout"],
        layout["qt_plugins"],
    )
    owners = sorted(set(owners) | set(plugin_owners))
    if len(owners) > 256:
        raise ValueError("Calibre selected package closure exceeds finite owner bound")
    packages = []
    for index, name in enumerate(owners):
        status = execute(
            "dpkg-query", ["--show", "--showformat=" + PACKAGE_FORMAT, name], f"linux-calibre-package-{index:02d}"
        )["stdout"]
        members = execute("dpkg-query", ["--listfiles", name], f"linux-calibre-files-{index:02d}")["stdout"]
        packages.append(_package(status, members, name))
    command, candidates = _plugin_command(packages, layout)
    roles["platform_plugin"] = _plugin(
        execute("calibre-debug", ["-c", command], "linux-calibre-qt-platform")["stdout"], candidates
    )
    runtime = observe_linux_calibre_packages(packages, roles, deadline=deadline)
    # Initial discovery supplies no body/loaded authority. Repeat embedded and
    # plugin selection only after the complete selected package bytes are held.
    if _layout(execute("calibre-debug", ["-c", DISCOVERY], "linux-calibre-bound-layout")["stdout"]) != layout:
        raise ValueError("Calibre embedded runtime changed after complete package admission")
    if (
        _plugin(execute("calibre-debug", ["-c", command], "linux-calibre-bound-platform")["stdout"], candidates)
        != roles["platform_plugin"]
    ):
        raise ValueError("Calibre Qt platform changed after complete package admission")
    validate_linux_calibre_packages(runtime, observe_linux_calibre_packages(packages, roles, deadline=deadline))
    _package_tool_bytes(runtime, executed)
    owner.verify(reader, run_id=run_id, deadline=deadline)
    if not reader.unchanged():
        raise ValueError("Linux Calibre discovery evidence changed during real Source observation")
    return {
        "schema_version": SELECTION_SCHEMA,
        "policy": POLICY,
        "nominations": nominations,
        "layout": layout,
        "tools": tools,
    }, runtime


def _checked_tool(tool: dict[str, Any], name: str, arguments: list[str], purpose: str, run_id: str) -> None:
    if (
        frozenset(tool) != TOOL_FIELDS
        or tool["schema_version"] != TOOL_SCHEMA
        or tool["tool"] != name
        or tool["purpose"] != purpose
        or tool["run_id"] != run_id
        or tool["command"] != [tool["executable"], *arguments]
        or tool["exit_code"] != 0
        or type(tool["exit_code"]) is not int
        or tool["original_exit_code"] != 0
        or type(tool["original_exit_code"]) is not int
        or tool["timed_out"] is not False
        or tool["custody_refused"] is not False
        or tool["diagnostic"] != ""
        or not isinstance(tool["stdout"], str)
        or not isinstance(tool["stderr"], str)
    ):
        raise ValueError("Linux Calibre actual discovery ToolAPI/signed outcome differs")
    for field in ("executable_observation_before", "executable_observation_after"):
        validate_executable_observation(tool[field], tool["executable"], tool["executable_sha256"])


def replay_linux_calibre_runtime(
    selection: dict[str, Any],
    before_binding: dict[str, str],
    after_binding: dict[str, str],
    *,
    read_artifact: Callable[[dict[str, Any]], bytes],
    authenticate_tool: Callable[[dict[str, Any], dict[str, Any]], None],
    run_id: str,
    reader_tool: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct package commands/Qt selection from actual signed tools."""
    if (
        set(selection) != {"schema_version", "policy", "nominations", "layout", "tools"}
        or selection["schema_version"] != SELECTION_SCHEMA
        or selection["policy"] != POLICY
    ):
        raise ValueError("Linux Calibre original selection fieldset/policy differs")
    nominations = selection["nominations"]
    if not isinstance(nominations, dict) or set(nominations) != {"ebook-convert", "calibre-debug", "dpkg-query"}:
        raise ValueError("Linux Calibre requires complete actual tool nominations")
    for label in nominations.values():
        canonical_linux_member(label)
    bindings = selection["tools"]
    if not isinstance(bindings, list) or not 1 <= len(bindings) <= 1024:
        raise ValueError("Linux Calibre discovery tool roster is absent/unbounded")
    index = 0
    executed: list[dict[str, Any]] = []

    def tool(name: str, arguments: list[str], purpose: str) -> dict[str, Any]:
        nonlocal index
        if index >= len(bindings):
            raise ValueError("Linux Calibre discovery command missing")
        binding = bindings[index]
        content = read_artifact(binding)
        if hashlib.sha256(content).hexdigest() != binding["sha256"]:
            raise ValueError("Linux Calibre original discovery artifact changed")
        raw = json_object_from_bytes(content)
        authenticate_tool(binding, raw)
        _checked_tool(raw, name, arguments, purpose, run_id)
        process_binding = raw["native_process_artifact"]
        process_content = read_artifact(process_binding)
        process = json_object_from_bytes(process_content)
        if hashlib.sha256(process_content).hexdigest() != process_binding["sha256"] or process["nomination"] != {
            "tool": name,
            "path": nominations[name],
            "resolved_path": raw["executable"],
        }:
            raise ValueError("Calibre discovered launcher nomination differs from actual native process")
        index += 1
        executed.append(raw)
        return raw

    embedded = tool("calibre-debug", ["-c", DISCOVERY], "linux-calibre-embedded-layout")
    layout = _layout(embedded["stdout"])
    if layout != selection["layout"]:
        raise ValueError("Calibre original layout differs from actual embedded discovery")
    runtime_records = []
    for binding in (before_binding, after_binding):
        content = read_artifact(binding)
        raw = json_object_from_bytes(content)
        if (
            hashlib.sha256(content).hexdigest() != binding["sha256"]
            or binding["path"] != f"output/readiness/native-reader-runtimes/{run_id}/{raw.get('digest')}.json"
        ):
            raise ValueError("Calibre retained package inventory differs from original run")
        runtime_records.append(raw)
    runtime = runtime_records[0]
    validate_linux_calibre_packages(runtime, runtime_records[1])
    if (
        runtime["schema_version"] != SCHEMA
        or runtime["roles"]["launcher"] != reader_tool["executable"]
        or runtime["roles"]["debug_launcher"] != embedded["executable"]
    ):
        raise ValueError("Calibre embedded/reader actual executable differs from package roles")
    for name in ("interpreter", "calibre_module", "qt_module"):
        if runtime["roles"][name] != layout[name]:
            raise ValueError("Calibre actual interpreter/module role differs from signed discovery")
    labels = sorted(
        {
            *(
                runtime["roles"][name]
                for name in (
                    "launcher",
                    "debug_launcher",
                    "package_query",
                    "interpreter",
                    "calibre_module",
                    "qt_module",
                )
            ),
            *nominations.values(),
        }
    )
    owners = sorted(
        {
            _owner(tool("dpkg-query", ["--search", label], f"linux-calibre-owner-{ordinal:02d}")["stdout"], label)
            for ordinal, label in enumerate(labels)
        }
    )
    plugin_owners = _plugin_owners(
        tool("dpkg-query", ["--search", layout["qt_plugins"] + "/*"], "linux-calibre-plugin-owners")["stdout"],
        layout["qt_plugins"],
    )
    owners = sorted(set(owners) | set(plugin_owners))
    if len(owners) > 256:
        raise ValueError("Calibre selected package closure exceeds finite owner bound")
    packages = []
    for ordinal, name in enumerate(owners):
        status = tool(
            "dpkg-query", ["--show", "--showformat=" + PACKAGE_FORMAT, name], f"linux-calibre-package-{ordinal:02d}"
        )["stdout"]
        members = tool("dpkg-query", ["--listfiles", name], f"linux-calibre-files-{ordinal:02d}")["stdout"]
        packages.append(_package(status, members, name))
    command, candidates = _plugin_command(packages, layout)
    plugin = _plugin(tool("calibre-debug", ["-c", command], "linux-calibre-qt-platform")["stdout"], candidates)
    if (
        _layout(tool("calibre-debug", ["-c", DISCOVERY], "linux-calibre-bound-layout")["stdout"]) != layout
        or _plugin(tool("calibre-debug", ["-c", command], "linux-calibre-bound-platform")["stdout"], candidates)
        != plugin
    ):
        raise ValueError("Calibre bound discovery changed after complete original package observation")
    reader_process_binding = reader_tool["native_process_artifact"]
    reader_process_bytes = read_artifact(reader_process_binding)
    reader_process = json_object_from_bytes(reader_process_bytes)
    if hashlib.sha256(reader_process_bytes).hexdigest() != reader_process_binding["sha256"] or reader_process[
        "nomination"
    ] != {"tool": "ebook-convert", "path": nominations["ebook-convert"], "resolved_path": reader_tool["executable"]}:
        raise ValueError("Calibre reader launcher differs from independently discovered actual nomination")
    if index != len(bindings) or packages != runtime["packages"] or plugin != runtime["roles"]["platform_plugin"]:
        raise ValueError("Calibre package/plugin discovery roster differs from retained custody")
    row = next(r for r in runtime["files"] if r["path"] == reader_tool["executable"])
    if row.get("sha256") != reader_tool["executable_sha256"]:
        raise ValueError("Calibre package bytes differ from actual conversion executable")
    _package_tool_bytes(runtime, executed)
    return runtime


def _package_tool_bytes(runtime: dict[str, Any], tools: list[dict[str, Any]]) -> None:
    """Every real discovery executable must match held selected package bytes."""
    files = {row["path"]: row for row in runtime["files"]}
    for tool in tools:
        row = files.get(tool["executable"], {})
        role = "debug_launcher" if tool["tool"] == "calibre-debug" else "package_query"
        if tool["executable"] != runtime["roles"][role] or row.get("sha256") != tool["executable_sha256"]:
            raise ValueError("Calibre discovery executable differs from actual selected package bytes")


def require_linux_calibre_plugin_trace(runtime: dict[str, Any], stderr: str) -> None:
    """Retain actual selected plugin consumption; package metadata cannot pass."""
    validate_linux_calibre_packages(runtime, runtime)
    expected = f'qt.core.library: "{runtime["roles"]["platform_plugin"]}" loaded library'
    if not isinstance(stderr, str) or expected not in {line.strip() for line in stderr.splitlines()}:
        raise ValueError("Linux Calibre lacks actual selected Qt plugin loaded-library trace")
