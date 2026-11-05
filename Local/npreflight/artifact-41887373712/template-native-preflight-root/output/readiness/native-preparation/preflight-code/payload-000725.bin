"""Fail-closed version contract for releases of the root template package."""

from __future__ import annotations

import argparse
import ast
import re
import tomllib
from pathlib import Path
from typing import Sequence

RUNTIME_VERSION_PROVIDER_SOURCE = """from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import tomllib
try:
    __version__ = version("research-project-template")
except PackageNotFoundError:
    __version__ = tomllib.loads(
        (Path(__file__).parent.parent / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["version"]
if not isinstance(__version__, str) or not __version__.strip():
    raise ValueError("Package metadata must declare a non-empty version")
"""


def validate_runtime_version_provider(source_text: str) -> None:
    """Validate the metadata binding using source bytes already held in custody."""
    tree = ast.parse(source_text)
    body = [
        node
        for node in tree.body
        if not (
            isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        )
    ]
    observed = ast.dump(ast.Module(body=body, type_ignores=[]), include_attributes=False)
    canonical = ast.dump(ast.parse(RUNTIME_VERSION_PROVIDER_SOURCE), include_attributes=False)
    if observed != canonical:
        raise ValueError("Runtime version must use only the canonical package metadata provider")


def root_package_version(repo_root: Path) -> str:
    """Return the root package version from ``pyproject.toml``."""
    pyproject = repo_root / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = payload.get("project")
    version = project.get("version") if isinstance(project, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise ValueError("root pyproject.toml must declare a non-empty project.version")
    if not isinstance(project, dict) or project.get("name") != "research-project-template":
        raise ValueError("root package metadata must identify research-project-template")
    return version.strip()


def root_changelog_versions(repo_root: Path) -> tuple[str, ...]:
    """Return released version headings from the root changelog in file order."""
    changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    versions = []
    for match in re.finditer(r"^##\s*\[([^\]]+)\]([^\n]*)", changelog, flags=re.MULTILINE):
        version = match.group(1).strip()
        if version.lower() != "unreleased" and "unreleased" not in match.group(2).lower():
            versions.append(version)
    return tuple(versions)


def root_runtime_version(repo_root: Path) -> str:
    """Verify the source metadata provider without executing checkout code.

    Installed-runtime agreement is exercised separately from an isolated wheel.
    The source contains no independently maintained version constant.
    """
    source = repo_root / "infrastructure" / "_version.py"
    validate_runtime_version_provider(source.read_text(encoding="utf-8"))
    return root_package_version(repo_root)


def validate_root_versions(repo_root: Path) -> str:
    """Require package metadata and the public runtime version to agree."""
    package = root_package_version(repo_root)
    runtime = root_runtime_version(repo_root)
    if package != runtime:
        raise ValueError(f"package version {package!r} differs from runtime version {runtime!r}")
    return package


def validate_root_release_tag(repo_root: Path, tag: str) -> str:
    """Return the package version when ``tag`` is its exact ``v``-prefixed tag.

    Project-exemplar releases have their own versions and standalone GitHub
    repositories.  Rejecting every other tag here prevents an exemplar release
    from becoming a root-repository release merely because both use semantic
    version-shaped tags.
    """
    version = validate_root_versions(repo_root)
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
    except (OSError, SyntaxError, tomllib.TOMLDecodeError, ValueError) as exc:
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
    "root_runtime_version",
    "validate_root_versions",
    "validate_root_release_tag",
    "validate_runtime_version_provider",
]
