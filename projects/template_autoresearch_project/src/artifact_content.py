"""Shared substance checks for generated artifacts.

The project historically treated an artifact as "present" or a claim as
"supported" using a bare ``Path.exists()`` test. That is a fail-open gate: an
empty file, a ``{}``/``[]`` JSON, a header-only CSV, or unparseable garbage all
satisfied existence while carrying no evidence. ``is_substantive_artifact`` is the
single shared predicate that binds validity to real, parseable content so the
claim, figure, and benchmark gates can distinguish a real run from a hollow one.

Depth matters: a cross-vendor audit showed a shallow predicate (``len(obj) > 0``,
suffix-only dispatch) still passes ``{"x": null}``, a bare ``0``/``false``, or a
``{}`` written to a ``.txt`` path. This implementation therefore (a) detects JSON
by content as well as suffix, and (b) requires a JSON object/array to contain at
least one *substantive* value, not merely one key.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

__all__ = ["is_substantive_artifact"]


def is_substantive_artifact(path: Path) -> bool:
    """Return True iff ``path`` exists and carries non-trivial, parseable content.

    Rules:
    - missing or whitespace-only file → False;
    - ``.csv`` → at least one data row beyond the header;
    - content that parses as JSON (by suffix OR by leading ``{``/``[``) → must be a
      JSON object/array with at least one substantive value, or a non-empty string;
      a bare top-level scalar (``0``, ``false``, ``null``, ``""``) is NOT evidence;
    - anything else (``.md``/``.txt``/…) → must contain non-whitespace text.
    """
    if not path.is_file():
        return False
    raw = path.read_bytes()
    if not raw.strip():
        return False
    text = raw.decode("utf-8", errors="replace")
    stripped = text.strip()

    if path.suffix.lower() == ".csv":
        data_rows = [row for row in csv.reader(text.splitlines()) if any(cell.strip() for cell in row)]
        return len(data_rows) >= 2

    # Detect JSON by content as well as suffix so hollow {}/[] cannot slip through
    # a non-.json path via the plain-text branch.
    looks_like_json = stripped[:1] in "{[" or path.suffix.lower() == ".json"
    if looks_like_json:
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            # A .json file that does not parse is not substantive; a non-.json file
            # that merely starts with a brace falls back to its text content.
            return path.suffix.lower() != ".json" and bool(stripped)
        return _json_is_substantive(payload)

    return bool(stripped)


def _json_is_substantive(payload: Any) -> bool:
    """True iff a parsed JSON payload carries at least one substantive value.

    A bare top-level number/bool/null is not, by itself, research evidence; an
    object/array is substantive only if it contains a substantive value
    (checked recursively, so an all-null nested tree is rejected).
    """
    if isinstance(payload, dict):
        return any(_value_is_substantive(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_value_is_substantive(value) for value in payload)
    if isinstance(payload, str):
        return bool(payload.strip())
    return False


def _value_is_substantive(value: Any) -> bool:
    """True iff a value inside a JSON structure carries real content.

    Recurses into nested containers — ``{"a": {"b": null}}`` and ``[{"k": null}]``
    are NOT substantive — and rejects non-finite floats (``NaN``/``Inf``).
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return not (isinstance(value, float) and not math.isfinite(value))
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_value_is_substantive(child) for child in value.values())
    if isinstance(value, list):
        return any(_value_is_substantive(child) for child in value)
    return True
