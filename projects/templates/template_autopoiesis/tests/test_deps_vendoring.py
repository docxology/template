"""Tests for dependency vendoring in materialize."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS, force_domain, parse_grammar
from src.expand import expand
from src.materialize import (
    materialize,
    _resolve_deps,
    _template_seam_file,
    _infra_seam_test_file,
    _vendor_infra_module,
)


def _make_grammar(domain=None, seed=42, dep_mode="vendor", deps=None):
    block = {
        "seed": seed,
        "slots": [
            {"name": "primitive_domain", "options": list(KNOWN_DOMAINS)},
            {"name": "dep_mode", "options": [dep_mode]},
            {"name": "figure_profile", "options": ["minimal"]},
            {"name": "qr_profile", "options": ["off"]},
            {"name": "integrity_profile", "options": ["sha256"]},
        ],
        "deps": deps or [],
    }
    g = parse_grammar(block)
    if domain:
        g = force_domain(g, domain)
    return g


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# _vendor_infra_module
# ---------------------------------------------------------------------------


def test_vendor_infra_module_returns_tuple():
    template_root = Path(__file__).parent.parent
    dest, content = _vendor_infra_module("glossary_gen", template_root)
    assert isinstance(dest, str)
    assert isinstance(content, str)


def test_vendor_infra_module_dest_under_vendored():
    template_root = Path(__file__).parent.parent
    dest, _ = _vendor_infra_module("glossary_gen", template_root)
    assert dest.startswith("vendored/")


def test_vendor_infra_module_stub_content():
    template_root = Path(__file__).parent.parent
    # steganography is unlikely to exist in infra
    _, content = _vendor_infra_module("steganography", template_root)
    assert isinstance(content, str)
    assert len(content) > 0


# ---------------------------------------------------------------------------
# _template_seam_file
# ---------------------------------------------------------------------------


def test_template_seam_file_imports_all():
    mods = ["logging", "glossary_gen"]
    seam = _template_seam_file(mods)
    assert "from . import logging" in seam
    assert "from . import glossary_gen" in seam


def test_template_seam_file_has_docstring():
    seam = _template_seam_file(["logging"])
    assert "Vendored" in seam


# ---------------------------------------------------------------------------
# _infra_seam_test_file
# ---------------------------------------------------------------------------


def test_infra_seam_test_file_has_test_functions():
    content = _infra_seam_test_file(["logging", "glossary_gen"])
    assert "def test_vendored_logging_importable" in content
    assert "def test_vendored_glossary_gen_importable" in content


def test_infra_seam_test_file_uses_importlib():
    content = _infra_seam_test_file(["logging"])
    assert "importlib" in content


# ---------------------------------------------------------------------------
# _resolve_deps — vendor mode
# ---------------------------------------------------------------------------


def test_resolve_deps_vendor_mode_adds_files(template_root):
    g = _make_grammar(domain="optimization", dep_mode="vendor", deps=["glossary_gen"])
    spec = expand(g)
    additions, manifest = _resolve_deps(spec, template_root)
    assert len(additions) > 0


def test_resolve_deps_vendor_mode_manifest_has_dep(template_root):
    g = _make_grammar(domain="optimization", dep_mode="vendor", deps=["glossary_gen"])
    spec = expand(g)
    _, manifest = _resolve_deps(spec, template_root)
    assert "glossary_gen" in manifest


def test_resolve_deps_vendor_mode_seam_init(template_root):
    g = _make_grammar(domain="optimization", dep_mode="vendor", deps=["glossary_gen"])
    spec = expand(g)
    additions, _ = _resolve_deps(spec, template_root)
    assert "vendored/__init__.py" in additions


def test_resolve_deps_empty_no_files(template_root):
    g = _make_grammar(domain="optimization", dep_mode="vendor", deps=[])
    spec = expand(g)
    additions, manifest = _resolve_deps(spec, template_root)
    assert len(additions) == 0
    assert len(manifest) == 0


# ---------------------------------------------------------------------------
# Materialize with deps
# ---------------------------------------------------------------------------


def test_materialize_with_glossary_dep(tmp_path, template_root):
    g = _make_grammar(domain="optimization", dep_mode="vendor", deps=["glossary_gen"])
    spec = expand(g)
    result = materialize(spec, out_root=tmp_path, template_root=template_root)
    assert result.root.is_dir()
    # Should have vendored/__init__.py
    assert (result.root / "vendored" / "__init__.py").exists()
