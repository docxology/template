# src/

Project-specific Python. Business logic for the literature pipeline lives here; generic pieces stay in `infrastructure/`.

Modules live in four subpackages: `search/` (deep search + CLI orchestration
bodies), `pipeline/` (literature pipeline, synthesis, composition, LLM
runtime, dotenv), `analysis/` (review-stage hooks, reading report, review
report), and `publish/` (figures, dashboard, config, manuscript variables).
All public names are re-exported from the package root, so
`template_search_project.<name>` imports keep working.

See [AGENTS.md](AGENTS.md) for module map and extension rules.
