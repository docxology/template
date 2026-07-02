"""Steganography post-processing wrapper.

This module replaces the inline Python heredoc that previously lived in
``secure_run.sh``. It dispatches to :mod:`infrastructure.steganography`
rather than re-implementing any cryptographic logic.

Public API:

- :func:`run_secure_pipeline` — full ``secure_run.sh`` workflow
  (pipeline + steganography post-processing).
- :func:`apply_steganography_to_project` — process the PDFs of a single
  project. Used standalone via ``--steganography-only``.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.orchestration.discovery import validate_project_slug
from infrastructure.orchestration.pipeline_runner import (
    PipelineInvocation,
    PipelineRunner,
)
from infrastructure.project.discovery import discover_projects

logger = get_logger(__name__)


@dataclass
class SecureRunOptions:
    """Options accepted by :func:`run_secure_pipeline`."""

    project: str | None = None
    steganography_only: bool = False
    skip_infra: bool = False
    core_only: bool = False
    resume: bool = False
    validate_kmyth: bool = False


def _load_steganography():  # pragma: no cover - import indirection
    """Lazy import to keep the orchestration package import-light.

    The steganography module pulls in ``reportlab`` / ``qrcode``; we don't
    want to pay for that on every CLI invocation.
    """
    from infrastructure.steganography import (
        SteganographyConfig,
        SteganographyProcessor,
    )

    return SteganographyConfig, SteganographyProcessor


def _load_project_config(project_path: Path) -> dict[str, Any]:
    """Load ``manuscript/config.yaml`` for the project, if present."""
    return _load_yaml_mapping(project_path / "manuscript" / "config.yaml")


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML mapping from *path*, returning ``{}`` when absent/invalid."""
    if not path.exists():
        return {}
    try:
        import yaml  # local import — yaml is already a project dep

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read %s: %s", path, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("Ignoring non-mapping YAML config: %s", path)
        return {}
    return data


def _load_repo_secure_config(repo_root: Path) -> dict[str, Any]:
    """Load repository-wide secure defaults from ``infrastructure/config``."""
    config = _load_yaml_mapping(repo_root / "infrastructure" / "config" / "secure_config.yaml")
    steg = config.get("steganography", {})
    return dict(steg) if isinstance(steg, dict) else {}


def _effective_steganography_config(repo_root: Path, project_config: dict[str, Any]) -> dict[str, Any]:
    """Merge steganography config with precedence: dataclass < repo < project."""
    merged = _load_repo_secure_config(repo_root)
    project_steg = project_config.get("steganography", {})
    if isinstance(project_steg, dict):
        merged.update(project_steg)
    elif project_steg:
        logger.warning("Ignoring non-mapping steganography config: %r", project_steg)
    return merged


def validate_kmyth_for_secure_run(repo_root: Path, project_qualified_name: str | None = None) -> int:
    """Validate optional Kmyth availability for the secure-run configuration."""
    project_config: dict[str, Any] = {}
    if project_qualified_name is not None:
        validated = validate_project_slug(project_qualified_name, repo_root)
        projects = discover_projects(repo_root)
        project = next((p for p in projects if p.qualified_name == validated), None)
        if project is None:
            logger.error("Unknown project: %s", validated)
            return 1
        project_config = _load_project_config(project.path)

    SteganographyConfig, _ = _load_steganography()
    steg_mapping = _effective_steganography_config(repo_root, project_config)
    steg_config = SteganographyConfig.from_dict(steg_mapping)

    from infrastructure.steganography import validate_kmyth_installation

    availability = validate_kmyth_installation(
        binary_dir=steg_config.kmyth_binary_dir,
        source_dir=steg_config.kmyth_source_dir,
    )
    if availability.available:
        logger.info(availability.summary())
        return 0

    logger.error(availability.summary())
    return 1


def apply_steganography_to_project(
    repo_root: Path,
    project_qualified_name: str,
    *,
    processor_factory=None,
) -> int:
    """Apply steganography to all PDFs in a single project.

    Args:
        repo_root: Repository root.
        project_qualified_name: Qualified project name (e.g. ``program/name``).
        processor_factory: Optional factory ``(config) -> processor`` used by
            tests. The default uses
            :class:`infrastructure.steganography.SteganographyProcessor`.

    Returns:
        ``0`` on success, ``1`` on failure, ``2`` if no PDFs were found.
    """
    projects = discover_projects(repo_root)
    project = next(
        (p for p in projects if p.qualified_name == project_qualified_name),
        None,
    )
    if project is None:
        logger.error("Unknown project: %s", project_qualified_name)
        return 1

    pdf_dir = project.path / "output" / "pdf"
    if not pdf_dir.exists():
        pdf_dir = repo_root / "output" / project_qualified_name / "pdf"
    if not pdf_dir.exists():
        logger.warning("No PDF output directory for %s", project_qualified_name)
        return 2

    pdfs = [p for p in pdf_dir.glob("*.pdf") if "_steganography" not in p.stem]
    if not pdfs:
        logger.warning("No PDFs found in %s", pdf_dir)
        return 2

    config_yaml = _load_project_config(project.path)
    title = config_yaml.get("paper", {}).get("title", project_qualified_name)
    authors = [a.get("name", "") for a in config_yaml.get("authors", [])]
    author_emails = [a.get("email") for a in config_yaml.get("authors", []) if a.get("email")]
    keywords = config_yaml.get("keywords", [])
    steg_mapping = _effective_steganography_config(repo_root, config_yaml)

    if processor_factory is None:  # pragma: no cover - heavy reportlab path
        SteganographyConfig, SteganographyProcessor = _load_steganography()
        steg_config = SteganographyConfig.from_dict(steg_mapping)
        processor = SteganographyProcessor(steg_config)
    else:
        processor = processor_factory(steg_mapping)

    success_count = 0
    for pdf_path in pdfs:
        try:
            result = processor.process(
                pdf_path,
                title=title,
                authors=authors,
                keywords=keywords,
                author_emails=author_emails,
            )
            logger.info("Processed %s -> %s", pdf_path.name, getattr(result, "name", result))
            success_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to process %s: %s", pdf_path.name, exc)

    logger.info(
        "Steganography complete for %s: %d/%d",
        project_qualified_name,
        success_count,
        len(pdfs),
    )
    return 0 if success_count == len(pdfs) else 1


def run_secure_pipeline(
    repo_root: Path,
    options: SecureRunOptions,
    *,
    runner_cls=PipelineRunner,
    processor_factory=None,
) -> int:
    """Run the secure pipeline.

    1. Optionally run the normal pipeline (skipped if ``steganography_only``).
    2. Apply steganography to all generated PDFs (one project, or all).

    Args:
        repo_root: Repository root.
        options: User-supplied options.
        runner_cls: Pipeline runner class (overridable for tests).
        processor_factory: Steganography processor factory (overridable
            for tests). Default uses real
            :class:`infrastructure.steganography.SteganographyProcessor`.

    Returns:
        Process exit code.
    """
    if options.validate_kmyth:
        return validate_kmyth_for_secure_run(repo_root, options.project)

    # Pipeline phase
    if not options.steganography_only:
        if options.project is None:
            logger.error("--project is required when running the secure pipeline phase")
            return 2
        validated = validate_project_slug(options.project, repo_root)
        runner = runner_cls(repo_root=repo_root)
        invocation = PipelineInvocation(
            project=validated,
            skip_infra=options.skip_infra,
            core_only=options.core_only,
            resume=options.resume,
        )
        rc = int(runner.run(invocation))
        if rc != 0:
            logger.error("Pipeline phase failed; skipping steganography.")
            return rc

    # Steganography phase — single project or all discovered projects
    if options.project is not None:
        targets = [validate_project_slug(options.project, repo_root)]
    else:
        targets = [p.qualified_name for p in discover_projects(repo_root)]
        if not targets:
            logger.error("No projects discovered for steganography phase")
            return 1

    overall_status = 0
    for target in targets:
        rc = apply_steganography_to_project(repo_root, target, processor_factory=processor_factory)
        if rc == 1:
            overall_status = 1
        # rc == 2 (no PDFs) is non-fatal here, mirroring secure_run.sh

    return overall_status
