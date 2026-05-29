"""Load invariant pass/total counts from reports or live analytical run."""

from __future__ import annotations

import json
from pathlib import Path

from analytical.invariants import run_invariants


def load_invariant_counts(project_root: Path) -> tuple[int, int]:
    """Return passed/total invariant counts from merged reports when present."""
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.is_file():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        analytical = data.get("invariants") or {}
        simulation = data.get("simulation") or {}
        if not simulation:
            si_inv_path = root / "output" / "reports" / "si_invariants.json"
            if si_inv_path.is_file():
                si_data = json.loads(si_inv_path.read_text(encoding="utf-8"))
                simulation = si_data.get("invariants") or {}
        combined = {**analytical, **simulation}
        if combined:
            return sum(1 for value in combined.values() if value), len(combined)
    inv = run_invariants()
    return sum(1 for value in inv.values() if value), len(inv)


def invariants_are_merged(project_root: Path) -> bool:
    """True when the invariants report actually contains simulation invariants.

    Binds the manuscript's "merged analytical and simulation" claim: returns False
    in the silent-degrade case (analytical-only) so a gate can refuse to certify the
    merged claim rather than print an analytical-only count under a "merged" caption.
    """
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.is_file():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        if data.get("simulation"):
            return True
    si_inv_path = root / "output" / "reports" / "si_invariants.json"
    if si_inv_path.is_file():
        si_data = json.loads(si_inv_path.read_text(encoding="utf-8"))
        return bool(si_data.get("invariants"))
    return False
