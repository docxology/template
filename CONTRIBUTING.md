# Contributing

GitHub surfaces this file when contributors open an issue or PR. It is a
pointer; the authoritative guides live under `docs/`.

## Start here

- **[`docs/development/contributing.md`](docs/development/contributing.md)** — full contribution workflow.
- **[`docs/development/code-review-checklist.md`](docs/development/code-review-checklist.md)** — the merge criteria (authoritative "ready to merge").
- **[`AGENTS.md`](AGENTS.md)** / **[`CLAUDE.md`](CLAUDE.md)** — system manual and operational rules (apply to humans and AI agents alike).
- **[`.github/AGENTS.md`](.github/AGENTS.md)** — CI jobs, quality gates, branch-protection requirements.

## Non-negotiable rules (enforced in CI)

These are gates, not suggestions — see the docs above for the rationale:

- **No mocks.** Tests use real data and computation (`scripts/verify_no_mocks.py`).
- **Thin-orchestrator pattern.** Business logic lives in `infrastructure/` or `projects/<name>/src/`; `scripts/` only orchestrate.
- **Coverage.** Infrastructure ≥ 60%, per-project ≥ 90%, combined-union all-projects ≥ 75%.
- **Type hints + `__all__`** on public infrastructure APIs (`mypy`, `check-all-exports`).
- **Conventional commits**; run `pre-commit` locally (`ruff`, `mypy`, `bandit`, the pre-push gates).
- **Confidentiality.** This is a public repo: only `projects/templates/template_active_inference`, `projects/templates/template_autoresearch_project`, `projects/templates/template_autoscientists`, `projects/templates/template_code_project`, `projects/templates/template_newspaper`, `projects/templates/template_prose_project`, `projects/templates/template_sia`, `projects/templates/template_template`, and `projects/templates/template_textbook` are tracked. Never commit any other project under `projects/` — `scripts/check_tracked_projects.py` blocks it in the pre-push hook and CI.

## Citation

Cite via the repository's [`CITATION.cff`](CITATION.cff) (GitHub's
"Cite this repository" widget) — DOI `10.5281/zenodo.19139090`.
