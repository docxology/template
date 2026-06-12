"""Project design-overlay validation for Stage 04 output checks."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_success, log_substep
from infrastructure.project.discovery import project_name_from_root
from infrastructure.project.domain_profile import load_domain_profile
from infrastructure.project.experiment_plan import load_experiment_plan, validate_experiment_plan

logger = get_logger(__name__)

#: An overlay validator is a domain-owned hook that inspects a project root and
#: returns a list of issue strings (empty when the overlay is absent or passes).
#: The generic design-validation layer invokes these hooks without knowing which
#: domain owns them, so domain-specific logic stays in its own module.
OverlayValidator = Callable[[Path, Path], list[str]]

# Re-exported for callers that imported the helper from this module historically;
# the canonical home is now ``infrastructure.project.discovery``.
__all__ = ["OverlayValidator", "project_name_from_root", "validate_project_design"]


def validate_project_design(
    project_root: Path,
    repo_root: Path,
    overlay_validators: Sequence[OverlayValidator] = (),
) -> tuple[bool, list[str]]:
    """Validate advisory domain profile, experiment plan, and opt-in overlays.

    Args:
        project_root: Filesystem root of the project being validated.
        repo_root: Repository root directory.
        overlay_validators: Optional domain-owned overlay validators. Each is
            called with ``(project_root, repo_root)`` and returns a list of issue
            strings. This keeps domain-specific readiness checks (e.g. AutoResearch)
            in their owning modules rather than special-cased here.

    Returns:
        ``(passed, issues)`` where ``passed`` is False if any issue was found.
    """
    log_substep("Validating project design overlays...", logger)
    issues: list[str] = []
    try:
        load_domain_profile(project_root)
    except ValueError as exc:
        issues.append(str(exc))

    try:
        experiment_plan = load_experiment_plan(project_root)
        result = validate_experiment_plan(experiment_plan)
        issues.extend(result.issues)
    except ValueError as exc:
        issues.append(str(exc))

    for overlay_validator in overlay_validators:
        issues.extend(overlay_validator(project_root, repo_root))

    if issues:
        for issue in issues:
            logger.warning(issue)
        return False, issues

    log_success("Project design overlays passed", logger)
    return True, []
