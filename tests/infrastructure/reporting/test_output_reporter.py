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
    pdf_dir = repo_root / "project" / "output" / "pdf"
    figures_dir = repo_root / "project" / "output" / "figures"
    data_dir = repo_root / "project" / "output" / "data"

    _create_file(pdf_dir / "paper.pdf")
    _create_file(figures_dir / "figure1.png")
    _create_file(figures_dir / "figure2.pdf")
    _create_file(data_dir / "data.csv")

    stats = collect_output_statistics(repo_root)

    assert stats["pdf_files"] == 1
    assert stats["figures"] == 2
    assert stats["data_files"] == 1
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

