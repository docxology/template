"""Tests for the optimizer invariants module and the build_dashboard CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from src.invariants import (
    InvariantResult,
    OptimizerSweepConfig,
    all_invariants,
    convergence_invariants,
    gradient_consistency_invariants,
    trajectory_invariants,
)


THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent


# ---------------------------------------------------------------------------
# OptimizerSweepConfig
# ---------------------------------------------------------------------------


class TestOptimizerSweepConfig:
    def test_defaults(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,))
        assert cfg.A == ((1.0,),)
        assert cfg.b == (1.0,)
        assert cfg.initial_point == (0.0,)

    def test_closed_form_minimum(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,), A=((2.0,),), b=(4.0,))
        x_star = cfg.closed_form_minimum()
        np.testing.assert_allclose(x_star, [2.0])

    def test_stable_step_bound(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,), A=((4.0,),))
        # 2 / λ_max = 2 / 4 = 0.5
        assert cfg.stable_step_bound() == pytest.approx(0.5)

    def test_run_for_returns_optimization_result(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,))
        r = cfg.run_for(0.1)
        assert hasattr(r, "solution")
        assert hasattr(r, "iterations")
        assert hasattr(r, "converged")


# ---------------------------------------------------------------------------
# Invariant builders
# ---------------------------------------------------------------------------


class TestConvergenceInvariants:
    def test_default_quadratic_all_pass(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.01, 0.1, 0.5, 1.0, 1.5))
        invs = convergence_invariants(cfg)
        # Each stable α contributes 3 invariants + 1 finite invariant overall
        assert len(invs) == 3 * 5 + 1
        for inv in invs:
            ok, _ = _evaluate(inv)
            assert ok, f"{inv.name} failed: {_witness(inv)}"

    def test_skips_divergent_step(self):
        # α = 2.5 > 2/λ_max = 2.0 ⇒ divergent; should not produce monotone/converged invariants
        cfg = OptimizerSweepConfig(step_sizes=(0.1, 2.5))
        invs = convergence_invariants(cfg)
        names = {i.name for i in invs}
        assert any("alpha=0.1" in n for n in names)
        assert not any("alpha=2.5" in n for n in names if "monotone" in n or "reached" in n)

    def test_well_conditioned_2d(self):
        # 2-D quadratic with diagonal Hessian = diag(1, 2); λ_max = 2 → bound = 1.0
        cfg = OptimizerSweepConfig(
            step_sizes=(0.1, 0.5),
            A=((1.0, 0.0), (0.0, 2.0)),
            b=(1.0, 2.0),
            initial_point=(0.0, 0.0),
        )
        assert cfg.stable_step_bound() == pytest.approx(1.0)
        np.testing.assert_allclose(cfg.closed_form_minimum(), [1.0, 1.0])
        for inv in convergence_invariants(cfg):
            ok, _ = _evaluate(inv)
            assert ok, f"{inv.name} failed"


class TestGradientConsistency:
    def test_default_passes(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,))
        invs = gradient_consistency_invariants(cfg)
        assert len(invs) == 1
        ok, _ = _evaluate(invs[0])
        assert ok

    def test_seed_makes_deterministic(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1,))
        a = gradient_consistency_invariants(cfg, seed=42)[0].actual
        b = gradient_consistency_invariants(cfg, seed=42)[0].actual
        assert a == b


class TestTrajectoryInvariants:
    def test_only_stable_emitted(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1, 2.5))
        invs = trajectory_invariants(cfg)
        assert all("alpha=2.5" not in i.name for i in invs)
        assert any("alpha=0.1" in i.name for i in invs)

    def test_monotone_on_stable(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.05, 0.2, 0.8))
        for inv in trajectory_invariants(cfg, max_iter=50):
            ok, w = _evaluate(inv)
            assert ok, f"{inv.name}: {w}"


class TestAllInvariants:
    def test_total_count(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.1, 0.5, 1.0))
        invs = all_invariants(cfg)
        # 1 gradient + (3*3 + 1) convergence + 3 trajectory = 14
        assert len(invs) == 14

    def test_all_pass_for_well_conditioned(self):
        cfg = OptimizerSweepConfig(step_sizes=(0.01, 0.1, 0.5, 1.0, 1.5, 2.5))
        for inv in all_invariants(cfg):
            ok, w = _evaluate(inv)
            assert ok, f"{inv.name}: {w}"


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------


class TestBuildDashboardCLI:
    def test_default_run(self, tmp_path):
        html = tmp_path / "d.html"
        js = tmp_path / "d.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "build_dashboard.py"),
                "--alpha-sweep-num", "10",
                "--html-out", str(html),
                "--json-out", str(js),
                "--invariants-out", str(inv),
                "--summary-out", str(sm),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, f"stderr:\n{result.stderr}"
        assert html.exists() and html.stat().st_size > 1000
        bundle = json.loads(js.read_text())
        # All invariants pass
        n_pass = sum(1 for i in bundle["invariants"] if i["passed"])
        assert n_pass == len(bundle["invariants"]) > 5
        # Plotly CDN embedded
        assert "cdn.plot.ly" in html.read_text()

    def test_custom_step_sizes(self, tmp_path):
        html = tmp_path / "d.html"
        js = tmp_path / "d.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "build_dashboard.py"),
                "--step-sizes", "0.05", "0.2", "0.8",
                "--alpha-sweep-num", "8",
                "--html-out", str(html),
                "--json-out", str(js),
                "--invariants-out", str(inv),
                "--summary-out", str(sm),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, f"stderr:\n{result.stderr}"
        bundle = json.loads(js.read_text())
        assert bundle["hyperparameters"]["step_sizes"] == [0.05, 0.2, 0.8]

    def test_custom_quadratic(self, tmp_path):
        html = tmp_path / "d.html"
        js = tmp_path / "d.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "build_dashboard.py"),
                "--A", "4.0",
                "--b", "8.0",
                "--x0", "0.0",
                "--step-sizes", "0.1", "0.4",
                "--alpha-sweep-min", "0.01",
                "--alpha-sweep-max", "0.49",
                "--alpha-sweep-num", "8",
                "--html-out", str(html),
                "--json-out", str(js),
                "--invariants-out", str(inv),
                "--summary-out", str(sm),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, f"stderr:\n{result.stderr}"
        bundle = json.loads(js.read_text())
        # x* = A^{-1} b = 8/4 = 2
        assert bundle["hyperparameters"]["x_star"][0] == pytest.approx(2.0)
        # bound = 2/4 = 0.5
        assert bundle["hyperparameters"]["stable_step_bound"] == pytest.approx(0.5)

    def test_rejects_mismatched_dims(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "build_dashboard.py"),
                "--A", "1.0", "2.0",
                "--b", "1.0",  # length mismatch
                "--html-out", str(tmp_path / "x.html"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Helpers — evaluate an InvariantResult against the dashboard's evaluator.
# ---------------------------------------------------------------------------


def _evaluate(r: InvariantResult) -> tuple[bool, str]:
    """Mirror the comparator semantics from
    :class:`infrastructure.reporting.interactive_dashboard.Invariant`.
    """
    import math
    try:
        if r.kind == "equal":
            a = float(r.actual)
            e = float(r.expected)
            return abs(a - e) <= r.tol, f"|{a:.6g} - {e:.6g}|"
        if r.kind == "le":
            a, e = float(r.actual), float(r.expected)
            return a <= e + r.tol, f"{a} <= {e}"
        if r.kind == "ge":
            a, e = float(r.actual), float(r.expected)
            return a >= e - r.tol, f"{a} >= {e}"
        if r.kind == "in_range":
            a = float(r.actual)
            lo, hi = r.expected
            return (lo - r.tol) <= a <= (hi + r.tol), f"{lo} <= {a} <= {hi}"
        if r.kind in ("monotone_increasing", "monotone_decreasing"):
            seq = list(r.actual)
            inc = r.kind == "monotone_increasing"
            worst = 0.0
            for x, y in zip(seq, seq[1:]):
                d = (y - x) if inc else (x - y)
                if d < -r.tol:
                    worst = min(worst, d)
            return worst >= -r.tol, f"worst={worst}"
        if r.kind == "finite":
            if hasattr(r.actual, "__iter__"):
                vals = [float(v) for v in r.actual]
                return all(math.isfinite(v) for v in vals), f"{len(vals)} values"
            return math.isfinite(float(r.actual)), str(r.actual)
        if r.kind == "nonneg":
            if hasattr(r.actual, "__iter__"):
                vals = [float(v) for v in r.actual]
                return min(vals) >= -r.tol, f"min={min(vals) if vals else 0}"
            return float(r.actual) >= -r.tol, str(r.actual)
    except Exception as exc:  # pragma: no cover
        return False, f"evaluation error: {exc!r}"
    return False, f"unknown kind {r.kind!r}"


def _witness(r: InvariantResult) -> str:
    return _evaluate(r)[1]
