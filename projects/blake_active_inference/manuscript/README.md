# Manuscript Documentation

## Purpose

This directory contains the academic manuscript for "The Doors of Perception are the Threshold of Prediction: Active Inference and William Blake's Theory of Seeing."

## Structure

### Main Sections (in order)

| File | Section | Description |
|:-----|:--------|:------------|
| `00_preamble.md` | Thematic Atlas | Title page and theme overview table |
| `01_abstract.md` | Abstract | Paper abstract (2 paragraphs) |
| `02_introduction.md` | Introduction | Historical framing and thesis |
| `02a_related_work.md` | Related Work | Prior scholarship connecting Blake and cognition |
| `03_theoretical_foundations.md` | Theory | Active Inference mathematics |
| `04_synthesis.md` | Synthesis | Parent overview for eight thematic correspondences |
| `04a_boundary.md` | §4.1 Boundary | Doors of Perception = Markov Blanket |
| `04b_vision.md` | §4.2 Vision | Fourfold Vision = Hierarchical Model |
| `04c_states.md` | §4.3 States | Newton's Sleep = Prior Dominance |
| `04d_imagination.md` | §4.4 Imagination | Human Existence = Generative Model |
| `04e_time.md` | §4.5 Time | Eternity in Hour = Temporal Horizons |
| `04f_space.md` | §4.6 Space | World in Grain = Spatial Hierarchy |
| `04g_action.md` | §4.7 Action | Cleansing = Free Energy Minimization |
| `04h_collectives.md` | §4.8 Collectives | Jerusalem & Zoas = Shared & Factorized Models |
| `05_implications.md` | Implications | Philosophy, cognitive science, creativity |
| `06_conclusion.md` | Conclusion | Summary and future directions |

### Configuration

- `config.yaml` - Paper metadata (title, subtitle, author, DOI, keywords)
- `preamble.md` - LaTeX preamble packages (graphicx, amsmath, hyperref, etc.)
- `references.bib` - BibTeX bibliography

## Key Features

- **Mathematical Notation**: LaTeX equations for Free Energy, Markov blankets, precision
- **Dense Quotations**: 20+ Blake quotations with Erdman edition plate/line numbers
- **Correspondence Tables**: Systematic Blake → Active Inference mappings
- **Hierarchical Diagrams**: Fourfold vision and predictive processing parallels
- **Eight Thematic Correspondences**: Including the Four Zoas as factorized collective mind

## Math Formatting Guide

All equations use LaTeX notation rendered via Pandoc. Key rules:

- **Display equations**: `\begin{equation}\label{eq:name}...\end{equation}` (always labeled)
- **Inline math**: `$variable$` delimiters
- **Cross-references**: `Equation \ref{eq:name}`

> **⚠️ Critical**: LaTeX subscripts use `}_{` (underscore), **never** `}*{` (asterisk).
> Pandoc misparses `*` as markdown italics, causing text to render as run-on
> Unicode math italic characters without word spacing.

### Core Equations

| Label | Name | File |
|:------|:-----|:-----|
| `eq:free_energy` | Variational Free Energy | `03_theoretical_foundations.md` |
| `eq:fe_decomposition` | FE Decomposition | `03_theoretical_foundations.md` |
| `eq:conditional_independence` | Conditional Independence | `03_theoretical_foundations.md` |
| `eq:expected_free_energy` | Expected Free Energy | `03_theoretical_foundations.md` |
| `eq:hierarchical_model` | Hierarchical Factorization | `03_theoretical_foundations.md` |
| `eq:precision` | Precision | `03_theoretical_foundations.md` |
| `eq:prediction_error` | Prediction Error | `03_theoretical_foundations.md` |
| `eq:temporal_hierarchy` | Temporal Hierarchy | `03_theoretical_foundations.md` |
| `eq:multi_agent` | Multi-Agent Coordination | `03_theoretical_foundations.md` |
| `eq:mean_field` | Mean-Field Approximation | `03_theoretical_foundations.md` |
| `eq:model_evidence` | Model Evidence | `03_theoretical_foundations.md` |
| `eq:agent_identity` | Agent Identity | `04d_imagination.md` |
| `eq:cleansing` | Cleansing | `04g_action.md` |

## Rendering

```bash
./run.sh                                # Full pipeline
# or
uv run python scripts/03_render_pdf.py --project blake_active_inference
```
