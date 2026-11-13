"""Source provider selection and real bounded preparation refusal boundaries."""

from __future__ import annotations

import hashlib
import json
import stat
import struct
import subprocess
import sys
import time
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from infrastructure.reporting.native_document_elf import glibc_interpreter, require_glibc_executable
from infrastructure.reporting.native_document_preparation import (
    _canonical_archive,
    _require_derivation_graph,
    document_archive_member,
    prepare_document_providers,
)
from infrastructure.reporting.native_document_provider_contracts import (
    PIN_SOURCE,
    select_document_provider,
    select_document_tool,
)

_REPO = Path(__file__).resolve().parents[3]
_LINUX = {"system": "Linux", "machine": "x86_64"}


def _manifest() -> dict:
    return json.loads((_REPO / PIN_SOURCE).read_bytes())


def _content(document: dict) -> bytes:
    return json.dumps(document).encode()


def _fixture_pin(body: bytes, *, name: str = "crossref") -> dict:
    pin = select_document_tool(_content(_manifest()), _LINUX, name)
    # This is parser fixture DATA only, never an actual native source admission.
    return {**pin, "binary_sha256": hashlib.sha256(body).hexdigest(), "binary_bytes": len(body)}


@pytest.mark.parametrize(
    "host",
    [
        {"system": "Linux", "machine": "aarch64"},
        {"system": "Linux", "machine": "ARM64"},
        {"system": "Darwin", "machine": "amd64"},
        {"system": "Windows", "machine": "x86_64"},
        {"system": "Linux", "machine": "x86_64", "provider": "official-archives"},
        {"system": "Linux", "machine": True},
        {},
    ],
)
def test_unknown_host_cannot_choose_a_provider(host: dict) -> None:
    with pytest.raises(ValueError):
        select_document_provider(_content(_manifest()), host)


@pytest.mark.parametrize(
    "path,value",
    [
        (("extra",), True),
        (("schema_version",), "unknown"),
        (("providers", "FreeBSD-x86_64"), {}),
        (("providers", "Linux-x86_64", "kind"), "official-archives"),
        (("providers", "Linux-x86_64", "build", "compiler"), "ghc-latest"),
        (("providers", "Linux-x86_64", "build", "compiler"), "ghc-9.8.4"),
        (("providers", "Linux-x86_64", "build", "upstream_compiler"), "ghc-9.12.2"),
        (("providers", "Linux-x86_64", "build", "ghc_options"), []),
        (("providers", "Linux-x86_64", "build", "recipe_path"), "../unreviewed.nix"),
        (("providers", "Linux-x86_64", "build", "freeze_path"), "/tmp/unreviewed.freeze"),
        (("providers", "Linux-x86_64", "build", "compiler_patch_path"), "/tmp/unreviewed.patch"),
        (("providers", "Linux-x86_64", "build", "compiler_patch_sha256"), "A" * 64),
        (("providers", "Linux-x86_64", "build", "resolved_freeze_sha256"), "A" * 64),
        (("providers", "Linux-x86_64", "build", "compiler_output"), "/nix/store/../ghc-9.12.2"),
        (("providers", "Linux-x86_64", "build", "plan_derivation"), "/tmp/unreviewed.drv"),
        (("providers", "Linux-x86_64", "build", "revision"), "0" * 40),
        (("providers", "Linux-x86_64", "build", "nar_hash"), "sha256-not-a-hash"),
        (("providers", "Linux-x86_64", "build", "flake_url"), "github:lierdakil/pandoc-crossref#pandoc-with-crossref"),
        (("providers", "Linux-x86_64", "build", "flake_url"), []),
        (("providers", "Linux-x86_64", "build", "derivation"), "/nix/store/../bad.drv"),
        (("providers", "Linux-x86_64", "tools", "pandoc", "binary_bytes"), True),
        (("providers", "Linux-x86_64", "tools", "crossref", "binary_sha256"), "A" * 64),
        (("providers", "Linux-x86_64", "tools", "crossref", "archive_sha256"), "0" * 64),
        (("providers", "Darwin-arm64", "build"), {}),
        (("providers", "Darwin-arm64", "tools", "crossref", "member"), "../pandoc-crossref"),
        (("providers", "Darwin-x86_64", "tools", "pandoc", "member"), "/bin/pandoc"),
        (("providers", "Darwin-x86_64", "tools", "pandoc", "url"), "https://example.org/pandoc.zip"),
        (("providers", "Darwin-x86_64", "tools", "crossref", "format"), "zip"),
        (("providers", "Darwin-x86_64", "tools", "crossref", "archive_bytes"), 0),
    ],
)
def test_malformed_pin_in_any_union_branch_is_rejected(path: tuple[str, ...], value: object) -> None:
    document = _manifest()
    row = document
    for field in path[:-1]:
        row = row[field]
    row[path[-1]] = value
    with pytest.raises(ValueError):
        select_document_provider(_content(document), _LINUX)


@pytest.mark.parametrize("content", [b"", b"[]", b"null", b"{", b"\xff", b'{"n":NaN}', b" " * 131073])
def test_manifest_is_bounded_unambiguous_utf8_json(content: bytes) -> None:
    with pytest.raises(ValueError):
        select_document_provider(content, _LINUX)


@pytest.mark.parametrize("field", ["schema_version", "binary_bytes"])
def test_duplicate_manifest_fields_are_rejected_at_every_depth(field: str) -> None:
    content = _content(_manifest())
    token = json.dumps(field).encode() + b":"
    ambiguous = content.replace(token, token + b"1," + token, 1)
    assert ambiguous != content
    with pytest.raises(ValueError, match="duplicate"):
        select_document_provider(ambiguous, _LINUX)


@pytest.mark.parametrize("name", ["", "pandoc-crossref", "compiler", None])
def test_tool_selector_has_no_caller_selected_fallback(name: str | None) -> None:
    with pytest.raises(ValueError):
        select_document_tool(_content(_manifest()), _LINUX, name)  # type: ignore[arg-type]


@pytest.mark.parametrize("fault", ["digest", "length", "member", "trailing", "truncated"])
def test_source_archive_rejects_tampered_complete_transport_or_body(fault: str) -> None:
    body = b"complete source-owned parser fixture body\n"
    pin = _fixture_pin(body)
    content = _canonical_archive(body, pin["member"])
    if fault == "digest":
        pin["binary_sha256"] = "0" * 64
    elif fault == "length":
        pin["binary_bytes"] += 1
    elif fault == "member":
        content = _canonical_archive(body, "other-member")
    elif fault == "trailing":
        content += b"trailing bytes"
    else:
        content = content[:-1]
    with pytest.raises((ValueError, EOFError)):
        document_archive_member(content, pin, deadline=time.monotonic() + 10)


def _official_zip(body: bytes, member: str) -> bytes:
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        row = zipfile.ZipInfo(member)
        row.external_attr = (stat.S_IFREG | 0o755) << 16
        archive.writestr(row, body)
    return stream.getvalue()


@pytest.mark.parametrize("fault", ["none", "digest", "length", "unsafe-member"])
def test_official_archive_keeps_complete_archive_authenticity(fault: str) -> None:
    pin = select_document_tool(_content(_manifest()), {"system": "Darwin", "machine": "arm64"}, "pandoc")
    body = b"official archive parser fixture body"
    content = _official_zip(body, "../unsafe" if fault == "unsafe-member" else pin["member"])
    pin = {**pin, "archive_bytes": len(content), "archive_sha256": hashlib.sha256(content).hexdigest()}
    if fault == "digest":
        pin["archive_sha256"] = "0" * 64
    elif fault == "length":
        pin["archive_bytes"] += 1
    if fault == "none":
        assert document_archive_member(content, pin, deadline=time.monotonic() + 10) == body
    else:
        with pytest.raises(ValueError):
            document_archive_member(content, pin, deadline=time.monotonic() + 10)


@pytest.mark.parametrize("selected_alias", [False, True])
def test_official_zip_aliases_cannot_replace_the_selected_regular_body(selected_alias: bool) -> None:
    pin = select_document_tool(_content(_manifest()), {"system": "Darwin", "machine": "arm64"}, "pandoc")
    body = b"regular executable parser fixture, not native evidence"
    regular = pin["member"] + "-body" if selected_alias else pin["member"]
    stream = BytesIO(_official_zip(body, regular))
    with zipfile.ZipFile(stream, "a") as archive:
        alias = zipfile.ZipInfo(pin["member"] if selected_alias else pin["member"] + "-alias")
        alias.external_attr = (stat.S_IFLNK | 0o755) << 16
        archive.writestr(alias, regular.rsplit("/", 1)[-1])
    content = stream.getvalue()
    pin = {**pin, "archive_bytes": len(content), "archive_sha256": hashlib.sha256(content).hexdigest()}
    if selected_alias:
        with pytest.raises(ValueError):
            document_archive_member(content, pin, deadline=time.monotonic() + 10)
    else:
        assert document_archive_member(content, pin, deadline=time.monotonic() + 10) == body


def test_tampered_cache_cannot_trigger_build_or_publish_a_path(tmp_path: Path) -> None:
    pin = select_document_tool(_content(_manifest()), _LINUX, "pandoc")
    archives = tmp_path / "archives"
    archives.mkdir()
    (archives / pin["asset"]).write_bytes(_canonical_archive(b"not the exact Source binary", pin["member"]))
    destination = tmp_path / "not-created"
    with pytest.raises(ValueError):
        prepare_document_providers(_REPO, archives, destination, host=_LINUX, deadline=time.monotonic() + 10)
    assert not destination.exists()
    assert {path.name for path in tmp_path.iterdir()} == {"archives"}


@pytest.mark.parametrize("changed", ["recipe", "freeze", "compiler_patch", "missing_compiler_patch"])
def test_changed_root_build_input_cannot_trigger_acquisition(tmp_path: Path, changed: str) -> None:
    source = tmp_path / "source"
    manifest = source / PIN_SOURCE
    manifest.parent.mkdir(parents=True)
    document = _manifest()
    manifest.write_bytes(_content(document))
    for name in ("recipe", "freeze", "compiler_patch"):
        if name == "compiler_patch" and changed == "missing_compiler_patch":
            continue
        relative = document["providers"]["Linux-x86_64"]["build"][name + "_path"]
        body = (_REPO / relative).read_bytes()
        (source / relative).write_bytes(body + b"\n# changed after pinning\n" if name == changed else body)
    archives, destination = tmp_path / "archives", tmp_path / "destination"
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare_document_providers(
            source,
            archives,
            destination,
            host=_LINUX,
            nix=tmp_path / "must-not-launch",
            deadline=time.monotonic() + 10,
        )
    assert not archives.exists() and not destination.exists()


def test_cli_rejects_malformed_source_before_acquisition(tmp_path: Path) -> None:
    source = tmp_path / "source"
    manifest = source / PIN_SOURCE
    manifest.parent.mkdir(parents=True)
    document = _manifest()
    document["providers"]["Linux-x86_64"]["build"]["compiler"] = "unconstrained"
    manifest.write_bytes(_content(document))
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            'import runpy,sys; sys.path.insert(0,sys.argv.pop(1)); runpy.run_module("infrastructure.reporting.native_document_preparation",run_name="__main__")',
            str(_REPO),
            "--source-root",
            str(source),
            "--archives",
            str(tmp_path / "archives"),
            "--destination",
            str(tmp_path / "destination"),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode != 0
    assert not (tmp_path / "archives").exists() and not (tmp_path / "destination").exists()


def _elf(interpreter: bytes | None, machine: int = 62) -> bytes:
    count = 1 if interpreter is None else 2
    size = 64 + 56 * count + (0 if interpreter is None else len(interpreter))
    header = struct.pack(
        "<16sHHIQQQIHHHHHH", b"\x7fELF\x02\x01\x01" + b"\0" * 9, 3, machine, 1, 0, 64, 0, 0, 64, 56, count, 0, 0, 0
    )
    load = struct.pack("<IIQQQQQQ", 1, 5, 0, 0, 0, size, size, 4096)
    if interpreter is None:
        return header + load
    return (
        header
        + load
        + struct.pack("<IIQQQQQQ", 3, 4, 64 + 56 * count, 0, 0, len(interpreter), len(interpreter), 1)
        + interpreter
    )


@pytest.mark.parametrize(
    "machine,abi,loader",
    [
        (62, "x86_64", "/lib64/ld-linux-x86-64.so.2"),
        (62, "amd64", "/lib64/ld-linux-x86-64.so.2"),
        (183, "aarch64", "/lib/ld-linux-aarch64.so.1"),
        (183, "arm64", "/lib/ld-linux-aarch64.so.1"),
    ],
)
def test_real_elf_interpreter_structure_preserves_both_reviewed_abis(machine: int, abi: str, loader: str) -> None:
    assert glibc_interpreter(_elf(loader.encode() + b"\0", machine), machine=abi) == loader


@pytest.mark.parametrize(
    "body",
    [
        b"#!/bin/sh\nexit 0\n",
        _elf(None),
        _elf(b"/lib/ld-musl-x86_64.so.1\0"),
        _elf(b"/lib64/ld-linux-x86-64.so.2"),
        _elf(b"/lib64/ld-linux-x86-64.so.2\0extra\0"),
    ],
)
def test_static_musl_wrappers_and_malformed_interp_are_not_dynamic_glibc(body: bytes) -> None:
    with pytest.raises(ValueError):
        glibc_interpreter(body, machine="x86_64")


def test_physical_glibc_check_refuses_a_wrapper(tmp_path: Path) -> None:
    wrapper = tmp_path / "pandoc"
    wrapper.write_bytes(b"#!/bin/sh\nprintf 'pandoc 3.11\\n'\n")
    wrapper.chmod(0o755)
    with pytest.raises(ValueError):
        require_glibc_executable(wrapper, machine="x86_64")


@pytest.mark.parametrize("fault", ["root", "duplicate", "machine", "output", "version", "unversioned-basename"])
def test_actual_nix_derivation_cannot_override_source_build_pins(fault: str) -> None:
    build = select_document_provider(_content(_manifest()), _LINUX)["build"]
    path = build["derivation"]
    row = {"system": "x86_64-linux", "outputs": {"out": {"path": build["output"]}}}
    graph = {path: row}
    if fault == "root":
        graph = {path + "-other": row}
    elif fault == "duplicate":
        graph[Path(path).name] = row
    elif fault == "machine":
        row["system"] = "aarch64-linux"
    elif fault == "output":
        row["outputs"]["out"]["path"] += "-other"
    elif fault == "version":
        row["version"] = 99
    else:
        graph = {Path(path).name: row}
    with pytest.raises(ValueError):
        _require_derivation_graph(graph, build)
