"""LOG-SEP-CENTRAL-1: banner separators must route through named width constants.

Two guarantees:

1. The shared width constants are exported with the values the codebase assumes.
2. No infrastructure module reintroduces an ad-hoc ``"=" * N`` banner literal for
   the centralized widths — the substitution is byte-identical, so the only
   reason to write the literal again is drift.

No mocks: the lint walks the real ``infrastructure/`` source tree.
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.logging import constants

_REPO_ROOT = Path(__file__).resolve().parents[3]
_INFRA = _REPO_ROOT / "infrastructure"

# Widths that now have a named constant. New code must use the constant.
_CENTRALIZED_WIDTHS = (60, 70, 72, 78, 80)
# Match an `=` bar in either quote style — `"=" * 60` or `'=' * 60` — at a
# centralized width. Single-quoted bars were a blind spot in the first cut.
_AD_HOC = re.compile(r"""['"]=['"] \* (?:""" + "|".join(str(w) for w in _CENTRALIZED_WIDTHS) + r")\b")

# constants.py legitimately assigns the integer values; it is the single source.
_ALLOWED = {_INFRA / "core" / "logging" / "constants.py"}


def test_width_constants_exported_with_expected_values() -> None:
    assert constants.BANNER_WIDTH == 60
    assert constants.PIPELINE_STAGE_WIDTH == 70
    assert constants.TELEMETRY_WIDTH == 72
    assert constants.DOCTOR_WIDTH == 78
    assert constants.TABLE_WIDTH == 80


def test_no_ad_hoc_separator_literals_in_infrastructure() -> None:
    offenders: list[str] = []
    for py in sorted(_INFRA.rglob("*.py")):
        if py in _ALLOWED:
            continue
        text = py.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            if _AD_HOC.search(line):
                offenders.append(f"{py.relative_to(_REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Ad-hoc banner separators found — route these through a width constant "
        "in infrastructure.core.logging.constants (BANNER_WIDTH / PIPELINE_STAGE_WIDTH / "
        "TELEMETRY_WIDTH / DOCTOR_WIDTH / TABLE_WIDTH):\n" + "\n".join(offenders)
    )
