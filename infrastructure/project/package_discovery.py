"""Static import-target discovery for public project source layouts.

This describes source import roots without executing projects or installing
packages. Actual installed-wheel acceptance is a separate bounded contract.
"""

from __future__ import annotations

from pathlib import Path


def discover_import_targets(src_root: Path) -> tuple[str, ...]:
    """Return importable top-level modules and packages under ``src_root``.

    A source tree with its own ``__init__.py`` is a ``src`` package. Preserve
    that layout's relative imports instead of treating its children as unrelated
    top-level modules. This static source description is not wheel admission.
    """
    targets: set[str] = set()
    if not src_root.is_dir():
        return ()
    if (src_root / "__init__.py").is_file():
        return ("src",)
    for child in src_root.iterdir():
        if child.name.startswith("_"):
            continue
        if child.is_file() and child.suffix == ".py" and child.stem.isidentifier():
            targets.add(child.stem)
        elif child.is_dir() and child.name.isidentifier() and any(child.rglob("*.py")):
            targets.add(child.name)
    return tuple(sorted(targets))


__all__ = ["discover_import_targets"]
