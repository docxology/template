"""Bounded physical file preparation and evidence transport for CI UID handoff."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess  # nosec B404 - fixed argv helpers
import sys
import time
from pathlib import Path

RESERVE = 2 * 1024**3
MAX_BYTES = 16 * 1024**3
MAX_FILES = 300_000
PHASE = "entry"


def _phase(label: str) -> None:
    global PHASE
    _require(
        label
        in {"request", "account", "public-caches", "assets", "handoff", "state", "run-preflight", "payload", "export"},
        "unknown profile phase",
    )
    PHASE = label


def _diagnostic(error: BaseException) -> None:
    value = {
        "execution_profile_error": type(error).__name__,
        "phase": PHASE,
        "errno": error.errno if isinstance(error, OSError) else None,
        "command_exit": error.returncode if isinstance(error, subprocess.CalledProcessError) else None,
        "runtime_acceptance": False,
    }
    try:
        print(json.dumps(value), file=sys.stderr)
    except OSError:
        pass  # A failed diagnostic write cannot replace the original refusal.


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _physical(path: Path) -> Path:
    _require(path.is_absolute() and ".." not in path.parts, "an absolute physical path is required")
    _require(path.resolve(strict=True) == path, "symlinked or noncanonical path refused")
    return path


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    _require(remaining > 0, "execution-profile preparation/transport deadline exhausted")
    return remaining


def _command(argv: list[str], deadline: float, **kwargs: object) -> subprocess.CompletedProcess:
    result: subprocess.CompletedProcess = subprocess.run(  # type: ignore[call-overload]  # nosec B603
        argv, check=True, timeout=_remaining(deadline), **kwargs
    )
    return result


def _entries(root: Path, deadline: float) -> list[Path]:
    def refuse(error: OSError) -> None:
        raise error

    result = [root]
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=refuse):
        _remaining(deadline)
        result.extend(Path(directory) / name for name in (*dirs, *files))
        _require(len(result) <= MAX_FILES, "execution profile file bound exceeded")
    return result


def _signature(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_gid,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
        info.st_nlink,
    )


def _open_physical(path: Path, flags: int) -> int:
    directory_flags = getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, directory_flags)
    try:
        for name in path.parts[1:-1]:
            following = os.open(name, directory_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        return os.open(path.name, flags | os.O_NOFOLLOW, 0o600, dir_fd=descriptor)
    finally:
        os.close(descriptor)


def _stable_copy(source: Path, destination: Path, deadline: float, *, mode: int | None = None) -> int:
    before = source.lstat()
    _require(stat.S_ISREG(before.st_mode), "only physical regular files may be copied")
    _require(before.st_size <= MAX_BYTES, "execution profile byte bound exceeded")
    _require(
        shutil.disk_usage(destination.parent).free >= RESERVE + before.st_size, "execution profile disk reserve refused"
    )
    digest = hashlib.sha256()
    with (
        os.fdopen(_open_physical(source, os.O_RDONLY), "rb") as reader,
        os.fdopen(_open_physical(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL), "wb") as writer,
    ):
        _require(_signature(os.fstat(reader.fileno())) == _signature(before), "copy source changed before open")
        while chunk := reader.read(1024 * 1024):
            _remaining(deadline)
            digest.update(chunk)
            writer.write(chunk)
        _require(
            _signature(os.fstat(reader.fileno())) == _signature(before)
            and _signature(source.lstat()) == _signature(before),
            "copy source changed",
        )
    os.chmod(destination, stat.S_IMODE(before.st_mode) if mode is None else mode)
    with destination.open("rb") as copied:
        _remaining(deadline)
        _require(hashlib.file_digest(copied, "sha256").digest() == digest.digest(), "copied bytes disagree")
    _remaining(deadline)
    return before.st_size


def _detach(path: Path, deadline: float) -> None:
    if path.lstat().st_nlink > 1:
        temporary = path.with_name(path.name + ".template-ci-private")
        _stable_copy(path, temporary, deadline)
        os.replace(temporary, path)


def _copy_cache(source: Path, destination: Path, deadline: float) -> None:
    _physical(source)
    entries = _entries(source, deadline)
    total = sum(p.lstat().st_size for p in entries if p.is_file() and not p.is_symlink())
    _require(
        total <= MAX_BYTES and shutil.disk_usage(destination.parent).free >= RESERVE + total,
        "public cache copy budget refused",
    )
    for path in entries:
        _remaining(deadline)
        target = destination / path.relative_to(source)
        current = path.lstat()
        _require(path.name not in {".netrc", ".git-credentials", ".npmrc"}, "credential/config cache entry refused")
        if stat.S_ISDIR(current.st_mode):
            target.mkdir(mode=0o700)
        elif stat.S_ISLNK(current.st_mode):
            resolved = path.resolve(strict=True)
            _require(resolved.is_relative_to(source), "escaping public cache link refused")
            target.symlink_to(os.path.relpath(destination / resolved.relative_to(source), target.parent))
        else:
            _stable_copy(path, target, deadline)


def _acl(paths: list[Path], uid: int, access: str, deadline: float, *, default: bool = False) -> None:
    value = f"u:{uid}:{access}"
    for offset in range(0, len(paths), 128):
        _command(
            [
                "/usr/bin/setfacl",
                "-m",
                f"d:{value}" if default else value,
                "--",
                *(str(p) for p in paths[offset : offset + 128]),
            ],
            deadline,
            capture_output=True,
        )


def _ancestor_search(paths: list[Path], uid: int, deadline: float) -> None:
    ancestors = {parent for path in paths for parent in (path, *path.parents)}
    _require(len(ancestors) <= 128, "execution profile ancestor bound refused")
    selected = [parent for parent in ancestors if not _physical(parent).stat().st_mode & stat.S_IXOTH]
    _acl(selected, uid, "--x", deadline)


def _handoff(root: Path, uid: int, gid: int, caller: int, deadline: float) -> None:
    venv_dirs, git_entries = [], []
    for path in _entries(root, deadline):
        _remaining(deadline)
        relative = path.relative_to(root)
        current = path.lstat()
        in_venv = bool(relative.parts and relative.parts[0] == ".venv")
        if stat.S_ISLNK(current.st_mode):
            resolved = path.resolve(strict=True)
            _require(
                resolved.is_relative_to(root)
                or in_venv
                and any(
                    resolved.is_relative_to(base) for base in (Path("/opt/hostedtoolcache"), Path("/usr"), Path("/lib"))
                ),
                "escaping checkout symlink refused",
            )
            os.chown(path, uid, gid, follow_symlinks=False)
        elif stat.S_ISREG(current.st_mode):
            if (
                in_venv
                and current.st_mode & stat.S_IROTH
                and (not current.st_mode & 0o111 or current.st_mode & stat.S_IXOTH)
            ):
                continue  # Shared readable runtime inodes and their ACLs remain untouched.
            _detach(path, deadline)
            os.chown(path, uid, gid)
        elif stat.S_ISDIR(current.st_mode):
            os.chown(path, uid, gid)
            if in_venv:
                venv_dirs.append(path)
        else:
            raise ValueError("special checkout entry refused")
        if relative.parts and relative.parts[0] == ".git":
            _require(not path.is_symlink(), "symlinked Git admin refused")
            git_entries.append(path)
    _acl(venv_dirs, caller, "r-x", deadline)
    _acl(venv_dirs, caller, "r-x", deadline, default=True)
    _acl(git_entries, caller, "rwX", deadline)


def _evidence_entries(root: Path, deadline: float) -> tuple[list[Path], list[str]]:
    def refuse(error: OSError) -> None:
        raise error

    entries, excluded = [root], []
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=refuse):
        _remaining(deadline)
        parent = Path(directory)
        # Exact scratch names emitted by public_root_{case,lane}_contract.
        declared = (parent / "census-spec.json").is_file() or (
            re.fullmatch(r"chunk-[0-9]{4}", parent.name) is not None and (parent.parent / "lane-spec.json").is_file()
        )
        if "pytest-tmp" in dirs and declared:
            scratch = parent / "pytest-tmp"
            _require(not scratch.is_symlink(), "symlinked declared scratch root refused")
            dirs.remove("pytest-tmp")
            excluded.append(scratch.relative_to(root).as_posix())
        entries.extend(parent / name for name in (*dirs, *files))
        _require(len(entries) <= MAX_FILES and len(excluded) <= 4096, "artifact entry bound exceeded")
    return entries, excluded


def _export(root: Path, destination: Path, deadline: float, *, exclusions: list[str] | None = None) -> int:
    _physical(root)
    _physical(destination)
    _require(destination.is_dir() and not any(destination.iterdir()), "fresh artifact transport directory required")
    entries, excluded = _evidence_entries(root, deadline)
    before = {str(entry): _signature(entry.lstat()) for entry in entries}
    total = 0
    for source in entries:
        target = destination / source.relative_to(root)
        if source.is_dir() and not source.is_symlink():
            if target != destination:
                target.mkdir(mode=0o755)
        else:
            _require(source.is_file() and not source.is_symlink(), "artifact link/special entry refused")
            total += source.stat().st_size
            _require(total <= MAX_BYTES, "artifact transport byte bound exceeded")
            _stable_copy(source, target, deadline, mode=0o644)
    _require((entries, excluded) == _evidence_entries(root, deadline), "artifact entry roster changed during transport")
    _require(
        before == {str(entry): _signature(entry.lstat()) for entry in entries},
        "artifact bytes/types changed during transport",
    )
    if exclusions is not None:
        exclusions.extend(excluded)
    return total
