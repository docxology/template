# fep_lean/docs — Documentation Index

Reference material for the 50-topic Lean 4 / Mathlib 4 catalogue and its Python pipeline.

**Version**: v0.7.0 | **Native verify**: 50/50 `lake env lean` (green sweep) | **Mathlib4**: v4.29.0 | **Model**: moonshotai/kimi-k2.6 (Hermes primary; `z-ai/glm-5.1` demoted to fallback)

- **Catalogue**: [`../config/topics.yaml`](../config/topics.yaml) (50 rows, all `mathlib_status: real`, 214 theorems avg 4.3/topic) — `lean_sketch` bodies authored in [`../scripts/catalogue_sketches.py`](../scripts/catalogue_sketches.py) with namespace wrappers; [`tests/test_catalogue_sketches_ssot.py`](../tests/test_catalogue_sketches_ssot.py) enforces YAML ↔ `SKETCHES` match
- **Python source**: [`../src/`](../src/) — 6 top-level packages (`catalogue`, `gauss`, `llm`, `output`, `pipeline`, `verification`; `output` includes `manuscript` and related writers)
- **Tests**: [`../tests/`](../tests/) — 30 modules, **320** collected tests, coverage exceeds the **90%** gate (see [`tests/AGENTS.md`](../tests/AGENTS.md))
- **Lean workspace**: [`../lean/`](../lean/) (Lake + Mathlib v4.29.0, pinned in `lakefile.lean`)
- **Manuscript**: [`../manuscript/`](../manuscript/) — 27 Markdown sections + `config.yaml` + generated `09z_appendix_b_lean_catalogue.md` (v0.7.0: fully expanded with real run data)
- **Pipeline deliverables**: under the repository `output/` directory in a subdirectory named for the project slug (template default when active: `output/fep_lean/`) — PDF, slides, HTML, figures, reports

> **Benchmark note**: Full end-to-end runs with `FEP_LEAN_GAUSS_WORKFLOWS=1` are LLM-latency dominated (order tens of minutes depending on keys and model). Native compilation headline is **`50/50`** after a green verifier sweep; see `manuscript_vars.yaml` / `verification_manifest.json`.

This folder (`docs/`, beside `src/` and `manuscript/`) holds the hand-maintained reference docs *about* the project. For the narrative paper content go to `../manuscript/`; for the tech contracts that agents must honour read `../AGENTS.md`; for the system functional spec read `../SPEC.md`. Cursor Gauss skill (math-inc CLI vs `fep_lean` modules): [`../../../.cursor/skills/gauss/SKILL.md`](../../../.cursor/skills/gauss/SKILL.md).

---

## Document index

### Getting started

| Document | Contents |
| -------- | -------- |
| [getting-started.md](getting-started.md) | First-run setup: prerequisites, `uv sync`, pytest, preflight, initial pipeline run |
| [quickref.md](quickref.md) | One-page cheat sheet: commands, env vars, common flags, expected outputs |
| [troubleshooting.md](troubleshooting.md) | Failure modes (including Stage 02 subprocess timeout) with root cause + fix commands |
| [cli-reference.md](cli-reference.md) | Full CLI reference: every script, every flag, every env var, every exit code |

### Architecture and pipeline

| Document | Contents |
| -------- | -------- |
| [architecture.md](architecture.md) | Layer separation, module responsibilities, data flow, thin-orchestrator pattern, **monorepo Stage 02** boundary |
| [pipeline.md](pipeline.md) | `FEPPipeline` DAG: Load Catalogue → Environment → Gauss Sessions → Manuscript Artifacts → Reporter; template script discovery; default **7200 s** per analysis script |
| [configuration.md](configuration.md) | `FEP_LEAN_*`, **`ANALYSIS_SCRIPT_TIMEOUT_SEC`** (repo root), `settings.yaml`, `topics.yaml` schema, pyproject pointers |
| [reporter.md](reporter.md) | Output layout under `output/reports/run_*/`, 13-check validation report |

### Components

| Document | Contents |
| -------- | -------- |
| [opengauss.md](opengauss.md) | math-inc `gauss` CLI, `gauss doctor`, `OpenGaussClient` SQLite schema, session lifecycle |
| [hermes.md](hermes.md) | Hermes LLM explainer: OpenRouter `urllib` client, **429** + **transient** retries (`HERMES_*_MAX_RETRIES`), fallback chain, key↔endpoint affinity, reasoning-model handling |
| [lean4.md](lean4.md) | Mathlib orientation, catalogue SSOT, `LeanVerifier`, full lean4-skills `/lean4:*` map vs Gauss/Hermes (incl. draft / prove / doctor / refactor / golf) |

### Catalogue and theory

| Document | Contents |
| -------- | -------- |
| [topics-reference.md](topics-reference.md) | 50 topics by area with pedagogical Lean sketches (narrative may simplify; committed `lean_sketch` matches `catalogue_sketches.SKETCHES`) |
| [fep-background.md](fep-background.md) | Free Energy Principle, Active Inference, Bayesian Mechanics, Info Geometry, Thermodynamics primer |
| [glossary.md](glossary.md) | Definitions for FEP / Bayesian-mechanics terms used in the catalogue |

### Development

| Document | Contents |
| -------- | -------- |
| [testing.md](testing.md) | Pytest setup, no-mocks policy, coverage gate, how to add a test |
| [development.md](development.md) | Dev workflow: adding topics, editing modules, extending Hermes, CI pattern |
| [authorship-guide.md](authorship-guide.md) | Step-by-step: adding new topics to the 50-topic catalogue (data model, Lean sketch authoring, Mathlib maturity, workflow stages, testing) |
| [api.md](api.md) | Public APIs extracted from `src/` (dataclasses, classes, functions) |

### Contracts and conventions (this folder only)

| Document | Contents |
| -------- | -------- |
| [SPEC.md](SPEC.md) | Documentation-specific specification (not to be confused with [`../SPEC.md`](../SPEC.md) which is the functional spec) |
| [AGENTS.md](AGENTS.md) | Conventions for docs-folder edits (not to be confused with [`../AGENTS.md`](../AGENTS.md) which is the project contract) |

### Tooling scripts (executable)

| File | Purpose |
| ---- | ------- |
| [check_links.py](check_links.py) | Validate internal Markdown links; `--strict` also validates `#anchor` targets |
| [md_hygiene.py](md_hygiene.py) | Lint headers, list markers, trailing whitespace, duplicate H1, line length |

### Generated at runtime

| Path | Source |
| ---- | ------ |
| [`../manuscript/09z_appendix_b_lean_catalogue.md`](../manuscript/09z_appendix_b_lean_catalogue.md) | Auto-written by `output.manuscript.write_full_topic_lean_catalogue_markdown` — **do not edit** |
| [`../manuscript/manuscript_vars.yaml`](../manuscript/manuscript_vars.yaml) | Auto-written by `output.manuscript.write_manuscript_vars` — **do not edit** |
| `../output/reports/run_*/topics/fep-NNN.md` | Per-topic reference markdown written by `Reporter.generate` at pipeline run time |

---

## Local checks

From this directory (`docs/`; paths in the check scripts resolve from `__file__`, so any clone works):

```bash
# Basic link and hygiene checks (pass / fail exit codes)
uv run python check_links.py
uv run python md_hygiene.py

# Stricter checks (validate anchors + orphan brackets + trailing whitespace)
uv run python check_links.py --strict
uv run python md_hygiene.py --strict --max-line 200

# Also scan sibling top-level docs (../README.md, ../AGENTS.md, ../SPEC.md, ../PAI.md)
uv run python check_links.py --strict --include-root
```

Both scripts exit **0** when clean and **1** on any issue — suitable for CI gates. After editing [pipeline.md](pipeline.md) or [configuration.md](configuration.md), run `check_links.py --strict` so new `#anchor` targets are validated (see [docs/AGENTS.md](AGENTS.md)).

---

## Relationship between `docs/SPEC.md`, `docs/AGENTS.md` and their project-root siblings

This confuses people, so: there are **four** governance files total — one pair at the project root (authoritative for the system) and one pair in this folder (authoritative for the docs).

| Scope | File | What it defines |
| ----- | ---- | --------------- |
| System | [`../SPEC.md`](../SPEC.md) | Functional spec: pipeline stages, catalogue maturity, testing policy, CI gates |
| System | [`../AGENTS.md`](../AGENTS.md) | Project contracts: layout, env vars, validation checks, invariants agents must preserve |
| Docs | [`SPEC.md`](SPEC.md) | What this docs folder promises: completeness, cross-linking, metric alignment |
| Docs | [`AGENTS.md`](AGENTS.md) | How to edit this folder: tone, link hygiene, PR checklist |

If a claim in `docs/SPEC.md` contradicts the project-root `SPEC.md`, **the project-root version wins** and this folder must be updated.

---

## Navigation

- [← Project README](../README.md)
- [Project AGENTS](../AGENTS.md)
- [Project SPEC](../SPEC.md)
- [Getting Started →](getting-started.md)
