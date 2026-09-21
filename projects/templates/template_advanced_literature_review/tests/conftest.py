"""Pytest configuration for template_advanced_literature_review tests."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ and scripts/ so tests resolve project modules the same way whether
# pytest is invoked from the repository root (documented AGENTS.md verification
# command) or standalone from this project directory (STANDALONE.md fork
# workflow). Mirrors the sibling conftest.py pattern in
# template_literature_meta_analysis/tests/conftest.py.
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_REPO_ROOT = _ROOT.parents[2]
for _path in (str(_REPO_ROOT), str(_SCRIPTS), str(_SRC)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# The sibling meta exemplar keeps a flat src/ package (analysis/, knowledge_graph/,
# reproducibility/, visualization/, config_loader.py), so the nested name
# ``template_literature_meta_analysis`` cannot resolve under plain sys.path rules.
# Register that flat package under the project-unique alias (the repo's
# _PKG_ALIAS pattern) and append its src AFTER this project's own entries, so
# meta-internal absolute imports (``from analysis...``, ``from config_loader...``)
# also resolve, while this project's top-level ``literature``/``config`` stay
# winning. Under repository-root runs, where the root conftest already inserts
# every projects/*/src, the extra entries are duplicates and no-ops.
_META_ROOT = _ROOT.parent / "template_literature_meta_analysis"
_META_SRC = _META_ROOT / "src"
if _META_SRC.is_dir():
    _meta_src_str = str(_META_SRC)
    if _meta_src_str not in sys.path:
        sys.path.append(_meta_src_str)
    _META_ALIAS = "template_literature_meta_analysis"
    if _META_ALIAS not in sys.modules:
        _meta_spec = importlib.util.spec_from_file_location(
            _META_ALIAS, _META_SRC / "__init__.py", submodule_search_locations=[_meta_src_str]
        )
        assert _meta_spec is not None and _meta_spec.loader is not None
        _meta_package = importlib.util.module_from_spec(_meta_spec)
        sys.modules[_META_ALIAS] = _meta_package
        _meta_spec.loader.exec_module(_meta_package)
