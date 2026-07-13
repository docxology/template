# scripts - AGENTS.md

Keep scripts thin and delegate preregistration logic to `src/registered_report/`.
`generate_figures.py` accepts explicit canonical/output/data destinations for
isolated runs, mirrors the four real PNGs, and writes the registry only after
the complete source-owned figure spec is satisfied.
