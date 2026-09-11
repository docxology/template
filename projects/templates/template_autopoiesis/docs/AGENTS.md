# AGENTS.md — docs/ for template_autopoiesis

Agent-facing notes for this documentation tree and the exemplar it documents.
The nearest authoritative contract is [`../AGENTS.md`](../AGENTS.md); the
monorepo-wide rules live in [`../../../../AGENTS.md`](../../../../AGENTS.md).

## Layout

- `src/template_autopoiesis/` — all business logic, in four domain subpackages:
  `core/` (`grammar.py`, `expand.py`, `common.py`, `honesty.py`,
  `project_paths.py`, `cli.py`), `gates/` (`materialize.py`, `realize.py`,
  `sealing.py`, `integrity.py`, `verify.py`), `manuscript/`
  (`manuscript_contract.py`, `manuscript_variables.py`, `manuscript_figures.py`,
  `emit_templates.py`), and `figures/` (`figures.py`, `cover_art.py`), plus
  `primitives/` registries.
- `scripts/` — thin orchestrators only; they import from `src/` and never
  contain business logic. Numeric-prefixed scripts are order-sensitive.
- `tests/` — zero-mock suite, mirrored one-to-one into `core/`, `gates/`,
  `figures/`, `manuscript/`, and `primitives/` directories with per-directory
  `README.md`/`AGENTS.md` contracts.
- `manuscript/` — source sections and config; `manuscript/AGENTS.md` is
  authoritative for token, figure, and bibliography rules.

## Conventions observed in this repo

- Deterministic outputs; seeds and provenance verification (`gates/verify.py`,
  `gates/sealing.py`) gate child-project materialization.
- Volatile counts come from generators (`manuscript/manuscript_variables.py`,
  `scripts/z_generate_manuscript_variables.py`), never hand-typed prose.
- No mocks in tests; real files and real subprocesses.
- Never hand-edit `output/` or `dist/`; regenerate through the pipeline.

## How docs here are maintained

- Keep this tree short and factual; one file per concern.
- Any measured count belongs in the monorepo's generated
  `docs/_generated/COUNTS.md`, not here.
- Update this tree in the same change that changes the documented surface.
