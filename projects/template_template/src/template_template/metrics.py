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

from infrastructure.project.public_scope import public_project_names

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


def _module_metric_slug(name: str) -> str:
    """Return a ``string.Template``-safe slug (``logrotate.d`` → ``logrotate_d``)."""
    return name.replace(".", "_").replace("-", "_")


def build_module_inventory_table(modules: list[ModuleInfo]) -> str:
    """Generate the module inventory Markdown table from ``ModuleInfo`` values."""
    key_exports_map = {
        "autoresearch": "`build_autoresearch_plan`, readiness validation CLI",
        "benchmark": "Template harness scoring + comparative gates",
        "core": "`get_logger`, `load_config`, `TemplateError`",
        "doctor": "Checkout diagnose/fix/undo repairs",
        "documentation": "`FigureManager`, `generate_glossary`",
        "llm": "Ollama helpers, sanitization, review + translation pipelines",
        "methods": "`build_methods_orchestration_plan`, methods-stage contracts + validation",
        "orchestration": "`PipelineRunner`, entry point for `./run.sh`",
        "prose": "Markdown readability + prose tooling",
        "reference": "BibTeX models, parsers, converters",
        "search": "`infrastructure.search.literature` clients + cache",
        "project": "`discover_projects`, workspace management",
        "publishing": "Zenodo, executable bundle, archival targets",
        "rendering": "PDF/HTML/slide rendering, Pandoc filters",
        "reporting": "Coverage parsers, dashboards, executive artefacts",
        "scientific": "`check_numerical_stability`, `benchmark_function`",
        "skills": "`discover_skills`, SKILL manifest regeneration",
        "steganography": "Watermark overlays + hash manifests",
        "validation": "PDF + Markdown + integrity CLIs",
        "config": "Repository defaults + hardened templates",
        "docker": "Containerisation scaffolding",
        "logrotate.d": "Rotation snippets (documentation-first)",
    }
    rows = [
        "| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |",
        "|--------|:-----------:|:-------------:|:-------------:|-------------|",
    ]
    for module in modules:
        agents = "✓" if module.has_agents_md else "—"
        readme = "✓" if module.has_readme_md else "—"
        exports = key_exports_map.get(module.name, "—")
        rows.append(f"| `{module.name}` | {module.python_file_count} | {agents} | {readme} | {exports} |")
    return "\n".join(rows)


def build_manuscript_metrics_dict(repo_root: Path) -> dict[str, Any]:
    """Compute the full metrics dictionary from live repository data.

    All values in the returned dictionary are injectable into manuscript
    chapters as ``${key}`` tokens.  Per-project metrics are exposed as
    ``project_{name}_{field}`` keys (e.g. ``project_template_code_project_test_count``).
    """
    logger.info("Building infrastructure report from repository data...")
    report = build_infrastructure_report(repo_root)

    project_metrics: dict[str, dict[str, int | str]] = {}
    for proj in report.projects:
        test_count = count_test_functions(proj.path / "tests")
        project_metrics[proj.name] = {
            "test_count": test_count,
            "test_file_count": proj.test_file_count,
            "chapter_count": proj.chapter_count,
            "script_count": proj.script_count,
            "src_module_count": proj.src_module_count,
            "figure_count": proj.figure_count,
        }

    # CONFIDENTIALITY: there is intentionally NO ``projects_archive/`` scan here.
    # ``projects_archive/`` symlinks private/rotating projects (retired research
    # workspaces, client work) whose names must never reach this public meta-template's
    # metrics, figures, or rendered manuscript. The only project metrics that may exist
    # are those produced by ``build_infrastructure_report`` → ``discover_projects``,
    # which is public-only (``PUBLIC_PROJECT_NAMES``) and additionally admits this
    # meta-project under its ``template_template`` name for self-introspection.
    # Re-introducing an archive / passive / projects_in_progress walk here would leak
    # private names into a public DOI; ``tests/test_confidentiality.py`` is the
    # negative control that keeps this closed.

    infra_test_count = count_test_functions(repo_root / "tests")
    infra_test_file_count = len(list((repo_root / "tests").rglob("test_*.py")))
    total_infra_py = sum(module.python_file_count for module in report.modules)
    docs_file_count = count_docs_markdown_files(repo_root)
    docs_subdir_count = count_docs_subdirs(repo_root)

    all_projects_test_count = sum(
        int(values["test_count"])
        for name, values in project_metrics.items()
        if (repo_root / "projects" / name).is_dir()
    )
    public_names = public_project_names(repo_root)
    public_exemplar_list = ", ".join(f"`{name}`" for name in public_names)

    metrics: dict[str, Any] = {
        # ── Top-level infrastructure metrics ──────────────────────────
        "module_count": len(report.modules),
        "stage_count": len(report.numbered_scripts),
        "pipeline_stages_declared": report.pipeline_stages_declared,
        "pipeline_stages_default_full": report.pipeline_stages_default_full,
        "pipeline_stages_core_only": report.pipeline_stages_core_only,
        "public_exemplar_list": public_exemplar_list,
        "project_count": len(report.projects),
        "total_infra_python_files": total_infra_py,
        "infra_test_file_count": infra_test_file_count,
        "infra_test_count": infra_test_count,
        "infra_test_count_approx": format_count(infra_test_count),
        "all_projects_test_count": all_projects_test_count,
        "total_test_count": infra_test_count + all_projects_test_count,
        "total_test_count_approx": format_count(infra_test_count + all_projects_test_count),
        "docs_file_count": docs_file_count,
        "docs_subdir_count": docs_subdir_count,
        "infrastructure_version": report.infrastructure_version,
        # ── Per-project metrics (flat) ────────────────────────────────
        **{f"project_{name}_{k}": str(v) for name, stats in project_metrics.items() for k, v in stats.items()},
        # ── Per-module metrics ────────────────────────────────────────
        **{
            f"module_{_module_metric_slug(module.name)}_python_file_count": module.python_file_count
            for module in report.modules
        },
        **{
            f"module_{_module_metric_slug(module.name)}_has_agents_md": str(module.has_agents_md).lower()
            for module in report.modules
        },
        **{
            f"module_{_module_metric_slug(module.name)}_has_readme_md": str(module.has_readme_md).lower()
            for module in report.modules
        },
        "module_inventory_table": build_module_inventory_table(report.modules),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    logger.info(
        "Metrics computed: %s modules, %s infra tests, %s infra Python files, %s per-project keys",
        len(report.modules),
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
