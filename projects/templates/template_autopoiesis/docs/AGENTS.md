# AGENTS.md — docs/ for template_autopoiesis

Agent-facing notes for this documentation tree and the exemplar it documents.
The nearest authoritative contract is [`../AGENTS.md`](../AGENTS.md); the
monorepo-wide rules live in [`../../../../AGENTS.md`](../../../../AGENTS.md).

## Layout

- `src/` — all business logic. Key modules: `grammar.py`, `expand.py`,
  `materialize.py`, `realize.py`, `sealing.py`, `integrity.py`, `verify.py`,
  `honesty.py`, `manuscript_contract.py`, `manuscript_variables.py`,
  `figures.py`, `cover_art.py`, plus `primitives/` registries.
- `scripts/` — thin orchestrators only; they import from `src/` and never
  contain business logic. Numeric-prefixed scripts are order-sensitive.
- `tests/` — zero-mock suite; per-directory `README.md`/`AGENTS.md` contracts.
- `manuscript/` — source sections and config; `manuscript/AGENTS.md` is
  authoritative for token, figure, and bibliography rules.

## Conventions observed in this repo

- Deterministic outputs; seeds and provenance verification (`verify.py`,
  `sealing.py`) gate child-project materialization.
- Volatile counts come from generators (`manuscript_variables.py`,
  `scripts/z_generate_manuscript_variables.py`), never hand-typed prose.
- No mocks in tests; real files and real subprocesses.
- Never hand-edit `output/` or `dist/`; regenerate through the pipeline.

## How docs here are maintained

- Keep this tree short and factual; one file per concern.
- Any measured count belongs in the monorepo's generated
  `docs/_generated/COUNTS.md`, not here.
- Update this tree in the same change that changes the documented surface.
