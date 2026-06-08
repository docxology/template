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

_EXCLUDED_DIRS = frozenset(
    {"__pycache__", ".venv", ".git", ".cursor", ".pytest_cache", ".mypy_cache", "node_modules", "dist", "build"}
)


def _is_excluded_path(p: Path) -> bool:
    """Return True if path contains any excluded directory segment."""
    return any(part in _EXCLUDED_DIRS for part in p.parts)


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
    """Rich analysis metrics for a single project workspace."""

    name: str
    path: Path
    has_manuscript: bool
    chapter_count: int
    has_tests: bool
    test_file_count: int
    test_count: int = 0
    has_scripts: bool = False
    script_count: int = 0
    src_module_count: int = 0
    figure_count: int = 0
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineStage:
    """A single pipeline stage descriptor."""

    number: int
    name: str
    script_name: str
    script_path: Path
    tags: list[str] = field(default_factory=list)
    method: str | None = None
    failure_mode: str | None = None


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
    numbered_scripts: list[PipelineStage]
    total_python_files: int
    total_test_files: int

    @property
    def pipeline_stages_declared(self) -> int:
        return len(self.pipeline_stages)

    @property
    def pipeline_stages_default_full(self) -> int:
        return sum(1 for stage in self.pipeline_stages if "bundle" not in stage.tags and "archival" not in stage.tags)

    @property
    def pipeline_stages_core_only(self) -> int:
        return sum(1 for stage in self.pipeline_stages if "core" in stage.tags and "llm" not in stage.tags)


def resolve_template_repo_root(project_dir: Path) -> Path:
    """Locate the Layer-1 template repository from a WIP or private project path."""
    resolved = project_dir.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    sibling = resolved.parents[2] / "template"
    if (sibling / "infrastructure").is_dir():
        return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {project_dir}")


def discover_infrastructure_modules(repo_root: Path) -> list[ModuleInfo]:
    """Scan ``infrastructure/`` for subpackages and their metadata."""
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

        public_symbols: list[str] = []
        if init_path.is_file():
            try:
                mod = importlib.import_module(f"infrastructure.{child.name}")
                all_symbols = getattr(mod, "__all__", None)
                if all_symbols is not None:
                    public_symbols = list(all_symbols)
                else:
                    public_symbols = [s for s in dir(mod) if not s.startswith("_")]
            except (ImportError, AttributeError, OSError) as exc:
                logger.debug(f"Could not import infrastructure.{child.name}: {exc}")

        modules.append(
            ModuleInfo(
                name=child.name,
                path=child,
                python_file_count=len(py_files),
                has_init=init_path.is_file(),
                has_agents_md=(child / "AGENTS.md").is_file(),
                has_readme_md=(child / "README.md").is_file(),
                has_skill_md=(child / "SKILL.md").is_file(),
                has_pai_md=(child / "PAI.md").is_file(),
                public_symbols=public_symbols,
            )
        )

    logger.info(f"Discovered {len(modules)} infrastructure modules")
    return modules


def _project_analysis_from_workspace(child: Path) -> ProjectAnalysis | None:
    """Build ``ProjectAnalysis`` for *child* if it contains ``manuscript/config.yaml``."""
    config_path = child / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return None

    config: dict[str, Any] = {}
    try:
        with open(config_path, encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, ValueError) as exc:
        logger.warning(f"Could not load config for {child.name}: {exc}")

    manuscript_dir = child / "manuscript"
    chapters: list[Path] = []
    if manuscript_dir.is_dir():
        numbered = [p for p in manuscript_dir.rglob("*.md") if p.name[0].isdigit()]
        if numbered:
            chapters = numbered
        else:
            skip = frozenset({"AGENTS.md", "README.md", "SKILL.md", "PAI.md"})
            chapters = [p for p in manuscript_dir.rglob("*.md") if p.name not in skip and not p.name.startswith(".")]

    tests_dir = child / "tests"
    test_files = list(tests_dir.rglob("test_*.py")) if tests_dir.is_dir() else []

    scripts_dir = child / "scripts"
    scripts = list(scripts_dir.glob("*.py")) if scripts_dir.is_dir() else []

    src_dir = child / "src"
    src_modules = (
        [f for f in src_dir.rglob("*.py") if not _is_excluded_path(f) and f.name != "__init__.py"]
        if src_dir.is_dir()
        else []
    )

    figures_dir = child / "output" / "figures"
    figures = list(figures_dir.glob("*.png")) if figures_dir.is_dir() else []

    return ProjectAnalysis(
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
    )


#: Typed program subfolders under ``projects/``. The public exemplars are
#: git-tracked under ``projects/templates/``; ``active/`` holds the hot-seat
#: rendered set; ``working``/``published``/``archive``/``other`` hold non-rendered
#: rotating work (symlinked from the private lifecycle repo). Keep in sync with
#: ``infrastructure.project.discovery.NON_RENDERED_SUBDIRS`` (the latter four).
_TYPED_PROJECT_SUBDIRS = frozenset({"templates", "active", "working", "published", "archive", "other"})

#: On-disk directory name (leaf) of this meta-project's workspace. It is now
#: git-tracked at ``projects/templates/template_template/``, so the leaf matches
#: :data:`META_PROJECT_PUBLIC_NAME` exactly; the rename mapping below is therefore
#: a no-op kept for back-compat with callers that key on the staging name.
META_PROJECT_DIR_NAME = "template_template"

#: Public identity of this meta-project. The ``src/`` package is named
#: ``template_template`` and the project is published as a public exemplar
#: under this name; its self-introspection metric keys are
#: ``project_template_template_*`` accordingly.
META_PROJECT_PUBLIC_NAME = "template_template"


def _candidate_workspaces(projects_dir: Path) -> list[Path]:
    """Yield candidate workspace dirs under ``projects/``: flat children plus the
    children of each typed program subfolder (``templates/``, ``active/``, …)."""
    candidates: list[Path] = []
    for child in sorted(projects_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        if child.name in _TYPED_PROJECT_SUBDIRS:
            for sub in sorted(child.iterdir()):
                if sub.is_dir() and not sub.name.startswith(("_", ".")):
                    candidates.append(sub)
        else:
            candidates.append(child)
    return candidates


def discover_projects(repo_root: Path, *, public_only: bool = True) -> list[ProjectAnalysis]:
    """Scan ``projects/`` (flat children + typed program subfolders) for workspaces.

    The layout is uniform program-prefix: public exemplars live under
    ``projects/templates/<name>``, the hot-seat rendered set under
    ``projects/active/<name>``, and non-rendered rotating work under
    ``projects/{working,published,archive,other}/<name>``. Discovery returns the
    bare leaf name (e.g. ``template_code_project``) so metric keys remain
    ``project_<leaf>_*``.

    CONFIDENTIALITY: ``public_only`` defaults to True so this meta-template — which
    is itself published as a public exemplar — only ever introspects the public
    canonical exemplars (``infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES``,
    matched by leaf name) plus this meta-project itself (:data:`META_PROJECT_PUBLIC_NAME`),
    and never embeds private/rotating project names into its metrics, figures, or
    rendered manuscript. The allowed leaf set is the single source of truth; private
    lifecycle trees outside ``projects/`` are never scanned. Set ``public_only=False``
    only for local diagnostics that never get published.
    """
    allowed: set[str] | None = None
    if public_only:
        from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

        # Allowed names are the public exemplars' bare leaf names (PUBLIC_PROJECT_NAMES
        # are slash-qualified, e.g. ``templates/template_code_project``) plus this
        # meta-project's public identity.
        allowed = {Path(name).name for name in PUBLIC_PROJECT_NAMES} | {META_PROJECT_PUBLIC_NAME}

    base = repo_root / "projects"
    combined: dict[str, ProjectAnalysis] = {}
    if base.is_dir():
        for child in _candidate_workspaces(base):
            if allowed is not None and child.name not in allowed:
                continue
            analysis = _project_analysis_from_workspace(child)
            if analysis is None:
                continue
            # No-op under the git-tracked layout (leaf == public name); retained so
            # any future staging directory name still maps to the public identity.
            if analysis.name == META_PROJECT_DIR_NAME:
                analysis.name = META_PROJECT_PUBLIC_NAME
            combined[analysis.name] = analysis

    projects = sorted(combined.values(), key=lambda p: p.name)
    logger.info(f"Discovered {len(projects)} projects (public_only={public_only})")
    return projects


def enumerate_numbered_scripts(scripts_dir: Path) -> list[PipelineStage]:
    """Enumerate numbered pipeline scripts in the root ``scripts/`` directory."""
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
            stages.append(
                PipelineStage(
                    number=stage_num,
                    name=stage_name,
                    script_name=script.name,
                    script_path=script,
                )
            )

    logger.info(f"Discovered {len(stages)} numbered pipeline scripts")
    return stages


count_pipeline_stages = enumerate_numbered_scripts


def load_pipeline_stages_from_yaml(repo_root: Path) -> list[PipelineStage]:
    """Load declared pipeline stages from ``infrastructure/core/pipeline/pipeline.yaml``."""
    yaml_path = repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
    if not yaml_path.is_file():
        logger.warning(f"Pipeline YAML not found: {yaml_path}")
        return []

    with open(yaml_path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    stages: list[PipelineStage] = []
    for index, stage in enumerate(data.get("stages", [])):
        script = stage.get("script") or ""
        script_path = repo_root / "scripts" / script if script else repo_root
        stages.append(
            PipelineStage(
                number=index,
                name=str(stage.get("name", f"Stage {index}")),
                script_name=script or str(stage.get("method", "")),
                script_path=script_path,
                tags=list(stage.get("tags") or []),
                method=stage.get("method"),
                failure_mode=stage.get("failure_mode"),
            )
        )

    logger.info(f"Loaded {len(stages)} pipeline stages from YAML")
    return stages


def analyze_test_coverage_config(project_dir: Path) -> CoverageConfig | None:
    """Extract test failure tolerances from a project's ``config.yaml``."""
    config_path = project_dir / "manuscript" / "config.yaml"
    if not config_path.is_file():
        logger.warning(f"Config not found: {config_path}")
        return None

    try:
        with open(config_path, encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, ValueError) as exc:
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
    """Build a complete introspection report for the repository."""
    modules = discover_infrastructure_modules(repo_root)
    projects = discover_projects(repo_root)
    numbered_scripts = enumerate_numbered_scripts(repo_root / "scripts")
    pipeline_stages = load_pipeline_stages_from_yaml(repo_root)

    total_py = len([p for p in repo_root.rglob("*.py") if not _is_excluded_path(p)])
    total_tests = len([p for p in repo_root.rglob("test_*.py") if not _is_excluded_path(p)])

    version = "unknown"
    try:
        import infrastructure

        version = getattr(infrastructure, "__version__", "unknown")
    except ImportError:
        version = "unknown"

    report = InfrastructureReport(
        repo_root=repo_root,
        infrastructure_version=version,
        modules=modules,
        projects=projects,
        pipeline_stages=pipeline_stages,
        numbered_scripts=numbered_scripts,
        total_python_files=total_py,
        total_test_files=total_tests,
    )

    logger.info(
        "Infrastructure report: %s modules, %s projects, %s YAML stages, %s numbered scripts, %s Python files",
        len(report.modules),
        len(report.projects),
        len(report.pipeline_stages),
        len(report.numbered_scripts),
        report.total_python_files,
    )
    return report
