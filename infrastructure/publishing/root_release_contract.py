"""Fail-closed version contract for releases of the root template package."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Sequence

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib  # type: ignore[no-redef]


def root_package_version(repo_root: Path) -> str:
    """Return the root package version from ``pyproject.toml``."""
    pyproject = repo_root / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = payload.get("project")
    version = project.get("version") if isinstance(project, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise ValueError("root pyproject.toml must declare a non-empty project.version")
    return version.strip()


def root_changelog_versions(repo_root: Path) -> tuple[str, ...]:
    """Return released version headings from the root changelog in file order."""
    changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = []
    for match in re.finditer(r"^##\s*\[([^\]]+)\]", changelog, flags=re.MULTILINE):
        version = match.group(1).strip()
        if version.lower() != "unreleased":
            versions.append(version)
    return tuple(versions)


def validate_root_release_tag(repo_root: Path, tag: str) -> str:
    """Return the package version when ``tag`` is its exact ``v``-prefixed tag.

    Project-exemplar releases have their own versions and standalone GitHub
    repositories.  Rejecting every other tag here prevents an exemplar release
    from becoming a root-repository release merely because both use semantic
    version-shaped tags.
    """
    version = root_package_version(repo_root)
    expected = f"v{version}"
    if tag != expected:
        raise ValueError(
            f"root release tag {tag!r} does not match package version {version!r}; "
            "publish exemplar releases only to their configured standalone repository"
        )
    if version not in root_changelog_versions(repo_root):
        raise ValueError(f"CHANGELOG.md has no released heading for package version {version!r}")
    return version


def build_parser() -> argparse.ArgumentParser:
    """Build the root-release contract command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Root Git tag to validate")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the requested root tag and print the matching package version."""
    args = build_parser().parse_args(argv)
    try:
        version = validate_root_release_tag(args.repo_root.resolve(), args.tag)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"root release contract failed: {exc}")
        return 2
    print(f"root release contract passed: v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "build_parser",
    "main",
    "root_changelog_versions",
    "root_package_version",
    "validate_root_release_tag",
]
