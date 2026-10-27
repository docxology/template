"""Observe actual print font resources without redistributing installed fonts."""

from __future__ import annotations

import ast
import hashlib
import importlib
import io
import os
import re
from dataclasses import fields
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.reporting.native_storybook_source import source_identity, source_package

SCHEMA = "template-print-font-observation-v1"
MAX_FONT_BYTES = 64 * 1024 * 1024
ROLES = {
    "storybook": ("regular", "bold"),
    "newspaper": (
        "display",
        "display_bold",
        "body",
        "body_bold",
        "body_italic",
        "body_bolditalic",
        "sans",
        "sans_bold",
    ),
}
_SYSTEM = ("/System/Library/Fonts/", "/Library/Fonts/", "/usr/share/fonts/", "/usr/local/share/fonts/")


def _resource(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if not any(str(path).startswith(prefix) for prefix in _SYSTEM):
        raise ValueError("print font is outside admitted installed system font resources")
    before = path.stat()
    content = read_bytes_confined(path.parent, path, max_bytes=MAX_FONT_BYTES)
    after = path.stat()

    def identity(value: os.stat_result) -> list[int]:
        return [value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns]

    if identity(before) != identity(after) or len(content) != before.st_size:
        raise ValueError("original print font changed during bounded observation")
    return {
        "path": str(path),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "identity": identity(before),
    }


def _name(value: object) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(char) < 32 for char in value):
        raise ValueError("print font has no bounded explicit native face name")
    return value


def _builtin_newspaper_font(face: object, name: str) -> bool:
    """Recognize the actual ReportLab base-14 provider and its integer flag."""
    from reportlab.pdfbase import pdfmetrics

    flag = getattr(face, "builtIn", None)
    return (
        isinstance(face, pdfmetrics.TypeFace)
        and type(face) is pdfmetrics.TypeFace
        and type(flag) in (bool, int)
        and flag == 1
        and name in pdfmetrics.standardFonts
        and face.name == name
    )


def observe_print_fonts(project: Path, kind: str) -> dict[str, Any]:
    """Observe real provider choices with original resource bytes before/after.

    Source review admits the canonical literal font selection implementation.
    This local transcript is coupled to its enclosing original native worker;
    metadata hashes alone are not an execution or remote-origin attestation.
    """
    if kind not in ROLES:
        raise ValueError("unknown source print font selection")
    identity = source_identity(project)
    rendering = source_package(project, kind)
    provider = importlib.import_module(
        rendering.__package__ + (".text_layout" if kind == "storybook" else ".typography")
    )
    if not isinstance(provider.__file__, str):
        raise ValueError("missing current font selector source")
    path = Path(provider.__file__).resolve(strict=True)
    if not path.is_relative_to(project.resolve() / "src"):
        raise ValueError("font selector is outside current source provider")
    source = read_bytes_confined(project, path, max_bytes=512 * 1024)
    candidates = {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lower().endswith((".ttf", ".ttc", ".otf"))
    }
    held = {}
    names = {Path(candidate).name for candidate in candidates}
    resources = {
        Path(candidate) for candidate in candidates if Path(candidate).is_absolute() and Path(candidate).is_file()
    }
    # Pillow can resolve a requested basename in its installed font directories.
    # Admit every matching public system resource before the actual load occurs.
    for prefix in _SYSTEM:
        for parent, directories, files in os.walk(prefix, followlinks=False):
            directories[:] = [name for name in directories if not (Path(parent) / name).is_symlink()]
            resources.update(Path(parent) / name for name in files if name in names)
    if len(resources) > 64:
        raise ValueError("candidate print font resource closure exceeds its finite file budget")
    for resource in sorted(resources):
        row = _resource(resource)
        held[row["path"]] = row
    roles = []
    if kind == "storybook":
        for role, bold in (("regular", False), ("bold", True)):
            font = provider.load_font(27, bold=bold)
            origin = getattr(font, "path", None)
            if isinstance(origin, str):
                actual = _resource(Path(origin))
                if held.get(actual["path"]) != actual:
                    raise ValueError("selected print font was not admitted before native loading")
                roles.append(
                    {
                        "role": role,
                        "kind": "system-file",
                        "resource": actual,
                        "native_face": [_name(item) for item in font.getname()],
                        "index": font.index,
                    }
                )
            elif isinstance(origin, io.BytesIO):
                content = origin.getvalue()
                if not 0 < len(content) <= MAX_FONT_BYTES:
                    raise ValueError("embedded font exceeds its finite provider budget")
                roles.append(
                    {
                        "role": role,
                        "kind": "embedded-provider",
                        "resource": {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()},
                        "native_face": [_name(item) for item in font.getname()],
                        "index": font.index,
                    }
                )
            else:
                raise ValueError("selected print font has unsupported original resource custody")
    else:
        from reportlab.pdfbase import pdfmetrics

        selected = provider.register_fonts()
        if tuple(field.name for field in fields(selected)) != ROLES[kind]:
            raise ValueError("source newspaper font roles changed")
        for role in ROLES[kind]:
            name = getattr(selected, role)
            font = pdfmetrics.getFont(name)
            face = font.face
            origin = getattr(face, "filename", None)
            if isinstance(origin, str):
                actual = _resource(Path(origin))
                if held.get(actual["path"]) != actual:
                    raise ValueError("selected print font was not admitted before native loading")
                loaded = getattr(face, "_ttf_data", None)
                if not isinstance(loaded, bytes) or hashlib.sha256(loaded).hexdigest() != actual["sha256"]:
                    raise ValueError("native loaded newspaper font differs from original complete resource")
                roles.append(
                    {
                        "role": role,
                        "kind": "system-file",
                        "resource": actual,
                        "native_face": [_name(face.name)],
                        "index": None,
                    }
                )
            elif _builtin_newspaper_font(face, name):
                roles.append(
                    {
                        "role": role,
                        "kind": "builtin-provider",
                        "resource": None,
                        "native_face": [_name(face.name)],
                        "index": None,
                    }
                )
            else:
                raise ValueError("selected newspaper font has unsupported original provider custody")
    if read_bytes_confined(project, path, max_bytes=512 * 1024) != source or source_identity(project) != identity:
        raise ValueError("print font source provider changed during native observation")
    for row in held.values():
        if _resource(Path(row["path"])) != row:
            raise ValueError("original print font resources changed during native observation")
    return {
        "schema_version": SCHEMA,
        "kind": kind,
        "source_identity": identity,
        "selector_path": path.relative_to(project).as_posix(),
        "selector_sha256": hashlib.sha256(source).hexdigest(),
        "roles": roles,
    }


def validate_print_fonts(raw: object, kind: str, project: Path) -> None:
    """Validate transported original observations without opening producer fonts."""
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "kind",
        "source_identity",
        "selector_path",
        "selector_sha256",
        "roles",
    }:
        raise ValueError("original print font observation has incomplete or extra fields")
    expected_path = f"src/{kind}/" + ("text_layout.py" if kind == "storybook" else "typography.py")
    if (
        kind not in ROLES
        or raw["schema_version"] != SCHEMA
        or raw["kind"] != kind
        or raw["source_identity"] != source_identity(project)
        or raw["selector_path"] != expected_path
        or raw["selector_sha256"] != hashlib.sha256((project / expected_path).read_bytes()).hexdigest()
        or not isinstance(raw["roles"], list)
        or [row.get("role") for row in raw["roles"] if isinstance(row, dict)] != list(ROLES[kind])
    ):
        raise ValueError("original font/source role inventory is missing, changed or stale")
    for row in raw["roles"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"role", "kind", "resource", "native_face", "index"}
            or row["kind"] not in {"system-file", "embedded-provider", "builtin-provider"}
            or not isinstance(row["native_face"], list)
            or not 1 <= len(row["native_face"]) <= 2
            or row["index"] is not None
            and (type(row["index"]) is not int or not 0 <= row["index"] <= 64)
        ):
            raise ValueError("original native font role is malformed")
        for face in row["native_face"]:
            _name(face)
        if (
            kind == "storybook"
            and (len(row["native_face"]) != 2 or type(row["index"]) is not int or row["kind"] == "builtin-provider")
            or kind == "newspaper"
            and (len(row["native_face"]) != 1 or row["index"] is not None or row["kind"] == "embedded-provider")
        ):
            raise ValueError("original native font has an unsupported cross-provider role")
        resource = row["resource"]
        if row["kind"] == "builtin-provider":
            if resource is not None or kind != "newspaper":
                raise ValueError("builtin original print font has altered resource custody")
            continue
        expected = {"bytes", "sha256"} | ({"path", "identity"} if row["kind"] == "system-file" else set())
        if (
            not isinstance(resource, dict)
            or set(resource) != expected
            or type(resource["bytes"]) is not int
            or not 0 < resource["bytes"] <= MAX_FONT_BYTES
            or not isinstance(resource["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", resource["sha256"]) is None
        ):
            raise ValueError("original print font resource is unbounded or malformed")
        if row["kind"] == "system-file":
            path = resource["path"]
            if (
                not isinstance(path, str)
                or "\\" in path
                or "\0" in path
                or str(Path(path)) != path
                or ".." in Path(path).parts
                or not any(path.startswith(prefix) for prefix in _SYSTEM)
                or not isinstance(resource["identity"], list)
                or len(resource["identity"]) != 5
                or any(type(item) is not int or item < 0 for item in resource["identity"])
                or resource["identity"][2] != resource["bytes"]
            ):
                raise ValueError("original print font path/identity is malformed")
