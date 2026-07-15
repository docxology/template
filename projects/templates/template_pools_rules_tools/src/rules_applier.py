"""rules_applier.py — Load and apply rules from rules/templates/ exemplars.

Supports both soft (guideline) and strong (constraint) rules. All functions
use graceful fallbacks when paths are absent.

Repo-root discovery: 4 levels up from this file.
"""

from __future__ import annotations

import logging
import pathlib

import yaml

from .type_defs import (
    AllRulesResult,
    RuleSetResult,
    SoftRuleEntry,
    StrongRuleEntry,
)

__all__ = [
    "load_soft_rules",
    "load_strong_rules",
    "validate_against_rules",
    "load_all_project_rules",
    "load_all_manuscript_rules",
    "get_rules_root",
]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Repo-root resolution
# ---------------------------------------------------------------------------


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[4]


def _rules_root() -> pathlib.Path:
    bundled = (
        pathlib.Path(__file__).resolve().parents[1] / "_template_resources" / "rules" / "templates"
    )
    if bundled.is_dir():
        return bundled
    return _repo_root() / "rules" / "templates"


# Expose for test use (not part of the main public API)
get_rules_root = _rules_root


# ---------------------------------------------------------------------------
# Soft rules
# ---------------------------------------------------------------------------


def load_soft_rules(
    rule_set_name: str,
    *,
    templates_root: pathlib.Path | None = None,
) -> list[SoftRuleEntry]:
    """Load all soft rule files from a rule set's ``soft/`` directory.

    Each entry in the returned list has:

    - ``filename``: str
    - ``content``: str (raw Markdown text)

    Returns an empty list if the rule set or its ``soft/`` directory is absent.
    """
    rules_root = templates_root if templates_root is not None else _rules_root()
    soft_dir = rules_root / rule_set_name / "soft"
    if not soft_dir.is_dir():
        logger.warning("soft rules: directory not found — %s", soft_dir)
        return []

    results: list[SoftRuleEntry] = []
    for md_file in sorted(soft_dir.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            results.append(SoftRuleEntry(filename=md_file.name, content=content))
        except (OSError, UnicodeDecodeError) as exc:
            logger.warning("soft rules: could not read %s — %s", md_file, exc)

    return results


# ---------------------------------------------------------------------------
# Strong rules
# ---------------------------------------------------------------------------


def load_strong_rules(
    rule_set_name: str,
    *,
    templates_root: pathlib.Path | None = None,
) -> list[StrongRuleEntry]:
    """Load all strong rule YAML files from a rule set's ``strong/`` directory.

    Each entry has:

    - ``filename``: str
    - ``schema``: parsed dict (the YAML content)

    Returns an empty list if the rule set or its ``strong/`` directory is absent.
    """
    rules_root = templates_root if templates_root is not None else _rules_root()
    strong_dir = rules_root / rule_set_name / "strong"
    if not strong_dir.is_dir():
        logger.warning("strong rules: directory not found — %s", strong_dir)
        return []

    results: list[StrongRuleEntry] = []
    for yaml_file in sorted(strong_dir.glob("*.yaml")):
        try:
            schema: object = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            results.append(StrongRuleEntry(filename=yaml_file.name, schema=schema))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            logger.warning("strong rules: could not parse %s — %s", yaml_file, exc)

    return results


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------


def validate_against_rules(
    rule_set_name: str,
    context: dict[str, object] | None = None,
    *,
    templates_root: pathlib.Path | None = None,
) -> RuleSetResult:
    """Load and report on all rules for the given rule set.

    Performs structural validation only (checks the schema is present and
    parseable). Full semantic validation is out of scope for this module.

    Returns a :class:`RuleSetResult` with:

    - ``rule_set``: str
    - ``manifest``: parsed rules.yaml (or ``None``)
    - ``soft_rules_count``: int
    - ``strong_rules_count``: int
    - ``soft_rules``: list of rule stem names (without extension)
    - ``strong_rules``: list of rule stem names (without extension)
    - ``soft_rules_loaded``: list of full filenames
    - ``strong_rules_loaded``: list of full filenames
    - ``status``: ``"ok"`` | ``"partial"`` | ``"missing"``
    - ``warnings``: list[str]
    """
    _ = context or {}  # reserved for future semantic validation
    warnings: list[str] = []

    rules_root = templates_root if templates_root is not None else _rules_root()
    manifest_path = rules_root / rule_set_name / "rules.yaml"
    manifest: object | None = None
    if manifest_path.exists():
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            warnings.append(f"rules.yaml parse error: {exc}")
    else:
        warnings.append(f"rules.yaml not found at {manifest_path}")

    soft = load_soft_rules(rule_set_name, templates_root=templates_root)
    strong = load_strong_rules(rule_set_name, templates_root=templates_root)

    if manifest is None and not soft and not strong:
        status = "missing"
    elif warnings:
        status = "partial"
    else:
        status = "ok"

    return RuleSetResult(
        rule_set=rule_set_name,
        manifest=manifest,
        soft_rules_count=len(soft),
        strong_rules_count=len(strong),
        soft_rules=[r["filename"].removesuffix(".md") for r in soft],
        strong_rules=[r["filename"].removesuffix(".yaml") for r in strong],
        soft_rules_loaded=[r["filename"] for r in soft],
        strong_rules_loaded=[r["filename"] for r in strong],
        status=status,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Convenience loaders
# ---------------------------------------------------------------------------


def load_all_project_rules() -> AllRulesResult:
    """Load all rules from ``template_project_rules``.

    Returns an :class:`AllRulesResult` with ``soft`` and ``strong`` lists.
    """
    return AllRulesResult(
        soft=load_soft_rules("template_project_rules"),
        strong=load_strong_rules("template_project_rules"),
    )


def load_all_manuscript_rules() -> AllRulesResult:
    """Load all rules from ``template_manuscript_rules``.

    Returns an :class:`AllRulesResult` with ``soft`` and ``strong`` lists.
    """
    return AllRulesResult(
        soft=load_soft_rules("template_manuscript_rules"),
        strong=load_strong_rules("template_manuscript_rules"),
    )
