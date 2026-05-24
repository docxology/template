#!/usr/bin/env python3
"""Tests for infrastructure.validation.line_count."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.line_count import (
    LineCountThresholds,
    count_lines,
    scan_line_counts,
    scan_project_scripts,
)


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


def test_scan_project_scripts_any_project(tmp_path: Path) -> None:
    scripts = tmp_path / "projects" / "template_code_project" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "big.py").write_text("\n".join(["# line"] * 260), encoding="utf-8")
    _warnings, failures = scan_project_scripts(tmp_path)
    assert any("projects/template_code_project/scripts/big.py" in rel for rel, _ in failures)
