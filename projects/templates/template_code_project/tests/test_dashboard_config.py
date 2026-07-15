"""Tests for dashboard config loading and argument validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dashboard import (
    _compute_payload,
    _load_yaml_defaults,
    CFG_DEFAULT,
    cli_main as dashboard_main,
    parse_dashboard_args as _parse_args,
)
from src.experiment_config import ExperimentConfig, load_experiment_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDashboardConfig:
    def test_yaml_defaults_match_experiment_config(self):
        cfg = _load_yaml_defaults(CFG_DEFAULT)
        expected = load_experiment_config(PROJECT_ROOT)
        assert cfg.step_sizes == expected.step_sizes
        assert cfg.tolerance == expected.tolerance
        assert cfg.max_iterations == expected.max_iterations


class TestDashboardParseArgs:
    def test_rejects_empty_step_sizes(self):
        with pytest.raises(SystemExit):
            _parse_args(["--step-sizes"])

    def test_rejects_mismatched_x0_length(self):
        with pytest.raises(SystemExit):
            _parse_args(["--A", "1.0", "2.0", "--b", "1.0", "2.0", "--x0", "0.0"])

    def test_rejects_invalid_alpha_sweep_range(self):
        with pytest.raises(SystemExit):
            _parse_args(["--alpha-sweep-min", "2.0", "--alpha-sweep-max", "1.0"])

    def test_rejects_empty_default_step_sizes(self):
        with pytest.raises(SystemExit):
            _parse_args([], defaults_loader=lambda _path: ExperimentConfig(step_sizes=()))

    def test_rejects_non_positive_step_size_direct(self):
        with pytest.raises(SystemExit):
            _parse_args(["--step-sizes", "-0.1"])

    def test_rejects_alpha_sweep_num_lt_2(self):
        with pytest.raises(SystemExit):
            _parse_args(["--alpha-sweep-num", "1"])


class TestDashboardPayload:
    def test_compute_payload_records_divergent_alpha_sweep(self):
        args = _parse_args(
            [
                "--step-sizes",
                "0.1",
                "--A",
                "1.0",
                "--b",
                "1.0",
                "--x0",
                "0.0",
                "--alpha-sweep-min",
                "0.01",
                "--alpha-sweep-max",
                "4.0",
                "--alpha-sweep-num",
                "5",
                "--max-iter",
                "50",
            ]
        )
        payload = _compute_payload(args)
        assert any(payload["alpha_sweep"]["diverged"])
        assert any(d > 1e3 for d in payload["alpha_sweep"]["final_dist"])

    def test_compute_payload_records_sweep_exception(self):
        from src.invariants import OptimizerSweepConfig
        from src.sweeps import run_alpha_sweep

        calls = {"n": 0}
        original = OptimizerSweepConfig.run_for

        def _run_for_maybe_fail(self: OptimizerSweepConfig, alpha: float):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OverflowError("diverged")
            return original(self, alpha)

        class _FailingFirstSweep(OptimizerSweepConfig):
            run_for = _run_for_maybe_fail

        def _run_sweep(config):
            return run_alpha_sweep(config, optimizer_factory=_FailingFirstSweep)

        args = _parse_args(
            [
                "--step-sizes",
                "0.1",
                "--A",
                "1.0",
                "--b",
                "1.0",
                "--x0",
                "0.0",
                "--alpha-sweep-min",
                "0.01",
                "--alpha-sweep-max",
                "0.5",
                "--alpha-sweep-num",
                "4",
                "--max-iter",
                "50",
            ]
        )
        payload = _compute_payload(args, sweep_runner=_run_sweep)
        sweep = payload["alpha_sweep"]
        assert float("inf") in sweep["final_dist"]
        assert True in sweep["diverged"]

    def test_main_prints_output_paths(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        html = tmp_path / "dash.html"
        js = tmp_path / "dash.json"
        inv = tmp_path / "inv.txt"
        sm = tmp_path / "sum.txt"
        dashboard_main(
            [
                "--alpha-sweep-num",
                "8",
                "--html-out",
                str(html),
                "--json-out",
                str(js),
                "--invariants-out",
                str(inv),
                "--summary-out",
                str(sm),
            ]
        )
        captured = capsys.readouterr()
        assert str(html) in captured.out
        bundle = json.loads(js.read_text())
        assert "payload" in bundle

    def test_main_exits_on_failed_invariants(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        class _FailedDashboard:
            def write(self, **kwargs: object) -> dict[str, str]:
                return {
                    "html": str(kwargs.get("html_path", "")),
                    "json": str(kwargs.get("json_path", "")),
                    "invariants": str(kwargs.get("invariants_path", "")),
                    "summary": str(kwargs.get("txt_path", "")),
                }

            def evaluate_invariants(self) -> list[dict[str, object]]:
                return [{"name": "bad_invariant", "passed": False}]

        html = tmp_path / "dash.html"
        js = tmp_path / "dash.json"
        with pytest.raises(SystemExit) as exc:
            dashboard_main(
                [
                    "--html-out",
                    str(html),
                    "--json-out",
                    str(js),
                    "--invariants-out",
                    str(tmp_path / "inv.txt"),
                    "--summary-out",
                    str(tmp_path / "sum.txt"),
                ],
                dashboard_builder=lambda _args, _payload: _FailedDashboard(),
            )
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "FAILED INVARIANTS" in captured.err
        assert "bad_invariant" in captured.err
