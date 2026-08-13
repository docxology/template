"""Source-bound contracts for the reusable textbook scaffold.

The textbook is intentionally configurable, but configuration and generated
teaching examples must not drift silently. This module keeps the checks small,
deterministic, and offline: it compares structure, verifies declared source
snippets, and audits generated Mermaid names without invoking a renderer.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _scalar_kind(value: Any) -> str:
    """Return a stable, schema-oriented scalar kind."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def compare_config_shapes(live: Any, example: Any, *, path: str = "$") -> tuple[str, ...]:
    """Return structural differences between live and example YAML values.

    Scalar values are deliberately ignored. Mapping keys and the shape of
    mapping-valued lists are checked. Scalar lists (keywords, languages, and
    similar author choices) may legitimately have different lengths.
    """
    differences: list[str] = []
    if isinstance(live, Mapping) and isinstance(example, Mapping):
        live_keys = set(live)
        example_keys = set(example)
        for key in sorted(live_keys - example_keys):
            differences.append(f"{path}.{key}: missing from example")
        for key in sorted(example_keys - live_keys):
            differences.append(f"{path}.{key}: missing from live config")
        for key in sorted(live_keys & example_keys):
            differences.extend(compare_config_shapes(live[key], example[key], path=f"{path}.{key}"))
        return tuple(differences)

    if isinstance(live, list) and isinstance(example, list):
        if not live and not example:
            return ()
        # Exactly one side is empty. A scalar list (keywords, languages, …)
        # may legitimately shrink to empty, but a mapping list that disappears
        # (or appears) is structural drift in a book configuration and must be
        # reported so live/example configs cannot silently diverge.
        if not live or not example:
            nonempty = live if live else example
            if all(isinstance(item, Mapping) for item in nonempty):
                differences.append(f"{path}: mapping-list length differs ({len(live)} != {len(example)})")
            return tuple(differences)
        live_mapping_items = all(isinstance(item, Mapping) for item in live)
        example_mapping_items = all(isinstance(item, Mapping) for item in example)
        if live_mapping_items != example_mapping_items:
            return (f"{path}: list item mapping shape differs",)
        if live_mapping_items:
            if len(live) != len(example):
                differences.append(f"{path}: mapping-list length differs ({len(live)} != {len(example)})")
            for index, (live_item, example_item) in enumerate(zip(live, example, strict=False)):
                differences.extend(compare_config_shapes(live_item, example_item, path=f"{path}[{index}]"))
        return tuple(differences)

    live_kind = "list" if isinstance(live, list) else _scalar_kind(live)
    example_kind = "list" if isinstance(example, list) else _scalar_kind(example)
    if live_kind != example_kind:
        differences.append(f"{path}: kind differs ({live_kind} != {example_kind})")
    return tuple(differences)


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML mapping for a contract file."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected a YAML mapping: {path}")
    return data


@dataclass(frozen=True)
class NumericFact:
    """One registered numeric source assertion."""

    fact_id: str
    source: str
    needle: str
    rationale: str
    status: str
    value: str | int | float | None = None


def load_numeric_facts(path: Path) -> tuple[NumericFact, ...]:
    """Load the versioned numeric-fact registry."""
    data = load_yaml_mapping(path)
    if data.get("schema_version") != "template-textbook-numeric-facts-v1":
        raise ValueError("unsupported numeric-facts schema version")
    rows = data.get("facts")
    if not isinstance(rows, list):
        raise ValueError("numeric-facts registry requires a facts list")
    facts: list[NumericFact] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("numeric-facts rows must be mappings")
        facts.append(
            NumericFact(
                fact_id=str(row.get("fact_id", "")),
                source=str(row.get("source", "")),
                needle=str(row.get("needle", "")),
                rationale=str(row.get("rationale", "")),
                status=str(row.get("status", "")),
                value=row.get("value"),
            )
        )
    return tuple(facts)


def validate_numeric_facts(path: Path, *, project_root: Path | None = None) -> tuple[str, ...]:
    """Validate registry rows and prove every bound snippet remains present."""
    registry_path = Path(path).resolve()
    root = Path(project_root).resolve() if project_root is not None else registry_path.parent.parent
    try:
        facts = load_numeric_facts(registry_path)
    except (OSError, ValueError) as exc:
        return (str(exc),)

    issues: list[str] = []
    seen: set[str] = set()
    allowed_statuses = {"bound", "documentation_only"}
    for fact in facts:
        if not fact.fact_id:
            issues.append("numeric fact has an empty fact_id")
        if fact.fact_id in seen:
            issues.append(f"duplicate numeric fact id: {fact.fact_id}")
        seen.add(fact.fact_id)
        if fact.status not in allowed_statuses:
            issues.append(f"{fact.fact_id}: unsupported status {fact.status!r}")
        if not fact.source or not fact.needle or not fact.rationale:
            issues.append(f"{fact.fact_id}: source, needle, and rationale are required")
            continue
        source_path = (root / fact.source).resolve()
        try:
            source_path.relative_to(root)
        except ValueError:
            issues.append(f"{fact.fact_id}: source escapes project root")
            continue
        if not source_path.is_file():
            issues.append(f"{fact.fact_id}: missing source {fact.source}")
            continue
        if fact.needle not in source_path.read_text(encoding="utf-8"):
            issues.append(f"{fact.fact_id}: registered source snippet is absent")
    if not facts:
        issues.append("numeric-facts registry must not be empty")
    return tuple(issues)


def numeric_fact_receipt(path: Path, *, project_root: Path | None = None) -> dict[str, Any]:
    """Return a deterministic receipt for a validated numeric-fact registry.

    When the registry cannot be loaded (missing file or unsupported schema) this
    still returns a receipt with ``status: "fail"`` and the reason in
    ``issues`` rather than raising — mirroring :func:`validate_numeric_facts`,
    so a single call path reports every failure mode deterministically.
    """
    issues = validate_numeric_facts(path, project_root=project_root)
    try:
        facts = load_numeric_facts(path)
    except (OSError, ValueError) as exc:
        facts = ()
        reason = str(exc)
        if reason not in issues:
            issues = (*issues, reason)
    canonical = [
        {
            "fact_id": fact.fact_id,
            "source": fact.source,
            "needle": fact.needle,
            "rationale": fact.rationale,
            "status": fact.status,
            "value": fact.value,
        }
        for fact in facts
    ]
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema_version": "template-textbook-numeric-fact-receipt-v1",
        "registry": Path(path).name,
        "fact_count": len(facts),
        "digest": digest,
        "status": "pass" if not issues else "fail",
        "issues": list(issues),
    }


def validate_diagram_inventory(specs: list[Mapping[str, Any]], output_dir: Path | None = None) -> tuple[str, ...]:
    """Check Mermaid spec names and, optionally, generated output names.

    A generated ``.mmd`` fallback or a rendered ``.png`` satisfies a spec. Any
    other file in the generated directory is stale and should not be shipped.
    """
    issues: list[str] = []
    names: list[str] = []
    for index, spec in enumerate(specs):
        name = spec.get("name")
        if not isinstance(name, str) or not name or "/" in name or "\\" in name:
            issues.append(f"diagram spec {index} has an unsafe or empty name")
            continue
        if name in names:
            issues.append(f"duplicate diagram name: {name}")
        names.append(name)
        if not isinstance(spec.get("kind"), str) or not spec["kind"]:
            issues.append(f"diagram {name}: kind is required")

    if output_dir is not None:
        generated_dir = Path(output_dir)
        actual: set[str] = set()
        if generated_dir.exists():
            for path in generated_dir.iterdir():
                if path.is_file() and path.suffix in {".mmd", ".png"}:
                    actual.add(path.stem)
        expected = set(names)
        issues.extend(f"missing generated diagram: {name}" for name in sorted(expected - actual))
        issues.extend(f"stale generated diagram: {name}" for name in sorted(actual - expected))
    if not names:
        issues.append("diagram inventory must not be empty")
    return tuple(issues)


__all__ = [
    "NumericFact",
    "compare_config_shapes",
    "load_numeric_facts",
    "load_yaml_mapping",
    "numeric_fact_receipt",
    "validate_diagram_inventory",
    "validate_numeric_facts",
]
