"""Original Mermaid/Node runtime bytes and exact observed platform-font faces.

Inventories are bounded and portable by member content identities. The reader
selects its own installed runtime roots explicitly; original path labels never
authorize reopening producer tools or fonts. Original process and OS library
custody remain obligations of the enclosing admission, separate from this leaf.
"""

from __future__ import annotations

import hashlib
import json
import math
import stat
import time
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_browser_runtime import observe_runtime, validate_runtime

if TYPE_CHECKING:
    from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidRuntimeAdmission

SCHEMA = "template-native-mermaid-runtime-custody-v1"
MAX_FILES = 40000
MAX_BYTES = 1024 * 1024 * 1024
MAX_FONT_BYTES = 128 * 1024 * 1024
FONT_SCHEMA = "template-native-mermaid-platform-font-custody-v1"
DEFAULT_FONT_SCHEMA = "template-native-mermaid-source-licensed-default-font-custody-v1"


def _budget(deadline: float) -> None:
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("Mermaid runtime custody exhausted its original finite deadline")


def _file(path: Path, *, deadline: float) -> dict[str, Any]:
    _budget(deadline)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > 512 * 1024 * 1024:
        raise ValueError("Mermaid runtime member is not a bounded regular file")
    digest = hashlib.sha256()
    consumed = 0
    with path.open("rb") as file:
        while block := file.read(1024 * 1024):
            _budget(deadline)
            consumed += len(block)
            if consumed > before.st_size:
                raise ValueError("Mermaid runtime member grew during byte inventory")
            digest.update(block)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ValueError("Mermaid runtime member changed during actual byte inventory")
    if consumed != before.st_size:
        raise ValueError("Mermaid runtime member truncated during byte inventory")
    return {"bytes": after.st_size, "sha256": digest.hexdigest()}


def observe_package_tree(directory: Path, *, deadline: float) -> dict[str, Any]:
    """Hash the complete original installed CLI/dependency/resource tree."""
    root = directory.resolve(strict=True)
    package_path = root / "package.json"
    if package_path.stat().st_size > 1024 * 1024:
        raise ValueError("original Mermaid package manifest exceeds its finite source bound")
    package = json.loads(package_path.read_bytes())
    if not isinstance(package, dict):
        raise ValueError("original Mermaid installed package manifest is not an object")
    if package.get("name") != "@mermaid-js/mermaid-cli" or package.get("version") != "12.0.0":
        raise ValueError("selected original Mermaid package differs from the current admitted major/version")
    rows: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*")):
        _budget(deadline)
        info = path.lstat()
        relative = path.relative_to(root).as_posix()
        if stat.S_ISDIR(info.st_mode):
            continue
        if len(rows) >= MAX_FILES:
            raise ValueError("Mermaid complete package member bound exceeded")
        if stat.S_ISLNK(info.st_mode):
            target = path.resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError("Mermaid installed dependency alias escapes the declared complete package tree")
            rows.append({"path": relative, "kind": "alias", "target": target.relative_to(root).as_posix()})
        elif stat.S_ISREG(info.st_mode):
            observed = _file(path, deadline=deadline)
            total += observed["bytes"]
            if total > MAX_BYTES:
                raise ValueError("Mermaid complete package byte bound exceeded")
            rows.append({"path": relative, "kind": "file", **observed})
        else:
            raise ValueError("Mermaid runtime contains an unsupported filesystem node")
    result = {"package_name": package["name"], "version": package["version"], "members": rows, "bytes": total}
    return {**result, "content_digest": canonical_digest(result)}


def observe_mermaid_runtime(
    package_root: Path,
    node_executable: Path,
    chrome_executable: Path,
    *,
    deadline: float,
    runtime_admission: NativeMermaidRuntimeAdmission | None = None,
) -> dict[str, Any]:
    """Record actual package/Node/Chrome byte identities for before/after holds."""
    if runtime_admission is not None:
        from infrastructure.reporting.native_mermaid_runtime_selection import NativeMermaidRuntimeAdmission

        if not isinstance(runtime_admission, NativeMermaidRuntimeAdmission):
            raise ValueError("Source11 runtime requires its genuine live Source-owned admission")
        selected = runtime_admission.selection
        if (package_root, node_executable, chrome_executable) != (
            selected.package_root,
            selected.node_executable,
            selected.chrome_executable,
        ):
            raise ValueError("Source11 producer paths differ from its independently nominated admission")
        return runtime_admission.observe(deadline=deadline)
    package_root = package_root.resolve(strict=True)
    node = node_executable.resolve(strict=True)
    chrome = chrome_executable.resolve(strict=True)
    cli = package_root / "src/cli.js"
    if not cli.is_file():
        raise ValueError("current original Mermaid12 literal CLI entrypoint is absent")
    result = {
        "schema_version": SCHEMA,
        "package": observe_package_tree(package_root, deadline=deadline),
        "cli_member": "src/cli.js",
        "package_root_label": str(package_root),
        "node_executable_label": str(node),
        "node": _file(node, deadline=deadline),
        "chrome": observe_runtime(chrome, deadline=deadline),
    }
    return {**result, "content_digest": canonical_digest(result)}


def validate_mermaid_runtime(raw: dict[str, Any]) -> None:
    """Validate original portable inventories without reopening their paths."""
    from infrastructure.reporting.native_mermaid_runtime_selection import SCHEMA as SOURCE11_SCHEMA

    if raw.get("schema_version") == SOURCE11_SCHEMA:
        from infrastructure.reporting.native_mermaid_runtime_selection import validate_source_mermaid_runtime

        validate_source_mermaid_runtime(raw)
        return
    if raw.get("schema_version") != SCHEMA or set(raw) != {
        "schema_version",
        "package_root_label",
        "node_executable_label",
        "package",
        "cli_member",
        "node",
        "chrome",
        "content_digest",
    }:
        raise ValueError("portable original Mermaid runtime schema differs")
    for label in ("package_root_label", "node_executable_label"):
        if not isinstance(raw[label], str) or not Path(raw[label]).is_absolute() or ".." in Path(raw[label]).parts:
            raise ValueError("portable original Mermaid runtime origin label is not absolute/confined")
    _validate_file_identity(raw["node"])
    package = raw["package"]
    if not isinstance(package, dict) or set(package) != {
        "package_name",
        "version",
        "members",
        "bytes",
        "content_digest",
    }:
        raise ValueError("portable original Mermaid package fields differ")
    if package.get("package_name") != "@mermaid-js/mermaid-cli" or package.get("version") != "12.0.0":
        raise ValueError("portable original Mermaid package identity differs")
    members = package.get("members")
    if not isinstance(members, list) or not 0 < len(members) <= MAX_FILES:
        raise ValueError("portable original Mermaid package closure is absent/unbounded")
    seen = set()
    total = 0
    files = {}
    aliases = []
    for row in members:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError("portable original Mermaid member is not a literal object/path")
        path = PurePosixPath(row["path"])
        if (
            path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or path.as_posix() != row["path"]
            or row["path"] in seen
        ):
            raise ValueError("portable original Mermaid member is unconfined/duplicate")
        seen.add(row["path"])
        if row["kind"] == "file":
            if (
                set(row) != {"path", "kind", "bytes", "sha256"}
                or type(row["bytes"]) is not int
                or not 0 <= row["bytes"] <= 512 * 1024 * 1024
            ):
                raise ValueError("portable original Mermaid file metadata differs")
            _validate_file_identity({"bytes": row["bytes"], "sha256": row["sha256"]})
            total += row["bytes"]
            files[row["path"]] = row
        elif row["kind"] == "alias" and set(row) == {"path", "kind", "target"}:
            if not isinstance(row["target"], str):
                raise ValueError("portable original Mermaid alias target is not literal")
            target = PurePosixPath(row["target"])
            if target.is_absolute() or not target.parts or ".." in target.parts:
                raise ValueError("portable original Mermaid alias escapes its package")
            aliases.append(row["target"])
        else:
            raise ValueError("portable original Mermaid runtime member fields differ")
    if (
        type(package["bytes"]) is not int
        or total > MAX_BYTES
        or total != package["bytes"]
        or raw["cli_member"] != "src/cli.js"
        or raw["cli_member"] not in files
    ):
        raise ValueError("portable original Mermaid package bytes/CLI closure differs")
    if any(target not in seen and not any(member.startswith(target + "/") for member in seen) for target in aliases):
        raise ValueError("portable original Mermaid dependency alias has no declared target")
    if package["content_digest"] != canonical_digest(
        {key: value for key, value in package.items() if key != "content_digest"}
    ):
        raise ValueError("portable original Mermaid package digest differs")
    chrome = raw["chrome"]
    executable = PurePosixPath(chrome["executable"]).relative_to(PurePosixPath(chrome["root"])).as_posix()
    digest = next(
        (row["sha256"] for row in chrome["files"] if row["path"] == executable and row["kind"] == "file"), None
    )
    if digest is None:
        raise ValueError("portable original Chrome executable is absent from its runtime closure")
    validate_runtime(chrome, chrome["executable"], digest)
    if raw["content_digest"] != canonical_digest({key: value for key, value in raw.items() if key != "content_digest"}):
        raise ValueError("portable original Mermaid runtime digest differs")


def admit_reader_mermaid_runtime(
    original: dict[str, Any],
    package_root: Path,
    node_executable: Path,
    chrome_executable: Path,
    *,
    deadline: float,
    runtime_admission: NativeMermaidRuntimeAdmission | None = None,
) -> dict[str, Any]:
    """Authenticate independently selected reader roots against original bytes."""
    validate_mermaid_runtime(original)
    current = observe_mermaid_runtime(
        package_root, node_executable, chrome_executable, deadline=deadline, runtime_admission=runtime_admission
    )
    if original.get("schema_version") != SCHEMA:
        for key in (
            "package_name",
            "version",
            "source_npm_inputs",
            "installation",
            "dependency_tree",
            "cli_member",
            "node",
        ):
            if current.get(key) != original[key]:
                raise ValueError("reader-local Source11 npm/Node complete original bytes differ")
    else:
        for key in ("package", "cli_member", "node"):
            if current[key] != original[key]:
                raise ValueError("reader-local installed Mermaid/Node bytes differ from the original runtime")
    original_chrome, reader_chrome = original["chrome"], current["chrome"]
    if (original_chrome["files"], original_chrome["bytes"]) != (reader_chrome["files"], reader_chrome["bytes"]):
        raise ValueError("reader-local Chrome complete application bytes differ")
    return current


def _validate_file_identity(raw: Any) -> None:
    if (
        not isinstance(raw, dict)
        or set(raw) != {"bytes", "sha256"}
        or type(raw["bytes"]) is not int
        or not 0 <= raw["bytes"] <= 512 * 1024 * 1024
        or not isinstance(raw["sha256"], str)
        or len(raw["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in raw["sha256"])
    ):
        raise ValueError("original runtime file byte/hash metadata is invalid")


def _font_names(platform_fonts: Any) -> set[str]:
    if not isinstance(platform_fonts, list) or not 0 < len(platform_fonts) <= 1000:
        raise ValueError("actual Mermaid platform font usage is absent/unbounded")
    names = set()
    for row in platform_fonts:
        if (
            not isinstance(row, dict)
            or set(row) != {"familyName", "postScriptName", "isCustomFont", "glyphCount"}
            or row["isCustomFont"] is not False
            or not isinstance(row["postScriptName"], str)
            or not row["postScriptName"]
            or not isinstance(row["familyName"], str)
            or not row["familyName"]
            or type(row["glyphCount"]) is not int
            or not 0 < row["glyphCount"] <= 1000000
        ):
            raise ValueError("actual Mermaid font usage requires admitted native font bytes")
        names.add(row["postScriptName"])
    return names


def _default_font_names(platform_fonts: Any) -> set[str]:
    """Validate Source-default usage DATA; native authority stays external."""
    from infrastructure.rendering._mermaid_source_font_default import NAMES

    if not isinstance(platform_fonts, list) or not 0 < len(platform_fonts) <= 1000:
        raise ValueError("Source default font usage is absent/unbounded")
    names = set()
    for row in platform_fonts:
        if not isinstance(row, dict) or set(row) != {"familyName", "postScriptName", "isCustomFont", "glyphCount"}:
            raise ValueError("Source default font usage schema differs")
        if row["isCustomFont"] is True:
            if row["postScriptName"] not in NAMES or not isinstance(row["familyName"], str) or not row["familyName"]:
                raise ValueError("actual custom font escapes the Source-declared default body cohort")
            if type(row["glyphCount"]) is not int or not 0 < row["glyphCount"] <= 1000000:
                raise ValueError("actual Source default glyph usage exceeds its finite count")
            names.add(row["postScriptName"])
        else:
            names.update(_font_names([row]))
    return names


def observe_platform_font_files(
    platform_fonts: list[dict[str, Any]],
    font_files: tuple[Path, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Bind actual DevTools postscript face names to independently read fonts.

    Explicit reader-selected files are bounded before font table parsing; their
    original paths are never recorded as portable read authorities. Duplicate
    aliases with identical face bytes collapse; ambiguous different bytes fail.
    """
    from fontTools.ttLib import TTCollection, TTFont

    required = _font_names(platform_fonts)
    if not 0 < len(font_files) <= 2048:
        raise ValueError("actual Mermaid selected font-file census is absent/unbounded")
    selected = sorted({path.resolve(strict=True) for path in font_files})
    total = 0
    before = {}
    for path in selected:
        _budget(deadline)
        observed = _file(path, deadline=deadline)
        total += observed["bytes"]
        if total > MAX_FONT_BYTES:
            raise ValueError("selected native font aggregate bytes exceed the original finite bound")
        before[path] = observed
    matches: dict[str, list[dict[str, Any]]] = {name: [] for name in required}
    for path in selected:
        _budget(deadline)
        with path.open("rb") as file:
            magic = file.read(4)
        if magic not in {b"ttcf", b"OTTO", b"\x00\x01\x00\x00", b"true", b"typ1"}:
            raise ValueError("selected native font requires unsupported table decoding")
        collection = TTCollection(str(path), lazy=True) if magic == b"ttcf" else None
        single = None if collection is not None else TTFont(str(path), lazy=True)
        faces = collection.fonts if collection is not None else [single]
        if len(faces) > 256:
            raise ValueError("selected native font collection face count exceeds finite bound")
        try:
            for index, face in enumerate(faces):
                _budget(deadline)
                if face is None:
                    raise ValueError("selected native font face is absent")
                name = face["name"].getDebugName(6)
                if name in required:
                    matches[name].append({"postscript_name": name, "face_index": index, **before[path]})
        finally:
            if collection is not None:
                collection.close()
            elif single is not None:
                single.close()
        if _file(path, deadline=deadline) != before[path]:
            raise ValueError("actual Mermaid font bytes changed while decoding original face tables")
    for name, rows in matches.items():
        if len({(row["sha256"], row["face_index"]) for row in rows}) != 1:
            raise ValueError("actual Mermaid platform font has missing/ambiguous byte ownership: " + name)
    result = {
        "schema_version": FONT_SCHEMA,
        "platform_fonts": platform_fonts,
        "font_faces": [rows[0] for _, rows in sorted(matches.items())],
    }
    return {**result, "content_digest": canonical_digest(result)}


def validate_platform_font_files(raw: dict[str, Any]) -> None:
    """Validate original portable face ownership without producer-path reads."""
    default = raw.get("schema_version") == DEFAULT_FONT_SCHEMA
    expected = {"schema_version", "platform_fonts", "font_faces", "content_digest"}
    if default:
        from infrastructure.rendering._mermaid_source_font_default import validate_default_font_buffers

        expected.add("source_default_buffers")
        validate_default_font_buffers(raw.get("source_default_buffers"))
    if set(raw) != expected or raw["schema_version"] not in {FONT_SCHEMA, DEFAULT_FONT_SCHEMA}:
        raise ValueError("portable actual platform-font custody schema differs")
    required = _default_font_names(raw["platform_fonts"]) if default else _font_names(raw["platform_fonts"])
    faces = raw["font_faces"]
    if not isinstance(faces, list) or len(faces) != len(required):
        raise ValueError("portable actual native font-face closure is incomplete")
    seen = set()
    for row in faces:
        if (
            not isinstance(row, dict)
            or set(row) != {"postscript_name", "face_index", "bytes", "sha256"}
            or row["postscript_name"] not in required
            or row["postscript_name"] in seen
            or type(row["face_index"]) is not int
            or not 0 <= row["face_index"] < 256
        ):
            raise ValueError("portable actual font face is undeclared/duplicate")
        _validate_file_identity({"bytes": row["bytes"], "sha256": row["sha256"]})
        if default:
            from infrastructure.rendering._web_font_assets import FONT_BODIES
            from infrastructure.rendering._mermaid_source_font_default import NAMES

            if row["postscript_name"] in NAMES:
                original = FONT_BODIES[row["postscript_name"]]
                if row["face_index"] != 0 or row["sha256"] != original["sha256"] or row["bytes"] != original["bytes"]:
                    raise ValueError("portable Source custom face is not the exact declared font body")
        seen.add(row["postscript_name"])
    if raw["content_digest"] != canonical_digest({key: value for key, value in raw.items() if key != "content_digest"}):
        raise ValueError("portable actual font custody digest differs")


def admit_reader_platform_fonts(
    original: dict[str, Any],
    font_files: tuple[Path, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Reconstruct the original platform face map from explicit reader files."""
    validate_platform_font_files(original)
    if original["schema_version"] == DEFAULT_FONT_SCHEMA:
        from infrastructure.reporting.native_mermaid_font_bodies import (
            NativeMermaidFontSelection,
            admit_source_mermaid_font_bodies,
        )
        from infrastructure.reporting.native_tool_producer import current_native_producer_operation

        producer = current_native_producer_operation()
        if producer is None:
            raise ValueError("Source-default font replay requires actual current Source producer")
        owner = admit_source_mermaid_font_bodies(
            NativeMermaidFontSelection(font_files), producer.source, deadline=deadline
        )
        try:
            for face in original["font_faces"]:
                content, index = owner.face_bytes(face["postscript_name"], deadline=deadline)
                if (
                    index != face["face_index"]
                    or len(content) != face["bytes"]
                    or hashlib.sha256(content).hexdigest() != face["sha256"]
                ):
                    raise ValueError("reader Source-declared or explicitly nominated override face body differs")
            owner.verify_terminal_bytes(deadline=deadline)
        finally:
            owner.close()
        return original
    current = observe_platform_font_files(original["platform_fonts"], font_files, deadline=deadline)
    if current != original:
        raise ValueError("reader-local native font-face bytes differ from original painted labels")
    return current
