#!/usr/bin/env python3
"""Tests for infrastructure.validation.line_count."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from infrastructure.validation.line_count import (
    LineCountThresholds,
    LineCountRatchet,
    count_lines,
    scan_line_counts,
    scan_project_scripts,
    scan_project_src,
)
from scripts.gates.module_line_count_check import main as line_count_gate_main


def test_count_lines(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text("a\nb\nc\n", encoding="utf-8")
    assert count_lines(sample) == 3


def test_scan_line_counts_warn_and_fail(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    (infra / "ok.py").write_text("\n".join(["# x"] * 10), encoding="utf-8")
    (infra / "warn.py").write_text("\n".join(["# x"] * 810), encoding="utf-8")
    (infra / "fail.py").write_text("\n".join(["# x"] * 960), encoding="utf-8")

    warnings, failures = scan_line_counts(
        tmp_path,
        ("infrastructure",),
        thresholds=LineCountThresholds(warn_at=800, fail_at=950),
    )
    assert any("warn.py" in rel for rel, _ in warnings)
    assert any("fail.py" in rel for rel, _ in failures)


def test_line_count_ratchet_fails_growth_beyond_ceiling(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    path = infra / "grandfathered.py"
    path.write_text("\n".join(["# x"] * 101), encoding="utf-8")
    ratchets = {
        "infrastructure/grandfathered.py": LineCountRatchet(
            max_lines=100,
            expires_on=date(2999, 1, 1),
        )
    }

    _warnings, failures = scan_line_counts(
        tmp_path,
        ("infrastructure",),
        thresholds=LineCountThresholds(warn_at=80, fail_at=95),
        allowlist=ratchets,
    )
    assert failures == [("infrastructure/grandfathered.py", 101)]


def test_expired_line_count_ratchet_fails_closed(tmp_path: Path) -> None:
    infra = tmp_path / "infrastructure"
    infra.mkdir()
    path = infra / "expired.py"
    path.write_text("# x\n", encoding="utf-8")
    ratchets = {
        "infrastructure/expired.py": LineCountRatchet(
            max_lines=100,
            expires_on=date(2000, 1, 1),
        )
    }

    _warnings, failures = scan_line_counts(
        tmp_path,
        ("infrastructure",),
        thresholds=LineCountThresholds(warn_at=80, fail_at=95),
        allowlist=ratchets,
    )
    assert failures == [("infrastructure/expired.py", 1)]


def test_scan_project_scripts_any_project(tmp_path: Path) -> None:
    scripts = tmp_path / "projects" / "templates" / "template_code_project" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "big.py").write_text("\n".join(["# line"] * 260), encoding="utf-8")
    _warnings, failures = scan_project_scripts(tmp_path)
    assert any("projects/templates/template_code_project/scripts/big.py" in rel for rel, _ in failures)


def test_scan_project_src_any_project(tmp_path: Path) -> None:
    src = tmp_path / "projects" / "templates" / "template_code_project" / "src"
    src.mkdir(parents=True)
    (src / "big.py").write_text("\n".join(["# line"] * 960), encoding="utf-8")
    _warnings, failures = scan_project_src(tmp_path)
    assert any("projects/templates/template_code_project/src/big.py" in rel for rel, _ in failures)


def test_gate_fails_when_required_scan_roots_are_missing(tmp_path: Path) -> None:
    assert line_count_gate_main(["--repo-root", str(tmp_path)]) == 1


def test_gate_fails_on_syntax_invalid_counted_module(tmp_path: Path) -> None:
    (tmp_path / "infrastructure").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "infrastructure" / "broken.py").write_text("def broken(:\n", encoding="utf-8")

    assert line_count_gate_main(["--repo-root", str(tmp_path)]) == 1
