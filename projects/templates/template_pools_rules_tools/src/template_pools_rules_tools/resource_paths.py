"""Public resource custody shared by source exports and installed wheels."""

from __future__ import annotations

import shutil
from pathlib import Path

RESOURCE_KINDS = ("fonds", "rules", "tools")
_CONTROL_NAMES = frozenset({".git", ".venv", "__pycache__", "output", "build", "dist"})


def public_resource_root(kind: str) -> Path:
    """Prefer wheel-owned data, then a source export or canonical public checkout."""
    if kind not in RESOURCE_KINDS:
        raise ValueError("resource kind is outside the public package contract")
    package = Path(__file__).resolve().parent
    installed = package / "_template_resources" / kind / "templates"
    if installed.is_dir():
        return installed
    project = package.parent.parent
    exported = project / "_template_resources" / kind / "templates"
    if exported.is_dir():
        return exported
    if project.parent.name == "templates" and project.parent.parent.name == "projects":
        return project.parent.parent.parent / kind / "templates"
    return installed


def bundle_public_resources(project: Path, destination: Path) -> tuple[str, ...]:
    """Copy declared public sibling templates into the built package, never private lanes."""
    exported = project / "_template_resources"
    if exported.is_dir():
        source = exported
    elif project.parent.name == "templates" and project.parent.parent.name == "projects":
        source = project.parent.parent.parent
    else:
        raise ValueError("a standalone wheel requires its declared exported public resources")
    for boundary in (source.absolute(), destination.absolute()):
        if ".." in boundary.parts or any(
            path.is_symlink() for path in (boundary, *boundary.parents)
        ):
            raise ValueError("bundled resource custody refuses ancestor symlinks and traversal")
    files = []
    for kind in RESOURCE_KINDS:
        root = source / kind / "templates"
        if not root.is_dir() or any(
            component.is_symlink() for component in (source, source / kind, root)
        ):
            raise ValueError("bundled resource root is absent or contains a symlink")
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(source)
            if path.is_symlink():
                raise ValueError("bundled public resources refuse symlinks")
            if any(part in _CONTROL_NAMES for part in relative.parts):
                continue
            if any(
                part == ".private_projects_root"
                or part == ".env"
                or part.startswith(".env.")
                and not part.endswith((".example", ".template"))
                for part in relative.parts
            ):
                raise ValueError("bundled resources refuse credential/private control files")
            if path.is_file():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                files.append(relative.as_posix())
    if not files:
        raise ValueError("public resource bundle is empty")
    return tuple(files)
