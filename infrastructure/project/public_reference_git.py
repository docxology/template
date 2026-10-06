"""Read-only native Git custody for an explicitly nominated public reference."""

from __future__ import annotations

import configparser
import hashlib
import math
import os
import re
import shutil
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.project.git_guards import (
    ALLOWED_FOND_DIRS,
    ALLOWED_FONDS_TOPLEVEL_FILES,
    ALLOWED_PROJECT_DIRS,
    ALLOWED_PROJECTS_TOPLEVEL_FILES,
    ALLOWED_RULE_DIRS,
    ALLOWED_RULES_TOPLEVEL_FILES,
    ALLOWED_TOOL_DIRS,
    ALLOWED_TOOLS_TOPLEVEL_FILES,
)

MAX_GIT_BYTES = 16 * 1024 * 1024
MAX_FILES = 100_000
_PINNED_SUBMODULE = "infrastructure/steganography/kmyth"
_PINNED_SUBMODULE_URL = "https://github.com/docxology/kmyth.git"
_PARTIAL_CONFIGURATION = (
    "config",
    "--includes",
    "--get-regexp",
    r"^(extensions\.partialclone|remote\..*\.promisor)$",
)


@dataclass(frozen=True)
class GitFile:
    """One exact committed regular blob, never a filter's working-tree output."""

    mode: str
    oid: str
    path: str


@dataclass(frozen=True)
class GitReference:
    """Original native commit, object format and full committed/index inventory."""

    commit: str
    object_format: str
    files: tuple[GitFile, ...]
    gitlinks: tuple[GitFile, ...] = ()
    submodules: tuple[tuple[str, GitReference], ...] = ()


def remaining(deadline: float) -> float:
    """Share the original finite operation clock; never reset it per command."""
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("public reference requires an original finite monotonic deadline")
    value = deadline - time.monotonic()
    if value <= 0:
        raise TimeoutError("public reference deadline exhausted")
    return value


def native_git(root: Path, deadline: float, *arguments: str) -> bytes:
    """Use fixed native builtins with no replacement, ambient Git state or filters.

    Trusted read-only Git commands receive a finite remaining timeout. Filesystem
    enumeration and subprocess output allocation also require an enclosing
    supervised caller for a hard whole-operation/resource bound.
    """
    remaining(deadline)
    if arguments not in {
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--verify", "HEAD^{commit}"),
        ("rev-parse", "--show-object-format"),
        ("ls-tree", "-rz", "--full-tree", "HEAD"),
        ("ls-files", "--stage", "-z"),
        ("ls-files", "-v", "-z"),
        _PARTIAL_CONFIGURATION,
    }:
        raise ValueError("public reference permits only its fixed read-only native Git inventory commands")
    executable = shutil.which("git", path=os.defpath)
    if executable is None:
        raise ValueError("native Git is required for complete public source-data custody")
    environment = {
        "PATH": os.defpath,
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    if os.name == "nt" and "SystemRoot" in os.environ:
        environment["SystemRoot"] = os.environ["SystemRoot"]
    result = subprocess.run(  # nosec B603 -- selected native Git, fixed read-only builtin argv
        [
            executable,
            "--no-replace-objects",
            "--no-pager",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.hooksPath=" + os.devnull,
            *arguments,
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        timeout=min(30.0, remaining(deadline)),
        check=False,
    )
    remaining(deadline)
    if arguments == _PARTIAL_CONFIGURATION and result.returncode == 1 and not result.stdout and not result.stderr:
        return b""
    if result.returncode != 0 or result.stderr or len(result.stdout) > MAX_GIT_BYTES:
        raise ValueError("native public reference Git custody is unavailable or exceeds its bound")
    return result.stdout


def _path(raw: bytes) -> str:
    value = raw.decode("utf-8", errors="strict")
    parts = value.split("/")
    if not value or "\\" in value or "\0" in value or any(part in ("", ".", "..") for part in parts):
        raise ValueError("committed reference contains an unsupported lexical path")
    if Path(value).is_absolute():
        raise ValueError("committed reference path escapes its nominated root")
    return value


def _public_inventory_path(path: str) -> None:
    """Apply existing public project/resource confinement to native metadata."""
    parts = Path(path).parts
    if any(
        part in {".git", ".private_projects_root", ".env"}
        or part.startswith(".env.")
        and not part.endswith((".example", ".template"))
        for part in parts
    ):
        raise ValueError("native public reference inventory contains a private/control filename")
    policies = (
        ("projects/", ALLOWED_PROJECTS_TOPLEVEL_FILES, ALLOWED_PROJECT_DIRS),
        ("fonds/", ALLOWED_FONDS_TOPLEVEL_FILES, ALLOWED_FOND_DIRS),
        ("rules/", ALLOWED_RULES_TOPLEVEL_FILES, ALLOWED_RULE_DIRS),
        ("tools/", ALLOWED_TOOLS_TOPLEVEL_FILES, ALLOWED_TOOL_DIRS),
    )
    for prefix, navigation, directories in policies:
        if path.startswith(prefix) and path not in navigation and not path.startswith(directories):
            raise ValueError("native public reference inventory contains a private/control lifecycle or resource path")


def inventory(root: Path, expected_commit: str, deadline: float) -> GitReference:
    """Require exact native Root/index and its declared, initialized pinned submodule."""
    return _inventory(root, expected_commit, deadline, allow_submodule=True)


def _inventory(root: Path, expected_commit: str, deadline: float, *, allow_submodule: bool) -> GitReference:
    if root.absolute() != root.resolve(strict=True):
        raise ValueError("native reference refuses symlink checkout roots")
    initial = root.lstat()
    if not stat.S_ISDIR(initial.st_mode):
        raise ValueError("native reference requires its actual checkout directory")
    physical = initial.st_dev, initial.st_ino
    if not isinstance(expected_commit, str) or re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", expected_commit) is None:
        raise ValueError("public reference needs its harness-admitted full commit identity")
    top = native_git(root, deadline, "rev-parse", "--show-toplevel").decode().rstrip("\n")
    if Path(top).absolute() != root:
        raise ValueError("public reference must be the nominated native Git top-level")
    if native_git(root, deadline, *_PARTIAL_CONFIGURATION):
        raise ValueError("public reference refuses partial/promisor Git custody before object traversal")
    commit = native_git(root, deadline, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    object_format = native_git(root, deadline, "rev-parse", "--show-object-format").decode().strip()
    if (
        commit != expected_commit
        or object_format not in {"sha1", "sha256"}
        or len(commit) != (40 if object_format == "sha1" else 64)
    ):
        raise ValueError("public reference commit differs from its explicit admitted binding")
    files = []
    for raw in native_git(root, deadline, "ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0"):
        if not raw:
            continue
        header, filename = raw.split(b"\t", 1)
        mode, kind, oid = header.decode().split(" ")
        if (
            (mode, kind) not in {("100644", "blob"), ("100755", "blob"), ("160000", "commit")}
            or re.fullmatch(r"[0-9a-f]+", oid) is None
            or len(oid) != len(commit)
        ):
            raise ValueError("public reference refuses committed symlinks and unsupported objects")
        path = _path(filename)
        if allow_submodule:
            _public_inventory_path(path)
        else:
            _public_inventory_path(_PINNED_SUBMODULE + "/" + path)
        files.append(GitFile(mode, oid, path))
        if len(files) > MAX_FILES:
            raise ValueError("committed public reference inventory exceeds its file bound")
    if not files or len({row.path for row in files}) != len(files):
        raise ValueError("public reference needs a nonempty unique committed inventory")
    index = []
    for raw in native_git(root, deadline, "ls-files", "--stage", "-z").split(b"\0"):
        if not raw:
            continue
        header, filename = raw.split(b"\t", 1)
        mode, oid, stage = header.decode().split(" ")
        if stage != "0":
            raise ValueError("public reference index has an unresolved merge")
        index.append(GitFile(mode, oid, _path(filename)))
        if len(index) > MAX_FILES:
            raise ValueError("public reference index exceeds its file bound")
    if sorted(index, key=lambda row: row.path) != sorted(files, key=lambda row: row.path):
        raise ValueError("public reference index differs from its immutable committed tree")
    flagged = native_git(root, deadline, "ls-files", "-v", "-z").split(b"\0")
    flags = {_path(raw[2:]): raw[:2] for raw in flagged if raw}
    if set(flags) != {row.path for row in files} or any(value != b"H " for value in flags.values()):
        raise ValueError("public reference refuses skip-worktree, assume-unchanged or unsupported index flags")
    links = tuple(row for row in files if row.mode == "160000")
    submodules: tuple[tuple[str, GitReference], ...] = ()
    if links:
        if not allow_submodule or len(links) != 1 or links[0].path != _PINNED_SUBMODULE:
            raise ValueError("public reference refuses undeclared or nested submodules")
        declarations = configparser.ConfigParser(interpolation=None, strict=True)
        declaration_bytes = read_bytes_confined(root, root / ".gitmodules", max_bytes=64 * 1024)
        declaration_blob = next((row for row in files if row.path == ".gitmodules"), None)
        if declaration_blob is None or blob_identity(declaration_bytes, object_format) != declaration_blob.oid:
            raise ValueError("pinned submodule declaration differs from its actual Root committed blob")
        declarations.read_string(declaration_bytes.decode("utf-8"))
        section = 'submodule "' + _PINNED_SUBMODULE + '"'
        if (
            declarations.defaults()
            or declarations.sections() != [section]
            or not set(declarations[section]).issubset({"path", "url", "branch"})
            or declarations.get(section, "path", fallback="") != _PINNED_SUBMODULE
            or declarations.get(section, "url", fallback="") != _PINNED_SUBMODULE_URL
        ):
            raise ValueError("pinned public reference submodule differs from its actual declaration")
        nested = _inventory(root / links[0].path, links[0].oid, deadline, allow_submodule=False)
        if len(files) + len(nested.files) > MAX_FILES:
            raise ValueError("expanded committed public reference exceeds its file bound")
        submodules = ((links[0].path, nested),)
    final = root.lstat()
    if not stat.S_ISDIR(final.st_mode) or (final.st_dev, final.st_ino) != physical:
        raise ValueError("native public reference checkout changed during inventory")
    remaining(deadline)
    return GitReference(
        commit,
        object_format,
        tuple(sorted((row for row in files if row.mode != "160000"), key=lambda row: row.path)),
        links,
        submodules,
    )


def committed_blobs(reference: GitReference) -> dict[str, tuple[GitFile, str]]:
    """Expose genuine raw blobs with their own repository's object format."""
    result = {row.path: (row, reference.object_format) for row in reference.files}
    for prefix, nested in reference.submodules:
        for row in nested.files:
            path = prefix + "/" + row.path
            if path in result:
                raise ValueError("expanded committed public reference repeats a blob")
            result[path] = (row, nested.object_format)
    return result


def blob_identity(content: bytes, object_format: str) -> str:
    """Hash the genuine raw blob representation without textconv/checkout filters."""
    if object_format not in {"sha1", "sha256"}:
        raise ValueError("unsupported reference Git object format")
    framed = b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    return hashlib.new(object_format, framed, usedforsecurity=False).hexdigest()
