# Standalone repository guide

This template is designed to live on its own — copy `projects/templates/template_active_inference/`
out of the monorepo and it is a complete, runnable GitHub repository. **No code under
`src/`, `scripts/`, or `tests/` imports the monorepo's `infrastructure/` layer or any
sibling project** — enforced by `tests/test_self_contained.py` (a static AST scan plus a
clean-room import with `infrastructure` blocked).

## What runs standalone

| Step | Command | Depends on |
| --- | --- | --- |
| Tests + coverage | `uv run pytest tests/` | project `src/` only |
| Analytical sweep | `uv run python scripts/run_analytical_sweep.py` | numpy/scipy |
| pymdp T-maze rollout | `uv run python scripts/simulate_si_tmaze.py` | inferactively-pymdp |
| Statistics + figures | `uv run python scripts/compute_statistics.py && uv run python scripts/generate_figures.py` | matplotlib |
| Compose manuscript | `uv run python scripts/compose_manuscript.py` | project sheaf engine |
| Validate gates | `uv run python scripts/validate_outputs.py` | project `src/gates/` |
| **Render PDF** | `uv run python scripts/render_pdf.py` | `pandoc`, `xelatex` (external CLIs) |

## Self-contained rendering

`scripts/render_pdf.py` composes, hydrates, and renders the manuscript to
`output/pdf/template_active_inference_standalone.pdf` using only this project's code plus
the external `pandoc` and `xelatex` tools. Typography is read from project-owned sources:

- **Margins** — `manuscript/config.yaml` → `metadata.geometry`.
- **Dense 9 pt body** — `manuscript/preamble.md` (the `fontsize` package).
- **Red hyperlinks** — pandoc `colorlinks` variables set by the renderer.

The monorepo pipeline (`scripts/03_render_pdf.py` in the template repo, which *does* use
`infrastructure/`) adds transmission bookends, QR strips, and LaTeX post-processing — that
is the full-polish path and is **not** required to build the PDF standalone. The portable
renderer here is the subset a standalone checkout needs.

## The generic-engine / bespoke-registry split

The sheaf composition engine (`src/manuscript/sheaf/`) is the reusable core; the bespoke
binding lives in data, not code:

- **Engine (code)** — `laws.py` (sheaf-axiom oracle), `compose.py`, `coverage.py`,
  `manifest.py`, `registry.py`, `renderers.py`, `models.py`.
- **Bespoke registry (data)** — `manuscript/sheaf/manifest.yaml` (IMRAD rows → fragments),
  `manuscript/sheaf/tracks.yaml` (track registry), `figures.yaml`, `pymdp.yaml`.

To reuse the engine in another project, copy `src/manuscript/sheaf/` and supply your own
manifest/registry/figures YAML — the engine reads them; it hard-codes none of this project's
content. Keeping the engine *in the project* (rather than in shared infrastructure) is a
deliberate choice: it is what makes this template copy-out-and-run standalone.
