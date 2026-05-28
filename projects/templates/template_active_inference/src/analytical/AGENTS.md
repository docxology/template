# Analytical Track Notes

These functions are the reference implementation of the manuscript's formalism.

- Results must be deterministic and analytically derivable; cross-check against
  the Lean statements (`../../lean/`) and the numeric/pymdp tracks.
- No randomness without a fixed seed; prefer exact expressions over sampling.
- Each public function is exercised by `../../tests/` — keep signatures stable.
