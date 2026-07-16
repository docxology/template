# Source contract

- Put reusable decisions and transformations in `src/`; keep `scripts/` thin.
- Preserve per-phase provenance through filtering and cross-phase deduplication.
- Keep deterministic paths network-free and seed any stochastic computation.
- Keep mirrored single-term modules aligned through the strict template-drift
  gate; project-specific behavior belongs in `multi_phase/` or `deep_research/`.
- Validate configuration at the boundary and report unavailable external
  providers honestly instead of fabricating successful results.
- Test real behavior with temporary files and local HTTP servers; prohibited
  mock frameworks and semantic dependency replacements remain at zero.
