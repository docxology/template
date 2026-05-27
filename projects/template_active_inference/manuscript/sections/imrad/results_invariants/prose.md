The analytical invariant registry (`src/invariants.py`) runs before PDF rendering. On a clean checkout **{{invariants_passed}} / {{invariants_total}}** analytical checks pass in the merged report at `output/reports/invariants.json`, which also records simulation invariants when the pymdp harness ran.

Per-domain SI checks live in `output/reports/si_invariants.json` before merge. Failures block publication artifacts.
