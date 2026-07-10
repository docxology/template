"""Evaluate strong rule YAML schemas against a runtime context dict.

Context keys (all optional; missing keys skip semantic checks for that rule):

- ``coverage``: ``dict[str, float]`` — measured percentages keyed by constraint name
  (``infrastructure``, ``project_src``, ``public_api``).
- ``manuscript_sections``: ``list[str]`` — ordered section heading names.
- ``forbidden_sections_found``: ``list[str]`` — headings that must not appear.
- ``references``: ``list[dict[str, object]]`` — reference records for schema checks.
- ``project_root``: :class:`pathlib.Path` — project tree for module-structure rules.
- ``fond_freshness``: ``list[dict[str, object]]`` — one record per fond, each with
  ``name`` (str), ``manifest_mtime`` (float), ``latest_data_mtime`` (float), for
  ``manifest_freshness`` rules.

``manifest_freshness`` is implemented here (dispatch + evaluator + synthetic-dict
unit tests) but deliberately has no corresponding strong-rule YAML file under
``rules/templates/*/strong/`` yet — adding one would mean writing into the shared
``rules/`` tree, which this project's own read-only invariant reserves for an
explicit, separately-considered decision (see ``manuscript/07_conclusion.md``).
"""

from __future__ import annotations

import logging
import pathlib
import re
from typing import TypedDict

import yaml

from .rules_applier import load_strong_rules
from .type_defs import StrongRuleEntry

__all__ = [
    "StrongRuleViolation",
    "StrongRuleEvaluation",
    "StrongRulesEvaluationResult",
    "evaluate_strong_rule",
    "evaluate_strong_rules",
    "load_rule_context_from_project",
    "parse_bib_entries",
]

logger = logging.getLogger(__name__)


class StrongRuleViolation(TypedDict):
    """Data container for StrongRuleViolation."""

    rule_name: str
    filename: str
    message: str


class StrongRuleEvaluation(TypedDict):
    """Data container for StrongRuleEvaluation."""

    filename: str
    rule_name: str
    passed: bool
    violations: list[StrongRuleViolation]


class StrongRulesEvaluationResult(TypedDict):
    """Data container for StrongRulesEvaluationResult."""

    rule_set: str
    evaluations: list[StrongRuleEvaluation]
    passed: bool
    violation_count: int


def _rule_block(schema: object) -> dict[str, object]:
    if not isinstance(schema, dict):
        return {}
    rule = schema.get("rule")
    return rule if isinstance(rule, dict) else {}


def _rule_name(entry: StrongRuleEntry, rule: dict[str, object]) -> str:
    name = rule.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return entry["filename"].removesuffix(".yaml")


def evaluate_strong_rule(
    entry: StrongRuleEntry,
    context: dict[str, object],
) -> StrongRuleEvaluation:
    """Evaluate one strong rule entry against *context*."""
    rule = _rule_block(entry["schema"])
    rule_name = _rule_name(entry, rule)
    violations: list[StrongRuleViolation] = []

    if not rule:
        violations.append(
            StrongRuleViolation(
                rule_name=rule_name,
                filename=entry["filename"],
                message="schema missing top-level 'rule' mapping",
            )
        )
        return StrongRuleEvaluation(
            filename=entry["filename"],
            rule_name=rule_name,
            passed=False,
            violations=violations,
        )

    dispatch = {
        "coverage_threshold": _evaluate_coverage_threshold,
        "section_schema": _evaluate_section_schema,
        "module_structure": _evaluate_module_structure,
        "reference_schema": _evaluate_reference_schema,
        "manifest_freshness": _evaluate_manifest_freshness,
    }
    evaluator = dispatch.get(rule_name)
    if evaluator is None:
        logger.info("strong rules: no semantic evaluator for %s — structural only", rule_name)
    else:
        violations.extend(evaluator(rule_name, entry["filename"], rule, context))

    return StrongRuleEvaluation(
        filename=entry["filename"],
        rule_name=rule_name,
        passed=len(violations) == 0,
        violations=violations,
    )


def evaluate_strong_rules(
    rule_set_name: str,
    context: dict[str, object] | None = None,
    *,
    templates_root: pathlib.Path | None = None,
) -> StrongRulesEvaluationResult:
    """Evaluate all strong rules for *rule_set_name* against *context*."""
    ctx = context or {}
    evaluations: list[StrongRuleEvaluation] = []
    for entry in load_strong_rules(rule_set_name, templates_root=templates_root):
        evaluations.append(evaluate_strong_rule(entry, ctx))

    violation_count = sum(len(item["violations"]) for item in evaluations)
    return StrongRulesEvaluationResult(
        rule_set=rule_set_name,
        evaluations=evaluations,
        passed=violation_count == 0,
        violation_count=violation_count,
    )


def _evaluate_coverage_threshold(
    rule_name: str,
    filename: str,
    rule: dict[str, object],
    context: dict[str, object],
) -> list[StrongRuleViolation]:
    coverage = context.get("coverage")
    if not isinstance(coverage, dict):
        return []

    constraints = rule.get("constraints")
    if not isinstance(constraints, dict):
        return [
            StrongRuleViolation(
                rule_name=rule_name,
                filename=filename,
                message="coverage_threshold rule missing constraints mapping",
            )
        ]

    violations: list[StrongRuleViolation] = []
    for key, minimum in constraints.items():
        if not isinstance(key, str) or not isinstance(minimum, (int, float)):
            continue
        measured = coverage.get(key)
        if measured is None:
            violations.append(
                StrongRuleViolation(
                    rule_name=rule_name,
                    filename=filename,
                    message=f"coverage.{key} not provided in context",
                )
            )
            continue
        if not isinstance(measured, (int, float)):
            violations.append(
                StrongRuleViolation(
                    rule_name=rule_name,
                    filename=filename,
                    message=f"coverage.{key} must be numeric, got {type(measured).__name__}",
                )
            )
            continue
        if float(measured) < float(minimum):
            violations.append(
                StrongRuleViolation(
                    rule_name=rule_name,
                    filename=filename,
                    message=f"coverage.{key} {measured}% below minimum {minimum}%",
                )
            )
    return violations


def _evaluate_section_schema(
    rule_name: str,
    filename: str,
    rule: dict[str, object],
    context: dict[str, object],
) -> list[StrongRuleViolation]:
    sections_raw = context.get("manuscript_sections")
    if not isinstance(sections_raw, list):
        return []

    sections = [str(item).strip() for item in sections_raw if str(item).strip()]
    violations: list[StrongRuleViolation] = []

    required = rule.get("required_sections")
    if isinstance(required, list):
        for item in required:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str):
                continue
            aliases = item.get("aliases")
            names = {name}
            if isinstance(aliases, list):
                names.update(str(alias) for alias in aliases if str(alias).strip())
            if not any(section in names for section in sections):
                violations.append(
                    StrongRuleViolation(
                        rule_name=rule_name,
                        filename=filename,
                        message=f"required section missing: {name}",
                    )
                )

    forbidden = rule.get("forbidden_sections")
    found = context.get("forbidden_sections_found")
    if isinstance(forbidden, list) and isinstance(found, list):
        forbidden_set = {str(name) for name in forbidden}
        for heading in found:
            heading_str = str(heading).strip()
            if heading_str in forbidden_set:
                violations.append(
                    StrongRuleViolation(
                        rule_name=rule_name,
                        filename=filename,
                        message=f"forbidden section present: {heading_str}",
                    )
                )
    return violations


def _evaluate_module_structure(
    rule_name: str,
    filename: str,
    rule: dict[str, object],
    context: dict[str, object],
) -> list[StrongRuleViolation]:
    project_root = context.get("project_root")
    if not isinstance(project_root, pathlib.Path):
        return []

    src_root = project_root / "src"
    if not src_root.is_dir():
        return [
            StrongRuleViolation(
                rule_name=rule_name,
                filename=filename,
                message=f"src/ directory missing under {project_root}",
            )
        ]

    violations: list[StrongRuleViolation] = []
    required_layout = rule.get("required_layout")
    if isinstance(required_layout, dict):
        src_required = required_layout.get("src_root")
        if isinstance(src_required, list):
            for rel in src_required:
                if isinstance(rel, str) and not (src_root / rel).exists():
                    violations.append(
                        StrongRuleViolation(
                            rule_name=rule_name,
                            filename=filename,
                            message=f"required src file missing: src/{rel}",
                        )
                    )

    forbidden_patterns = rule.get("forbidden_patterns")
    if isinstance(forbidden_patterns, list):
        for pattern in forbidden_patterns:
            if not isinstance(pattern, str):
                continue
            if "**/__pycache__/" in pattern:
                continue
            if "**/*.pyc" in pattern:
                continue
            basename = pattern.split("/")[-1]
            if basename.startswith("*."):
                ext = basename.removeprefix("*")
                for path in src_root.rglob("*"):
                    if not path.is_file() or "__pycache__" in path.parts:
                        continue
                    if path.name.endswith(ext):
                        violations.append(
                            StrongRuleViolation(
                                rule_name=rule_name,
                                filename=filename,
                                message=f"forbidden file pattern matched under src/: {pattern}",
                            )
                        )
                        break
            elif basename.endswith(".py"):
                if any(src_root.rglob(basename)):
                    violations.append(
                        StrongRuleViolation(
                            rule_name=rule_name,
                            filename=filename,
                            message=f"forbidden file matched under src/: {basename}",
                        )
                    )

    max_depth = rule.get("max_depth")
    if isinstance(max_depth, dict):
        limit = max_depth.get("src")
        if isinstance(limit, int):
            for path in src_root.rglob("*"):
                if path.is_file():
                    rel_parts = path.relative_to(src_root).parts
                    if len(rel_parts) > limit:
                        violations.append(
                            StrongRuleViolation(
                                rule_name=rule_name,
                                filename=filename,
                                message=(
                                    f"src file exceeds max depth {limit}: "
                                    f"{path.relative_to(project_root).as_posix()}"
                                ),
                            )
                        )
                        break
    return violations


def _evaluate_reference_schema(
    rule_name: str,
    filename: str,
    rule: dict[str, object],
    context: dict[str, object],
) -> list[StrongRuleViolation]:
    references = context.get("references")
    if not isinstance(references, list):
        return []

    required_fields = rule.get("required_fields")
    if not isinstance(required_fields, list):
        return []

    violations: list[StrongRuleViolation] = []
    for index, record in enumerate(references):
        if not isinstance(record, dict):
            violations.append(
                StrongRuleViolation(
                    rule_name=rule_name,
                    filename=filename,
                    message=f"reference[{index}] is not a mapping",
                )
            )
            continue
        for field in required_fields:
            if not isinstance(field, str):
                continue
            value = record.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                violations.append(
                    StrongRuleViolation(
                        rule_name=rule_name,
                        filename=filename,
                        message=f"reference[{index}] missing required field {field!r}",
                    )
                )
    return violations


def _evaluate_manifest_freshness(
    rule_name: str,
    filename: str,
    _rule: dict[str, object],
    context: dict[str, object],
) -> list[StrongRuleViolation]:
    """Flag a fond whose ``fonds.yaml`` was not touched despite its ``data/``
    files changing more recently — the manifest ``version`` field cannot have
    been bumped in step with a manifest mtime that predates the data change."""
    records = context.get("fond_freshness")
    if not isinstance(records, list):
        return []

    violations: list[StrongRuleViolation] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = record.get("name")
        manifest_mtime = record.get("manifest_mtime")
        latest_data_mtime = record.get("latest_data_mtime")
        if not isinstance(name, str):
            continue
        if not isinstance(manifest_mtime, (int, float)) or not isinstance(
            latest_data_mtime, (int, float)
        ):
            continue
        if latest_data_mtime > manifest_mtime:
            violations.append(
                StrongRuleViolation(
                    rule_name=rule_name,
                    filename=filename,
                    message=(
                        f"fond '{name}': data/ changed after fonds.yaml was last "
                        "modified — version field may need bumping"
                    ),
                )
            )
    return violations


def _normalize_heading(raw: str) -> str:
    heading = raw.removeprefix("# ").strip()
    return re.sub(r"\s*\{#.*\}\s*$", "", heading).strip()


def parse_bib_entries(bib_text: str) -> list[dict[str, object]]:
    """Parse a BibTeX string into a list of entry dicts (``key``, ``type``, fields).

    Deliberately simple line-oriented parser (no full BibTeX grammar); shared by
    ``load_rule_context_from_project()`` for ``reference_schema`` evaluation and by
    ``src/integration.py``'s cross-fond citation overlap check, so both consumers
    agree on exactly what counts as a cite key.
    """
    references: list[dict[str, object]] = []
    entry: dict[str, object] = {}
    for line in bib_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("@") and "{" in stripped:
            entry_type, _, remainder = stripped.partition("{")
            citekey = remainder.split(",", 1)[0].strip()
            entry = {"type": entry_type.strip("@").strip(), "key": citekey}
            continue
        if "=" in stripped and entry:
            field, _, value = stripped.partition("=")
            normalized = value.strip(" ,")
            field_name = field.strip()
            if field_name == "author":
                entry["authors"] = normalized
            else:
                entry[field_name] = normalized
        if stripped == "}" and entry:
            references.append(dict(entry))
            entry = {}
    return references


def _load_strong_rules_config(project_root: pathlib.Path) -> dict[str, object]:
    config_path = project_root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return {}
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        logger.warning("strong rules: could not parse %s", config_path)
        return {}
    if not isinstance(loaded, dict):
        return {}
    block = loaded.get("strong_rules")
    return block if isinstance(block, dict) else {}


def load_rule_context_from_project(project_root: pathlib.Path) -> dict[str, object]:
    """Build a default evaluation context for *project_root*."""
    manuscript_dir = project_root / "manuscript"
    config_block = _load_strong_rules_config(project_root)

    sections: list[str] = []
    if manuscript_dir.is_dir():
        for md_file in sorted(manuscript_dir.glob("*.md")):
            first_line = md_file.read_text(encoding="utf-8").splitlines()[:1]
            if first_line and first_line[0].startswith("# "):
                sections.append(_normalize_heading(first_line[0]))

    canonical = config_block.get("canonical_sections")
    if isinstance(canonical, list):
        for item in canonical:
            name = str(item).strip()
            if name and name not in sections:
                sections.append(name)

    references: list[dict[str, object]] = []
    bib_path = manuscript_dir / "references.bib"
    if bib_path.is_file():
        references = parse_bib_entries(bib_path.read_text(encoding="utf-8"))

    coverage = config_block.get("coverage")
    forbidden_set = {"TODO", "FIXME", "Draft", "PLACEHOLDER", "Scratch", "Notes"}
    context: dict[str, object] = {
        "project_root": project_root,
        "manuscript_sections": sections,
        "forbidden_sections_found": [name for name in sections if name in forbidden_set],
        "references": references,
    }
    if isinstance(coverage, dict):
        context["coverage"] = coverage
    return context
