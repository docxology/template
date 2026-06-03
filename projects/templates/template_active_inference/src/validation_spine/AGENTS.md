# Source Module Notes

`validation_spine/` holds the deterministic artifact contracts for the Active
Inference exemplar. All reusable, tested logic lives here; `../../scripts/`
(e.g. `generate_validation_spine.py`) only parses arguments, resolves paths, and
calls these functions (thin-orchestrator pattern).

- `artifacts.py` writes and validates the artifact-provenance, deterministic
  replay, and counterexample-matrix records consumed by the gate tests before
  manuscript/output validation.
- Keep every contract deterministic (fixed seeds, no network, no runtime
  downloads) so replays are byte-stable.
- The validation spine runs ahead of manuscript/output validation; changes here
  must keep the five tracks (prose / formalism / numerics / pymdp / Lean)
  concordant.
