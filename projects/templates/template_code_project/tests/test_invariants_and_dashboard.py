"""Tests for the build_dashboard CLI and dashboard-specific payload behavior."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent


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

    def test_payload_step_sizes_match_config_yaml(self, tmp_path):
        from src.experiment_config import load_experiment_config

        cfg = load_experiment_config(PROJECT_ROOT)
        js = tmp_path / "d.json"
        html = tmp_path / "d.html"
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
        payload = json.loads(js.read_text())["payload"]
        assert payload["step_sizes"] == [float(s) for s in cfg.step_sizes]
        assert len(payload["step_sizes"]) == 6

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

    def test_rejects_non_positive_step_size(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "build_dashboard.py"),
                "--step-sizes", "0.0",
                "--html-out", str(tmp_path / "x.html"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_dashboard_main_writes_outputs(self, tmp_path):
        html = tmp_path / "dash.html"
        js = tmp_path / "dash.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        from scripts.build_dashboard import main as dashboard_main

        dashboard_main(
            [
                "--alpha-sweep-num", "8",
                "--html-out", str(html),
                "--json-out", str(js),
                "--invariants-out", str(inv),
                "--summary-out", str(sm),
            ]
        )
        assert html.exists()
        assert js.exists()

    def test_alpha_sweep_handles_divergent_regime(self, tmp_path):
        html = tmp_path / "dash.html"
        js = tmp_path / "dash.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        from scripts.build_dashboard import main as dashboard_main

        dashboard_main(
            [
                "--step-sizes", "0.1",
                "--alpha-sweep-min", "0.01",
                "--alpha-sweep-max", "3.0",
                "--alpha-sweep-num", "6",
                "--html-out", str(html),
                "--json-out", str(js),
                "--invariants-out", str(inv),
                "--summary-out", str(sm),
            ]
        )
        payload = json.loads(js.read_text())["payload"]
        assert any(payload["alpha_sweep"]["diverged"])
