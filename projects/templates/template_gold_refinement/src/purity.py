"""Karat grading and purity computation for the gold-refinement analogy.

Maps metallurgical purity fractions to standard gold karat grades and
computes purity targets for each refinement stage. Purity is expressed
as a fraction in [0, 1] and increases monotonically across stages.

The "nine nines" scale (99.9999999%) represents ultra-high-purity gold
used in electronics and certification — the analog of a fully validated,
reproducible manuscript.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


# Standard karat grades: karat → purity fraction
KARAT_GRADES: dict[int, float] = {
    9: 0.375,
    10: 0.4167,
    12: 0.500,
    14: 0.585,
    18: 0.750,
    20: 0.833,
    22: 0.9167,
    23: 0.958,
    24: 0.999,
}

# Nine-nines purity: 99.9999999% — ultra-high-purity certification
NINE_NINES_PURITY: float = 0.999999999


@dataclass(frozen=True)
class KaratGrade:
    """A karat grade with its purity fraction and label."""

    karat: int
    purity: float
    label: str

    @property
    def percentage(self) -> float:
        """Process percentage."""
        return self.purity * 100.0

    @property
    def nines(self) -> int:
        """Count of consecutive 9s in the percentage representation."""
        pct = self.percentage
        n = 0
        for ch in f"{pct:.10f}":
            if ch == "9":
                n += 1
            elif ch == ".":
                continue
            else:
                break  # pragma: no branch
        return n


def karat_for_purity(purity: float) -> KaratGrade:
    """Return the highest standard karat grade not exceeding *purity*.

    Raises:
        ValueError: If purity is outside [0, 1].
    """
    if not 0.0 <= purity <= 1.0:
        raise ValueError(f"purity must be in [0, 1], got {purity}")
    best_karat = 0
    best_purity = 0.0
    for karat, frac in sorted(KARAT_GRADES.items()):
        if frac <= purity:
            best_karat = karat
            best_purity = frac
    if best_karat == 0:
        return KaratGrade(karat=0, purity=0.0, label="below 9K (unrefined ore)")
    label = f"{best_karat}K"
    if best_karat == 24:
        if purity >= NINE_NINES_PURITY:
            label = "24K (nine-nines certified)"
        else:
            label = "24K"
    return KaratGrade(karat=best_karat, purity=best_purity, label=label)


def purity_to_nines(purity: float) -> int:
    """Count how many consecutive 9s appear in the purity percentage.

    Examples:
        0.9 → 1 ("90%")
        0.99 → 2 ("99%")
        0.999 → 3 ("99.9%")
        0.999999999 → 9 ("99.9999999%")
    """
    if purity <= 0:
        return 0
    pct = purity * 100.0
    s = f"{pct:.10f}"
    # Remove leading "9" digits before the decimal
    nines = 0
    started = False
    for ch in s:
        if ch == "9":
            nines += 1
            started = True
        elif ch == ".":
            continue
        elif started:
            break
    return nines


def format_purity(purity: float) -> str:
    """Format a purity fraction as a human-readable percentage string."""
    pct = purity * 100.0
    if purity >= NINE_NINES_PURITY:
        return "99.9999999% (nine-nines)"
    if pct >= 99.0:
        return f"{pct:.3f}%"
    if pct >= 10.0:
        return f"{pct:.2f}%"
    return f"{pct:.1f}%"


def assert_monotone_increase(purities: Sequence[float]) -> bool:
    """Assert that purity values are strictly increasing.

    Returns True if monotonically increasing; raises ValueError otherwise.
    """
    if len(purities) < 2:
        return True
    for i in range(1, len(purities)):
        if purities[i] <= purities[i - 1]:
            raise ValueError(
                f"Purity must increase monotonically: stage {i - 1} = {purities[i - 1]}, stage {i} = {purities[i]}"
            )
    return True


__all__ = [
    "KARAT_GRADES",
    "NINE_NINES_PURITY",
    "KaratGrade",
    "assert_monotone_increase",
    "format_purity",
    "karat_for_purity",
    "purity_to_nines",
]
