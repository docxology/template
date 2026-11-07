"""File identities shared by secure PDF production and source discovery."""

import hashlib
import json
import os
import stat
from pathlib import Path

from infrastructure.core.files.secure_write import read_bytes_confined


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


def owned_secure_pdf_sha256(source: Path, output: Path) -> str | None:
    """Identify a custom output by the exact bytes named in its source manifest."""

    manifest = hash_manifest_path(source)
    try:
        directory = manifest.parent.resolve()
        receipt = json.loads(read_bytes_confined(directory, directory / manifest.name, max_bytes=64 * 1024))
        if (
            isinstance(receipt, dict)
            and receipt.get("source_file") == source.name
            and receipt.get("steganography_applied") == "true"
            and receipt.get("secure_pdf") == output.name
        ):
            digest = secure_file_sha256(output)
            if receipt.get("secure_pdf_sha256") == digest:
                return digest
    except (OSError, ValueError):
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
