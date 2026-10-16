"""Prepare exact public fixture DATA from committed declarations, using stdlib only.

The direct-file entry point also works before hosted Python/dependency setup.
Preparation does not admit a Source reference or grant an acceptance gate.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, cast

MANIFEST_PATH = "infrastructure/config/acceptance-source-fixtures.json"
SCHEMA_VERSION = "template-acceptance-source-fixtures-v1"
# Match the existing public-reference/snapshot census and held-byte ceilings.
MAX_FILES = 100_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
_ROOTS = {
    "requests": "tests/fixtures/real_codebases/requests",
    "fastapi": "tests/fixtures/real_codebases/fastapi",
    "timeseries": "tests/fixtures/timeseries",
}
_SOURCES = {"requests": "psf/requests", "fastapi": "fastapi/fastapi"}
_SELECTIONS = {"requests": ["LICENSE", "src/requests"], "fastapi": ["LICENSE", "fastapi"]}
_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
_ANCESTOR_FLAGS = getattr(os, "O_PATH", os.O_RDONLY) | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise ValueError("fixture path must be a normalized relative lexical path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")) or str(path) != value:
        raise ValueError("fixture path is absolute, traversing or noncanonical")
    return value


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"fixture {label} has missing or unexpected fields")
    return cast(dict[str, Any], value)


def _digest(value: Any) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("fixture declaration needs an exact SHA-256")


def _size(value: Any) -> None:
    if type(value) is not int or not 0 <= value <= MAX_FILE_BYTES:
        raise ValueError("fixture declaration exceeds the existing file-byte ceiling")


def parse_fixture_manifest(content: bytes) -> dict[str, Any]:
    """Parse one strict declaration; callers first authenticate its Git blob.

    This function performs no filesystem reads, writes or network requests.
    The acquisition script and complete Source readers share this schema.
    """
    if not isinstance(content, bytes) or not content or len(content) > MAX_FILE_BYTES:
        raise ValueError("fixture manifest bytes are missing or exceed their held-byte ceiling")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("fixture manifest repeats a JSON field")
            result[key] = value
        return result

    manifest = _object(json.loads(content, object_pairs_hook=unique), {"schema_version", "groups"}, "manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError("fixture manifest schema is unsupported")
    groups = manifest["groups"]
    if not isinstance(groups, list) or len(groups) != len(_ROOTS):
        raise ValueError("fixture manifest requires its complete fixed group roster")
    seen: set[str] = set()
    total = count = 0
    for group in groups:
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("id"), str)
            or group["id"] not in _ROOTS
            or group["id"] in seen
        ):
            raise ValueError("fixture manifest contains an unknown or repeated group")
        name = group["id"]
        seen.add(name)
        keys = {"id", "root", "directories", "files"}
        _object(group, keys | ({"archive", "selections"} if name != "timeseries" else set()), "group")
        if group["root"] != _ROOTS[name]:
            raise ValueError("fixture group root differs from its fixed public destination")
        if name != "timeseries":
            archive = _object(group["archive"], {"url", "bytes", "sha256", "root"}, "archive")
            prefix = f"https://codeload.github.com/{_SOURCES[name]}/tar.gz/"
            url = archive["url"]
            if not isinstance(url, str) or not url.startswith(prefix):
                raise ValueError("fixture archive needs its fixed official HTTPS source")
            commit = url[len(prefix) :]
            if re.fullmatch(r"[0-9a-f]{40}", commit) is None or archive["root"] != f"{name}-{commit}":
                raise ValueError("fixture archive URL/root does not name an immutable source commit")
            _size(archive["bytes"])
            _digest(archive["sha256"])
            if not archive["bytes"] or group["selections"] != _SELECTIONS[name]:
                raise ValueError("fixture archive selection differs from its fixed library/license scope")
        files = group["files"]
        if not isinstance(files, list) or not files:
            raise ValueError("fixture group needs a nonempty exact file roster")
        paths: list[str] = []
        directories: set[str] = set()
        for record in files:
            _object(
                record,
                {"path", "source"} if name == "timeseries" else {"path", "member", "bytes", "sha256", "executable"},
                "file",
            )
            relative = _relative(record["path"])
            paths.append(relative)
            directories.update(str(parent) for parent in PurePosixPath(relative).parents if str(parent) != ".")
            if name == "timeseries":
                match = re.fullmatch(r"synthetic/synthetic_(00[1-9]|010)\.json", relative)
                if (
                    match is None
                    or record["source"] != "tests/fixtures/timeseries_seed/" + PurePosixPath(relative).name
                ):
                    raise ValueError("fixture seed destination/source is outside the fixed committed series roster")
            else:
                if record["member"] != group["archive"]["root"] + "/" + relative or not any(
                    relative == selected or relative.startswith(selected + "/") for selected in group["selections"]
                ):
                    raise ValueError("fixture archive member is outside its fixed selected tree")
                _size(record["bytes"])
                _digest(record["sha256"])
                if type(record["executable"]) is not bool:
                    raise ValueError("fixture executable declaration must be a boolean")
                total += record["bytes"]
            count += 1
        if paths != sorted(set(paths)):
            raise ValueError("fixture file roster is repeated or noncanonical")
        if group["directories"] != sorted(directories):
            raise ValueError("fixture directory roster differs from its exact file ancestors")
        if name == "timeseries" and len(paths) != 10:
            raise ValueError("fixture manifest requires every committed synthetic series")
        if count > MAX_FILES or total > MAX_TOTAL_BYTES:
            raise ValueError("fixture declarations exceed the existing Source census/byte ceilings")
    return manifest


def _root(path: Path) -> Path:
    root = path.absolute()
    if root != root.resolve(strict=True) or not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError("fixture preparation requires a real absolute directory without symlink components")
    return root


def _identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        metadata.st_mode,
    )


def _directory_identity(metadata: os.stat_result) -> tuple[int, int]:
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("fixture confinement requires a real directory")
    return metadata.st_dev, metadata.st_ino


@contextmanager
def _held_parent(
    root: Path,
    relative: str,
    *,
    create: bool = False,
    expected_root: tuple[int, int] | None = None,
) -> Iterator[tuple[int, str]]:
    """Retain the full named chain, including every ancestor above Root."""
    parts = _relative(relative).split("/")
    opened = [os.open(root.anchor, _DIRECTORY_FLAGS if len(root.parts) == 1 else _ANCESTOR_FLAGS)]
    bindings: list[tuple[int, str, int]] = []

    def verify() -> None:
        for parent, name, descriptor in reversed(bindings):
            expected = _directory_identity(os.fstat(descriptor))
            try:
                actual = _directory_identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
            except OSError as exc:
                raise ValueError("fixture ancestor namespace changed") from exc
            if actual != expected:
                raise ValueError("fixture ancestor namespace changed")

    def descend(name: str, *, make: bool, ancestor: bool = False) -> None:
        parent = opened[-1]
        if make:
            try:
                os.mkdir(name, mode=0o755, dir_fd=parent)
            except FileExistsError:
                pass
        descriptor = os.open(name, _ANCESTOR_FLAGS if ancestor else _DIRECTORY_FLAGS, dir_fd=parent)
        bindings.append((parent, name, descriptor))
        opened.append(descriptor)

    try:
        for index, part in enumerate(root.parts[1:], start=1):
            descend(part, make=False, ancestor=index < len(root.parts) - 1)
        if expected_root is not None and _directory_identity(os.fstat(opened[-1])) != expected_root:
            raise ValueError("fixture nominated Root changed after operation entry")
        for part in parts[:-1]:
            descend(part, make=create)
        verify()
        yield opened[-1], parts[-1]
        verify()
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _read_regular(
    root: Path,
    relative: str,
    *,
    expected_root: tuple[int, int] | None = None,
    observations: dict[str, tuple[int, ...]] | None = None,
    expected_observation: tuple[int, ...] | None = None,
) -> tuple[bytes, bool]:
    with _held_parent(root, relative, expected_root=expected_root) as (parent, name):
        original = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISREG(original.st_mode) or original.st_size > MAX_FILE_BYTES:
            raise ValueError("fixture input is not a bounded regular file")
        if expected_observation is not None and _identity(original) != expected_observation:
            raise ValueError("fixture held file identity changed")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
        with os.fdopen(os.open(name, flags, dir_fd=parent), "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or _identity(before) != _identity(original):
                raise ValueError("fixture input changed before its held regular read")
            body = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
            namespaced = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if len(body) > MAX_FILE_BYTES or any(
                _identity(item) != _identity(original) for item in (after, namespaced)
            ):
                raise ValueError("fixture input changed during its held read")
            if observations is not None:
                observations[relative] = _identity(original)
            return body, bool(original.st_mode & 0o111)


def _git(root: Path, *arguments: str) -> bytes:
    executable = shutil.which("git", path=os.defpath)
    if executable is None:
        raise ValueError("fixture preparation requires actual native Git")
    # The selected native Git receives only fixed read-only builtin argv.
    result = subprocess.run(  # nosec B603
        [executable, "--no-replace-objects", "--no-pager", "-c", "core.hooksPath=" + os.devnull, *arguments],
        cwd=root,
        env={
            "PATH": os.defpath,
            "LC_ALL": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
        },
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0 or result.stderr or len(result.stdout) > MAX_FILE_BYTES:
        raise ValueError("fixture native committed input custody is unavailable")
    return result.stdout


def _committed_bytes(
    root: Path,
    relative: str,
    *,
    commit: str,
    expected_root: tuple[int, int] | None = None,
    observations: dict[str, tuple[int, ...]] | None = None,
) -> tuple[bytes, bool]:
    relative = _relative(relative)
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) is None:
        raise ValueError("fixture committed input needs the original exact Source object ID")
    raw = _git(root, "ls-tree", "-z", commit, "--", relative)
    rows = [row for row in raw.split(b"\0") if row]
    if len(rows) != 1:
        raise ValueError("fixture input lacks one committed raw Git blob: " + relative)
    metadata, path = rows[0].split(b"\t", 1)
    mode, kind, oid = metadata.decode("ascii").split(" ")
    if (
        path.decode("utf-8") != relative
        or kind != "blob"
        or mode not in {"100644", "100755"}
        or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
    ):
        raise ValueError("fixture input does not name a committed regular Git blob")
    committed = _git(root, "cat-file", "blob", oid)
    actual, executable = _read_regular(root, relative, expected_root=expected_root, observations=observations)
    if actual != committed or executable != (mode == "100755"):
        raise ValueError("fixture input differs from its committed raw Git blob: " + relative)
    return actual, executable


def _archive_bodies(group: dict[str, Any], content: bytes) -> dict[str, tuple[bytes, bool]]:
    declaration = group["archive"]
    if len(content) != declaration["bytes"] or hashlib.sha256(content).hexdigest() != declaration["sha256"]:
        raise ValueError("fixture archive differs from its source-pinned length/hash")
    with gzip.GzipFile(fileobj=io.BytesIO(content)) as compressed:
        expanded = compressed.read(MAX_TOTAL_BYTES + 1)
    if len(expanded) > MAX_TOTAL_BYTES:
        raise ValueError("fixture archive exceeds the existing expanded-byte ceiling")
    expected = {record["member"]: record for record in group["files"]}
    prefix = declaration["root"] + "/"
    bodies: dict[str, tuple[bytes, bool]] = {}
    directories: set[str] = set()
    seen: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(expanded), mode="r:") as archive:
        for member in archive:
            name = _relative(member.name.removesuffix("/") if member.isdir() else member.name)
            if name in seen or not (name == declaration["root"] or name.startswith(prefix)):
                raise ValueError("fixture archive contains duplicate or out-of-root members")
            seen.add(name)
            if len(seen) > MAX_FILES:
                raise ValueError("fixture archive exceeds the existing member census")
            relative = name[len(prefix) :] if name.startswith(prefix) else ""
            selected = any(relative == item or relative.startswith(item + "/") for item in group["selections"])
            if not selected:
                continue
            if member.isdir():
                directories.add(relative)
                continue
            record = expected.get(name)
            if record is None or not member.isfile() or member.size != record["bytes"]:
                raise ValueError("fixture archive has an unexpected selected member or nonregular body")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("fixture archive selected body is unavailable")
            with stream:
                body = stream.read(MAX_FILE_BYTES + 1)
            executable = bool(member.mode & 0o111)
            if (
                len(body) != record["bytes"]
                or hashlib.sha256(body).hexdigest() != record["sha256"]
                or executable != record["executable"]
            ):
                raise ValueError("fixture archive selected member differs from its exact declaration")
            bodies[record["path"]] = (body, executable)
    expected_directories = {
        name
        for name in group["directories"]
        if any(name == item or name.startswith(item + "/") for item in group["selections"])
    }
    if set(bodies) != {record["path"] for record in group["files"]} or directories != expected_directories:
        raise ValueError("fixture archive selected file/directory census is incomplete or different")
    return bodies


def _write_new(
    root: Path,
    relative: str,
    body: bytes,
    executable: bool,
    *,
    expected_root: tuple[int, int],
) -> tuple[int, ...]:
    with _held_parent(root, relative, expected_root=expected_root) as (parent, name):
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
        mode = 0o755 if executable else 0o644
        descriptor = os.open(name, flags, mode, dir_fd=parent)
        try:
            remaining = memoryview(body)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("fixture exclusive write returned a short write")
                remaining = remaining[written:]
            os.fchmod(descriptor, mode)
            os.fsync(descriptor)
            original = os.fstat(descriptor)
            os.lseek(descriptor, 0, os.SEEK_SET)
            chunks = []
            total = 0
            while chunk := os.read(descriptor, min(65536, MAX_FILE_BYTES + 1 - total)):
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise ValueError("created fixture exceeds its held-byte ceiling")
                chunks.append(chunk)
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (
                b"".join(chunks) != body
                or _identity(named) != _identity(original)
                or _identity(os.fstat(descriptor)) != _identity(original)
            ):
                raise ValueError("created fixture body or namespace changed before write closure")
            return _identity(original)
        finally:
            os.close(descriptor)


def _make_new_directory(root: Path, relative: str, expected_root: tuple[int, int]) -> tuple[int, int]:
    with _held_parent(root, relative, create=True, expected_root=expected_root) as (parent, name):
        os.mkdir(name, mode=0o755, dir_fd=parent)
        descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
        try:
            original = _directory_identity(os.fstat(descriptor))
            if _directory_identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != original:
                raise ValueError("created fixture directory namespace changed")
            return original
        finally:
            os.close(descriptor)


def _verify_directory_snapshot(parent: int, name: str, descriptor: int, original: os.stat_result) -> tuple[int, ...]:
    expected = _identity(original)
    if (
        _identity(os.fstat(descriptor)) != expected
        or _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != expected
    ):
        raise ValueError("created fixture directory changed during census")
    return expected


def _verify_created(
    root: Path,
    groups: list[dict[str, Any]],
    prepared: dict[str, dict[str, tuple[bytes, bool]]],
    directories: dict[str, tuple[int, int]],
    files: dict[str, tuple[int, ...]],
    expected_root: tuple[int, int],
) -> None:
    """Close the exact physical census and original created inode observations."""
    observed_files: set[str] = set()
    observed_directories: set[str] = set()
    held_directories: dict[str, tuple[int, ...]] = {}

    def visit(parent: int, name: str, relative: str) -> None:
        descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
        try:
            original = os.fstat(descriptor)
            if _directory_identity(original) != directories.get(relative):
                raise ValueError("created fixture directory differs from its original inode")
            observed_directories.add(relative)
            names = tuple(sorted(os.listdir(descriptor)))
            for child in names:
                child_relative = relative + "/" + child
                metadata = os.stat(child, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(metadata.st_mode):
                    visit(descriptor, child, child_relative)
                elif stat.S_ISREG(metadata.st_mode) and child_relative in files:
                    observed_files.add(child_relative)
                else:
                    raise ValueError("created fixture census has an undeclared or nonregular member")
            if (
                tuple(sorted(os.listdir(descriptor))) != names
                or _directory_identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != directories[relative]
            ):
                raise ValueError("created fixture directory changed during final census")
            held_directories[relative] = _verify_directory_snapshot(parent, name, descriptor, original)
        finally:
            os.close(descriptor)

    for group in groups:
        with _held_parent(root, group["root"], expected_root=expected_root) as (parent, name):
            visit(parent, name, group["root"])
        for relative, expected in prepared[group["id"]].items():
            full = group["root"] + "/" + relative
            actual = _read_regular(root, full, expected_root=expected_root, expected_observation=files[full])
            if actual != expected:
                raise ValueError("created fixture readback differs from its exact admitted body")
    if observed_files != set(files) or observed_directories != set(directories):
        raise ValueError("created fixture complete physical census changed")
    for relative, expected_directory in held_directories.items():
        with _held_parent(root, relative, expected_root=expected_root) as (parent, name):
            if _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != expected_directory:
                raise ValueError("created fixture directory changed after complete census")


def prepare_acceptance_fixtures(root: Path, *, archives: Path | None = None) -> dict[str, Any]:
    """Prepare every declared group once; never overwrite an existing target.

    An optional outside-Source archive directory nominates only byte inputs;
    every archive still passes its committed exact length/hash/member checks.
    """
    root = _root(root)
    expected_root = _directory_identity(root.lstat())
    with _held_parent(root, ".fixture-operation-boundary", expected_root=expected_root):
        return _prepare_acceptance_fixtures(root, archives=archives, expected_root=expected_root)


def _prepare_acceptance_fixtures(
    root: Path, *, archives: Path | None, expected_root: tuple[int, int]
) -> dict[str, Any]:
    original_commit = _git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    inputs: dict[str, tuple[int, ...]] = {}
    manifest_bytes, _ = _committed_bytes(
        root, MANIFEST_PATH, commit=original_commit, expected_root=expected_root, observations=inputs
    )
    manifest = parse_fixture_manifest(manifest_bytes)
    for group in manifest["groups"]:
        target = root / group["root"]
        if target.exists() or target.is_symlink():
            raise ValueError("fixture preparation refuses an existing target: " + group["root"])
        # Read-only parent traversal refuses linked or non-directory ancestors.
        parent = target.parent
        while parent != root:
            if (parent.exists() or parent.is_symlink()) and (parent.is_symlink() or not parent.is_dir()):
                raise ValueError("fixture preparation refuses a substituted target ancestor")
            parent = parent.parent
    supplied = _root(archives) if archives is not None else None
    prepared: dict[str, dict[str, tuple[bytes, bool]]] = {}
    nominated_temporary = os.environ.get("RUNNER_TEMP")
    temporary_parent = _root(
        Path(nominated_temporary)
        if nominated_temporary is not None
        else Path(tempfile.gettempdir()).resolve(strict=True)
    )
    with tempfile.TemporaryDirectory(prefix="template-source-fixtures.", dir=str(temporary_parent)) as temporary:
        scratch = _root(Path(temporary))
        for group in manifest["groups"]:
            name = group["id"]
            if name == "timeseries":
                prepared[name] = {
                    record["path"]: _committed_bytes(
                        root, record["source"], commit=original_commit, expected_root=expected_root, observations=inputs
                    )
                    for record in group["files"]
                }
                continue
            filename = name + ".tar.gz"
            if supplied is None:
                executable = shutil.which("curl", path=os.defpath)
                if executable is None:
                    raise ValueError("fixture acquisition requires actual curl")
                # Native curl receives a fixed HTTPS origin and an owned output.
                result = subprocess.run(  # nosec B603
                    [
                        executable,
                        "--fail",
                        "--location",
                        "--proto",
                        "=https",
                        "--proto-redir",
                        "=https",
                        "--retry",
                        "2",
                        "--max-time",
                        "180",
                        "--output",
                        str(scratch / filename),
                        group["archive"]["url"],
                    ],
                    check=False,
                )
                if result.returncode:
                    raise ValueError("fixture acquisition failed with original curl exit " + str(result.returncode))
            body, _ = _read_regular(supplied or scratch, filename)
            prepared[name] = _archive_bodies(group, body)
        if sum(len(body) for values in prepared.values() for body, _ in values.values()) > MAX_TOTAL_BYTES:
            raise ValueError("fixture preparation exceeds the existing total held-byte ceiling")
        if (
            _committed_bytes(root, MANIFEST_PATH, commit=original_commit, expected_root=expected_root)[0]
            != manifest_bytes
        ):
            raise ValueError("fixture declaration changed during preparation")
        created_directories: dict[str, tuple[int, int]] = {}
        created_files: dict[str, tuple[int, ...]] = {}
        for group in manifest["groups"]:
            created_directories[group["root"]] = _make_new_directory(root, group["root"], expected_root)
            for directory in group["directories"]:
                relative = group["root"] + "/" + directory
                created_directories[relative] = _make_new_directory(root, relative, expected_root)
            for relative, (body, body_executable) in prepared[group["id"]].items():
                full = group["root"] + "/" + relative
                created_files[full] = _write_new(root, full, body, body_executable, expected_root=expected_root)
        _verify_created(root, manifest["groups"], prepared, created_directories, created_files, expected_root)
        for relative, identity in inputs.items():
            _read_regular(root, relative, expected_root=expected_root, expected_observation=identity)
        if _git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip() != original_commit:
            raise ValueError("fixture original Source commit changed during preparation")
    return {
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "groups": {name: len(files) for name, files in prepared.items()},
        "acceptance": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--archives", type=Path, help="Nominate existing exact archives; verify every pinned byte before use."
    )
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(
            json.dumps(prepare_acceptance_fixtures(args.repo_root, archives=args.archives), sort_keys=True) + "\n"
        )
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(1, "Fixture preparation refused: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["MANIFEST_PATH", "SCHEMA_VERSION", "parse_fixture_manifest", "prepare_acceptance_fixtures", "main"]
