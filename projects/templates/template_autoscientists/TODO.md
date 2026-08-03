# template_autoscientists TODO

Forward-only backlog for the deterministic coordination-mechanism testbed exemplar (arXiv:2605.28655 primitives: proposer, dead-end registry, confirmation band, reorganization).

## Current validation evidence

- Pre-render validation passed with no render-blocking pitfalls or undefined citations.
- Project test gate: **114 passed, 1 skipped** (`requires_ollama`), **99.29%** isolated source coverage.
- Full core pipeline (8 stages) completed green; single-stage analysis/render/validate/copy all exit 0 with Stage-04 validation passing every check (PDF, transmission bookends, Markdown, output structure, figure registry, evidence registry, project design overlays, artifact manifest, rendered provenance).
- Combined PDF: **14 pages**, **0** `^! ` LaTeX error lines, **0** unresolved `??` markers.
- Qualified template-drift gate: `template_drift: no drift detected.`

## Fixes completed in this pass

- Corrected claim-ledger `confirmation-noise-seeds` from 5 to the measured `SearchConfig.confirm_seeds` count of 3 and bound its source to `src/search.py`.
- Expanded `tests/AGENTS.md` to list every test file and identify the opt-in Ollama test.
- Synchronized `manuscript/config.yaml.example` with live publication shape (`repository_url`, `published_artifacts`).
- Documented `ablation_efficiency.png` output and corrected troubleshooting guidance to `SearchConfig.confirm_seeds`.
- Repaired manuscript champion notation with `$p^{\ast}$`, eliminating invalid escaped-star LaTeX (`Missing {`/`Missing }` recoverable errors).
- Regenerated figures, data, PDF/HTML manuscript outputs, validation reports, output statistics, composition, and provenance evidence; refreshed the artifact manifest snapshot.

## Remaining gaps (forward-only ladder)

1. Keep deterministic fixture replay green under the project coverage gate.
2. Keep `manuscript/config.yaml.example` aligned when `SearchConfig` or `SyntheticObjective` defaults change.
3. Add a script-level config summary only if analysis scripts begin reading YAML directly.
4. Promote the live agent path only with offline transcript fixtures, stale-transcript detection, and a no-network default validation.
5. The single-stage rendered-provenance bridge remains sensitive to `git check-ignore` under concurrent repo churn; full `PipelineExecutor` runs are the manifest-authoritative path. Any further hardening belongs in shared infrastructure, not this exemplar.
