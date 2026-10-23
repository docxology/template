# scripts - AGENTS.md

Keep scripts thin and delegate preregistration logic to `src/registered_report/`.

- `generate_figures.py` accepts explicit canonical/output/data destinations for
  isolated runs, mirrors the four real PNGs, and writes the registry only after
  the complete source-owned figure spec is satisfied.
- `generate_review_artifacts.py` freezes the fixture registration and writes the
  deterministic review-packet, deviation-ledger, sensitivity-findings, and
  adherence-report JSON artifacts under `output/reports/`.

Ordinary `generate_figures.py` execution writes actual current figures and the
complete registry to `output/figures/`; do not rewrite admitted manuscript PNGs
during a frozen-source pipeline. `--figures-dir` remains available for explicit
standalone regeneration that is reviewed as a source change before a fresh run.
