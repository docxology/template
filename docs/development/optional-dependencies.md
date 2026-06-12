# Optional Dependencies & Capability Matrix

This template is modular: the core pipeline (tests, analysis, PDF rendering of the
default path) runs without any optional external tools, and several capabilities
layer on top only when an optional dependency is installed. This page documents
**which optional dependency gates which tests and features**, **how the gate
behaves when the dependency is missing** (skip vs. fail-loud), **how to opt out**,
and **how to install** each one.

## How gating works

Each optional dependency is associated with a pytest marker. Two distinct gate
policies are used on purpose:

- **fail-loud** — when the dependency is absent, the marked tests **fail** (not
  skip) with an actionable setup message. This is deliberate for Ollama: a silent
  skip would let LLM regressions slip through unnoticed on a developer machine
  that is *supposed* to have Ollama. The opt-out below makes the choice explicit.
- **skip-if-absent** — when the dependency is absent, the marked tests **skip**
  with a reason. This is used for LaTeX/PDF rendering, which most contributors do
  not have locally and which CI provides on demand.

Either way the behaviour is **opt-out by marker**, so a contributor can carve the
optional surface out of a run with one flag.

## Capability matrix

| Optional dependency | pytest marker | Gate policy when absent | Tests that need it | Template features unavailable without it | Opt-out (deselect) | Setup |
| --- | --- | --- | --- | --- | --- | --- |
| **Ollama** (local LLM server) | `requires_ollama` | **fail-loud** (tests FAIL with setup guidance; Ollama is auto-started first) | `tests/infra_tests/llm/` real-daemon smoke tests, `tests/integration/test_module_interoperability.py` | Pipeline Stage 7 (LLM Scientific Review) and Stage 8 (LLM Translations); `06_llm_review.py` reviews/translations | `pytest -m "not requires_ollama"` | Install from <https://ollama.ai>, then `ollama serve` and `ollama pull smollm2` (or `gemma3:4b`). See env vars below. |
| **LaTeX / xelatex** (TeX engine) | `requires_latex` | **skip-if-absent** (via `skip_if_no_latex` fixture) | `tests/infra_tests/rendering/` LaTeX/PDF tests (`test_latex_utils.py`, `test_renderers.py`, `test_core.py`, `test_slides_renderer_core.py`, …) | Pipeline Stage 5 PDF rendering (`03_render_pdf.py`); Beamer slide generation | `pytest -m "not requires_latex"` | Install TeX Live / MacTeX (provides `xelatex`). Missing packages: `sudo tlmgr install multirow cleveref doi newunicodechar`. |
| **pandoc** (document converter) | _(no dedicated marker; covered by `requires_latex` PDF tests + format-toggle tests)_ | **skip-if-absent** (rendering config sets `pandoc_path=None` when `pandoc` is not on `PATH`; format toggles guard on availability) | `tests/infra_tests/rendering/` markdown→PDF/DOCX/EPUB conversion paths | DOCX/EPUB export and the pandoc-backed markdown→LaTeX combine step | run a non-rendering subset, e.g. `pytest -m "not requires_latex"`, or target non-rendering dirs | Install pandoc: `brew install pandoc` (macOS) or your distro package; CI installs it in the rendering job. |

Markers compose: to skip every optional-dependency surface in one run use

```bash
uv run pytest tests/infra_tests/ -m "not requires_ollama and not requires_latex"
```

This is exactly what the automated pipeline and the default CI infra gate do for
the LLM surface (`-m "not requires_ollama"`), so the core suite stays green on a
machine with neither Ollama nor a TeX engine.

## Ollama: fail-loud rationale and opt-out

The `requires_ollama` tests **fail rather than skip** when Ollama is unavailable —
this is intentional. A silent skip hides LLM regressions on machines that are
meant to run the LLM path. The session fixture (`ensure_ollama_for_tests` in
[`../../tests/conftest.py`](../../tests/conftest.py)) first tries to auto-start
Ollama, then emits a setup-guidance failure if it cannot. To run *without* the
LLM surface, deselect it explicitly:

```bash
uv run pytest tests/infra_tests/ -m "not requires_ollama"
```

To set the LLM path **up** instead of opting out:

```bash
# 1. install Ollama: https://ollama.ai
ollama serve            # 2. start the server (auto-started by the fixture too)
ollama pull smollm2     # 3. pull a small/fast test model (or gemma3:4b)
ollama list             # 4. verify
```

### Relevant environment variables

| Variable | Effect |
| --- | --- |
| `OLLAMA_HOST` | Point the client at a non-default Ollama URL (the LLM test fixtures set this to a local stub for the deterministic suite). |
| `OLLAMA_TEST_PULL_MODEL` | Test model to auto-pull (default `smollm2`). |
| `OLLAMA_SKIP_TEST_MODEL_PULL` | Set to `1` for air-gapped runs: skip auto-pull and use whatever is already installed. |
| `OLLAMA_TEST_PULL_TIMEOUT` | Seconds for the auto-pull (default `180`; `none`/`inf` disables the timeout). |

## LaTeX / pandoc: skip-if-absent and opt-out

Rendering tests are marked `requires_latex` and additionally request the
`skip_if_no_latex` fixture, so they **skip with a reason** when neither `xelatex`
nor `pdflatex` is found. The rendering config also degrades gracefully: it sets
`latex_compiler=None` and `pandoc_path=None` when those binaries are missing. To
opt out explicitly (e.g. on a machine without TeX):

```bash
uv run pytest tests/infra_tests/ -m "not requires_latex"
```

To check what is available on the current machine:

```bash
python -c "import shutil; print('xelatex:', bool(shutil.which('xelatex'))); print('pandoc:', bool(shutil.which('pandoc')))"
```

## See also

- [`../../tests/infra_tests/README.md`](../../tests/infra_tests/README.md) — infrastructure test overview
- [`../../tests/infra_tests/llm/AGENTS.md`](../../tests/infra_tests/llm/AGENTS.md) — LLM test categories and the `requires_ollama` real-daemon layer
- [`../../tests/infra_tests/rendering/AGENTS.md`](../../tests/infra_tests/rendering/AGENTS.md) — rendering tests and LaTeX/pandoc gating
- [`coverage-gaps.md`](coverage-gaps.md) — live coverage aggregate
