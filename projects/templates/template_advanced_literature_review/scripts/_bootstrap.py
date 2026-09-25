"""Shared sys.path bootstrap for project orchestrator scripts."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """Locate the monorepo root (the directory that holds ``infrastructure/``).

    A fixed ``parents[N]`` hop is fragile: a project nested at
    ``projects/templates/<name>`` sits one level deeper than one at
    ``projects/<name>``. Prefer the render pipeline's ``TEMPLATE_REPO_ROOT`` env
    var, then walk upward looking for the ``infrastructure/`` marker, and only
    fall back to a fixed hop if neither is available.
    """
    env_root = os.environ.get("TEMPLATE_REPO_ROOT")
    if env_root and (Path(env_root) / "infrastructure").is_dir():
        return Path(env_root)
    for parent in (start, *start.parents):
        if (parent / "infrastructure").is_dir():
            return parent
    return start.parent.parent


def bootstrap_project(*, include_infrastructure: bool = False) -> Path:
    """Insert ``src/`` (and optionally template repo root) on ``sys.path``.

    Returns:
        Project root directory (parent of ``scripts/``).
    """
    root = Path(__file__).resolve().parent.parent
    _consume_project_argument(root)
    src = root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    if include_infrastructure:
        repo_text = str(_find_repo_root(root))
        if repo_text not in sys.path:
            sys.path.insert(0, repo_text)
    _register_meta_alias(root)
    return root


def _register_meta_alias(project_root: Path) -> None:
    """Register the sibling meta exemplar's flat ``src`` under the unique alias.

    The meta exemplar (``template_literature_meta_analysis``) keeps a flat
    ``src/`` package, so its modules cannot be imported under the nested
    ``template_literature_meta_analysis.*`` name through sys.path alone. Scripts
    that previously resolved cross-exemplar code through tracked symlinks
    (``src/analysis``, ``src/config_loader.py``, ...) now reach it through the
    project-unique alias registration below — the repo's ``_PKG_ALIAS``
    pattern. The alias registration is idempotent; meta's ``src`` is appended
    after this project's own ``src`` so its internal absolute imports
    (``from analysis...``, ``from config_loader...``) resolve without shadowing
    this project's top-level ``literature``/``config`` packages.
    """
    meta_src = project_root.parent / "template_literature_meta_analysis" / "src"
    if not meta_src.is_dir():
        return
    meta_text = str(meta_src)
    if meta_text not in sys.path:
        sys.path.append(meta_text)
    alias = "template_literature_meta_analysis"
    if alias in sys.modules:
        return
    spec = importlib.util.spec_from_file_location(
        alias, meta_src / "__init__.py", submodule_search_locations=[meta_text]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not build a spec for the {alias} package at {meta_src}")
    package = importlib.util.module_from_spec(spec)
    sys.modules[alias] = package
    spec.loader.exec_module(package)


def _consume_project_argument(project_root: Path) -> None:
    """Validate and remove the shared ``--project`` context argument.

    Project-local scripts historically inferred their root from ``__file__``.
    The repository methods contract now passes an explicit qualified project
    name to every stage command, so these wrappers accept that argument while
    retaining their existing script-specific argparse surfaces.
    """
    try:
        index = sys.argv.index("--project")
    except ValueError:
        return
    if index + 1 >= len(sys.argv):
        raise SystemExit("--project requires a qualified project name")
    supplied = Path(sys.argv[index + 1]).name
    if supplied != project_root.name:
        raise SystemExit(
            f"this project-local entrypoint only supports {project_root.name!r}; received {sys.argv[index + 1]!r}"
        )
    del sys.argv[index : index + 2]
