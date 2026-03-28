"""Manuscript metrics computation for the template project.

This module contains pure and testable logic for building manuscript metrics
from the live repository. The Stage 02 script remains a thin orchestrator that
imports and invokes these functions.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

from .introspection import ModuleInfo, build_infrastructure_report

logger = get_logger(__name__)

_EXCLUDED_DOC_DIRS = frozenset({"__pycache__", ".venv", ".git", ".pytest_cache"})


def count_test_functions(test_dir: Path) -> int:
    """Count ``def test_`` function definitions in ``test_*.py`` files."""
    if not test_dir.is_dir():
        return 0
    count = 0
    for file_path in test_dir.rglob("test_*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
            count += len(re.findall(r"^\s*def test_", content, re.MULTILINE))
        except OSError as e:
            logger.debug(f"Skipping unreadable test file {file_path}: {e}")
            continue
    return count


def count_docs_markdown_files(repo_root: Path) -> int:
    """Count ``.md`` files under ``docs/`` while excluding cache/vendor paths."""
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        return 0

    count = 0
    for path in docs_dir.rglob("*.md"):
        if not any(part in _EXCLUDED_DOC_DIRS for part in path.parts):
            count += 1
    return count


def count_docs_subdirs(repo_root: Path) -> int:
    """Count first-level subdirectories under ``docs/``."""
    docs_dir = repo_root / "docs"
    if not docs_dir.is_dir():
        return 0
    return sum(1 for path in docs_dir.iterdir() if path.is_dir())


def format_count(n: int, approx: bool = False) -> str:
    """Format a count and optionally prefix with ``~`` for approximate display."""
    if n >= 1000:
        rounded = round(n / 100) * 100
        return f"~{rounded:,}" if approx else f"{n:,}"
    return f"~{n}" if approx else str(n)


def build_module_inventory_table(modules: list[ModuleInfo]) -> str:
    """Generate the module inventory Markdown table from ``ModuleInfo`` values."""
    key_exports_map = {
        "core": "`get_logger`, `load_config`, `TemplateError`",
        "documentation": "`FigureManager`, `generate_glossary`",
        "llm": "LLM review, literature search, translation",
        "project": "`discover_projects`, workspace management",
        "publishing": "Citation generation (APA, BibTeX, MLA), Zenodo",
        "rendering": "PDF rendering, Pandoc filters, HTML reports",
        "reporting": "Coverage parsing, executive reports",
        "scientific": "`check_numerical_stability`, `benchmark_function`",
        "steganography": "Metadata injection, QR overlays, hashing",
        "validation": "PDF validation, Markdown checking, CLI",
        "config": "Configuration schemas",
        "docker": "Containerisation",
    }
    rows = [
        "| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |",
        "|--------|:-----------:|:-------------:|:-------------:|-------------|",
    ]
    for module in modules:
        agents = "✓" if module.has_agents_md else "—"
        readme = "✓" if module.has_readme_md else "—"
        exports = key_exports_map.get(module.name, "—")
        rows.append(
            f"| `{module.name}` | {module.python_file_count} | {agents} | {readme} | {exports} |"
        )
    return "\n".join(rows)


def build_manuscript_metrics_dict(repo_root: Path) -> dict[str, Any]:
    """Compute the full metrics dictionary from live repository data.

    All values in the returned dictionary are injectable into manuscript
    chapters as ``${key}`` tokens.  Per-project metrics are exposed as
    ``project_{name}_{field}`` keys (e.g. ``project_code_project_test_count``).
    """
    logger.info("Building infrastructure report from repository data...")
    report = build_infrastructure_report(repo_root)

    # ── Per-project metrics (from report + test function counting) ──────
    projects_dir = repo_root / "projects"
    projects_in_progress_dir = repo_root / "projects_in_progress"
    project_metrics: dict[str, dict[str, int | str]] = {}

    # Also count test *functions* (not just files) for finer granularity
    all_project_dirs = sorted(
        list(projects_dir.iterdir()) + list(projects_in_progress_dir.iterdir())
        if projects_in_progress_dir.is_dir()
        else list(projects_dir.iterdir())
    )

    for project_dir in all_project_dirs:
        if not project_dir.is_dir():
            continue
        config_file = project_dir / "manuscript" / "config.yaml"
        if not config_file.is_file():
            continue
        test_count = count_test_functions(project_dir / "tests")
        test_file_count = (
            len(list((project_dir / "tests").rglob("test_*.py")))
            if (project_dir / "tests").is_dir()
            else 0
        )
        project_metrics[project_dir.name] = {
            "test_count": test_count,
            "test_file_count": test_file_count,
        }

    # Merge structural counts from InfrastructureReport.projects
    for proj in report.projects:
        if proj.name in project_metrics:
            project_metrics[proj.name]["chapter_count"] = proj.chapter_count
            project_metrics[proj.name]["script_count"] = proj.script_count
            project_metrics[proj.name]["src_module_count"] = proj.src_module_count
            project_metrics[proj.name]["figure_count"] = proj.figure_count

    infra_test_count = count_test_functions(repo_root / "tests")
    infra_test_file_count = len(list((repo_root / "tests").rglob("test_*.py")))
    total_infra_py = sum(module.python_file_count for module in report.modules)
    docs_file_count = count_docs_markdown_files(repo_root)
    docs_subdir_count = count_docs_subdirs(repo_root)

    all_projects_test_count = sum(
        values["test_count"]
        for name, values in project_metrics.items()
        if (repo_root / "projects" / name).is_dir()
    )

    metrics: dict[str, Any] = {
        # ── Top-level infrastructure metrics ──────────────────────────
        "module_count": report.module_count,
        "stage_count": report.stage_count,
        "project_count": report.project_count,
        "total_infra_python_files": total_infra_py,
        "infra_test_file_count": infra_test_file_count,
        "infra_test_count": infra_test_count,
        "infra_test_count_approx": format_count(infra_test_count),
        "all_projects_test_count": all_projects_test_count,
        "docs_file_count": docs_file_count,
        "docs_subdir_count": docs_subdir_count,
        "infrastructure_version": report.infrastructure_version,
        # ── Per-project metrics (flat) ────────────────────────────────
        **{
            f"project_{name}_{k}": str(v)
            for name, stats in project_metrics.items()
            for k, v in stats.items()
        },
        # ── Per-module metrics ────────────────────────────────────────
        **{
            f"module_{module.name}_python_file_count": module.python_file_count
            for module in report.modules
        },
        **{
            f"module_{module.name}_has_agents_md": str(module.has_agents_md).lower()
            for module in report.modules
        },
        **{
            f"module_{module.name}_has_readme_md": str(module.has_readme_md).lower()
            for module in report.modules
        },
        "module_inventory_table": build_module_inventory_table(report.modules),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    logger.info(
        "Metrics computed: %s modules, %s infra tests, %s infra Python files, "
        "%s per-project keys",
        report.module_count,
        infra_test_count,
        total_infra_py,
        sum(len(v) for v in project_metrics.values()),
    )
    return metrics


def save_metrics_json(metrics: dict[str, Any], output_path: Path) -> Path:
    """Save metrics JSON to disk and return the written path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, ensure_ascii=False)
    return output_path
