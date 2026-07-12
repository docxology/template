"""Artifact collectors for :mod:`infrastructure.validation.evidence_registry`."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by the Python 3.10 CI lane
    import tomli as tomllib  # type: ignore[no-redef]

from infrastructure.core.project_paths import resolve_source_manuscript_dir
from infrastructure.validation.evidence_registry import (
    EvidenceFact,
    VerifiedEvidenceRegistry,
    _canonical_number_token,
    _csv_source_field,
    _is_numeric_cell,
    _number_to_string,
)

_BIBTEX_KEY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)")
_FIGURE_LABEL_RE = re.compile(r"#(fig:[A-Za-z0-9_:-]+)")
_TABLE_LABEL_RE = re.compile(r"#(tbl:[A-Za-z0-9_:-]+)")
_SECTION_LABEL_RE = re.compile(r"#(sec:[A-Za-z0-9_:-]+)")
_EQUATION_LABEL_RE = re.compile(r"#(eq:[A-Za-z0-9_:-]+)")
_LISTING_LABEL_RE = re.compile(r"#(lst:[A-Za-z0-9_:-]+)")
_LATEX_EQUATION_LABEL_RE = re.compile(r"\\label\{(eq:[A-Za-z0-9_:-]+)\}")
_VERSION_NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)+(?![\w.])")
_CONTROL_REPORT_NAMES = frozenset(
    {
        "artifact_manifest.json",
        "evidence_registry.json",
        "evidence_registry_full.json",
        "figure_registry.json",
        "validation_report.json",
    }
)


def register_all_project_facts(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    """Register facts from all known project-local artifact surfaces."""
    project_root = project_root.resolve()
    _register_config_numbers(project_root, registry)
    _register_json_numbers(project_root, registry)
    _register_tabular_numbers(project_root, registry)
    _register_claim_ledgers(project_root, registry)
    _register_bibtex_citations(project_root, registry)
    _register_markdown_labels(project_root, registry)
    _register_output_artifacts(project_root, registry)


def _register_config_numbers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    """Register numeric facts from manuscript-facing project configuration."""
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    config_paths = {
        project_root / "figures.yaml",
        project_root / "tracks.yaml",
        manuscript_dir / "config.yaml",
        manuscript_dir / "sheaf" / "tracks.yaml",
        manuscript_dir / "sheaf" / "manifest.yaml",
        manuscript_dir / "sheaf" / "coverage.yaml",
    }
    for root in (project_root / "content", project_root / "data"):
        for pattern in ("*.yaml", "*.yml"):
            config_paths.update(_iter_existing(root, pattern))
    for yaml_path in sorted(config_paths):
        _register_numbers_from_yaml(yaml_path, project_root, registry)
    for toml_path in (project_root / "pyproject.toml", manuscript_dir / "config.toml"):
        _register_numbers_from_toml(toml_path, project_root, registry)


def _register_numbers_from_yaml(
    yaml_path: Path,
    project_root: Path,
    registry: VerifiedEvidenceRegistry,
) -> None:
    if not yaml_path.exists():
        return
    try:
        payload = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return
    relative = _relative_to_project(yaml_path, project_root)
    for value_path, value in _walk_json(payload):
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            registry.add(
                EvidenceFact(
                    kind="number",
                    value=_number_to_string(value),
                    source=f"{relative}:{value_path}",
                    source_path=str(relative),
                    source_field=value_path,
                    source_tier="configuration",
                )
            )


def _register_numbers_from_toml(
    toml_path: Path,
    project_root: Path,
    registry: VerifiedEvidenceRegistry,
) -> None:
    """Register numeric policy values and the declared Python version."""
    if not toml_path.exists():
        return
    try:
        payload = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return
    relative = _relative_to_project(toml_path, project_root)
    for value_path, value in _walk_json(payload):
        values: list[str] = []
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            values.append(_number_to_string(value))
        elif value_path == "$.project.requires-python" and isinstance(value, str):
            values.extend(_VERSION_NUMBER_RE.findall(value))
        for numeric_value in values:
            registry.add(
                EvidenceFact(
                    kind="number",
                    value=numeric_value,
                    source=f"{relative}:{value_path}",
                    source_path=str(relative),
                    source_field=value_path,
                    source_tier="configuration",
                )
            )


def _register_json_numbers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    for json_path in _iter_existing(project_root / "data", "*.json"):
        if _is_claim_ledger_path(json_path):
            continue
        _register_numbers_from_json(json_path, project_root, registry)
    output_dir = project_root / "output"
    for json_path in _iter_existing(output_dir, "*.json"):
        if _is_claim_ledger_path(json_path) or not _is_output_evidence_json(json_path, output_dir):
            continue
        _register_numbers_from_json(json_path, project_root, registry)


def _is_output_evidence_json(path: Path, output_dir: Path) -> bool:
    """Return whether an output JSON file is a domain artifact, not a control report."""
    try:
        relative = path.relative_to(output_dir)
    except ValueError:
        return False
    return ".pipeline" not in relative.parts and path.name not in _CONTROL_REPORT_NAMES


def _register_claim_ledgers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    for root in (project_root / "data", project_root / "output" / "data", manuscript_dir):
        for ledger_path in _iter_existing(root, "*claim*ledger*.json"):
            _register_claim_ledger(ledger_path, project_root, registry)
        for ledger_path in _iter_existing(root, "*claim*ledger*.yaml"):
            _register_claim_ledger(ledger_path, project_root, registry)
        for ledger_path in _iter_existing(root, "*claim*ledger*.yml"):
            _register_claim_ledger(ledger_path, project_root, registry)


def _register_claim_ledger(
    ledger_path: Path,
    project_root: Path,
    registry: VerifiedEvidenceRegistry,
) -> None:
    try:
        if ledger_path.suffix == ".json":
            payload = json.loads(ledger_path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError):
        return
    claims = payload.get("claims", payload) if isinstance(payload, dict) else payload
    if not isinstance(claims, list):
        return
    relative = _relative_to_project(ledger_path, project_root)
    for row in claims:
        if not isinstance(row, dict):
            continue
        value = row.get("value")
        claim_id = str(row.get("claim_id", "") or row.get("id", "") or "")
        if value is None or not claim_id:
            continue
        kind = str(row.get("kind", "") or ("number" if isinstance(value, int | float) else "citation"))
        freshness = str(row.get("freshness", "active") or "active").lower()
        artifact_path = str(row.get("artifact_path", "") or row.get("source_path", "") or relative)
        registry.add(
            EvidenceFact(
                kind=kind,
                value=_number_to_string(value)
                if isinstance(value, int | float) and not isinstance(value, bool)
                else str(value),
                source=str(row.get("source", "") or f"{relative}:{claim_id}"),
                source_path=artifact_path,
                source_field=claim_id,
                source_tier=str(row.get("source_tier", "") or "claim_ledger"),
                active=freshness not in {"inactive", "retired"},
                stale=freshness in {"stale", "expired", "outdated"},
            )
        )


def _register_numbers_from_json(
    json_path: Path,
    project_root: Path,
    registry: VerifiedEvidenceRegistry,
) -> None:
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    relative = _relative_to_project(json_path, project_root)
    for value_path, value in _walk_json(payload):
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            registry.add(
                EvidenceFact(
                    kind="number",
                    value=_number_to_string(value),
                    source=f"{relative}:{value_path}",
                    source_path=str(relative),
                    source_field=value_path,
                    source_tier="generated_metric" if relative.parts[:1] == ("output",) else "data_source",
                )
            )


def _register_tabular_numbers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    for root in (
        project_root / "data",
        manuscript_dir / "assets" / "data",
        project_root / "output" / "data",
        project_root / "output" / "reports",
    ):
        for csv_path in _iter_existing(root, "*.csv"):
            _register_numbers_from_csv(csv_path, project_root, registry)


def _register_numbers_from_csv(csv_path: Path, project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
    except OSError:
        return
    if not rows:
        return
    header = rows[0]
    data_rows = rows[1:] if any(not _is_numeric_cell(cell) for cell in header) else rows
    relative = _relative_to_project(csv_path, project_root)
    for row_index, row in enumerate(data_rows, start=1):
        for col_index, cell in enumerate(row):
            if not _is_numeric_cell(cell):
                continue
            source_field = _csv_source_field(header, row_index, col_index)
            registry.add(
                EvidenceFact(
                    kind="number",
                    value=_canonical_number_token(cell.strip()),
                    source=f"{relative}:{source_field}",
                    source_path=str(relative),
                    source_field=source_field,
                    source_tier="generated_metric" if relative.parts[:1] == ("output",) else "data_source",
                )
            )


def _is_claim_ledger_path(path: Path) -> bool:
    return "claim" in path.name.lower() and "ledger" in path.name.lower()


def _register_bibtex_citations(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    for bib_path in _iter_existing(manuscript_dir, "*.bib"):
        try:
            text = bib_path.read_text(encoding="utf-8")
        except OSError:
            continue
        relative = _relative_to_project(bib_path, project_root)
        for key in _BIBTEX_KEY_RE.findall(text):
            registry.add(
                EvidenceFact(
                    kind="citation",
                    value=key,
                    source=str(relative),
                    source_path=str(relative),
                    source_tier="bibliography",
                )
            )


def _register_markdown_labels(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    manuscript_dir = resolve_source_manuscript_dir(project_root)
    for markdown_path in _iter_existing(manuscript_dir, "*.md"):
        try:
            text = markdown_path.read_text(encoding="utf-8")
        except OSError:
            continue
        relative = _relative_to_project(markdown_path, project_root)
        for label in _FIGURE_LABEL_RE.findall(text):
            registry.add(EvidenceFact(kind="figure", value=label, source=str(relative), source_path=str(relative)))
        for label in _TABLE_LABEL_RE.findall(text):
            registry.add(EvidenceFact(kind="table", value=label, source=str(relative), source_path=str(relative)))
        for label in _SECTION_LABEL_RE.findall(text):
            registry.add(EvidenceFact(kind="section", value=label, source=str(relative), source_path=str(relative)))
        for label in [*_EQUATION_LABEL_RE.findall(text), *_LATEX_EQUATION_LABEL_RE.findall(text)]:
            registry.add(EvidenceFact(kind="equation", value=label, source=str(relative), source_path=str(relative)))
        for label in _LISTING_LABEL_RE.findall(text):
            registry.add(EvidenceFact(kind="listing", value=label, source=str(relative), source_path=str(relative)))


def _register_output_artifacts(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    output_dir = project_root / "output"
    if not output_dir.exists():
        return
    for artifact in output_dir.rglob("*"):
        if artifact.is_file():
            relative = _relative_to_project(artifact, project_root)
            registry.add(
                EvidenceFact(kind="artifact", value=str(relative), source="filesystem", source_path=str(relative))
            )
            if "figures" in relative.parts:
                registry.add(
                    EvidenceFact(
                        kind="figure", value=f"fig:{artifact.stem}", source=str(relative), source_path=str(relative)
                    )
                )
            if "tables" in relative.parts:
                registry.add(
                    EvidenceFact(
                        kind="table", value=f"tbl:{artifact.stem}", source=str(relative), source_path=str(relative)
                    )
                )


def _iter_existing(root: Path, pattern: str) -> Iterable[Path]:
    if not root.exists():
        return ()
    return root.rglob(pattern)


def _walk_json(payload: Any, prefix: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield from _walk_json(value, f"{prefix}.{key}")
        return
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            yield from _walk_json(value, f"{prefix}[{index}]")
        return
    yield prefix, payload


def _relative_to_project(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path
