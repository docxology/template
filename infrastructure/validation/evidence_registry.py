"""Verified evidence registry for manuscript-facing claims.

The registry is intentionally lightweight: it collects facts that already exist
in project artifacts and lets validation flag unsupported manuscript numbers,
citations, labels, and generated paths before publication.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class EvidenceFact:
    """One registered fact with enough provenance to debug drift."""

    kind: str
    value: str
    source: str
    source_path: str = ""
    source_field: str = ""
    source_tier: str = "artifact"
    tolerance: float = 0.0
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    active: bool = True
    stale: bool = False


@dataclass(frozen=True)
class EvidenceIssue:
    """One unsupported manuscript evidence token."""

    kind: str
    value: str
    severity: str
    zone: str


@dataclass(frozen=True)
class EvidenceValidationReport:
    """Unsupported claim-like tokens found in a manuscript text."""

    errors: list[EvidenceIssue] = field(default_factory=list)
    warnings: list[EvidenceIssue] = field(default_factory=list)

    @property
    def unsupported_numbers(self) -> list[str]:
        """Backward-compatible list of unsupported numeric tokens."""
        return [issue.value for issue in [*self.errors, *self.warnings] if issue.kind == "number"]

    @property
    def unsupported_citations(self) -> list[str]:
        """Backward-compatible list of unsupported citation tokens."""
        return [issue.value for issue in [*self.errors, *self.warnings] if issue.kind == "citation"]

    @property
    def has_issues(self) -> bool:
        """Return true when validation found unsupported evidence tokens."""
        return bool(self.errors or self.warnings)

    @property
    def has_errors(self) -> bool:
        """Return true when validation found strict-zone unsupported evidence."""
        return bool(self.errors)


class VerifiedEvidenceRegistry:
    """In-memory registry keyed by fact kind and normalized value."""

    def __init__(self, facts: Iterable[EvidenceFact] | None = None) -> None:
        self._facts: dict[str, dict[str, list[EvidenceFact]]] = {}
        for fact in facts or ():
            self.add(fact)

    def add(self, fact: EvidenceFact) -> None:
        """Add a fact to the registry."""
        self._add_exact(fact)
        if fact.kind == "number":
            for variant in _number_variants(fact.value):
                if variant != fact.value:
                    self._add_exact(
                        EvidenceFact(
                            kind=fact.kind,
                            value=variant,
                            source=f"{fact.source} (numeric variant)",
                            source_path=fact.source_path,
                            source_field=fact.source_field,
                            source_tier=fact.source_tier,
                            tolerance=fact.tolerance,
                            checked_at=fact.checked_at,
                            active=fact.active,
                            stale=fact.stale,
                        )
                    )

    def _add_exact(self, fact: EvidenceFact) -> None:
        normalized = _normalize_number_value(fact.value) if fact.kind == "number" else _normalize_value(fact.value)
        self._facts.setdefault(fact.kind, {}).setdefault(normalized, []).append(fact)

    def has(self, kind: str, value: str) -> bool:
        """Return true when ``kind`` contains ``value``."""
        return bool(self.lookup(kind, value))

    def lookup(self, kind: str, value: str) -> tuple[EvidenceFact, ...]:
        """Return matching facts for a kind/value pair."""
        normalized = _normalize_number_value(value) if kind == "number" else _normalize_value(value)
        direct = tuple(self._facts.get(kind, {}).get(normalized, ()))
        if direct or kind != "number":
            return direct
        try:
            number = float(_canonical_number_token(value).rstrip("%"))
        except ValueError:
            return ()
        matches: list[EvidenceFact] = []
        for facts in self._facts.get(kind, {}).values():
            for fact in facts:
                try:
                    candidate = float(fact.value.rstrip("%"))
                except ValueError:
                    continue
                tolerance = fact.tolerance or 0.0000001
                if abs(number - candidate) <= tolerance:
                    matches.append(fact)
        return tuple(matches)

    def facts(self, kind: str | None = None) -> tuple[EvidenceFact, ...]:
        """Return all facts, optionally filtered by kind."""
        if kind is not None:
            return tuple(fact for facts in self._facts.get(kind, {}).values() for fact in facts)
        return tuple(
            fact for values_by_kind in self._facts.values() for facts in values_by_kind.values() for fact in facts
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the registry into a JSON-safe payload."""
        facts = [asdict(fact) for fact in self.facts()]
        return {
            "facts": facts,
            "source_tiers": _source_tier_counts(self.facts()),
            "freshness_warnings": [
                {
                    "kind": fact.kind,
                    "value": fact.value,
                    "source": fact.source,
                    "source_path": fact.source_path,
                    "source_field": fact.source_field,
                }
                for fact in self.facts()
                if fact.stale or not fact.active
            ],
        }


def build_project_evidence_registry(project_root: Path) -> VerifiedEvidenceRegistry:
    """Build a verified evidence registry from project-local artifacts."""
    registry = VerifiedEvidenceRegistry()
    project_root = project_root.resolve()

    _register_json_numbers(project_root, registry)
    _register_tabular_numbers(project_root, registry)
    _register_claim_ledgers(project_root, registry)
    _register_bibtex_citations(project_root, registry)
    _register_markdown_labels(project_root, registry)
    _register_output_artifacts(project_root, registry)
    return registry


def validate_text_against_registry(
    text: str,
    registry: VerifiedEvidenceRegistry,
    *,
    strict: bool = False,
) -> EvidenceValidationReport:
    """Validate citation and number tokens in ``text`` against ``registry``."""
    errors: list[EvidenceIssue] = []
    warnings: list[EvidenceIssue] = []
    seen_numbers: set[str] = set()
    seen_citations: set[str] = set()

    current_zone = "lenient"
    in_code_fence = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(("```", "~~~")):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if line.startswith("#"):
            current_zone = _zone_for_heading(line)
        line_zone = "strict" if current_zone == "strict" or _looks_strict_line(line) else current_zone
        severity = "error" if strict or line_zone == "strict" else "warning"
        bucket = errors if severity == "error" else warnings
        claim_line = _strip_inline_code_spans(raw_line)
        for raw_number in _NUMBER_RE.findall(claim_line):
            number = _canonical_number_token(raw_number)
            if number in seen_numbers or _is_always_allowed_number(number):
                continue
            seen_numbers.add(number)
            if not registry.has("number", number):
                bucket.append(EvidenceIssue(kind="number", value=number, severity=severity, zone=line_zone))
        for citation in _CITATION_RE.findall(claim_line):
            if citation in seen_citations:
                continue
            seen_citations.add(citation)
            if citation.startswith("fig:"):
                supported = registry.has("figure", citation) or registry.has("table", citation)
            elif citation.startswith("tbl:"):
                supported = registry.has("table", citation)
            elif citation.startswith("sec:"):
                supported = registry.has("section", citation)
            elif citation.startswith("eq:"):
                supported = registry.has("equation", citation)
            else:
                supported = registry.has("citation", citation)
            if not supported:
                bucket.append(EvidenceIssue(kind="citation", value=citation, severity=severity, zone=line_zone))
    return EvidenceValidationReport(
        errors=errors,
        warnings=warnings,
    )


def write_evidence_registry_report(project_output_dir: Path, registry: VerifiedEvidenceRegistry) -> Path:
    """Write ``output/reports/evidence_registry.json`` for inspection."""
    report_dir = project_output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "evidence_registry.json"
    path.write_text(json.dumps(registry.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_@.-])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?(?![A-Za-z0-9_.-])")
_CITATION_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_:-]+)")
_BIBTEX_KEY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)")
_FIGURE_LABEL_RE = re.compile(r"#(fig:[A-Za-z0-9_:-]+)")
_TABLE_LABEL_RE = re.compile(r"#(tbl:[A-Za-z0-9_:-]+)")
_SECTION_LABEL_RE = re.compile(r"#(sec:[A-Za-z0-9_:-]+)")
_EQUATION_LABEL_RE = re.compile(r"#(eq:[A-Za-z0-9_:-]+)")
_LATEX_EQUATION_LABEL_RE = re.compile(r"\\label\{(eq:[A-Za-z0-9_:-]+)\}")
_STRICT_HEADINGS = frozenset({"abstract", "results", "evaluation", "findings", "experiments", "analysis"})
_LENIENT_HEADINGS = frozenset({"introduction", "background", "related work", "discussion", "conclusion"})
_ALWAYS_ALLOWED_NUMBERS = frozenset({"0", "1", "2", "3", "4", "5", "10", "100"})


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


def _unique_in_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _relative_to_project(path: Path, project_root: Path) -> Path:
    try:
        return path.relative_to(project_root)
    except ValueError:
        return path


def _normalize_value(value: str) -> str:
    return str(value).strip()


def _normalize_number_value(value: str) -> str:
    return _canonical_number_token(str(value))


def _strip_inline_code_spans(text: str) -> str:
    return re.sub(r"`[^`]*`", "", text)


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


def _number_variants(value: str) -> set[str]:
    variants = {str(value)}
    try:
        number = float(_canonical_number_token(str(value)).rstrip("%"))
    except ValueError:
        return variants
    for digits in (1, 2, 3, 4):
        variants.add(f"{number:.{digits}f}".rstrip("0").rstrip("."))
    if 0 < abs(number) <= 1:
        percent = number * 100
        variants.add(f"{percent:g}")
        variants.add(f"{percent:g}%")
        for digits in (1, 2):
            variants.add(f"{percent:.{digits}f}".rstrip("0").rstrip("."))
            variants.add(f"{percent:.{digits}f}".rstrip("0").rstrip(".") + "%")
    if abs(number) > 1:
        variants.add(f"{number / 100:g}")
    return variants


def _source_tier_counts(facts: Iterable[EvidenceFact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        counts[fact.source_tier] = counts.get(fact.source_tier, 0) + 1
    return counts


def _zone_for_heading(line: str) -> str:
    heading = line.lstrip("#").strip().lower()
    if any(name in heading for name in _STRICT_HEADINGS):
        return "strict"
    if any(name in heading for name in _LENIENT_HEADINGS):
        return "lenient"
    return "lenient"


def _looks_strict_line(line: str) -> bool:
    lower = line.lower()
    return line.startswith("|") or lower.startswith(("table:", "figure:", "caption:", "fig.", "table "))


def _is_always_allowed_number(value: str) -> bool:
    stripped = value.rstrip("%")
    if stripped in _ALWAYS_ALLOWED_NUMBERS:
        return True
    try:
        number = float(stripped)
    except ValueError:
        return False
    return 1900 <= number <= 2100
