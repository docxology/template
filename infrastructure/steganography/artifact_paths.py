"""File identities shared by secure PDF production and source discovery."""

from pathlib import Path


DEFAULT_OUTPUT_SUFFIX = "_steganography"


def secure_pdf_path(source: Path, output_suffix: str) -> Path:
    """Return the derived secure PDF destination."""

    return source.with_stem(source.stem + output_suffix)


def hash_manifest_path(source: Path) -> Path:
    """Return the legacy manifest destination beside the original PDF."""

    return source.with_suffix(".hashes.json")


def is_secure_pdf(path: Path, output_suffix: str = DEFAULT_OUTPUT_SUFFIX) -> bool:
    """Recognize historical markers and the current terminal suffix."""

    return DEFAULT_OUTPUT_SUFFIX in path.stem or (bool(output_suffix) and path.stem.endswith(output_suffix))
