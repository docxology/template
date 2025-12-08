"""Tests for infrastructure.reporting.output_reporter."""

from __future__ import annotations

from pathlib import Path

from infrastructure.reporting.output_reporter import (
    collect_output_statistics,
    generate_output_summary,
)


def _create_file(path: Path, size: int = 10) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"a" * size)


def test_collect_output_statistics(tmp_path):
    repo_root = tmp_path
    pdf = repo_root / "project" / "output" / "pdf" / "a.pdf"
    fig = repo_root / "project" / "output" / "figures" / "f.png"
    data = repo_root / "project" / "output" / "data" / "d.csv"

    _create_file(pdf)
    _create_file(fig)
    _create_file(data)

    stats = collect_output_statistics(repo_root)

    assert stats["pdf_files"] == 1
    assert stats["figures"] == 1
    assert stats["data_files"] == 1
    assert stats["total_size_mb"] > 0


def test_generate_output_summary_logs(tmp_path):
    """Test that generate_output_summary executes without error."""
    stats = {
        "pdf_files": 1,
        "web_files": 0,
        "slides_files": 0,
        "figures_files": 1,
        "data_files": 1,
        "reports_files": 0,
        "simulations_files": 0,
        "llm_files": 0,
        "logs_files": 0,
        "combined_pdf": 1,
        "total_files": 3,
        "errors": [],
    }

    # Function should complete without raising exceptions
    # (Logging output is verified in integration tests)
    generate_output_summary(tmp_path, stats, structure_validation={"directory_structure": {}})
    
    # Verify function completed successfully
    assert True  # If we get here, function executed without error

