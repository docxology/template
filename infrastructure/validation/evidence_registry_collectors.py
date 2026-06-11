"""Artifact collectors for :mod:`infrastructure.validation.evidence_registry`."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from infrastructure.validation.evidence_registry import EvidenceFact, VerifiedEvidenceRegistry

_BIBTEX_KEY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)")
_FIGURE_LABEL_RE = re.compile(r"#(fig:[A-Za-z0-9_:-]+)")
_TABLE_LABEL_RE = re.compile(r"#(tbl:[A-Za-z0-9_:-]+)")
_SECTION_LABEL_RE = re.compile(r"#(sec:[A-Za-z0-9_:-]+)")
_EQUATION_LABEL_RE = re.compile(r"#(eq:[A-Za-z0-9_:-]+)")
_LATEX_EQUATION_LABEL_RE = re.compile(r"\\label\{(eq:[A-Za-z0-9_:-]+)\}")


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
    config_paths = (
        project_root / "figures.yaml",
        project_root / "tracks.yaml",
        project_root / "manuscript" / "sheaf" / "tracks.yaml",
        project_root / "manuscript" / "sheaf" / "manifest.yaml",
        project_root / "manuscript" / "sheaf" / "coverage.yaml",
    )
    for yaml_path in config_paths:
        _register_numbers_from_yaml(yaml_path, project_root, registry)


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


def _register_json_numbers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    for json_path in _iter_existing(project_root / "data", "*.json"):
        if _is_claim_ledger_path(json_path):
            continue
        _register_numbers_from_json(json_path, project_root, registry)
    for json_path in _iter_existing(project_root / "output" / "data", "*.json"):
        if _is_claim_ledger_path(json_path):
            continue
        _register_numbers_from_json(json_path, project_root, registry)


def _register_claim_ledgers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    for root in (project_root / "data", project_root / "output" / "data", project_root / "manuscript"):
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
                    source_tier="generated_metric" if "output/data" in str(relative) else "data_source",
                )
            )


def _register_tabular_numbers(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    for root in (project_root / "data", project_root / "output" / "data", project_root / "output" / "reports"):
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
                    source_tier="generated_metric" if "output/data" in str(relative) else "data_source",
                )
            )


def _is_claim_ledger_path(path: Path) -> bool:
    return "claim" in path.name.lower() and "ledger" in path.name.lower()


def _register_bibtex_citations(project_root: Path, registry: VerifiedEvidenceRegistry) -> None:
    manuscript_dir = project_root / "manuscript"
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
    manuscript_dir = project_root / "manuscript"
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


def _canonical_number_token(value: str) -> str:
    return value.strip().replace(",", "")


def _is_numeric_cell(value: str) -> bool:
    return bool(re.fullmatch(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:e[+-]?\d+)?%?", value.strip(), re.I))


def _csv_source_field(header: list[str], row_index: int, col_index: int) -> str:
    if col_index < len(header) and header[col_index] and not _is_numeric_cell(header[col_index]):
        return f"row_{row_index}.{header[col_index]}"
    return f"row_{row_index}.col_{col_index}"


def _number_to_string(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:g}"
