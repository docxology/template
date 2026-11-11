"""File identities shared by secure PDF production and source discovery."""

import hashlib
import json
import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.files.secure_write import HeldDirectory, hold_confined_directory, read_bytes_confined


DEFAULT_OUTPUT_SUFFIX = "_steganography"


def secure_pdf_path(source: Path, output_suffix: str) -> Path:
    """Return the derived secure PDF destination."""

    return source.with_stem(source.stem + output_suffix)


def hash_manifest_path(source: Path) -> Path:
    """Return the legacy manifest destination beside the original PDF."""

    return source.with_suffix(".hashes.json")


def is_secure_pdf(path: Path) -> bool:
    """Recognize the historical default filename marker."""

    return DEFAULT_OUTPUT_SUFFIX in path.stem


def secure_file_sha256(path: Path) -> str:
    """Hash a stable regular file without following its leaf symlink."""

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"Secure artifact must be a regular file: {path}")
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        current = path.lstat()
        after = os.fstat(stream.fileno())
        if any(
            (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            for info in (current, after)
        ):
            raise ValueError(f"Secure artifact changed while hashing: {path}")
    return digest


_OWNERSHIP_DIRECTORY = ".steganography-ownership"


def _require_private_directory(info: os.stat_result, directory: Path) -> None:
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError(f"Custom secure PDF receipts require a publisher-owned private directory: {directory}")


def is_private_ownership_receipt(info: os.stat_result) -> bool:
    return (
        stat.S_ISREG(info.st_mode)
        and info.st_nlink == 1
        and info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o600
    )


def _ownership_directory(output: Path, *, create: bool = False) -> tuple[Path, tuple[int, int]]:
    """Admit a publisher-private directory beside its custom PDF."""

    parent = output.parent.resolve(strict=True)
    parent_info = parent.stat()
    if parent_info.st_uid != os.geteuid() or (parent_info.st_mode & 0o022 and not parent_info.st_mode & stat.S_ISVTX):
        raise ValueError(f"Custom secure PDF receipts require a publisher-controlled PDF directory: {parent}")
    directory = parent / _OWNERSHIP_DIRECTORY
    with hold_confined_directory(
        parent, Path(), expected_root_identity=(parent_info.st_dev, parent_info.st_ino)
    ) as held:
        if create:
            with suppress(FileExistsError):
                os.mkdir(directory.name, mode=0o700, dir_fd=held.descriptor)
        info = os.stat(directory.name, dir_fd=held.descriptor, follow_symlinks=False)
        _require_private_directory(info, directory)
        if not held.matches_path():
            raise ValueError(f"Custom secure PDF directory changed during ownership admission: {parent}")
        return directory, (info.st_dev, info.st_ino)


def _ownership_receipt_name(output: Path) -> str:
    return hashlib.sha256(os.fsencode(output.name)).hexdigest() + ".json"


def _source_identity(source: Path, output: Path) -> str:
    return os.path.relpath(source.resolve(), output.parent.resolve(strict=True))


@dataclass(frozen=True)
class SecurePdfOwnership:
    target: Path
    directory_identity: tuple[int, int]
    contents: bytes


def prepare_secure_pdf_ownership(source: Path, output: Path, digest: str) -> SecurePdfOwnership:
    """Bind the private receipt and its parent before publication."""

    directory, identity = _ownership_directory(output, create=True)
    payload = {"source": _source_identity(source, output), "output": output.name, "sha256": digest}
    return SecurePdfOwnership(directory / _ownership_receipt_name(output), identity, json.dumps(payload).encode())


@contextmanager
def hold_secure_pdf_ownership(ownership: SecurePdfOwnership) -> Iterator[HeldDirectory]:
    directory = ownership.target.parent
    with hold_confined_directory(directory, Path(), expected_root_identity=ownership.directory_identity) as held:
        _require_private_directory(os.fstat(held.descriptor), directory)
        yield held


def owned_secure_pdf_sha256(source: Path, output: Path) -> str | None:
    """Verify a custom PDF against the publisher's private receipt."""

    try:
        directory, identity = _ownership_directory(output)
        target = directory / _ownership_receipt_name(output)
        info = target.lstat()
        if not is_private_ownership_receipt(info):
            return None
        receipt = json.loads(
            read_bytes_confined(directory, target, max_bytes=16 * 1024, expected_root_identity=identity)
        )
        expected_source = _source_identity(source, output)
        if isinstance(receipt, dict) and receipt.get("source") == expected_source:
            digest = secure_file_sha256(output)
            if receipt == {"source": expected_source, "output": output.name, "sha256": digest}:
                return digest
    except (OSError, ValueError, RecursionError):
        pass
    return None


def custom_secure_sources(pdfs: list[Path], output_suffix: str) -> list[Path]:
    """Keep originals and refuse a pre-existing custom destination with unknown ownership."""

    derived: dict[Path, Path] = {}
    for target in pdfs:
        source_stem = target.stem.removesuffix(output_suffix)
        if source_stem and source_stem != target.stem:
            source = target.with_stem(source_stem)
            if owned_secure_pdf_sha256(source, target) is not None:
                derived[target] = source

    sources = [path for path in pdfs if path not in derived]
    for source in sources:
        target = secure_pdf_path(source, output_suffix)
        if (
            (target.exists() or target.is_symlink())
            and derived.get(target) != source
            and owned_secure_pdf_sha256(source, target) is None
        ):
            raise ValueError(f"Custom secure PDF destination already exists without matching source evidence: {target}")
    return sources
