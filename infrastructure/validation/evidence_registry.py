"""Verified evidence registry for manuscript-facing claims.

The registry is intentionally lightweight: it collects facts that already exist
in project artifacts and lets validation flag unsupported manuscript numbers,
citations, labels, and generated paths before publication.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

EVIDENCE_REGISTRY_REPORT_SCHEMA = "template-evidence-registry-report-v1"
EVIDENCE_REGISTRY_FULL_ENV = "TEMPLATE_EVIDENCE_REGISTRY_FULL"
DEFAULT_COMPACT_SAMPLE_LIMIT = 200


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
    line_number: int = 0


@dataclass(frozen=True)
class EvidenceValidationReport:
    """Unsupported claim-like tokens found in a manuscript text."""

    errors: list[EvidenceIssue] = field(default_factory=list)
    warnings: list[EvidenceIssue] = field(default_factory=list)

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

    def has(self, kind: str, value: str, *, fresh_only: bool = False) -> bool:
        """Return true when ``kind`` contains ``value``.

        With ``fresh_only`` set, stale or inactive facts (per the claim ledger)
        do not count as support — used to fail closed in strict zones.
        """
        return bool(self.lookup(kind, value, fresh_only=fresh_only))

    def lookup(self, kind: str, value: str, *, fresh_only: bool = False) -> tuple[EvidenceFact, ...]:
        """Return matching facts for a kind/value pair.

        When ``fresh_only`` is true only ``active`` and non-``stale`` facts are
        returned, so a stale claim-ledger fact stops validating downstream
        numbers/citations (AI-SPINE-V2 stale-fails-closed). The default
        (``False``) preserves the historical accept-any behaviour for callers
        such as the freshness report builder.
        """

        def _fresh(fact: EvidenceFact) -> bool:
            return fact.active and not fact.stale

        normalized = _normalize_number_value(value) if kind == "number" else _normalize_value(value)
        direct = tuple(self._facts.get(kind, {}).get(normalized, ()))
        if fresh_only:
            direct = tuple(f for f in direct if _fresh(f))
        if direct or kind != "number":
            return direct
        try:
            number = float(_canonical_number_token(value).rstrip("%"))
        except ValueError:
            return ()
        matches: list[EvidenceFact] = []
        for facts in self._facts.get(kind, {}).values():
            for fact in facts:
                if fresh_only and not _fresh(fact):
                    continue
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
            "freshness_warnings": _freshness_warnings(self.facts()),
        }

    def to_compact_dict(self, sample_limit: int = DEFAULT_COMPACT_SAMPLE_LIMIT) -> dict[str, Any]:
        """Serialize a bounded reviewer-facing summary of the registry."""
        facts = self.facts()
        bounded_limit = max(0, sample_limit)
        sample_facts = [asdict(fact) for fact in facts[:bounded_limit]]
        return {
            "schema": EVIDENCE_REGISTRY_REPORT_SCHEMA,
            "fact_count": len(facts),
            "kind_counts": _fact_kind_counts(facts),
            "source_tiers": _source_tier_counts(facts),
            "freshness_warnings": _freshness_warnings(facts),
            "sample_facts": sample_facts,
            "omitted_fact_count": max(0, len(facts) - len(sample_facts)),
            "claim_boundary": (
                "Compact evidence summary for manuscript validation; full fact dumps are opt-in debug output."
            ),
        }


def build_project_evidence_registry(project_root: Path) -> VerifiedEvidenceRegistry:
    """Build a verified evidence registry from project-local artifacts."""
    from infrastructure.validation.evidence_registry_collectors import register_all_project_facts

    registry = VerifiedEvidenceRegistry()
    register_all_project_facts(project_root, registry)
    return registry


def missing_evidence_source_paths(
    project_root: Path,
    registry: VerifiedEvidenceRegistry,
) -> tuple[str, ...]:
    """Return declared local evidence paths that no longer resolve on disk."""
    missing: set[str] = set()
    root = project_root.resolve()
    for fact in registry.facts():
        source_path = fact.source_path.strip()
        if not source_path:
            continue
        candidate = Path(source_path)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            missing.add(source_path)
            continue
        if not resolved.is_file():
            missing.add(source_path)
    return tuple(sorted(missing))


def validate_text_against_registry(
    text: str,
    registry: VerifiedEvidenceRegistry,
    *,
    strict: bool = False,
    trusted_number_tiers: frozenset[str] | None = None,
) -> EvidenceValidationReport:
    """Validate citation and number tokens in ``text`` against ``registry``.

    ``trusted_number_tiers`` (opt-in; ``None`` preserves the historical behavior of
    accepting a number that matches any registered fact): when provided, a number in
    a STRICT zone must match at least one fact whose ``source_tier`` is in the
    trusted set. This closes the self-referential gap where a manuscript number that
    traces ONLY to the run's own ``generated_metric`` outputs validated against
    itself; a caller passes e.g.
    ``frozenset({"bibliography", "data_source", "claim_ledger"})`` to require strict
    numbers to trace to an external/input/declared source rather than self-output.
    """
    errors: list[EvidenceIssue] = []
    warnings: list[EvidenceIssue] = []
    seen_numbers: set[str] = set()
    seen_citations: set[str] = set()

    current_zone = "lenient"
    in_code_fence = False
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
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
        claim_line = _strip_nonclaim_markdown(raw_line)
        line_citations = _CITATION_RE.findall(claim_line)
        bibliographic_table = line.startswith("|") and any(
            registry.has("citation", citation) for citation in line_citations
        )
        for raw_number in () if bibliographic_table else _NUMBER_RE.findall(claim_line):
            number = _canonical_number_token(raw_number)
            if number in seen_numbers or _is_always_allowed_number(number):
                continue
            seen_numbers.add(number)
            # In strict zones (and strict mode) a stale/inactive fact no longer
            # counts as support: a number backed only by a stale claim-ledger
            # entry fails closed (AI-SPINE-V2). Lenient zones stay tolerant.
            require_fresh = strict or line_zone == "strict"
            if not registry.has("number", number, fresh_only=require_fresh):
                bucket.append(
                    EvidenceIssue(
                        kind="number",
                        value=number,
                        severity=severity,
                        zone=line_zone,
                        line_number=line_number,
                    )
                )
            elif trusted_number_tiers is not None and line_zone == "strict":
                facts = registry.lookup("number", number, fresh_only=True)
                if facts and not any(fact.source_tier in trusted_number_tiers for fact in facts):
                    bucket.append(
                        EvidenceIssue(
                            kind="number",
                            value=number,
                            severity=severity,
                            zone=line_zone,
                            line_number=line_number,
                        )
                    )
        for citation in line_citations:
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
            elif citation.startswith("lst:"):
                supported = registry.has("listing", citation)
            else:
                supported = registry.has("citation", citation)
            if not supported:
                bucket.append(
                    EvidenceIssue(
                        kind="citation",
                        value=citation,
                        severity=severity,
                        zone=line_zone,
                        line_number=line_number,
                    )
                )
    return EvidenceValidationReport(
        errors=errors,
        warnings=warnings,
    )


def write_evidence_registry_report(project_output_dir: Path, registry: VerifiedEvidenceRegistry) -> Path:
    """Write compact ``output/reports/evidence_registry.json`` for inspection."""
    report_dir = project_output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "evidence_registry.json"
    payload = registry.to_compact_dict()
    _preserve_existing_checked_at(path, payload)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_optional_full_registry_report(report_dir, registry)
    return path


def _write_optional_full_registry_report(report_dir: Path, registry: VerifiedEvidenceRegistry) -> None:
    full_path = report_dir / "evidence_registry_full.json"
    if os.environ.get(EVIDENCE_REGISTRY_FULL_ENV) != "1":
        if full_path.exists():
            full_path.unlink()
        return
    payload = registry.to_dict()
    _preserve_existing_checked_at(full_path, payload)
    full_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _preserve_existing_checked_at(path: Path, payload: dict[str, Any]) -> None:
    existing = _existing_checked_at_by_fact(path)
    if not existing:
        return
    for row in _fact_rows(payload):
        checked_at = existing.get(_fact_identity(row))
        if checked_at:
            row["checked_at"] = checked_at


def _existing_checked_at_by_fact(path: Path) -> dict[tuple[str, str, str, str, str], str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    checked_at_by_fact: dict[tuple[str, str, str, str, str], str] = {}
    for row in _fact_rows(payload):
        checked_at = row.get("checked_at")
        if isinstance(checked_at, str) and checked_at:
            checked_at_by_fact.setdefault(_fact_identity(row), checked_at)
    return checked_at_by_fact


def _fact_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("facts", "sample_facts"):
        value = payload.get(key, [])
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def _fact_identity(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("kind", "")),
        str(row.get("value", "")),
        str(row.get("source", "")),
        str(row.get("source_path", "")),
        str(row.get("source_field", "")),
    )


_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_@.-])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?(?!(?:[A-Za-z0-9_-]|\.\d))")
_CITATION_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_:-]+)")
_MARKDOWN_LINK_DESTINATION_RE = re.compile(r"(!?\[[^\]]*\])\([^\n)]*\)")
_PANDOC_ATTRIBUTE_RE = re.compile(r"(?<=\))\{[^{}\n]*\}")
_AUTOLINK_RE = re.compile(r"<(?:(?:https?|ftp)://|www\.)[^>]+>", re.IGNORECASE)
_BARE_URL_RE = re.compile(r"(?:(?:https?|ftp)://|www\.)[^\s<>)]+", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
_CRYPTO_IDENTIFIER_RE = re.compile(r"\b(?:SHA3?|MD|BLAKE2?)-?\d+\b", re.IGNORECASE)
_LATEX_NUMERIC_SUBSCRIPT_RE = re.compile(r"(?<![A-Za-z0-9_:])([A-Za-z])_(?:\{\d+\}|\d+)")
_PANDOC_CITATION_BLOCK_RE = re.compile(r"\[(@[^\]]+)\]")
_CITATION_LOCATOR_RE = re.compile(r",\s*(?:pp?\.|chap\.|sec\.)\s*\d+(?:\s*[–-]\s*\d+)?", re.IGNORECASE)
_ORDERED_LIST_PREFIX_RE = re.compile(r"^\s*\d{1,4}[.)]\s+")
_STRICT_HEADINGS = frozenset({"abstract", "results", "evaluation", "findings", "experiments", "analysis"})
_LENIENT_HEADINGS = frozenset({"introduction", "background", "related work", "discussion", "conclusion"})
_ALWAYS_ALLOWED_NUMBERS = frozenset({"0", "1", "2", "3", "4", "5", "10", "100"})


def _normalize_value(value: str) -> str:
    return str(value).strip()


def _normalize_number_value(value: str) -> str:
    return _canonical_number_token(str(value))


def _strip_inline_code_spans(text: str) -> str:
    return re.sub(r"`[^`]*`", "", text)


def _strip_nonclaim_markdown(text: str) -> str:
    """Remove identifier-bearing Markdown syntax before claim tokenization.

    Link destinations, URLs, DOIs, and ordered-list counters contain digits but
    are identifiers or structure rather than quantitative claims. Visible link
    labels remain so actual prose claims are still checked.
    """
    stripped = _strip_inline_code_spans(text)
    stripped = _PANDOC_ATTRIBUTE_RE.sub("", stripped)
    stripped = _MARKDOWN_LINK_DESTINATION_RE.sub(r"\1", stripped)
    stripped = _AUTOLINK_RE.sub("", stripped)
    stripped = _BARE_URL_RE.sub("", stripped)
    stripped = _DOI_RE.sub("", stripped)
    stripped = _CRYPTO_IDENTIFIER_RE.sub("", stripped)
    stripped = _LATEX_NUMERIC_SUBSCRIPT_RE.sub(r"\1", stripped)
    stripped = _PANDOC_CITATION_BLOCK_RE.sub(
        lambda match: f"[{_CITATION_LOCATOR_RE.sub('', match.group(1))}]",
        stripped,
    )
    return _ORDERED_LIST_PREFIX_RE.sub("", stripped)


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


def _number_variants(value: str) -> tuple[str, ...]:
    variants = {str(value)}
    try:
        number = float(_canonical_number_token(str(value)).rstrip("%"))
    except ValueError:
        return (str(value),)
    # Manuscripts commonly report small generated measurements to five or
    # more decimal places.  Preserve the evidence link for those ordinary
    # rounded presentations without requiring authors to duplicate the
    # rounded value in a claim ledger.  Eight places is deliberately bounded:
    # it covers normal scientific presentation while avoiding an unbounded
    # family of near-equal tokens.
    for digits in range(1, 9):
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
    # A set is useful while constructing the bounded presentation variants, but
    # never expose its hash-dependent iteration order in a persisted registry.
    return tuple(sorted(variants))


def _source_tier_counts(facts: Iterable[EvidenceFact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        counts[fact.source_tier] = counts.get(fact.source_tier, 0) + 1
    return dict(sorted(counts.items()))


def _fact_kind_counts(facts: Iterable[EvidenceFact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        counts[fact.kind] = counts.get(fact.kind, 0) + 1
    return dict(sorted(counts.items()))


def _freshness_warnings(facts: Iterable[EvidenceFact]) -> list[dict[str, str]]:
    return [
        {
            "kind": fact.kind,
            "value": fact.value,
            "source": fact.source,
            "source_path": fact.source_path,
            "source_field": fact.source_field,
        }
        for fact in facts
        if fact.stale or not fact.active
    ]


def _zone_for_heading(line: str) -> str:
    heading = line.lstrip("#").strip().lower()
    if any(name in heading for name in _STRICT_HEADINGS):
        return "strict"
    if any(name in heading for name in _LENIENT_HEADINGS):
        return "lenient"
    return "lenient"


def unsupported_number_tokens(report: EvidenceValidationReport) -> list[str]:
    """Return numeric tokens flagged as unsupported in *report*."""
    return [issue.value for issue in (*report.errors, *report.warnings) if issue.kind == "number"]


def unsupported_citation_tokens(report: EvidenceValidationReport) -> list[str]:
    """Return citation tokens flagged as unsupported in *report*."""
    return [issue.value for issue in (*report.errors, *report.warnings) if issue.kind == "citation"]


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
