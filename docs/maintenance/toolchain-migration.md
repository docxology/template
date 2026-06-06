# Toolchain Migration — pin the interface, not the tool

> Created 2026-05-20. Addresses World-Threat-Model RedTeam attack A5 (Python language drift + uv/ruff/mypy churn).

## Why this guide exists

The template currently depends on a specific toolchain: `uv` (package management), `ruff` (linting + formatting), `mypy` (type checking), `bandit` (security scanning), `pytest` (test runner), GitHub Actions (CI). Each of these is a 2024–2026-vintage choice. On a 10-year horizon, the probability of zero forced migrations is approximately zero.

The right move is not to pin specific tools forever — it is to **document the interface each tool fulfills**, so a future maintainer can swap the implementation without rewriting the repo. This guide is that documentation.

## The interface-vs-tool contract

For each tool the repo currently uses, this guide states:
1. **What contract the tool fulfills** (the interface)
2. **The current implementation** (the tool)
3. **The migration path** if the tool is succeeded

A maintainer in 2030 should be able to read this guide and know: "ruff is the implementation of contract X; if I'm replacing it with $NEW_TOOL, I need $NEW_TOOL to fulfill X."

## Package management

| | |
| --- | --- |
| **Contract** | Reproducible dependency resolution from a lockfile; isolated virtual environments per project; fast install. |
| **Current implementation** | `uv` (Astral, since ~2024). Replaces poetry/pip-tools/PDM/Hatch. Used via `uv sync`, `uv run`, `uvx`, `uv lock`. |
| **Lockfile format** | `uv.lock` (uv-specific TOML format) |
| **Fallback** | Generate `requirements.txt` from `uv export` and commit it periodically. This is the "runs even if uv vanishes" insurance — see `scripts/ci_local.sh`. |
| **Migration path** | If a successor (`pdm`, future tool, etc.) becomes dominant: (a) verify it can consume `pyproject.toml` (PEP 621 standard, so likely yes); (b) generate its lockfile alongside `uv.lock` for one release; (c) update `run.sh`, `scripts/00_setup_environment.py`, `.github/workflows/ci.yml`, and `.pre-commit-config.yaml` to use the new tool; (d) keep `uv.lock` as a legacy artifact for one major version, then remove. |

## Linting + formatting

| | |
| --- | --- |
| **Contract** | Style enforcement (formatting), error detection (linting), zero-config defaults that match community norms. Fast enough to run in pre-commit. |
| **Current implementation** | `ruff` (Astral). Replaces `black` + `flake8` + `isort` + `pycodestyle`. Used via `uvx ruff check`, `uvx ruff format`. |
| **Configuration location** | `pyproject.toml` under `[tool.ruff]` |
| **Migration path** | If `ruff` is succeeded: (a) the rule taxonomy (E, F, W, B, etc.) is mostly stable across linters; (b) the formatter behavior is the harder migration — pin a target style (e.g., "black 2024 compatible") in the migration PR; (c) update `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `CLAUDE.md` quick-reference. |

## Type checking

| | |
| --- | --- |
| **Contract** | Static type checking of the public CI source paths from `infrastructure.project.public_scope`. Strict mode where feasible. Catches type errors before runtime without traversing local-only private symlinks. |
| **Current implementation** | `mypy --strict` (community). Runs over the public CI source set returned by `uv run python -m infrastructure.project.public_scope source-paths` (do not hard-code a file count — it drifts as the tree grows). |
| **Configuration location** | `pyproject.toml` under `[tool.mypy]` |
| **Possible successors** | `pyright`/`pylance` (Microsoft, faster but different inference rules), `ty` (Astral, ~2026, faster), `pyrefly` (Meta). |
| **Migration path** | Type checkers DO NOT have perfectly compatible inference. Migration requires running both old and new for a transition period and fixing the delta in either inference or annotations. Allocate at least one focused day. Update `.pre-commit-config.yaml`, CI, and `CLAUDE.md`. |

## Security scanning

| | |
| --- | --- |
| **Contract** | Static analysis for common Python security antipatterns (eval, shell injection, weak crypto, etc.). |
| **Current implementation** | `bandit` (PyCQA), configured via `bandit.yaml`. |
| **Migration path** | If `bandit` is succeeded by an LLM-driven scanner (likely by 2028): keep both during transition; the rule set is well-documented and portable. |

## Test runner

| | |
| --- | --- |
| **Contract** | Discover tests under `tests/` and `projects/*/tests/`; coverage measurement; fixtures; parametrized tests; no-mocks policy (real I/O, real HTTP via `pytest-httpserver`). |
| **Current implementation** | `pytest` + `pytest-cov` + `pytest-httpserver`. Coverage floors: 60% infra, 90% per-project, plus a 75% combined union in the local all-project orchestrator. |
| **Migration path** | `pytest` is unusually durable (active since 2003). If succeeded, the most likely successor is a property-based/agentic test runner; the **no-mocks contract** is the harder thing to preserve — see `docs/maintenance/regression-testing.md` for the long-term direction (regression-pinned numerical outputs as the actual quality binding). |

## CI

| | |
| --- | --- |
| **Contract** | Matrix testing across Python versions (currently 3.10–3.12) on Ubuntu and macOS; coverage gates; linting; security scanning; doc-tree integrity checks. |
| **Current implementation** | GitHub Actions (`.github/workflows/ci.yml`). |
| **Local reproduction** | `act` (nektos) — see [`ci-local.md`](ci-local.md). |
| **Migration path** | If GitHub Actions is succeeded (or free-tier compresses to the point of unusability): (a) keep workflow YAML as the documentation of intent; (b) port to the successor (Forgejo Actions consumes the same YAML format; GitLab CI is a YAML rewrite; sovereign-cloud successors vary); (c) the local-reproduction path via `act` is the **portability hedge** — if you can run CI locally via act, you can move CI anywhere. |

## LLM integration

| | |
| --- | --- |
| **Contract** | Optional LLM-driven *draft assistance* (not "scientific review") for manuscript structure and language pass; optional translation of technical abstracts (currently zh / hi / ru). Must work offline; must be opt-out; must not gate the rest of the pipeline. |
| **Current implementation** | Local Ollama with `gemma3:4b` as default. Stages 7 and 8 in pipeline.yaml. |
| **Disclaimer** | Renamed 2026-05-20 from "LLM Scientific Review" to "LLM Structural Lint (Draft Assistance)" — see `infrastructure/llm/README.md` for why. |
| **Migration path** | The model pin (`gemma3:4b`) will be stale within 18 months. The Ollama API is stable; swap to a stronger local model (Qwen3-7B class, Llama-3.x, Gemma-3-larger, etc.) by changing the model name in project config. Re-tune prompts when changing model family. If Ollama-the-product is succeeded by a different local-model runner, the integration boundary is `infrastructure/llm/core/client.py` (and `infrastructure/llm/core/_connection.py`) — port those. |

## LaTeX / PDF rendering

| | |
| --- | --- |
| **Contract** | Markdown manuscript sections → professional PDF with citations, figures, tables, cross-references, and TOC. Deterministic given fixed seeds + `--deterministic` flag. |
| **Current implementation** | Pandoc → LaTeX → PDF pipeline (via `infrastructure/rendering/`). Uses `multirow`, `cleveref`, `doi`, `newunicodechar` from `tlmgr`. |
| **Migration path** | LaTeX is the most durable component in the stack (50+ year history); migration is unlikely to be forced before 2046. The risk is `tlmgr` package availability — pin package versions when a manuscript is locked for publication; archive a snapshot of the rendering environment as a Docker image (see [`stage-10-executable-bundle.md`](stage-10-executable-bundle.md)). |

## Toolchain-swap procedure (general)

When any of the above tools needs migration:

1. **Read this guide first** to confirm the contract being fulfilled.
2. **Write an ADR** under `docs/architecture/adrs/` documenting (a) what the old tool was, (b) why migration is forced, (c) what the new tool is, (d) any contract delta.
3. **Run both old and new in CI for one release** to surface any inference / behavior delta.
4. **Update**:
   - `pyproject.toml` config sections
   - `.pre-commit-config.yaml`
   - `.github/workflows/ci.yml`
   - `CLAUDE.md` quick-reference table
   - `AGENTS.md` system manual
   - This guide (mark the old tool as "succeeded by X" and add the new tool's row)
5. **Update `STATUS.md`** with the new "last verified" date for the affected subsystem.
6. **Tag the release** and note the migration in `CHANGELOG.md`.

## When NOT to migrate

- "The new tool is faster" alone is not a reason. Toolchain churn is expensive; only migrate when there is a forcing function (EOL, broken upstream, capability the current tool genuinely cannot provide).
- "The community moved on" needs to be at least 18 months sustained, not a 6-month surge.
- Migrating because of FOMO is the most common cause of repo decay. Don't.

## Related

- [`README.md`](README.md) — guide hub
- [`ci-local.md`](ci-local.md) — local reproduction via `act`
- [`regression-testing.md`](regression-testing.md) — the long-term direction for quality binding
- [`AGENTS.md`](../../AGENTS.md) — full system manual
- [`CLAUDE.md`](../../CLAUDE.md) — quick-reference table (kept in sync with this guide)
