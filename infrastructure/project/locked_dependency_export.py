"""Retain exact locked sdists as explicit artifacts for cold wheel reuse.

Registry requirement resolution can reject a release without registry wheels
before uv checks its prepared sdist wheel cache. A direct URL nominated by the
same frozen lock permits that cache lookup without enabling a cold build. A
lock may carry wheels for other interpreters, so nomination is decided per
target minor: a package whose locked wheels cannot serve that interpreter is
treated like a wheel-less release.
The archive hash does not authenticate mutable derived cache bytes. Callers
must retain a fresh owner-controlled preparation cache through cold execution.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import tomllib
from typing import Any
from urllib.parse import unquote, urlsplit

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name, parse_sdist_filename, parse_wheel_filename
from packaging.version import Version

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined

_HASH = re.compile(r"sha256:[0-9a-f]{64}")
_HASH_FLAGS = re.compile(r"(?:\s+--hash=sha256:[0-9a-f]{64})+")


def _artifact(package: dict[str, Any]) -> tuple[str, str]:
    if package["source"]["registry"] not in {"https://pypi.org/simple", "https://pypi.org/simple/"}:
        raise ValueError("locked sdist requires the declared public PyPI registry")
    sdist = package.get("sdist")
    if not isinstance(sdist, dict):
        raise ValueError("locked package without registry wheels requires its exact sdist")
    url, digest = sdist.get("url"), sdist.get("hash")
    if not isinstance(url, str) or not isinstance(digest, str) or not _HASH.fullmatch(digest):
        raise ValueError("locked sdist requires an exact URL and SHA256")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "files.pythonhosted.org"
        or parsed.port not in (None, 443)
        or not parsed.path.startswith("/packages/")
        or any(part in (".", "..") for part in parsed.path.split("/"))
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.query
        or any(character.isspace() for character in url)
    ):
        raise ValueError("locked sdist requires a credential-free HTTPS artifact URL")
    name, version = parse_sdist_filename(unquote(parsed.path.rsplit("/", 1)[-1]))
    if canonicalize_name(package["name"]) != name or Version(package["version"]) != version:
        raise ValueError("locked sdist filename differs from its exact package/version")
    return url, digest


def _wheel_serves_minor(filename: str, minor: str) -> bool:
    """Report whether a locked wheel filename can install on the target minor."""
    try:
        _, _, _, tags = parse_wheel_filename(filename)
    except ValueError:
        return False
    target = int(minor.replace(".", ""))
    exact = f"cp{target}"
    for tag in tags:
        if tag.interpreter in {"py3", "py2.py3"}:
            return True
        if tag.interpreter == exact:
            return True
        if tag.abi == "abi3" and tag.interpreter.startswith("cp") and tag.interpreter[2:].isdigit():
            if int(tag.interpreter[2:]) <= target:
                return True
    return False


def normalize_locked_sdist_requirements(
    lock_content: bytes, requirements_content: bytes, *, minor: str | None = None
) -> bytes:
    """Name only wheel-less locked registry artifacts; preserve other rows.

    Exact pins, markers and original archive hashes stay mandatory. No wheel
    bytes, cache paths, ambient overrides or generated hashes grant authority.
    With ``minor`` set, a locked release whose wheels cannot serve that
    interpreter is nominated exactly like a wheel-less release.
    """
    if minor is not None and not re.fullmatch(r"3\.\d+", minor):
        raise ValueError("target minor must be a CPython 3.x minor such as 3.15")
    lock = tomllib.loads(lock_content.decode("utf-8"))
    packages = lock.get("package")
    if not isinstance(packages, list):
        raise ValueError("dependency export requires the canonical locked package list")
    selected: dict[tuple[str, str], tuple[str, str]] = {}
    selected_names: set[str] = set()
    multi_hash: set[str] = set()
    registry_versions: set[tuple[str, str]] = set()
    for package in packages:
        if not isinstance(package, dict) or not isinstance(package.get("source"), dict):
            raise ValueError("dependency export requires valid locked package records")
        if "registry" not in package["source"]:
            continue
        name, version = package.get("name"), package.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            raise ValueError("locked registry package lacks its exact package/version")
        key = (canonicalize_name(name), version)
        if key in registry_versions:
            raise ValueError("dependency export refuses ambiguous locked registry packages")
        registry_versions.add(key)
        wheels = package.get("wheels") or []
        if wheels and (
            minor is None
            or any(_wheel_serves_minor(str(wheel.get("url", "")).rsplit("/", 1)[-1], minor) for wheel in wheels)
        ):
            continue
        selected[key] = _artifact(package)
        selected_names.add(key[0])
        if wheels:
            # The exporter lists every locked artifact hash for a release that
            # does carry wheels; the sdist digest must still be among them.
            multi_hash.add(key[0])
    blocks: list[str] = []
    pending: list[str] = []
    for line in requirements_content.decode("utf-8").splitlines(keepends=True):
        pending.append(line)
        if line.rstrip().endswith("\\"):
            continue
        blocks.append("".join(pending))
        pending = []
    if pending:
        raise ValueError("dependency export has an unfinished continuation")
    normalized: list[str] = []
    for block in blocks:
        logical = re.sub(r"\\\r?\n\s*", " ", block).strip()
        if not logical or logical.startswith("#"):
            normalized.append(block)
            continue
        header, separator, rest = logical.partition(" --hash=")
        requirement = Requirement(header)
        name = canonicalize_name(requirement.name)
        if name not in selected_names:
            normalized.append(block)
            continue
        if requirement.url is None:
            pins = tuple(requirement.specifier)
            if len(pins) != 1 or pins[0].operator != "==" or "*" in pins[0].version:
                raise ValueError("locked sdist export requires its exact registry version")
            key = (name, pins[0].version)
            if key not in registry_versions:
                raise ValueError("exported sdist version differs from the canonical lock")
            if key not in selected:
                normalized.append(block)
                continue
            url, digest = selected[key]
        else:
            matches = [
                artifact for key, artifact in selected.items() if key[0] == name and artifact[0] == requirement.url
            ]
            if len(matches) != 1:
                raise ValueError("exported sdist URL differs from the canonical lock")
            url, digest = matches[0]
        flags = separator + rest
        hashes = re.findall(r"--hash=(sha256:[0-9a-f]{64})", flags)
        exact_hashes = hashes == [digest]
        bound_among_artifact_hashes = name in multi_hash and digest in hashes
        if not _HASH_FLAGS.fullmatch(flags) or not (exact_hashes or bound_among_artifact_hashes):
            raise ValueError("exported sdist hash differs from the canonical lock")
        extras = "[" + ",".join(sorted(requirement.extras)) + "]" if requirement.extras else ""
        marker = f" ; {requirement.marker}" if requirement.marker else ""
        ending = "\n" if block.endswith("\n") else ""
        normalized.append(f"{requirement.name}{extras} @ {url}{marker} --hash={digest}{ending}")
    return "".join(normalized).encode("utf-8")


def normalize_locked_dependency_export(metadata_root: Path, requirements: Path, *, minor: str | None = None) -> None:
    """Rewrite a confined generated export using only its admitted lock bytes."""
    metadata_root, requirements = metadata_root.absolute(), requirements.absolute()
    original = read_bytes_confined(requirements.parent, requirements)
    lock_content = read_bytes_confined(metadata_root, metadata_root / "uv.lock")
    normalized = normalize_locked_sdist_requirements(lock_content, original, minor=minor)
    if read_bytes_confined(metadata_root, metadata_root / "uv.lock") != lock_content:
        raise ValueError("canonical lock changed during dependency export normalization")
    if normalized != original:
        atomic_write_bytes_confined(requirements.parent, requirements, normalized, mode=0o600)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-root", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--minor", help="Target CPython minor (for example 3.15)")
    arguments = parser.parse_args(argv)
    normalize_locked_dependency_export(arguments.metadata_root, arguments.requirements, minor=arguments.minor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
