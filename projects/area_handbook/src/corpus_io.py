"""Load and validate area corpus from YAML or JSON."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import yaml

from .models import AreaCorpus, EvidenceItem, Theme


class CorpusValidationError(ValueError):
    """Raised when corpus data fails structural or semantic checks."""


def _require_keys(obj: Mapping[str, Any], keys: set[str], ctx: str) -> None:
    missing = keys - obj.keys()
    if missing:
        raise CorpusValidationError(f"{ctx}: missing keys {sorted(missing)}")


def _parse_theme(raw: Mapping[str, Any], idx: int) -> Theme:
    _require_keys(raw, {"id", "label", "description"}, f"themes[{idx}]")
    tid = str(raw["id"]).strip()
    if not tid:
        raise CorpusValidationError(f"themes[{idx}]: empty id")
    label = str(raw["label"]).strip()
    desc = str(raw["description"]).strip()
    if not label:
        raise CorpusValidationError(f"themes[{idx}]: empty label")
    if not desc:
        raise CorpusValidationError(f"themes[{idx}]: empty description")
    return Theme(
        id=tid,
        label=label,
        description=desc,
    )


def _parse_evidence(raw: Mapping[str, Any], idx: int, theme_ids: set[str]) -> EvidenceItem:
    _require_keys(
        raw,
        {"id", "statement", "theme", "weight", "source_label", "reviewed_at"},
        f"evidence[{idx}]",
    )
    eid = str(raw["id"]).strip()
    if not eid:
        raise CorpusValidationError(f"evidence[{idx}]: empty id")
    statement = str(raw["statement"]).strip()
    if not statement:
        raise CorpusValidationError(f"evidence[{idx}]: empty statement")
    source_label = str(raw["source_label"]).strip()
    if not source_label:
        raise CorpusValidationError(f"evidence[{idx}]: empty source_label")
    reviewed = str(raw["reviewed_at"]).strip()
    if not reviewed:
        raise CorpusValidationError(f"evidence[{idx}]: empty reviewed_at")
    theme = str(raw["theme"]).strip()
    if theme not in theme_ids:
        raise CorpusValidationError(
            f"evidence[{idx}]: unknown theme {theme!r}; valid: {sorted(theme_ids)}"
        )
    try:
        weight = float(raw["weight"])
    except (TypeError, ValueError) as e:
        raise CorpusValidationError(f"evidence[{idx}]: invalid weight {raw['weight']!r}") from e
    if math.isnan(weight) or math.isinf(weight):
        raise CorpusValidationError(f"evidence[{idx}]: weight must be finite, got {weight}")
    if weight < 0.0 or weight > 1.0:
        raise CorpusValidationError(f"evidence[{idx}]: weight must be in [0, 1], got {weight}")
    return EvidenceItem(
        id=eid,
        statement=statement,
        theme=theme,
        weight=weight,
        source_label=source_label,
        reviewed_at=reviewed,
    )


def _assert_unique_ids(ids: list[str], ctx: str) -> None:
    seen: set[str] = set()
    dup: set[str] = set()
    for i in ids:
        if i in seen:
            dup.add(i)
        seen.add(i)
    if dup:
        raise CorpusValidationError(f"{ctx}: duplicate id(s): {sorted(dup)}")


def load_corpus_from_dict(data: Mapping[str, Any]) -> AreaCorpus:
    """Build ``AreaCorpus`` from a parsed mapping (used by tests and YAML loader)."""
    _require_keys(data, {"area_id", "area_label", "version", "themes", "evidence"}, "corpus")
    area_id = str(data["area_id"]).strip()
    area_label = str(data["area_label"]).strip()
    version = str(data["version"]).strip()
    if not area_id or not area_label or not version:
        raise CorpusValidationError("area_id, area_label, and version must be non-empty")

    themes_raw = data["themes"]
    if not isinstance(themes_raw, list) or not themes_raw:
        raise CorpusValidationError("themes must be a non-empty list")

    themes = tuple(_parse_theme(t, i) for i, t in enumerate(themes_raw))
    theme_id_list = [th.id for th in themes]
    _assert_unique_ids(theme_id_list, "themes")

    theme_ids = {t.id for t in themes}

    evidence_raw = data["evidence"]
    if not isinstance(evidence_raw, list):
        raise CorpusValidationError("evidence must be a list")
    evidence = tuple(
        _parse_evidence(e, i, theme_ids) for i, e in enumerate(evidence_raw)
    )
    _assert_unique_ids([ev.id for ev in evidence], "evidence")

    return AreaCorpus(
        area_id=area_id,
        area_label=area_label,
        version=version,
        themes=themes,
        evidence=evidence,
    )


def load_corpus(path: Path) -> AreaCorpus:
    """Load corpus from ``.yaml`` / ``.yml`` or ``.json`` path."""
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"corpus file not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise CorpusValidationError(f"unsupported corpus format: {suffix}")

    if not isinstance(data, dict):
        raise CorpusValidationError("corpus root must be a mapping")
    return load_corpus_from_dict(data)
