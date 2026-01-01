from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.reporting.output_reporter import (
    collect_output_statistics,
    generate_output_summary,
)


def _create_file(path: Path, size: int = 10) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"a" * size)


def test_collect_output_statistics_counts_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    pdf_dir = repo_root / "projects" / "project" / "output" / "pdf"
    figures_dir = repo_root / "projects" / "project" / "output" / "figures"
    data_dir = repo_root / "projects" / "project" / "output" / "data"

    _create_file(pdf_dir / "paper.pdf")
    _create_file(figures_dir / "figure1.png")
    _create_file(figures_dir / "figure2.pdf")
    _create_file(data_dir / "data.csv")

    stats = collect_output_statistics(repo_root, "project")

    # Check directory-level file counts
    assert stats["directories"]["pdf"]["file_count"] == 1
    assert stats["directories"]["figures"]["file_count"] == 2
    assert stats["directories"]["data"]["file_count"] == 1
    assert stats["total_size_mb"] > 0


def test_generate_output_summary_runs_without_errors() -> None:
    stats = {
        "pdf_files": 1,
        "web_files": 2,
        "slides_files": 0,
        "figures_files": 3,
        "data_files": 1,
        "reports_files": 1,
        "simulations_files": 0,
        "llm_files": 0,
        "logs_files": 1,
        "combined_pdf": 1,
        "total_files": 9,
        "errors": ["missing optional slide deck"],
    }
    structure_validation = {
        "directory_structure": {
            "pdf": {"exists": True, "files": 1, "size_mb": 0.01},
            "figures": {"exists": True, "files": 3},
        }
    }

    generate_output_summary(output_dir=Path("output"), stats=stats, structure_validation=structure_validation)
    # No assertions needed; success is lack of exceptions


def test_generate_output_summary_no_validation(tmp_path: Path) -> None:
    """Test generate_output_summary without structure validation."""
    stats = {
        "pdf_files": 1,
        "web_files": 0,
        "slides_files": 0,
        "figures_files": 0,
        "data_files": 0,
        "reports_files": 0,
        "simulations_files": 0,
        "llm_files": 0,
        "logs_files": 0,
        "combined_pdf": 0,
        "total_files": 1,
        "errors": [],
    }
    generate_output_summary(output_dir=tmp_path, stats=stats, structure_validation=None)
    # Should complete without errors


def test_generate_output_summary_with_errors(tmp_path: Path) -> None:
    """Test generate_output_summary with error messages."""
    stats = {
        "pdf_files": 0,
        "web_files": 0,
        "slides_files": 0,
        "figures_files": 0,
        "data_files": 0,
        "reports_files": 0,
        "simulations_files": 0,
        "llm_files": 0,
        "logs_files": 0,
        "combined_pdf": 0,
        "total_files": 0,
        "errors": ["Error 1", "Error 2", "Error 3"],
    }
    generate_output_summary(output_dir=tmp_path, stats=stats, structure_validation=None)
    # Should complete without errors


def test_collect_output_statistics_no_output_dir(tmp_path: Path) -> None:
    """Test collect_output_statistics when output directory doesn't exist."""
    stats = collect_output_statistics(tmp_path, "project")
    assert stats["directories"]["pdf"]["file_count"] == 0
    assert stats["directories"]["figures"]["file_count"] == 0
    assert stats["directories"]["data"]["file_count"] == 0
    assert stats["total_size_mb"] == 0.0


def test_collect_output_statistics_empty_directories(tmp_path: Path) -> None:
    """Test collect_output_statistics with empty directories."""
    repo_root = tmp_path
    (repo_root / "project" / "output" / "pdf").mkdir(parents=True, exist_ok=True)
    (repo_root / "project" / "output" / "figures").mkdir(parents=True, exist_ok=True)
    (repo_root / "project" / "output" / "data").mkdir(parents=True, exist_ok=True)
    
    stats = collect_output_statistics(repo_root, "project")
    assert stats["directories"]["pdf"]["file_count"] == 0
    assert stats["directories"]["figures"]["file_count"] == 0
    assert stats["directories"]["data"]["file_count"] == 0
    assert stats["total_size_mb"] == 0.0


def test_collect_output_statistics_size_calculation(tmp_path: Path) -> None:
    """Test collect_output_statistics calculates file sizes correctly."""
    repo_root = tmp_path
    pdf_dir = repo_root / "projects" / "project" / "output" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Create file with known size (1MB = 1024*1024 bytes)
    large_file = pdf_dir / "large.pdf"
    large_file.write_bytes(b"x" * (1024 * 1024))

    stats = collect_output_statistics(repo_root, "project")
    assert stats["directories"]["pdf"]["file_count"] == 1
    assert stats["total_size_mb"] >= 1.0

