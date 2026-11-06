"""Stage PDF artifacts and replace individual destinations without partial copies.

Publication is atomic per file. Ordinary errors roll back our own replacements;
this is not a crash-atomic transaction across the PDF and its sidecars.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from contextlib import ExitStack
from pathlib import Path

from infrastructure.core.files.secure_write import confined_file_lock

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


def _identity(path: Path) -> tuple[int, int, int, int, int]:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Artifact changed to a nonregular file: {path}")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def _nullable_identity(path: Path) -> tuple[int, int, int, int, int] | None:
    """Only a genuinely absent leaf is missing; a broken symlink is invalid."""
    try:
        return _identity(path)
    except FileNotFoundError:
        return None


def _copy_local(
    source: Path,
    destination: Path,
    *,
    mode: int,
    expected: tuple[int, int, int, int, int] | None = None,
) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.steg-", dir=destination.parent)
    staged = Path(name)
    try:
        with (
            os.fdopen(descriptor, "wb") as output,
            os.fdopen(os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as original,
        ):
            info = os.fstat(original.fileno())
            identity = info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
            if not stat.S_ISREG(info.st_mode) or (expected is not None and identity != expected):
                raise ValueError(f"Artifact changed while opening its held preimage: {source}")
            shutil.copyfileobj(original, output)
            after = os.fstat(original.fileno())
            if identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValueError(f"Artifact changed while copying its held bytes: {source}")
            output.flush()
            os.fchmod(output.fileno(), mode)
            os.fsync(output.fileno())
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return staged


def _unlink_owned(path: Path, identity: tuple[int, int, int, int, int] | None) -> None:
    if identity is None:
        return
    try:
        actual = path.lstat()
    except FileNotFoundError:
        return
    if (actual.st_dev, actual.st_ino) == identity[:2]:
        path.unlink()


def publish_artifacts(
    artifacts: dict[Path, Path],
    *,
    source: Path,
    no_overwrite: set[Path] | None = None,
) -> None:
    """Publish destination→staged-source mappings, preserving previous modes.

    All inputs and previous destinations are copied before the first replace.
    If rollback sees a foreign edit, it preserves the recovery preimages and
    reports their paths instead of overwriting that edit.
    """
    destinations = list(artifacts)
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
        try:
            validate_destinations(source, destinations)
            for destination, staged in artifacts.items():
                if staged.is_symlink() or not staged.is_file():
                    raise ValueError(f"Staged artifact must be a regular file: {staged}")
                admitted = _nullable_identity(destination)
                if admitted is not None:
                    if destination in (no_overwrite or set()):
                        raise FileExistsError(destination)
                    previous[destination] = admitted
                    mode = stat.S_IMODE(destination.stat().st_mode)
                    backup = _copy_local(destination, destination, mode=0o600, expected=previous[destination])
                    backups[destination] = backup
                    backup_modes[destination] = mode
                    backup_identities[destination] = _identity(backup)
                    if _identity(destination) != previous[destination]:
                        raise ValueError(f"Artifact changed while retaining its preimage: {destination}")
                else:
                    previous[destination] = None
                    backups[destination] = None
                    mode = stat.S_IMODE(staged.stat().st_mode)
                prepared[destination] = _copy_local(staged, destination, mode=mode)
                prepared_identities[destination] = _identity(prepared[destination])
            for destination in destinations:
                current = _nullable_identity(destination)
                if current != previous[destination]:
                    raise ValueError(f"Artifact changed before publication: {destination}")
                if previous[destination] is None:
                    # Linking is an atomic no-clobber operation even if a
                    # foreign creator races the preflight observation.
                    os.link(prepared[destination], destination)
                else:
                    os.replace(prepared[destination], destination)
                try:
                    published[destination] = _identity(destination)
                except (OSError, ValueError) as exc:
                    preserve_recovery = True
                    recovery = [str(path) for path in backups.values() if path is not None and path.exists()]
                    exc.add_note(f"A published destination changed before identification; preimages: {recovery}")
                    raise
                if previous[destination] is None:
                    prepared[destination].unlink()
                    # Removing our second hardlink changes ctime; record the
                    # final identity used by a later rollback decision.
                    published[destination] = _identity(destination)
        except BaseException as failure:
            restoration_errors = []
            for destination in reversed(published):
                try:
                    if _identity(destination) != published[destination]:
                        raise ValueError("destination was edited after publication")
                    rollback_backup = backups[destination]
                    if rollback_backup is None:
                        destination.unlink()
                    else:
                        if _identity(rollback_backup) != backup_identities[destination]:
                            raise ValueError("retained preimage was edited after admission")
                        rollback_backup.chmod(backup_modes[destination])
                        os.replace(rollback_backup, destination)
                except (OSError, ValueError) as exc:
                    restoration_errors.append(f"{destination}: {exc}")
            if restoration_errors:
                preserve_recovery = True
                recovery = [str(path) for path in backups.values() if path is not None and path.exists()]
                failure.add_note(f"Rollback refused a changed destination: {restoration_errors}; preimages: {recovery}")
            raise
        finally:
            for destination, path in prepared.items():
                _unlink_owned(path, prepared_identities.get(destination))
            if not preserve_recovery:
                for destination, retained_backup in backups.items():
                    if retained_backup is not None:
                        _unlink_owned(retained_backup, backup_identities.get(destination))
