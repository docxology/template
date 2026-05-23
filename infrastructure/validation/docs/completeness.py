"""Phase 3: Completeness Analysis for documentation scanning."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger
from infrastructure.validation.docs.lint_runner import doc_roots
from infrastructure.validation.docs.cross_link_lint import find_broken_links
from infrastructure.validation.docs.models import CompletenessGap, DocumentationFile

logger = get_logger(__name__)


def check_feature_documentation(repo_root: Path, documentation_files: list[DocumentationFile]) -> list[CompletenessGap]:
    """Check if all features are documented."""
    gaps = []
    # Check src/ modules are documented
    src_dir = repo_root / "src"
    if src_dir.exists():
        src_modules = list(src_dir.glob("*.py"))
        src_modules = [m for m in src_modules if m.name != "__init__.py"]

        for module in src_modules:
            module_name = module.stem
            # Check if documented in docs/ or AGENTS.md
            documented = False
            for doc_file in documentation_files:
                if module_name in doc_file.relative_path.lower():
                    documented = True
                    break

            if not documented:
                gaps.append(
                    CompletenessGap(
                        category="features",
                        item=module_name,
                        description=f"Module {module_name} may not be fully documented",
                        severity="info",
                    )
                )

    return gaps


def check_script_documentation(repo_root: Path) -> list[CompletenessGap]:
    """Check if all scripts have documentation."""
    gaps = []
    scripts_dir = repo_root / "scripts"
    repo_utils_dir = repo_root / "repo_utilities"

    for script_dir in [scripts_dir, repo_utils_dir]:
        if script_dir.exists():
            for script in script_dir.glob("*.py"):
                if script.name.startswith("_"):
                    continue
                # Check if script has docstring and is mentioned in docs
                try:
                    content = script.read_text(encoding="utf-8")
                    if not re.search(r'""".*?"""', content, re.DOTALL):
                        gaps.append(
                            CompletenessGap(
                                category="scripts",
                                item=script.name,
                                description=f"Script {script.name} lacks docstring",
                                severity="warning",
                            )
                        )
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"Failed to check script docstring for {script}: {e}")

    return gaps


def _collect_doc_text(repo_root: Path) -> str:
    parts: list[str] = []
    for candidate in (repo_root / "docs", repo_root / "AGENTS.md", repo_root / "README.md"):
        if candidate.is_file():
            parts.append(candidate.read_text(encoding="utf-8").lower())
        elif candidate.is_dir():
            for md in candidate.rglob("*.md"):
                try:
                    parts.append(md.read_text(encoding="utf-8").lower())
                except OSError as exc:
                    logger.debug("Skipping unreadable doc %s: %s", md, exc)
    return "\n".join(parts)


def check_config_documentation(
    config_files: dict[str, Path],
    repo_root: Path,
) -> list[CompletenessGap]:
    """Check if top-level configuration keys from config.yaml.example appear in docs."""
    gaps: list[CompletenessGap] = []
    example_path = config_files.get("config.yaml.example")
    if example_path is None or not example_path.exists():
        return gaps

    try:
        data = yaml.safe_load(example_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError, ValueError) as exc:
        logger.debug("Failed to load config.yaml.example: %s", exc)
        return gaps

    if not isinstance(data, dict):
        return gaps

    doc_text = _collect_doc_text(repo_root)
    for key in data:
        if key.lower() not in doc_text:
            gaps.append(
                CompletenessGap(
                    category="config",
                    item=key,
                    description=f"Top-level config key '{key}' not mentioned in repo docs",
                    severity="info",
                )
            )
    return gaps


def check_cross_reference_completeness(repo_root: Path) -> list[CompletenessGap]:
    """Report unresolved internal links as completeness gaps."""
    gaps: list[CompletenessGap] = []
    for broken in find_broken_links(doc_roots(repo_root)):
        rel = str(broken.file.relative_to(repo_root)) if broken.file.is_relative_to(repo_root) else str(broken.file)
        gaps.append(
            CompletenessGap(
                category="cross_reference",
                item=broken.target,
                description=f"Broken link in {rel}:{broken.line} — {broken.reason}",
                severity="warning",
            )
        )
    return gaps


def check_troubleshooting(
    documentation_files: list[DocumentationFile],
) -> list[CompletenessGap]:
    """Check troubleshooting guide completeness."""
    gaps = []
    has_troubleshooting = any("TROUBLESHOOTING" in d.relative_path for d in documentation_files)
    if not has_troubleshooting:
        gaps.append(
            CompletenessGap(
                category="troubleshooting",
                item="troubleshooting_guide",
                description="No dedicated troubleshooting guide found",
                severity="info",
            )
        )
    return gaps


def check_workflow_documentation(
    documentation_files: list[DocumentationFile],
) -> list[CompletenessGap]:
    """Check workflow documentation completeness."""
    gaps = []
    has_workflow = any("WORKFLOW" in d.relative_path for d in documentation_files)
    if not has_workflow:
        gaps.append(
            CompletenessGap(
                category="workflows",
                item="workflow_guide",
                description="Workflow documentation may be incomplete",
                severity="info",
            )
        )
    return gaps


def check_onboarding(
    documentation_files: list[DocumentationFile],
) -> list[CompletenessGap]:
    """Check new user onboarding completeness."""
    gaps = []
    has_getting_started = any("GETTING_STARTED" in d.relative_path for d in documentation_files)
    has_quick_start = any("QUICK_START" in d.relative_path for d in documentation_files)

    if not has_getting_started and not has_quick_start:
        gaps.append(
            CompletenessGap(
                category="onboarding",
                item="getting_started",
                description="Getting started guide may be missing",
                severity="warning",
            )
        )
    return gaps


def group_gaps_by_category(gaps: list[CompletenessGap]) -> dict[str, int]:
    """Group completeness gaps by category."""
    categories: dict[str, int] = defaultdict(int)
    for gap in gaps:
        categories[gap.category] += 1
    return dict(categories)


def group_gaps_by_severity(gaps: list[CompletenessGap]) -> dict[str, int]:
    """Group completeness gaps by severity."""
    severities: dict[str, int] = defaultdict(int)
    for gap in gaps:
        severities[gap.severity] += 1
    return dict(severities)


def run_completeness_phase(
    repo_root: Path,
    documentation_files: list[DocumentationFile],
    config_files: dict[str, Path],
) -> tuple[dict[str, Any], list[CompletenessGap]]:
    """Run Phase 3: Completeness Analysis.

    Args:
        repo_root: Root path of the repository
        documentation_files: List of documentation file metadata
        config_files: Dictionary of config file paths

    Returns:
        Dictionary with completeness report
    """
    logger.info("Phase 3: Completeness Analysis...")

    gaps = []

    # Check feature documentation
    feature_gaps = check_feature_documentation(repo_root, documentation_files)
    gaps.extend(feature_gaps)

    # Check script documentation
    script_gaps = check_script_documentation(repo_root)
    gaps.extend(script_gaps)

    # Check configuration documentation
    config_gaps = check_config_documentation(config_files, repo_root)
    gaps.extend(config_gaps)

    # Check troubleshooting guides
    troubleshooting_gaps = check_troubleshooting(documentation_files)
    gaps.extend(troubleshooting_gaps)

    # Check workflow documentation
    workflow_gaps = check_workflow_documentation(documentation_files)
    gaps.extend(workflow_gaps)

    # Check onboarding
    onboarding_gaps = check_onboarding(documentation_files)
    gaps.extend(onboarding_gaps)

    # Check cross-references
    crossref_gaps = check_cross_reference_completeness(repo_root)
    gaps.extend(crossref_gaps)

    completeness_report = {
        "total_gaps": len(gaps),
        "by_category": group_gaps_by_category(gaps),
        "severity_breakdown": group_gaps_by_severity(gaps),
    }

    logger.info(f"Found {len(gaps)} completeness gaps")
    return completeness_report, gaps
