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
    """True when the report contains genuine *simulation* invariants by content.

    Binds the manuscript's "merged analytical and simulation" claim. Presence of a
    non-empty ``simulation`` key is NOT enough — analytical invariants copied verbatim
    under the ``simulation`` label would launder a relabel past a presence check. We
    require the block's keys to intersect the canonical simulation-invariant names, so
    a relabeled/wrong block is rejected and the silent analytical-only degrade fails.
    """
    from simulation.invariants import SIMULATION_INVARIANTS

    known_sim = set(SIMULATION_INVARIANTS)
    root = project_root.resolve()
    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.is_file():
        data = json.loads(inv_path.read_text(encoding="utf-8"))
        simulation = data.get("simulation") or {}
        if known_sim & set(simulation):
            return True
    si_inv_path = root / "output" / "reports" / "si_invariants.json"
    if si_inv_path.is_file():
        si_data = json.loads(si_inv_path.read_text(encoding="utf-8"))
        return bool(known_sim & set(si_data.get("invariants") or {}))
    return False
