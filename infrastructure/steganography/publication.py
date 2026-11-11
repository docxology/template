"""Stage PDF artifacts and replace individual destinations without partial copies.

Publication is atomic per file. Ordinary errors roll back our own replacements;
this is not a crash-atomic transaction across the PDF and its sidecars.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import stat
import tempfile
from contextlib import ExitStack
from pathlib import Path

from infrastructure.core.files.secure_write import confined_file_lock
from infrastructure.steganography.artifact_paths import (
    SecurePdfOwnership,
    hold_secure_pdf_ownership,
    is_private_ownership_receipt,
    secure_file_sha256,
)

__all__ = ["validate_destinations", "validate_pdf", "publish_artifacts"]


def validate_destinations(source: Path, destinations: list[Path]) -> None:
    """Refuse source aliases, overlapping artifacts and nonregular targets."""
    paths = [source, *destinations]
    canonical: set[Path] = set()
    inodes: set[tuple[int, int]] = set()
    for index, path in enumerate(paths):
        resolved = path.resolve()
        if resolved in canonical:
            raise ValueError("Source and artifact destinations must be distinct")
        canonical.add(resolved)
        if index and path.is_symlink():
            raise ValueError(f"Artifact destinations must not be symlinks: {path}")
        try:
            info = path.stat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Artifact must name a regular file: {path}")
        identity = info.st_dev, info.st_ino
        if identity in inodes:
            raise ValueError("Source and artifacts must not share an inode")
        inodes.add(identity)
    for path in destinations:
        if not path.parent.is_dir():
            raise FileNotFoundError(f"Artifact parent does not exist: {path.parent}")


def validate_pdf(path: Path, *, password: str | None = None) -> None:
    """Read the staged PDF with the production parser before publication."""
    from pypdf import PdfReader

    reader = PdfReader(path)
    if reader.is_encrypted and (password is None or not reader.decrypt(password)):
        raise ValueError("Cannot validate the encrypted staged PDF")
    if not reader.pages:
        raise ValueError("Cannot publish a PDF without pages")
    for page in reader.pages:
        # Resolve the page objects while the staged original still exists.
        _ = page.mediabox


def _entry(path: Path, directory_fd: int | None) -> str | Path:
    return path.name if directory_fd is not None else path


def _stat(path: Path, directory_fd: int | None) -> os.stat_result:
    return os.stat(_entry(path, directory_fd), dir_fd=directory_fd, follow_symlinks=False)


def _stat_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _identity(path: Path, directory_fd: int | None = None) -> tuple[int, int, int, int, int]:
    info = _stat(path, directory_fd)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Artifact changed to a nonregular file: {path}")
    return _stat_identity(info)


def _nullable_identity(path: Path, directory_fd: int | None = None) -> tuple[int, int, int, int, int] | None:
    """Only a genuinely absent leaf is missing; a broken symlink is invalid."""
    try:
        return _identity(path, directory_fd)
    except FileNotFoundError:
        return None


def _create_local_temporary(destination: Path, directory_fd: int | None) -> tuple[int, Path]:
    if directory_fd is None:
        descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.steg-", dir=destination.parent)
        return descriptor, Path(name)
    for _ in range(64):
        path = destination.with_name(f".ownership-{secrets.token_hex(12)}.tmp")
        try:
            return os.open(
                path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory_fd
            ), path
        except FileExistsError:
            continue
    raise OSError("Could not allocate a private receipt temporary file")


def _copy_local(
    source: Path | bytes,
    destination: Path,
    *,
    mode: int,
    expected: tuple[int, int, int, int, int] | None = None,
    directory_fd: int | None = None,
    source_fd: int | None = None,
) -> Path:
    descriptor, staged = _create_local_temporary(destination, directory_fd)
    try:
        with os.fdopen(descriptor, "wb") as output:
            if isinstance(source, bytes):
                output.write(source)
            else:
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
                with os.fdopen(os.open(_entry(source, source_fd), flags, dir_fd=source_fd), "rb") as original:
                    info = os.fstat(original.fileno())
                    identity = _stat_identity(info)
                    if not stat.S_ISREG(info.st_mode) or (expected is not None and identity != expected):
                        raise ValueError(f"Artifact changed while opening its held preimage: {source}")
                    shutil.copyfileobj(original, output)
                    if identity != _stat_identity(os.fstat(original.fileno())):
                        raise ValueError(f"Artifact changed while copying its held bytes: {source}")
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
    except BaseException:
        _unlink(staged, directory_fd, missing_ok=True)
        raise
    return staged


def _unlink(path: Path, directory_fd: int | None, *, missing_ok: bool = False) -> None:
    try:
        os.unlink(_entry(path, directory_fd), dir_fd=directory_fd)
    except FileNotFoundError:
        if not missing_ok:
            raise


def _unlink_owned(path: Path, identity: tuple[int, int, int, int, int] | None, directory_fd: int | None) -> None:
    if identity is None:
        return
    try:
        actual = _stat(path, directory_fd)
    except FileNotFoundError:
        return
    if (actual.st_dev, actual.st_ino) == identity[:2]:
        _unlink(path, directory_fd)


def _replace(source: Path, destination: Path, directory_fd: int | None) -> None:
    os.replace(
        _entry(source, directory_fd),
        _entry(destination, directory_fd),
        src_dir_fd=directory_fd,
        dst_dir_fd=directory_fd,
    )


def publish_artifacts(
    artifacts: dict[Path, Path],
    *,
    source: Path,
    no_overwrite: set[Path] | None = None,
    expected_pdf: tuple[Path, str | None] | None = None,
    ownership: SecurePdfOwnership | None = None,
) -> None:
    """Publish destination→staged-source mappings, preserving previous modes.

    All inputs and previous destinations are copied before the first replace.
    An expected PDF binds its preimage digest or requires a new destination.
    A private receipt is written last through the admitted directory handle.
    Rollback preserves the recovery preimages if it sees a foreign edit.
    """
    publication: dict[Path, Path | bytes] = dict(artifacts)
    if ownership is not None:
        if ownership.target in artifacts:
            raise ValueError("Private receipt must be distinct from public artifacts")
        publication[ownership.target] = ownership.contents
    destinations = list(publication)
    validate_destinations(source, destinations)
    lock_root = Path(tempfile.gettempdir()).resolve()
    prepared: dict[Path, Path] = {}
    prepared_identities: dict[Path, tuple[int, int, int, int, int]] = {}
    backups: dict[Path, Path | None] = {}
    backup_modes: dict[Path, int] = {}
    backup_identities: dict[Path, tuple[int, int, int, int, int]] = {}
    previous: dict[Path, tuple[int, int, int, int, int] | None] = {}
    published: dict[Path, tuple[int, int, int, int, int]] = {}
    preserve_recovery = False
    with ExitStack() as locks:
        for destination in sorted(destinations, key=lambda item: str(item.resolve())):
            key = hashlib.sha256(os.fsencode(destination.resolve())).hexdigest()
            locks.enter_context(confined_file_lock(lock_root, lock_root / f"steganography-{key}.lock"))
        held = locks.enter_context(hold_secure_pdf_ownership(ownership)) if ownership is not None else None
        receipt_fds = {ownership.target: held.descriptor} if ownership is not None and held is not None else {}
        try:
            validate_destinations(source, destinations)
            for destination, staged in publication.items():
                directory_fd = receipt_fds.get(destination)
                if isinstance(staged, Path) and (staged.is_symlink() or not staged.is_file()):
                    raise ValueError(f"Staged artifact must be a regular file: {staged}")
                admitted = _nullable_identity(destination, directory_fd)
                if expected_pdf is not None and destination == expected_pdf[0]:
                    digest = secure_file_sha256(destination) if admitted is not None else None
                    if digest != expected_pdf[1] or _nullable_identity(destination) != admitted:
                        raise ValueError(f"Custom secure PDF changed before publication: {destination}")
                if admitted is not None:
                    if destination in (no_overwrite or set()):
                        raise FileExistsError(destination)
                    previous[destination] = admitted
                    info = _stat(destination, directory_fd)
                    if directory_fd is not None and not is_private_ownership_receipt(info):
                        raise ValueError(f"Existing ownership receipt is not a private regular file: {destination}")
                    mode = stat.S_IMODE(info.st_mode)
                    backup = _copy_local(
                        destination,
                        destination,
                        mode=0o600,
                        expected=admitted,
                        directory_fd=directory_fd,
                        source_fd=directory_fd,
                    )
                    backups[destination] = backup
                    backup_modes[destination] = mode
                    backup_identities[destination] = _identity(backup, directory_fd)
                    if _identity(destination, directory_fd) != previous[destination]:
                        raise ValueError(f"Artifact changed while retaining its preimage: {destination}")
                else:
                    previous[destination] = None
                    backups[destination] = None
                    mode = stat.S_IMODE(staged.stat().st_mode) if isinstance(staged, Path) else 0o600
                prepared[destination] = _copy_local(staged, destination, mode=mode, directory_fd=directory_fd)
                prepared_identities[destination] = _identity(prepared[destination], directory_fd)
            if held is not None and not held.matches_path():
                raise ValueError("Private ownership directory changed before publication")
            for destination in destinations:
                directory_fd = receipt_fds.get(destination)
                current = _nullable_identity(destination, directory_fd)
                if current != previous[destination]:
                    raise ValueError(f"Artifact changed before publication: {destination}")
                if previous[destination] is None:
                    # Linking is an atomic no-clobber operation even if a
                    # foreign creator races the preflight observation.
                    os.link(
                        _entry(prepared[destination], directory_fd),
                        _entry(destination, directory_fd),
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                    )
                else:
                    _replace(prepared[destination], destination, directory_fd)
                try:
                    published_identity = _identity(destination, directory_fd)
                    if directory_fd is not None and published_identity[:2] != prepared_identities[destination][:2]:
                        raise ValueError(f"Published receipt differs from the prepared inode: {destination}")
                    published[destination] = published_identity
                except (OSError, ValueError) as exc:
                    preserve_recovery = True
                    recovery = [str(path) for path in backups.values() if path is not None and path.exists()]
                    exc.add_note(f"A published destination changed before identification; preimages: {recovery}")
                    raise
                if previous[destination] is None:
                    _unlink(prepared[destination], directory_fd)
                    # Removing our second hardlink changes the rollback identity.
                    published[destination] = _identity(destination, directory_fd)
            if held is not None:
                os.fsync(held.descriptor)
                if not held.matches_path():
                    raise ValueError("Private ownership directory changed during publication")
        except BaseException as failure:
            restoration_errors = []
            for destination in reversed(published):
                directory_fd = receipt_fds.get(destination)
                try:
                    if _identity(destination, directory_fd) != published[destination]:
                        raise ValueError("destination was edited after publication")
                    rollback_backup = backups[destination]
                    if rollback_backup is None:
                        _unlink(destination, directory_fd)
                    else:
                        if _identity(rollback_backup, directory_fd) != backup_identities[destination]:
                            raise ValueError("retained preimage was edited after admission")
                        if directory_fd is None:
                            rollback_backup.chmod(backup_modes[destination])
                        _replace(rollback_backup, destination, directory_fd)
                except (OSError, ValueError) as exc:
                    restoration_errors.append(f"{destination}: {exc}")
            if restoration_errors:
                preserve_recovery = True
                recovery = [str(path) for path in backups.values() if path is not None and path.exists()]
                failure.add_note(f"Rollback refused a changed destination: {restoration_errors}; preimages: {recovery}")
            raise
        finally:
            for destination, path in prepared.items():
                _unlink_owned(path, prepared_identities.get(destination), receipt_fds.get(destination))
            if not preserve_recovery:
                for destination, retained_backup in backups.items():
                    if retained_backup is not None:
                        _unlink_owned(retained_backup, backup_identities.get(destination), receipt_fds.get(destination))
