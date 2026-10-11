# Source contract

- Put reusable decisions and transformations in `src/`; keep `scripts/` thin.
- Preserve per-phase provenance through filtering and cross-phase deduplication.
- Keep deterministic paths network-free and seed any stochastic computation.
- Consume shared analysis, knowledge-graph, reproducibility and visualization
  through the declared `template_literature_meta_analysis` distribution.
  Change shared methods in the Meta project's canonical `src/` and verify both
  consumers; phase-specific behavior belongs in this project's own source.
- Validate configuration at the boundary and report unavailable external
  providers honestly instead of fabricating successful results.
- Test real behavior with temporary files and local HTTP servers; prohibited
  mock frameworks and semantic dependency replacements remain at zero.
