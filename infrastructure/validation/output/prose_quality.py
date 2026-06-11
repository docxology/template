"""Optional prose-quality checks for Stage 04 output validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.validation.content.ai_writing import analyze_prose

logger = get_logger(__name__)


def load_project_config_yaml(manuscript_dir: Path) -> dict[str, Any] | None:
    """Load manuscript ``config.yaml`` as a plain dict for validation toggles."""
    cfg = manuscript_dir / "config.yaml"
    if not cfg.is_file():
        return None
    try:
        import yaml
    except ImportError:
        logger.debug("PyYAML not available; cannot read validation toggles from config.yaml")
        return None
    try:
        with cfg.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, yaml.YAMLError) as exc:
        logger.debug("Could not parse %s for validation toggles: %s", cfg.name, exc)
        return None


def prose_quality_enabled(project_root: Path) -> bool:
    """Return whether the opt-in AI-writing prose gate is enabled."""
    config = load_project_config_yaml(project_root / "manuscript")
    if not config:
        return False
    validation = config.get("validation") or {}
    prose = validation.get("prose_quality") or {}
    return bool(prose.get("enabled"))


def validate_prose_quality(project_root: Path) -> bool:
    """Run the report-only AI-writing fingerprint scan over manuscript Markdown."""
    log_substep("Analyzing prose quality (AI-writing fingerprints)...", logger)
    manuscript_dir = project_root / "manuscript"
    if not manuscript_dir.is_dir():
        logger.warning("Prose quality: manuscript directory not found at %s", manuscript_dir)
        return True

    flagged = 0
    for md_file in sorted(manuscript_dir.glob("*.md")):
        try:
            report = analyze_prose(md_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("Prose quality: could not read %s: %s", md_file.name, exc)
            continue
        if report.has_flags:
            flagged += 1
            logger.info("  %s (%d words):", md_file.name, report.word_count)
            for flag in report.flags:
                logger.info("    - %s", flag)

    if flagged:
        logger.info("Prose quality: %d manuscript file(s) flagged (informational only)", flagged)
    else:
        log_success("Prose quality: no AI-writing fingerprints flagged", logger)
    return True
