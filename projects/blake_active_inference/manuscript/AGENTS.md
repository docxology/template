# Manuscript - Blake Active Inference

## Purpose

Academic manuscript source files for "The Doors of Perception are the Threshold of Prediction."

## File Discovery

- Main sections: `00_preamble.md` through `06_conclusion.md`
- Synthesis subfiles: `04a_boundary.md` through `04h_collectives.md`

## Rendering

Rendered by infrastructure layer via:

```bash
uv run python scripts/03_render_pdf.py --project blake_active_inference
```

## Key Content

- 8 thematic correspondences (Boundary, Vision, States, Imagination, Time, Space, Action, Collectives & Zoas)
- 20+ Blake quotations with Erdman edition references
- Mathematical equations in LaTeX notation

## Configuration

- `config.yaml` - Paper metadata (single source of truth for title, author, DOI)
- `preamble.md` - LaTeX packages (single source of truth for LaTeX configuration)
- `references.bib` - Bibliography

## Conventions

- All quotations cite plate/line numbers
- Markdown headings use Pandoc anchor syntax `{#anchor}`
- Include directives use `{{< include file.md >}}` syntax

## Math Formatting Rules

> [!CAUTION]
> LaTeX subscript notation is `}_{` (underscore), NEVER `}*{` (asterisk).
> Pandoc misparses `}*{` as markdown italic, causing entire sentences to render
> as run-on Unicode math italic text without word spacing.

### Required Patterns

| Pattern | Correct | Incorrect |
|:--------|:--------|:----------|
| Underbrace label | `\underbrace{...}_{text}` | `\underbrace{...}*{text}` |
| Expectation subscript | `\mathbb{E}_{q}[...]` | `\mathbb{E}*{q}[...]` |
| Variable subscript | `o_\tau` | `o*\tau` |
| Inline math | `$F$` | `F` (naked) |
| Display math | `\begin{equation}...\end{equation}` | `$$...$$` (use labeled equations) |

### Style Guidelines

- All display equations use `\begin{equation}\label{eq:name}...\end{equation}`
- Cross-reference equations with `Equation \ref{eq:name}`
- Inline math variables use `$...$` delimiters
- Greek letters: `$\theta$`, `$\pi$`, `$\mu$`, `$\eta$`, `$\varepsilon$`
- Precision symbol: `$\pi$` (context distinguishes from policy)
- Use `\text{...}` inside math for descriptive labels
