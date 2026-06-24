"""Subfield registry: config loading and pattern cache."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from analysis.subfield_defaults import DEFAULT_SUBFIELDS

logger = logging.getLogger(__name__)

SUBFIELDS: dict[str, dict] = dict(DEFAULT_SUBFIELDS)
_PATTERN_CACHE: dict[str, list] = {}


def _build_pattern_cache() -> None:
    """Pre-compile word-boundary regex for every keyword in SUBFIELDS."""
    global _PATTERN_CACHE
    _PATTERN_CACHE = {
        field: [re.compile(r"\b" + re.escape(kw.lower()) + r"\b") for kw in info.get("keywords", [])]
        for field, info in SUBFIELDS.items()
    }


def load_subfields_from_config(config_path: Path) -> dict[str, dict]:
    """Load subfield keyword definitions from a YAML config file."""
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not available; using default subfields")
        return dict(DEFAULT_SUBFIELDS)

    try:
        with open(config_path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        logger.warning("Cannot read config %s: %s; using defaults", config_path, exc)
        return dict(DEFAULT_SUBFIELDS)

    subfield_kw = data.get("subfield_keywords") or data.get("project_config", {}).get("subfield_keywords")
    if not subfield_kw or not isinstance(subfield_kw, dict):
        logger.info("No subfield_keywords in config; using defaults")
        return dict(DEFAULT_SUBFIELDS)

    result: dict[str, dict] = {}
    priority_map = {"C": 1, "B": 2, "A1": 3, "A2": 4}
    for name, keywords in subfield_kw.items():
        if isinstance(keywords, list):
            priority = 4
            for prefix, prio in priority_map.items():
                if name.startswith(prefix):
                    priority = prio
                    break
            result[name] = {
                "keywords": keywords,
                "description": name.replace("_", " ").title(),
                "priority": priority,
            }
        else:
            logger.warning("Skipping non-list subfield entry: %s", name)

    if not result:
        logger.warning("Config subfield_keywords was empty; using defaults")
        return dict(DEFAULT_SUBFIELDS)

    logger.info(
        "Loaded %d subfield definitions from config: %s",
        len(result),
        list(result.keys()),
    )
    return result


def configure_subfields(config_path: Optional[Path] = None) -> dict[str, dict]:
    """Set module-level SUBFIELDS from config or defaults.

    Mutates the existing SUBFIELDS dict IN PLACE (clear + update) rather than
    rebinding it. Modules that did ``from ...subfield_registry import SUBFIELDS``
    (e.g. subfield_classifier) hold a reference to this exact object; rebinding
    the global here would leave their binding pointing at the stale default set,
    so the configured taxonomy would silently never apply at runtime.
    """
    new = load_subfields_from_config(config_path) if config_path is not None else dict(DEFAULT_SUBFIELDS)
    SUBFIELDS.clear()
    SUBFIELDS.update(new)
    _build_pattern_cache()
    return SUBFIELDS


def get_pattern_cache() -> dict[str, list]:
    """Return the compiled keyword pattern cache (for classification)."""
    return _PATTERN_CACHE


_build_pattern_cache()
