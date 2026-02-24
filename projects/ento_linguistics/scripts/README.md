# scripts/ — Thin Orchestrators

## Overview

Scripts are **thin orchestrators**: they import and call tested methods from `src/`, handle file I/O, and drive the analysis pipeline. Business logic lives exclusively in `src/`.

## Pipeline Entry Points

| Script | Command | Purpose |
|--------|---------|---------|
| `01_build_corpus.py` | `uv run python scripts/01_build_corpus.py` | Build literature corpus from entomological sources |
| `02_generate_figures.py` | `uv run python scripts/02_generate_figures.py` | **Main entry point** — clean slate, regenerate all 11 figures + data |

> `02_generate_figures.py` wipes `output/figures/` and `output/data/` on every run, then regenerates all outputs from scratch.

## Helper Scripts (prefixed `_`)

Run directly but **not** auto-discovered by the pipeline:

| Script | Command | Purpose |
|--------|---------|---------|
| `_analysis_pipeline.py` | `uv run python scripts/_analysis_pipeline.py` | Full analysis pipeline (all stages) |
| `_conceptual_mapping_script.py` | `uv run python scripts/_conceptual_mapping_script.py` | Concept mapping and network generation |
| `_convert_corpus.py` | `uv run python scripts/_convert_corpus.py` | Corpus format conversion |
| `_discourse_analysis_script.py` | `uv run python scripts/_discourse_analysis_script.py` | Discourse pattern analysis |
| `_domain_analysis_script.py` | `uv run python scripts/_domain_analysis_script.py` | Domain-specific terminology analysis |
| `_example_figure.py` | `uv run python scripts/_example_figure.py` | Example figure generation |
| `_generate_domain_figures.py` | `uv run python scripts/_generate_domain_figures.py` | Per-domain frequency and ambiguity figures |
| `_generate_missing_figures.py` | `uv run python scripts/_generate_missing_figures.py` | Regenerate any missing figures |
| `_generate_scientific_figures.py` | `uv run python scripts/_generate_scientific_figures.py` | Scientific simulation figures |
| `_literature_analysis_pipeline.py` | `uv run python scripts/_literature_analysis_pipeline.py` | Full literature mining + analysis |
| `_manuscript_preflight.py` | `uv run python scripts/_manuscript_preflight.py --strict` | Validate figure refs, glossary, bibliography |
| `_quality_report.py` | `uv run python scripts/_quality_report.py` | Readability, integrity, reproducibility snapshot |
| `_register_manuscript_figures.py` | `uv run python scripts/_register_manuscript_figures.py` | Figure registry updates |
| `_render_pdf_override.py` | `uv run python scripts/_render_pdf_override.py` | Custom PDF rendering override |
| `_scientific_simulation.py` | `uv run python scripts/_scientific_simulation.py` | Simulation workflows |

## Thin Orchestrator Pattern

```python
# Scripts do this:
from src.analysis.term_extraction import TerminologyExtractor
from src.visualization.concept_visualization import ConceptVisualizer

extractor = TerminologyExtractor()
terms = extractor.extract_terms(corpus)   # business logic in src/

visualizer = ConceptVisualizer()
visualizer.create_domain_comparison_plot(domain_data, filepath, terms)  # src/ renders
```

Scripts **never** implement algorithms or mathematical computations directly.

## See Also

- [`AGENTS.md`](AGENTS.md) — detailed script documentation
- [`../src/AGENTS.md`](../src/AGENTS.md) — available `src/` modules
- [`../docs/development_workflow.md`](../docs/development_workflow.md) — commands and workflow
