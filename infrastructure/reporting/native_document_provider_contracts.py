"""Pure Source pin selection; provider declarations grant no native authority."""

from __future__ import annotations

import base64
import binascii
import json
import re
from pathlib import PurePosixPath
from typing import Any

PIN_SOURCE = "infrastructure/config/native-document-providers.json"
SCHEMA = "template-native-document-providers-v2"
MAX_MANIFEST_BYTES = 128 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_BINARY_BYTES = 512 * 1024 * 1024
SOURCE_REVISION = "e6c2ae3418dcf63f974802f8b7c105ebc299706c"
BUILD_RECIPE = "infrastructure/config/native-document-build.nix"
BUILD_FREEZE = "infrastructure/config/native-document-build.freeze"
_STORE_PATH = r"/nix/store/[0-9abcdfghijklmnpqrsvwxyz]{32}-[A-Za-z0-9+._?=-]+"
_HOSTS = {"Linux-x86_64", "Darwin-arm64", "Darwin-x86_64"}


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("document provider manifest has duplicate fields")
        result[key] = value
    return result


def _nonfinite(value: str) -> Any:
    raise ValueError("document provider manifest contains a nonfinite number")


def _fields(value: Any, fields: set[str], label: str) -> None:
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f"document provider {label} has unknown or missing fields")


def _digest(value: Any, label: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"document provider {label} is not an exact SHA-256")


def _size(value: Any, limit: int, label: str) -> None:
    if type(value) is not int or not 0 < value <= limit:
        raise ValueError(f"document provider {label} exceeds its positive finite byte bound")


def _member(value: Any) -> None:
    if type(value) is not str or not value or "\\" in value or "\x00" in value:
        raise ValueError("document provider member is unsafe")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value or not path.parts:
        raise ValueError("document provider member is unsafe or noncanonical")


def _build(value: Any) -> None:
    _fields(
        value,
        {
            "flake_url",
            "revision",
            "nar_hash",
            "flake_lock_sha256",
            "upstream_freeze_sha256",
            "upstream_compiler",
            "recipe_path",
            "recipe_sha256",
            "freeze_path",
            "freeze_sha256",
            "resolved_freeze_sha256",
            "compiler",
            "compiler_derivation",
            "compiler_output",
            "plan_derivation",
            "plan_output",
            "ghc_options",
            "derivation",
            "output",
        },
        "source build",
    )
    if (
        value["revision"] != SOURCE_REVISION
        or value["upstream_compiler"] != "ghc-9.8.4"
        or value["compiler"] != "ghc-9.12.2"
        or value["ghc_options"] != ["-fobject-determinism"]
    ):
        raise ValueError("document provider source/compiler/options differ from the reviewed deterministic recipe")
    if value["flake_url"] != f"git+https://github.com/lierdakil/pandoc-crossref?rev={SOURCE_REVISION}":
        raise ValueError("document provider flake must pin the exact reviewed upstream source")
    if value["recipe_path"] != BUILD_RECIPE or value["freeze_path"] != BUILD_FREEZE:
        raise ValueError("document provider build inputs must name the exact reviewed Root recipe and freeze")
    for field in (
        "flake_lock_sha256",
        "upstream_freeze_sha256",
        "recipe_sha256",
        "freeze_sha256",
        "resolved_freeze_sha256",
    ):
        _digest(value[field], field)
    nar = value["nar_hash"]
    if type(nar) is not str or not nar.startswith("sha256-"):
        raise ValueError("document provider source requires a canonical SHA-256 NAR hash")
    try:
        decoded = base64.b64decode(nar[7:], validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError("document provider source NAR hash is malformed") from error
    if len(decoded) != 32 or base64.b64encode(decoded).decode("ascii") != nar[7:]:
        raise ValueError("document provider source NAR hash is noncanonical")
    for field in ("derivation", "output", "compiler_derivation", "compiler_output", "plan_derivation", "plan_output"):
        path = value[field]
        derivation = field.endswith("derivation")
        if type(path) is not str or re.fullmatch(_STORE_PATH, path) is None or path.endswith(".drv") != derivation:
            raise ValueError(f"document provider {field} is not an exact reviewed Nix store path")
        suffix = "-pandoc-with-crossref" if field in {"derivation", "output"} else "-ghc-9.12.2"
        if not field.startswith("plan_") and not path.endswith(suffix + (".drv" if derivation else "")):
            raise ValueError(f"document provider {field} selects a different named build component")


def _tool(value: Any, name: str, host: str, kind: str) -> None:
    common = {"version", "asset", "member"}
    fields = (
        {"binary_sha256", "binary_bytes"}
        if kind == "nix-source-build"
        else {"url", "format", "archive_sha256", "archive_bytes"}
    )
    _fields(value, common | fields, f"{name} tool")
    version = "3.11" if name == "pandoc" else "v0.3.25a"
    if value["version"] != version:
        raise ValueError("document provider nominal tool version differs from the reviewed JSON API pair")
    _member(value["member"])
    if kind == "nix-source-build":
        executable = "pandoc" if name == "pandoc" else "pandoc-crossref"
        asset = f"{executable}-{version}-linux-x86_64-source.tar.xz"
        if value["asset"] != asset or value["member"] != executable:
            raise ValueError("document source-built tool has an unknown archive or executable member")
        _digest(value["binary_sha256"], "binary_sha256")
        _size(value["binary_bytes"], MAX_BINARY_BYTES, "binary_bytes")
        return
    arm = host == "Darwin-arm64"
    if name == "pandoc":
        architecture = "arm64" if arm else "x86_64"
        asset = f"pandoc-{version}-{architecture}-macOS.zip"
        member = f"pandoc-{version}-{architecture}/bin/pandoc"
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/{asset}"
        archive_format = "zip"
    else:
        architecture = "ARM64" if arm else "X64"
        asset = f"pandoc-crossref-macOS-{architecture}.tar.xz"
        member = "pandoc-crossref"
        url = f"https://github.com/lierdakil/pandoc-crossref/releases/download/{version}/{asset}"
        archive_format = "tar.xz"
    if (value["asset"], value["member"], value["url"], value["format"]) != (asset, member, url, archive_format):
        raise ValueError("document official archive is not the reviewed platform release/member")
    _digest(value["archive_sha256"], "archive_sha256")
    _size(value["archive_bytes"], MAX_ARCHIVE_BYTES, "archive_bytes")


def select_document_provider(content: bytes, host: dict[str, str]) -> dict[str, Any]:
    """Validate the entire closed union before selecting an actual supported host."""
    if (
        type(host) is not dict
        or set(host) != {"system", "machine"}
        or any(type(value) is not str for value in host.values())
    ):
        raise ValueError("document provider requires exact actual system and machine facts")
    machine = "x86_64" if host == {"system": "Linux", "machine": "amd64"} else host["machine"]
    selected = f"{host['system']}-{machine}"
    if selected not in _HOSTS:
        raise ValueError("document provider has no admitted provider for this actual host")
    if type(content) is not bytes or not 0 < len(content) <= MAX_MANIFEST_BYTES:
        raise ValueError("document provider manifest exceeds its finite byte bound")
    try:
        document = json.loads(content.decode("utf-8"), object_pairs_hook=_object, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("document provider manifest is not bounded UTF-8 JSON") from error
    _fields(document, {"schema_version", "providers"}, "manifest")
    if document["schema_version"] != SCHEMA:
        raise ValueError("document provider manifest schema is unsupported")
    providers: dict[str, dict[str, Any]] = document["providers"]
    _fields(providers, _HOSTS, "host roster")
    for platform, provider in providers.items():
        linux = platform == "Linux-x86_64"
        _fields(provider, {"kind", "tools", "build"} if linux else {"kind", "tools"}, "row")
        kind = "nix-source-build" if linux else "official-archives"
        if provider["kind"] != kind:
            raise ValueError("document provider kind is unsupported for the declared host")
        if linux:
            _build(provider["build"])
        _fields(provider["tools"], {"pandoc", "crossref"}, "tool roster")
        for name, tool in provider["tools"].items():
            _tool(tool, name, platform, kind)
    return providers[selected]


def select_document_tool(content: bytes, host: dict[str, str], name: str) -> dict[str, Any]:
    """Select only the Source tool row, retaining the Linux build declaration."""
    if type(name) is not str or name not in {"pandoc", "crossref"}:
        raise ValueError("document provider has no admitted tool with this name")
    provider = select_document_provider(content, host)
    result = {**provider["tools"][name], "kind": provider["kind"]}
    if provider["kind"] == "nix-source-build":
        result["build"] = provider["build"]
    return result
