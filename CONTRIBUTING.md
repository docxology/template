# Contributing

GitHub surfaces this file when contributors open an issue or PR. It is a
pointer; the authoritative guides live under `docs/`.

## Start here

- **[`docs/development/contributing.md`](docs/development/contributing.md)** — full contribution workflow.
- **[`docs/development/contribution-map.md`](docs/development/contribution-map.md)** — overlap checks and contribution strategy before building.
- **[`docs/development/code-review-checklist.md`](docs/development/code-review-checklist.md)** — the merge criteria (authoritative "ready to merge").
- **[`AGENTS.md`](AGENTS.md)** / **[`CLAUDE.md`](CLAUDE.md)** — system manual and operational rules (apply to humans and AI agents alike).
- **[`.github/AGENTS.md`](.github/AGENTS.md)** — CI jobs, quality gates, branch-protection requirements.

## Non-negotiable rules (enforced in CI)

These are gates, not suggestions — see the docs above for the rationale:

- **No mocks.** Tests use real data and computation (`scripts/verify_no_mocks.py`).
- **Thin-orchestrator pattern.** Business logic lives in `infrastructure/` or `projects/<name>/src/`; `scripts/` only orchestrate.
- **Coverage.** Infrastructure ≥ 60%; each public exemplar project job ≥ 90% on its own `src/`. The local all-project orchestrator (`scripts/01_run_tests.py --project-only --all-projects --public-projects`) also enforces a 75% combined-union floor for release-style sweeps.
- **Type hints + `__all__`** on public infrastructure APIs (`mypy`, `check-all-exports`).
- **Conventional commits**; run `pre-commit` locally (`ruff`, `mypy`, `bandit`, the pre-push gates).
- **Confidentiality.** This is a public repo: only the public exemplars listed in [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md) are tracked. Never commit any other project under `projects/` — `scripts/check_tracked_projects.py` blocks it in the pre-push hook and CI.

## Citation

Cite via the repository's [`CITATION.cff`](CITATION.cff) (GitHub's
"Cite this repository" widget) — DOI `10.5281/zenodo.19139090`.
