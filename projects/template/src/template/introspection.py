"""Repository introspection utilities for the Docxology Template.

Programmatic analysis of the template repository structure: infrastructure
modules, project workspaces, pipeline stages, and test configurations.
All functions operate on filesystem paths and return plain data structures.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Directories excluded from repo-wide file counts (avoids .venv, caches, etc.)
_EXCLUDED_DIRS = frozenset(
    {"__pycache__", ".venv", ".git", ".cursor", ".pytest_cache", ".mypy_cache", "node_modules", "dist", "build"}
)


def _is_excluded_path(p: Path) -> bool:
    """Return True if path contains any excluded directory segment."""
    return any(part in _EXCLUDED_DIRS for part in p.parts)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ModuleInfo:
    """Metadata for a single infrastructure subpackage."""

    name: str
    path: Path
    python_file_count: int
    has_init: bool
    has_agents_md: bool
    has_readme_md: bool
    has_skill_md: bool = False
    has_pai_md: bool = False
    public_symbols: list[str] = field(default_factory=list)


@dataclass
class ProjectAnalysis:
    """Rich analysis metrics for a single project workspace.

    Distinct from ``infrastructure.project.project_info.ProjectInfo`` which
    records discovery/existence flags. ``ProjectAnalysis`` records counts
    (chapters, figures, tests, scripts) produced by repository introspection.
    """

    name: str
    path: Path
    has_manuscript: bool
    chapter_count: int
    has_tests: bool
    test_file_count: int
    has_scripts: bool
    script_count: int
    src_module_count: int = 0
    figure_count: int = 0
    config: dict[str, Any] = field(default_factory=dict)


# Backwards-compat alias — external code that imported ProjectInfo continues to work.
ProjectInfo = ProjectAnalysis


@dataclass
class PipelineStage:
    """A single pipeline stage descriptor."""

    number: int
    name: str
    script_name: str
    script_path: Path


@dataclass
class CoverageConfig:
    """Test coverage and failure tolerance settings for a project."""

    project_name: str
    max_test_failures: int
    max_infra_test_failures: int
    max_project_test_failures: int


@dataclass
class InfrastructureReport:
    """Aggregated report of the entire repository structure."""

    repo_root: Path
    infrastructure_version: str
    modules: list[ModuleInfo]
    projects: list[ProjectAnalysis]
    pipeline_stages: list[PipelineStage]
    total_python_files: int
    total_test_files: int

    @property
    def module_count(self) -> int:
        return len(self.modules)

    @property
    def project_count(self) -> int:
        return len(self.projects)

    @property
    def stage_count(self) -> int:
        return len(self.pipeline_stages)


# ---------------------------------------------------------------------------
# Discovery functions
# ---------------------------------------------------------------------------

def discover_infrastructure_modules(repo_root: Path) -> list[ModuleInfo]:
    """Scan ``infrastructure/`` for subpackages and their metadata.

    Args:
        repo_root: Absolute path to the repository root.

    Returns:
        Sorted list of ``ModuleInfo`` for every direct subpackage.
    """
    infra_dir = repo_root / "infrastructure"
    if not infra_dir.is_dir():
        logger.warning(f"Infrastructure directory not found: {infra_dir}")
        return []

    modules: list[ModuleInfo] = []
    for child in sorted(infra_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue

        init_path = child / "__init__.py"
        py_files = [f for f in child.rglob("*.py") if not _is_excluded_path(f)]

        # Attempt to extract public symbols from __init__.py
        public_symbols: list[str] = []
        if init_path.is_file():
            try:
                mod = importlib.import_module(f"infrastructure.{child.name}")
                all_symbols = getattr(mod, "__all__", None)
                if all_symbols is not None:
                    public_symbols = list(all_symbols)
                else:
                    public_symbols = [
                        s for s in dir(mod)
                        if not s.startswith("_")
                    ]
            except Exception as exc:
                logger.debug(f"Could not import infrastructure.{child.name}: {exc}")

        modules.append(ModuleInfo(
            name=child.name,
            path=child,
            python_file_count=len(py_files),
            has_init=init_path.is_file(),
            has_agents_md=(child / "AGENTS.md").is_file(),
            has_readme_md=(child / "README.md").is_file(),
            has_skill_md=(child / "SKILL.md").is_file(),
            has_pai_md=(child / "PAI.md").is_file(),
            public_symbols=public_symbols,
        ))

    logger.info(f"Discovered {len(modules)} infrastructure modules")
    return modules


def discover_projects(repo_root: Path) -> list[ProjectAnalysis]:
    """Scan ``projects/`` for valid project workspaces.

    A directory counts as a project if it contains ``manuscript/config.yaml``.

    Args:
        repo_root: Absolute path to the repository root.

    Returns:
        Sorted list of ``ProjectAnalysis``.
    """
    projects_dir = repo_root / "projects"
    if not projects_dir.is_dir():
        logger.warning(f"Projects directory not found: {projects_dir}")
        return []

    projects: list[ProjectAnalysis] = []
    for child in sorted(projects_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue

        config_path = child / "manuscript" / "config.yaml"
        if not config_path.is_file():
            continue

        # Load config
        config: dict[str, Any] = {}
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
        except Exception as exc:
            logger.warning(f"Could not load config for {child.name}: {exc}")

        # Count chapters (markdown files in manuscript/)
        manuscript_dir = child / "manuscript"
        chapters = [
            p for p in manuscript_dir.glob("*.md")
            if p.name[0].isdigit()
        ] if manuscript_dir.is_dir() else []

        # Count test files
        tests_dir = child / "tests"
        test_files = list(tests_dir.rglob("test_*.py")) if tests_dir.is_dir() else []

        # Count scripts
        scripts_dir = child / "scripts"
        scripts = list(scripts_dir.glob("*.py")) if scripts_dir.is_dir() else []

        # Count source modules (.py files in src/, excluding __init__.py)
        src_dir = child / "src"
        src_modules = (
            [f for f in src_dir.rglob("*.py") if not _is_excluded_path(f) and f.name != "__init__.py"]
            if src_dir.is_dir()
            else []
        )

        # Count auto-generated figures (.png in output/figures/)
        figures_dir = child / "output" / "figures"
        figures = list(figures_dir.glob("*.png")) if figures_dir.is_dir() else []

        projects.append(ProjectAnalysis(
            name=child.name,
            path=child,
            has_manuscript=manuscript_dir.is_dir(),
            chapter_count=len(chapters),
            has_tests=tests_dir.is_dir(),
            test_file_count=len(test_files),
            has_scripts=scripts_dir.is_dir(),
            script_count=len(scripts),
            src_module_count=len(src_modules),
            figure_count=len(figures),
            config=config,
        ))

    logger.info(f"Discovered {len(projects)} projects")
    return projects


def count_pipeline_stages(scripts_dir: Path) -> list[PipelineStage]:
    """Enumerate numbered pipeline scripts in the root ``scripts/`` directory.

    Expects filenames matching the pattern ``NN_name.py`` (e.g. ``01_run_tests.py``).

    Args:
        scripts_dir: Path to the repository's ``scripts/`` directory.

    Returns:
        List of ``PipelineStage`` ordered by stage number.
    """
    if not scripts_dir.is_dir():
        logger.warning(f"Scripts directory not found: {scripts_dir}")
        return []

    pattern = re.compile(r"^(\d{2})_(.+)\.py$")
    stages: list[PipelineStage] = []

    for script in sorted(scripts_dir.iterdir()):
        match = pattern.match(script.name)
        if match:
            stage_num = int(match.group(1))
            stage_name = match.group(2).replace("_", " ").title()
            stages.append(PipelineStage(
                number=stage_num,
                name=stage_name,
                script_name=script.name,
                script_path=script,
            ))

    logger.info(f"Discovered {len(stages)} pipeline stages")
    return stages


def analyze_test_coverage_config(project_dir: Path) -> CoverageConfig | None:
    """Extract test failure tolerances from a project's ``config.yaml``.

    Args:
        project_dir: Path to a project directory (must contain ``manuscript/config.yaml``).

    Returns:
        ``CoverageConfig`` or ``None`` if the config cannot be read.
    """
    config_path = project_dir / "manuscript" / "config.yaml"
    if not config_path.is_file():
        logger.warning(f"Config not found: {config_path}")
        return None

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning(f"Could not parse config: {exc}")
        return None

    testing = config.get("testing", {})
    return CoverageConfig(
        project_name=project_dir.name,
        max_test_failures=testing.get("max_test_failures", 0),
        max_infra_test_failures=testing.get("max_infra_test_failures", 0),
        max_project_test_failures=testing.get("max_project_test_failures", 0),
    )


def build_infrastructure_report(repo_root: Path) -> InfrastructureReport:
    """Build a complete introspection report for the repository.

    Aggregates module discovery, project discovery, pipeline stages,
    and file counts into a single ``InfrastructureReport``.

    Args:
        repo_root: Absolute path to the repository root.

    Returns:
        Populated ``InfrastructureReport``.
    """
    modules = discover_infrastructure_modules(repo_root)
    projects = discover_projects(repo_root)
    stages = count_pipeline_stages(repo_root / "scripts")

    # Count total Python files across the repo (excluding generated/cache dirs)
    total_py = len([p for p in repo_root.rglob("*.py") if not _is_excluded_path(p)])
    total_tests = len([p for p in repo_root.rglob("test_*.py") if not _is_excluded_path(p)])

    # Read infrastructure version
    version = "unknown"
    try:
        import infrastructure
        version = getattr(infrastructure, "__version__", "unknown")
    except ImportError:
        version = "unknown"  # infrastructure package not importable

    report = InfrastructureReport(
        repo_root=repo_root,
        infrastructure_version=version,
        modules=modules,
        projects=projects,
        pipeline_stages=stages,
        total_python_files=total_py,
        total_test_files=total_tests,
    )

    logger.info(
        f"Infrastructure report: {report.module_count} modules, "
        f"{report.project_count} projects, {report.stage_count} stages, "
        f"{report.total_python_files} Python files"
    )
    return report
