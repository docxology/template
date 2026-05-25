"""Comprehensive tests for ``infrastructure.reporting.interactive_dashboard``.

Covers every Invariant kind, every Control kind, panel + dashboard
construction, JSON-serialization of numpy arrays, plaintext rendering,
HTML structure, JS embed validity, and round-trip writes — plus the
reporting-package re-exports.

Real numpy arrays, real subprocess for JS syntax check (when ``node``
is available), zero mocks.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest


from infrastructure.reporting import (  # re-export sanity
    InteractiveDashboard,
    Invariant,
    Panel,
)
from infrastructure.reporting.interactive_dashboard import (
    PLOTLY_CDN,
    _to_jsonable,
)


# ---------------------------------------------------------------------------
# Re-exports
# ---------------------------------------------------------------------------


def test_reporting_package_exposes_dashboard_symbols():
    import infrastructure.reporting as rep

    for name in ("InteractiveDashboard", "Panel", "Control", "Invariant"):
        assert name in rep.__all__
        assert hasattr(rep, name)


# ---------------------------------------------------------------------------
# _to_jsonable
# ---------------------------------------------------------------------------


class TestToJsonable:
    def test_primitives(self):
        assert _to_jsonable(1) == 1
        assert _to_jsonable("x") == "x"
        assert _to_jsonable(True) is True
        assert _to_jsonable(None) is None

    def test_non_finite_floats_become_none(self):
        assert _to_jsonable(float("nan")) is None
        assert _to_jsonable(float("inf")) is None
        assert _to_jsonable(float("-inf")) is None

    def test_numpy_array_to_list(self):
        a = np.linspace(0, 1, 4)
        out = _to_jsonable(a)
        assert isinstance(out, list)
        assert out == pytest.approx([0.0, 1 / 3, 2 / 3, 1.0])

    def test_numpy_scalar_to_python(self):
        v = np.float64(3.14)
        out = _to_jsonable(v)
        assert isinstance(out, float)
        assert out == pytest.approx(3.14)

    def test_path_to_string(self):
        p = Path("/tmp/x")
        assert _to_jsonable(p) == "/tmp/x"

    def test_dict_recurses(self):
        out = _to_jsonable({"a": np.array([1, 2]), "b": {"c": Path("/")}})
        assert out == {"a": [1, 2], "b": {"c": "/"}}

    def test_list_and_tuple_recurse(self):
        out = _to_jsonable([np.array([1.0]), (np.array([2.0]),)])
        assert out == [[1.0], [[2.0]]]

    def test_dataclass_round_trip(self):
        from dataclasses import dataclass

        @dataclass
        class X:
            a: int
            b: list

        out = _to_jsonable(X(a=1, b=[np.float64(2)]))
        assert out == {"a": 1, "b": [2.0]}


# ---------------------------------------------------------------------------
# Invariant.evaluate — every kind, both pass and fail paths
# ---------------------------------------------------------------------------


class TestInvariantEqual:
    def test_pass(self):
        ok, w = Invariant("e", actual=1.0, expected=1.0, tol=1e-12).evaluate()
        assert ok and "0.000e+00" in w

    def test_fail(self):
        ok, w = Invariant("e", actual=1.0, expected=0.0, tol=1e-12).evaluate()
        assert not ok and "1.000e+00" in w


class TestInvariantLE:
    def test_within(self):
        assert Invariant("l", actual=0.5, expected=1.0, tol=0, kind="le").evaluate()[0]

    def test_within_with_tolerance(self):
        ok, _ = Invariant("l", actual=1.001, expected=1.0, tol=1e-2, kind="le").evaluate()
        assert ok

    def test_violated(self):
        ok, _ = Invariant("l", actual=2.0, expected=1.0, tol=0, kind="le").evaluate()
        assert not ok


class TestInvariantGE:
    def test_within(self):
        assert Invariant("g", actual=2.0, expected=1.0, tol=0, kind="ge").evaluate()[0]

    def test_violated(self):
        ok, _ = Invariant("g", actual=0.0, expected=1.0, tol=0, kind="ge").evaluate()
        assert not ok


class TestInvariantInRange:
    def test_within(self):
        ok, _ = Invariant("r", actual=0.5, expected=(0.0, 1.0), tol=0, kind="in_range").evaluate()
        assert ok

    def test_at_boundary(self):
        ok, _ = Invariant("r", actual=1.0, expected=(0.0, 1.0), tol=1e-12, kind="in_range").evaluate()
        assert ok

    def test_below(self):
        ok, _ = Invariant("r", actual=-0.5, expected=(0.0, 1.0), tol=0, kind="in_range").evaluate()
        assert not ok

    def test_above(self):
        ok, _ = Invariant("r", actual=1.5, expected=(0.0, 1.0), tol=0, kind="in_range").evaluate()
        assert not ok


class TestInvariantMonotone:
    def test_increasing_strict_ok(self):
        ok, _ = Invariant("m", actual=[1, 2, 3], tol=1e-12, kind="monotone_increasing").evaluate()
        assert ok

    def test_increasing_weak_ok(self):
        ok, _ = Invariant("m", actual=[1, 2, 2, 3], tol=1e-12, kind="monotone_increasing").evaluate()
        assert ok

    def test_increasing_violation_caught(self):
        ok, w = Invariant("m", actual=[1, 2, 1.5, 3], tol=1e-12, kind="monotone_increasing").evaluate()
        assert not ok and "worst" in w

    def test_decreasing_ok(self):
        ok, _ = Invariant("md", actual=[5, 4, 4, 3], tol=1e-12, kind="monotone_decreasing").evaluate()
        assert ok

    def test_decreasing_violation_caught(self):
        ok, _ = Invariant("md", actual=[5, 4, 6, 3], tol=1e-12, kind="monotone_decreasing").evaluate()
        assert not ok

    def test_within_tolerance(self):
        ok, _ = Invariant(
            "m",
            actual=[1.0, 1.0 - 1e-13, 2.0],
            tol=1e-9,
            kind="monotone_increasing",
        ).evaluate()
        assert ok

    def test_empty_sequence(self):
        ok, _ = Invariant("m", actual=[], tol=1e-12, kind="monotone_increasing").evaluate()
        assert ok

    def test_singleton(self):
        ok, _ = Invariant("m", actual=[1.0], tol=1e-12, kind="monotone_increasing").evaluate()
        assert ok


class TestInvariantFinite:
    def test_scalar_finite(self):
        assert Invariant("f", actual=1.0, kind="finite").evaluate()[0]

    def test_scalar_inf_fails(self):
        assert not Invariant("f", actual=float("inf"), kind="finite").evaluate()[0]

    def test_scalar_nan_fails(self):
        assert not Invariant("f", actual=float("nan"), kind="finite").evaluate()[0]

    def test_array_all_finite(self):
        ok, w = Invariant("f", actual=[1.0, 2.0, 3.0], kind="finite").evaluate()
        assert ok and "3 values" in w

    def test_array_with_nan(self):
        ok, w = Invariant("f", actual=[1.0, float("nan"), 3.0], kind="finite").evaluate()
        assert not ok and "1" in w


class TestInvariantNonNeg:
    def test_scalar_pos(self):
        assert Invariant("n", actual=0.5, kind="nonneg").evaluate()[0]

    def test_scalar_zero_with_tol(self):
        assert Invariant("n", actual=-1e-12, tol=1e-9, kind="nonneg").evaluate()[0]

    def test_scalar_neg(self):
        assert not Invariant("n", actual=-1.0, kind="nonneg", tol=0).evaluate()[0]

    def test_array_ok(self):
        ok, _ = Invariant("n", actual=[0.0, 1.0, 2.0], kind="nonneg").evaluate()
        assert ok

    def test_array_neg_caught(self):
        ok, w = Invariant("n", actual=[0.0, -0.5, 2.0], kind="nonneg", tol=0).evaluate()
        assert not ok and "-0.5" in w


class TestInvariantArrayClose:
    def test_pass(self):
        ok, w = Invariant(
            "ac",
            actual=[1.0, 2.0, 3.0],
            expected=[1.0 + 1e-13, 2.0, 3.0 - 1e-14],
            tol=1e-9,
            kind="array_close",
        ).evaluate()
        assert ok and "max |" in w

    def test_fail_with_index(self):
        ok, w = Invariant(
            "ac",
            actual=[1.0, 2.0, 3.0],
            expected=[1.0, 2.5, 3.0],
            tol=1e-3,
            kind="array_close",
        ).evaluate()
        assert not ok and "index 1" in w

    def test_length_mismatch(self):
        ok, w = Invariant(
            "ac",
            actual=[1.0, 2.0],
            expected=[1.0, 2.0, 3.0],
            tol=1e-3,
            kind="array_close",
        ).evaluate()
        assert not ok and "length mismatch" in w


class TestInvariantUnknownKind:
    def test_unknown_returns_false(self):
        inv = Invariant("u", actual=1.0, expected=1.0, kind="bogus")  # type: ignore[arg-type]
        ok, w = inv.evaluate()
        assert not ok and "unknown kind" in w


# ---------------------------------------------------------------------------
# InteractiveDashboard
# ---------------------------------------------------------------------------


@pytest.fixture
def dash():
    return InteractiveDashboard(title="Smoke", subtitle="sub", project_name="proj_x")


class TestBuilderSetters:
    def test_set_payload_makes_jsonable(self, dash):
        dash.set_payload({"a": np.array([1.0, 2.0])})
        assert dash.payload["a"] == [1.0, 2.0]

    def test_set_hyperparameters(self, dash):
        dash.set_hyperparameters({"n": 5, "alpha": np.float64(0.1)})
        assert dash.hyperparameters == {"n": 5, "alpha": 0.1}

    def test_set_meta(self, dash):
        dash.set_meta(seed=42, source="test")
        assert dash._extra_meta == {"seed": 42, "source": "test"}

    def test_add_table(self, dash):
        dash.add_table("rows", [{"x": np.float64(1.0)}, {"x": 2.0}])
        assert dash.tables["rows"] == [{"x": 1.0}, {"x": 2.0}]

    def test_add_note(self, dash):
        dash.add_note("hello").add_note("world")
        assert dash.notes == ["hello", "world"]


class TestBuilderControls:
    def test_add_slider(self, dash):
        dash.add_slider("s", "S", min=0, max=1, step=0.1, default=0.5, description="d")
        c = dash.controls[0]
        assert c.control_id == "s"
        assert c.kind == "slider"
        assert c.default == 0.5
        assert c.description == "d"

    def test_add_dropdown(self, dash):
        dash.add_dropdown("d", "D", options=["a", "b"], default="a", option_labels=["A", "B"])
        c = dash.controls[0]
        assert c.kind == "dropdown"
        assert c.options == ["a", "b"]
        assert c.option_labels == ["A", "B"]

    def test_add_toggle(self, dash):
        dash.add_toggle("t", "T", default=True)
        c = dash.controls[0]
        assert c.kind == "toggle" and c.default is True

    def test_duplicate_panel_id_rejected(self, dash):
        dash.add_panel(Panel(panel_id="p", title="A", traces=[]))
        with pytest.raises(ValueError, match="duplicate panel_id"):
            dash.add_panel(Panel(panel_id="p", title="B", traces=[]))

    def test_duplicate_control_id_rejected(self, dash):
        dash.add_slider("c", "C", min=0, max=1, step=0.1, default=0.5)
        with pytest.raises(ValueError, match="duplicate control_id"):
            dash.add_slider("c", "C", min=0, max=1, step=0.1, default=0.5)


class TestBuilderInvariants:
    def test_evaluate_invariants_returns_dicts(self, dash):
        dash.add_invariant(Invariant("ok", actual=1.0, expected=1.0, tol=1e-9))
        dash.add_invariant(Invariant("bad", actual=2.0, expected=1.0, tol=1e-9))
        results = dash.evaluate_invariants()
        assert results[0]["passed"] is True
        assert results[1]["passed"] is False
        # Required fields
        for r in results:
            for f in ("name", "kind", "tolerance", "witness", "description", "passed"):
                assert f in r


# ---------------------------------------------------------------------------
# Plaintext renderers
# ---------------------------------------------------------------------------


class TestPlaintextRendering:
    def test_invariants_summary_counts(self, dash):
        dash.add_invariant(Invariant("a", actual=1.0, expected=1.0, tol=1e-9))
        dash.add_invariant(Invariant("b", actual=2.0, expected=1.0, tol=1e-9))
        dash.add_invariant(Invariant("c", actual=3.0, expected=1.0, tol=1e-9))
        text = dash.render_invariants_text()
        assert "1/3 passed" in text and "2 failed" in text
        assert "[PASS] a" in text
        assert "[FAIL] b" in text
        assert "[FAIL] c" in text

    def test_empty_invariants(self, dash):
        text = dash.render_invariants_text()
        assert "0/0 passed" in text
        assert "(no invariants registered)" in text

    def test_summary_renders_hyperparameters(self, dash):
        dash.set_hyperparameters({"alpha": 0.1, "lams": list(range(20))})
        text = dash.render_summary_text()
        assert "alpha: 0.1" in text
        # Long list collapsed
        assert "len=20" in text or "len=20)" in text

    def test_summary_includes_notes(self, dash):
        dash.add_note("first").add_note("second")
        assert "first" in dash.render_summary_text()
        assert "second" in dash.render_summary_text()


# ---------------------------------------------------------------------------
# write() round-trip
# ---------------------------------------------------------------------------


class TestWriteRoundTrip:
    def test_html_json_invariants_summary(self, tmp_path):
        d = InteractiveDashboard(title="X", subtitle="sub", project_name="proj")
        d.set_payload({"x": np.linspace(0, 1, 5).tolist()})
        d.set_hyperparameters({"k": 3})
        d.add_slider("s", "S", min=0, max=1, step=0.25, default=0.5)
        d.add_panel(
            Panel(
                panel_id="p1",
                title="Panel One",
                traces=[
                    {
                        "type": "scatter",
                        "x": [0, 1, 2],
                        "y": [3, 4, 5],
                    }
                ],
            )
        )
        d.add_invariant(Invariant("nn", actual=[0, 1, 2], kind="nonneg"))
        d.add_table("t1", [{"a": 1}, {"a": 2}])
        d.add_note("hello")

        outs = d.write(
            html_path=tmp_path / "d.html",
            json_path=tmp_path / "d.json",
            invariants_path=tmp_path / "i.txt",
            txt_path=tmp_path / "s.txt",
        )
        assert set(outs) == {"html", "json", "invariants", "summary"}
        for p in outs.values():
            assert p.exists() and p.stat().st_size > 0

        # JSON bundle is parseable, contains expected keys
        bundle = json.loads(outs["json"].read_text())
        for k in (
            "title",
            "subtitle",
            "project",
            "generated_utc",
            "git_rev",
            "hyperparameters",
            "payload",
            "panels",
            "controls",
            "invariants",
            "tables",
            "notes",
        ):
            assert k in bundle
        assert bundle["panels"][0]["panel_id"] == "p1"
        assert bundle["controls"][0]["control_id"] == "s"
        assert bundle["invariants"][0]["passed"] is True
        assert bundle["tables"]["t1"] == [{"a": 1}, {"a": 2}]
        assert "hello" in bundle["notes"]

        # HTML structure: Plotly CDN, BUNDLE injection, panel title visible
        html = outs["html"].read_text()
        assert PLOTLY_CDN in html
        assert "Panel One" in html
        # BUNDLE is JSON-parseable
        m = re.search(r"const BUNDLE = (\{.*?\});", html, re.DOTALL)
        assert m is not None
        re_parsed = json.loads(m.group(1))
        assert re_parsed["panels"][0]["title"] == "Panel One"

    def test_html_only(self, tmp_path):
        d = InteractiveDashboard(title="HtmlOnly")
        out = d.write(html_path=tmp_path / "d.html")
        assert set(out) == {"html"}
        assert out["html"].exists()

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c" / "d.html"
        d = InteractiveDashboard(title="X")
        d.write(html_path=nested)
        assert nested.exists()


# ---------------------------------------------------------------------------
# JS validity (only when ``node`` is available)
# ---------------------------------------------------------------------------


_NODE = shutil.which("node")


@pytest.mark.skipif(_NODE is None, reason="node not installed")
class TestPanelUpdateFnSyntax:
    """Every ``Panel.update_fn`` must be valid JavaScript when wrapped in a
    function body. Invalid update_fns silently break the dashboard, so we
    syntax-check them with ``node --check`` whenever it is available.
    """

    def test_simple_update_fn(self, tmp_path):
        d = InteractiveDashboard(title="js")
        d.add_panel(
            Panel(
                panel_id="p1",
                title="P",
                traces=[],
                driven_by=["s"],
                update_fn=r"""
const v = controls.s;
Plotly.relayout(panelId, {title: 'v=' + v});
""",
            )
        )
        d.add_slider("s", "S", min=0, max=1, step=0.1, default=0.5)
        out = d.write(html_path=tmp_path / "d.html", json_path=tmp_path / "d.json")
        bundle = json.loads(out["json"].read_text())
        body = bundle["panels"][0]["update_fn"]
        wrap = "function _t(payload, controls, Plotly, panelId) {" + body + "}"
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(wrap)
            name = f.name
        try:
            r = subprocess.run(
                [_NODE, "--check", name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert r.returncode == 0, f"JS syntax error: {r.stderr}"
        finally:
            Path(name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# to_json (without write)
# ---------------------------------------------------------------------------


class TestToJsonSnapshot:
    def test_keys_and_types(self, dash):
        dash.add_invariant(Invariant("n", actual=1.0, expected=1.0, tol=1e-9))
        dash.add_panel(Panel(panel_id="p", title="t", traces=[]))
        dash.add_slider("s", "S", min=0, max=1, step=0.1, default=0.5)
        snap = dash.to_json()
        for key in (
            "title",
            "panels",
            "controls",
            "invariants",
            "tables",
            "notes",
            "git_rev",
            "generated_utc",
            "hyperparameters",
        ):
            assert key in snap
        assert snap["invariants"][0]["passed"] is True
