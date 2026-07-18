"""Tests for figure rendering module."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from src.figures import (
    _first_plottable_array,
    _scalar_summary_lines,
    render_primitive_figure,
    build_figure_registry,
)
from src.grammar import KNOWN_DOMAINS
from src.primitives import collect_primitives


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# render_primitive_figure — parametrized over domains
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_render_primitive_figure_per_domain(domain, tmp_path):
    prims = collect_primitives()
    specs = prims[domain]
    for spec in specs:
        result = spec.fn(spec.example_input)
        out = tmp_path / f"{domain}_{spec.name}.png"
        returned_path = render_primitive_figure(spec.name, result, out)
        assert returned_path.exists()
        assert returned_path.stat().st_size > 100


@pytest.mark.parametrize("domain", list(KNOWN_DOMAINS))
def test_render_primitive_figure_returns_path(domain, tmp_path):
    prims = collect_primitives()
    spec = prims[domain][0]
    result = spec.fn(spec.example_input)
    out = tmp_path / "fig.png"
    returned = render_primitive_figure(spec.name, result, out)
    assert returned == out


# ---------------------------------------------------------------------------
# scalar fallback tests
# ---------------------------------------------------------------------------


def test_render_scalar_result(tmp_path):
    """A scalar result should produce a text-figure without crashing."""
    out = tmp_path / "scalar.png"
    path = render_primitive_figure("scalar_test", 42.0, out)
    assert path.exists()


def test_render_dict_result(tmp_path):
    out = tmp_path / "dict.png"
    path = render_primitive_figure("dict_test", {"key1": 1.0, "key2": 2.0}, out)
    assert path.exists()


def test_render_single_element_array(tmp_path):
    out = tmp_path / "single.png"
    path = render_primitive_figure("single_arr", np.array([3.14]), out)
    assert path.exists()


def test_render_empty_array_uses_explicit_empty_summary(tmp_path):
    out = tmp_path / "empty.png"
    path = render_primitive_figure("empty_arr", np.array([]), out)

    assert path.exists()
    assert "mean = n/a" in "\n".join(_scalar_summary_lines(np.array([])))


def test_render_multi_element_array_plots(tmp_path):
    """A plain array with >1 elements takes the line-plot branch, not the summary branch."""
    out = tmp_path / "plotted.png"
    path = render_primitive_figure("multi_arr", np.array([1.0, 2.0, 3.0, 4.0]), out)
    assert path.exists()
    assert path.stat().st_size > 100


def test_first_plottable_array_from_list():
    """A plain Python list (not ndarray) is coerced and ravelled."""
    result = _first_plottable_array([1.0, 2.0, 3.0])
    assert result is not None
    assert list(result) == [1.0, 2.0, 3.0]


def test_first_plottable_array_from_tuple():
    result = _first_plottable_array((4.0, 5.0))
    assert result is not None
    assert list(result) == [4.0, 5.0]


def test_first_plottable_array_empty_list_returns_none():
    assert _first_plottable_array([]) is None


def test_scalar_summary_lines_generic_repr_fallback():
    """A value that is neither int/float/complex/ndarray/dict falls back to repr()."""
    lines = _scalar_summary_lines("just a plain string")
    assert lines == [repr("just a plain string")[:80]]


# ---------------------------------------------------------------------------
# build_figure_registry
# ---------------------------------------------------------------------------


def test_figure_registry_roundtrip(tmp_path):
    prims = collect_primitives()
    domain = "optimization"
    results = [(spec.name, spec.fn(spec.example_input)) for spec in prims[domain]]
    registry = build_figure_registry(domain, results, tmp_path)
    for name, path in registry.items():
        assert path.exists()
        assert path.stat().st_size > 100


def test_figure_registry_keys_match_names(tmp_path):
    prims = collect_primitives()
    domain = "signal"
    results = [(spec.name, spec.fn(spec.example_input)) for spec in prims[domain]]
    registry = build_figure_registry(domain, results, tmp_path)
    expected_names = {spec.name for spec in prims[domain]}
    assert set(registry.keys()) == expected_names


def test_figure_registry_empty(tmp_path):
    registry = build_figure_registry("optimization", [], tmp_path)
    assert registry == {}


def test_figure_count_all_domains(tmp_path):
    prims = collect_primitives()
    total = 0
    for domain in KNOWN_DOMAINS:
        results = [(spec.name, spec.fn(spec.example_input)) for spec in prims[domain]]
        registry = build_figure_registry(domain, results, tmp_path / domain)
        total += len(registry)
    # 8 total primitives
    assert total == 8
