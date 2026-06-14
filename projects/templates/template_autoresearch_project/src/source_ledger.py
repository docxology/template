"""Offline source-ledger validation for the AutoResearch survey citations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any

import yaml

SOURCE_LEDGER_SCHEMA = "template-autoresearch-source-ledger-v1"
ALLOWED_SOURCE_TIERS = frozenset(
    {
        "conference_proceeding",
        "organizational_announcement",
        "peer_reviewed_article",
        "scholarly_preprint",
    }
)


@dataclass(frozen=True)
class SourceLedgerEntry:
    """One offline-audited citation source record."""

    citekey: str
    canonical_url: str
    source_tier: str
    checked_as_of: date

    def to_dict(self) -> dict[str, str]:
        """Serialize to a stable mapping."""
        return {
            "citekey": self.citekey,
            "canonical_url": self.canonical_url,
            "source_tier": self.source_tier,
            "checked_as_of": self.checked_as_of.isoformat(),
        }


def load_source_ledger(path: Path, *, today: date | None = None) -> tuple[SourceLedgerEntry, ...]:
    """Load and validate a source ledger without network access."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"source ledger root must be a mapping: {path}")
    schema = payload.get("schema", SOURCE_LEDGER_SCHEMA)
    if schema != SOURCE_LEDGER_SCHEMA:
        raise ValueError(f"source ledger schema must be {SOURCE_LEDGER_SCHEMA}")
    rows = payload.get("sources", [])
    if not isinstance(rows, list):
        raise ValueError("source ledger sources must be a list")
    seen: set[str] = set()
    entries: list[SourceLedgerEntry] = []
    resolved_today = today or date.today()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"source ledger row {index} must be a mapping")
        entry = _entry_from_row(row, index=index, today=resolved_today)
        if entry.citekey in seen:
            raise ValueError(f"duplicate source ledger citekey: {entry.citekey}")
        seen.add(entry.citekey)
        entries.append(entry)
    return tuple(entries)


def source_ledger_citekeys(path: Path) -> tuple[str, ...]:
    """Return the validated citekeys in ledger order."""
    return tuple(entry.citekey for entry in load_source_ledger(path))


def source_tier_counts(entries: tuple[SourceLedgerEntry, ...]) -> dict[str, int]:
    """Return source-tier counts for offline audit reporting."""
    counts = {tier: 0 for tier in sorted(ALLOWED_SOURCE_TIERS)}
    for entry in entries:
        counts[entry.source_tier] = counts.get(entry.source_tier, 0) + 1
    return {tier: count for tier, count in counts.items() if count}


def source_age_summary(entries: tuple[SourceLedgerEntry, ...], *, today: date | None = None) -> dict[str, int]:
    """Return coarse checked-age buckets for reviewer-facing reports."""
    resolved_today = today or date.today()
    buckets = {"0-180d": 0, "181-365d": 0, "366d+": 0}
    for entry in entries:
        age_days = max((resolved_today - entry.checked_as_of).days, 0)
        if age_days <= 180:
            buckets["0-180d"] += 1
        elif age_days <= 365:
            buckets["181-365d"] += 1
        else:
            buckets["366d+"] += 1
    return {bucket: count for bucket, count in buckets.items() if count}


def validate_source_ledger_contract(project_root: Path, *, today: date | None = None) -> list[str]:
    """Validate the project-local source ledger against offline manuscript evidence."""
    root = project_root.resolve()
    ledger_path = root / "manuscript" / "source_ledger.yaml"
    try:
        entries = load_source_ledger(ledger_path, today=today)
    except ValueError as exc:
        return [str(exc)]
    ledger_keys = {entry.citekey for entry in entries}
    bib_keys = _bibtex_citekeys(root / "manuscript" / "references.bib")
    manuscript_keys = _manuscript_citekeys(root / "manuscript")
    issues: list[str] = []
    missing_bib = sorted(ledger_keys - bib_keys)
    if missing_bib:
        issues.append(f"source ledger citekeys missing from references.bib: {', '.join(missing_bib)}")
    uncited = sorted(ledger_keys - manuscript_keys)
    if uncited:
        issues.append(f"source ledger citekeys not cited in manuscript: {', '.join(uncited)}")
    return issues


def _bibtex_citekeys(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(re.findall(r"@\w+\{([^,\s]+)", path.read_text(encoding="utf-8")))


def _manuscript_citekeys(manuscript_dir: Path) -> set[str]:
    keys: set[str] = set()
    for path in manuscript_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        keys.update(match for match in re.findall(r"(?<![A-Za-z0-9_:-])@([A-Za-z0-9_:-]+)", text))
    return {key for key in keys if not key.startswith("sec:")}


def _entry_from_row(row: dict[str, Any], *, index: int, today: date) -> SourceLedgerEntry:
    citekey = str(row.get("citekey", "") or "").strip()
    canonical_url = str(row.get("canonical_url", "") or "").strip()
    source_tier = str(row.get("source_tier", "") or "").strip()
    checked_text = str(row.get("checked_as_of", "") or "").strip()
    if not citekey:
        raise ValueError(f"source ledger row {index} is missing citekey")
    if not canonical_url.startswith("https://"):
        raise ValueError(f"source ledger row {citekey} must use an HTTPS canonical_url")
    if source_tier not in ALLOWED_SOURCE_TIERS:
        allowed = ", ".join(sorted(ALLOWED_SOURCE_TIERS))
        raise ValueError(f"source ledger row {citekey} source_tier must be one of: {allowed}")
    try:
        checked_as_of = date.fromisoformat(checked_text)
    except ValueError as exc:
        raise ValueError(f"source ledger row {citekey} checked_as_of must be an ISO date") from exc
    if checked_as_of > today:
        raise ValueError(f"source ledger row {citekey} checked_as_of is future-dated")
    return SourceLedgerEntry(
        citekey=citekey,
        canonical_url=canonical_url,
        source_tier=source_tier,
        checked_as_of=checked_as_of,
    )
