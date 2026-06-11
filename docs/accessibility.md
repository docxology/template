# Accessibility in Research Documentation

This guide describes the accessibility features of the template/ documentation system.

## Semantic Markup

- **Structure**: H1→H2→H3 hierarchy with meaningful heading text
- **Lists**: Use proper `<ul>/<ol>` — never ASCII tables for tabular data
- **Links**: Descriptive link text; never "click here"

## Math & Equations

- LaTeX math declared inside `$...$` (inline) and `$$...$$` (display)
- MathJax/KaTeX auto-loads in HTML; ensure semantic alt-text in PDF

## Color & Contrast

- PDF production uses black text on white background (high contrast)
- Figures: avoid color-only distinction; add patterns/labels

## Enforced Accessibility Checks

Accessibility is enforced by the markdown validator, not by `config.yaml` flags.
Run `uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/`
to check the manuscript. The validator inspects:

| Check | What it verifies |
|-------|------------------|
| Image alt-text | Markdown images declare descriptive alt-text |
| Figure captions | Figures carry caption text |
| Link integrity | Internal and cross-references resolve; no bare "click here" links |
| Heading structure | H1→H2→H3 hierarchy is well-formed |

## Testing Accessibility

```bash
# Validate manuscript markdown (alt-text, figure captions, links, structure)
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/

# Check PDF structure with pdftotext + grep for heading levels
pdftotext output/{name}/pdf/{name}_combined.pdf - | grep '^Chapter\|^Section'
```

## Further Reading

- WCAG 2.1 Guidelines (W3C)
- [arXiv accessibility requirements](https://arxiv.org/help/accessibility)
