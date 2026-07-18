"""Materialize a Spec into a complete runnable child project.

This module takes a fully-resolved Spec and writes a self-contained project
directory under *out_root*.  The generated project can run its own tests,
produce figures, and render a manuscript — all without requiring the parent
template infrastructure at runtime.
"""

from __future__ import annotations

import json
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path

from .expand import Spec
from .emit_templates import emit_all
from .integrity import tree_hash_from_content_hashes

PROVENANCE_SCHEMA_VERSION = "autopoiesis/provenance/1"

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class MaterializeResult:
    """Outcome of a materialize() call."""

    root: Path
    name: str
    files: dict[str, str]  # relative_path -> content
    tree_hash: str
    provenance_path: Path


# ---------------------------------------------------------------------------
# Child naming
# ---------------------------------------------------------------------------


def child_name(spec: Spec) -> str:
    """Derive a filesystem-safe name for the generated child project."""
    selections = dict(spec.selections)
    domain = selections.get("primitive_domain", "unknown")
    return f"child_{domain}_{spec.spec_hash}"


# ---------------------------------------------------------------------------
# Import rewriting
# ---------------------------------------------------------------------------


def _rewrite_kernel_imports(code: str) -> str:
    """Rewrite 'from src.primitives' imports to local 'from primitives'."""
    return code.replace("from src.primitives", "from primitives").replace("from .primitives", "from primitives")


# ---------------------------------------------------------------------------
# Vendoring helpers
# ---------------------------------------------------------------------------

_VENDORABLE_MODULE_PATHS: dict[str, str] = {
    "logging": "infrastructure/core/logging/utils.py",
    "glossary_gen": "infrastructure/rendering/glossary_gen.py",
    "figure_manager": "infrastructure/rendering/figure_manager.py",
    "manuscript_injection": "infrastructure/rendering/manuscript_injection.py",
    "steganography": "infrastructure/rendering/steganography.py",
}

_MULTI_FILE_VENDOR_DEPS: dict[str, list[str]] = {
    # deps that require multiple files (package vs single module)
}


def _vendor_kernel_sources(spec: Spec, template_root: Path) -> dict[str, str]:
    """Collect the primitive kernel sources for the selected domain."""
    domain = spec.primitive_domain
    prim_dir = template_root / "src" / "primitives"
    files: dict[str, str] = {}

    # Copy base.py
    for fname in ["base.py", f"{domain}.py"]:
        src_path = prim_dir / fname
        if src_path.exists():
            content = src_path.read_text()
            files[f"primitives/{fname}"] = _rewrite_kernel_imports(content)

    # Write a minimal __init__.py that only imports the selected domain
    init_content = f'''"""Primitives package — generated for domain: {domain}."""
from __future__ import annotations

from .base import PrimitiveSpec


def collect_primitives() -> dict[str, tuple]:
    """Return registered primitive specs for the {domain} domain."""
    from . import {domain}
    return {{"{domain}": {domain}.PRIMITIVES}}


__all__ = ["PrimitiveSpec", "collect_primitives"]
'''
    files["primitives/__init__.py"] = init_content

    return files


def _vendor_figures_source(template_root: Path) -> dict[str, str]:
    """Vendor the figures.py source into the child."""
    figures_path = template_root / "src" / "figures.py"
    if figures_path.exists():
        return {"figures.py": figures_path.read_text()}
    return {}


def _vendor_infra_module(module: str, template_root: Path) -> tuple[str, str]:
    """Return (relative_dest, content) for a vendored infra module."""
    rel_path = _VENDORABLE_MODULE_PATHS.get(module, "")
    src = template_root.parent.parent.parent / rel_path  # repo root relative
    if src.exists():
        return (f"vendored/{module}.py", src.read_text())
    # Generate a stub
    stub = f'"""Vendored stub for {module}."""\n# Source not found at build time.\n'
    return (f"vendored/{module}.py", stub)


def _template_seam_file(template_modules: list[str]) -> str:
    """Generate the seam __init__.py that re-exports all vendored modules."""
    lines = ['"""Vendored infrastructure seam — auto-generated."""']
    for mod in template_modules:
        lines.append(f"from . import {mod}  # noqa: F401")
    return "\n".join(lines) + "\n"


def _infra_seam_test_file(template_modules: list[str]) -> str:
    """Generate a smoke test for the vendored seam."""
    lines = [
        '"""Smoke tests for vendored infrastructure seam."""',
        "import importlib",
        "",
        "",
    ]
    for mod in template_modules:
        lines.append(f"def test_vendored_{mod}_importable():")
        lines.append(f'    """Vendored {mod} must be importable."""')
        lines.append(f'    m = importlib.import_module("vendored.{mod}")')
        lines.append("    assert m is not None")
        lines.append("")
    return "\n".join(lines)


def _vendor_test_file(module: str) -> str:
    """Generate a test stub for a vendored module."""
    return textwrap.dedent(f"""\
        \"\"\"Stub tests for vendored {module}.\"\"\"


        def test_{module}_stub():
            \"\"\"Vendored {module} module stub exists.\"\"\"
            import importlib
            m = importlib.import_module("vendored.{module}")
            assert m is not None
        """)


def _resolve_deps(spec: Spec, template_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Resolve dependency vendoring.

    Returns (tree_additions, vendoring_manifest).
    """
    tree_additions: dict[str, str] = {}
    vendoring_manifest: dict[str, str] = {}

    if not spec.deps:
        return tree_additions, vendoring_manifest

    selections = dict(spec.selections)
    dep_mode = selections.get("dep_mode", "vendor")

    if dep_mode not in ("vendor", "template"):
        raise ValueError(f"Unknown dep_mode '{dep_mode}'. Known: ('vendor', 'template')")

    if dep_mode == "template":
        # SYNTAX.md documents a per-dependency "template" mode ("use template
        # infrastructure seam") as an alternative to "vendor" ("vendor as
        # single-file stub"), but that mode has never been implemented: only
        # a single scalar `dep_mode` selection exists (there is no per-dep
        # override), and this module's own contract — a materialized child
        # "can run its own tests, produce figures, and render a manuscript —
        # all without requiring the parent template infrastructure at
        # runtime" (see module docstring) — is fundamentally incompatible
        # with a "seam" mode whose entire point is to import from the parent
        # repo's infrastructure/ package at runtime instead of vendoring a
        # standalone copy. Implementing it for real would require either
        # relaxing that self-containment guarantee or defining a new,
        # currently-unspecified seam contract. Fail loudly instead of
        # silently producing zero files/seam so a fork cannot mistake this
        # for a working feature. See TODO.md for the tracked follow-up.
        raise NotImplementedError(
            "dep_mode='template' is a documented-but-unimplemented gap in "
            "materialize.py::_resolve_deps — see SYNTAX.md 'Deps Syntax' and "
            "the code comment at this raise site. Use dep_mode='vendor' "
            "instead, or implement the template seam contract before relying "
            "on this mode."
        )

    for dep in spec.deps:
        if dep_mode == "vendor":
            dest, content = _vendor_infra_module(dep, template_root)
            tree_additions[dest] = content
            vendoring_manifest[dep] = dest

    if vendoring_manifest:
        # Write the seam __init__
        mods = list(vendoring_manifest.keys())
        tree_additions["vendored/__init__.py"] = _template_seam_file(mods)

    return tree_additions, vendoring_manifest


# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------


def _build_tree(spec: Spec, template_root: Path) -> dict[str, str]:
    """Assemble the full file tree for the child project."""
    tree: dict[str, str] = {}

    # Kernel / primitives
    tree.update(_vendor_kernel_sources(spec, template_root))

    # Figures source
    tree.update(_vendor_figures_source(template_root))

    # Deps
    dep_additions, _ = _resolve_deps(spec, template_root)
    tree.update(dep_additions)

    # The child-facing file bodies have one source of truth.  Keeping this
    # registry shared with ``emit_file`` prevents materialization from drifting
    # from the standalone template-emission API.
    tree.update(emit_all(spec))
    tree["tests/__init__.py"] = ""

    return tree


# ---------------------------------------------------------------------------
# Main materialize function
# ---------------------------------------------------------------------------


def materialize(
    spec: Spec,
    out_root: str | Path,
    template_root: str | Path,
    clean: bool = False,
) -> MaterializeResult:
    """Write a complete child project derived from *spec* under *out_root*.

    Parameters
    ----------
    spec:
        The expansion spec to materialize.
    out_root:
        Parent directory; the child will be created at out_root/child_name.
    template_root:
        Root of the template_autopoiesis project (contains src/, manuscript/).
    clean:
        If True, remove any existing child directory before writing.
    """
    out_root = Path(out_root)
    template_root = Path(template_root)
    name = child_name(spec)
    child_root = out_root / name

    if clean and child_root.exists():
        shutil.rmtree(child_root)

    child_root.mkdir(parents=True, exist_ok=True)

    tree = _build_tree(spec, template_root)

    written: dict[str, str] = {}
    for rel_path, content in tree.items():
        abs_path = child_root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        written[rel_path] = content

    # Compute tree hash
    content_hashes = {k: v for k, v in written.items()}
    th = tree_hash_from_content_hashes({k: v for k, v in content_hashes.items()})

    # Provenance record
    provenance = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "spec": spec.to_dict(),
        "tree_hash": th,
        "files": sorted(written.keys()),
    }
    prov_path = child_root / "provenance.json"
    prov_path.write_text(json.dumps(provenance, indent=2, sort_keys=True))

    return MaterializeResult(
        root=child_root,
        name=name,
        files=written,
        tree_hash=th,
        provenance_path=prov_path,
    )
