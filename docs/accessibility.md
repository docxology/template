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
- Color palettes from `infrastructure/documentation/` adhere to WCAG AA

## Key `manuscript/config.yaml` Accessibility Flags

| Key | Advisory | Test-Enforced |
|-----|----------|---------------|
| `include_alt_text` | ✓ | — |
| `figure_captions_required` | — | ✓ |
| `equation_label_prefix` (eq) | ✓ | ✓ |

## Testing Accessibility

```bash
# Verify all figures have Alt text in source markdown
uv run python scripts/validate_alt_text.py

# Check PDF structure with pdftotext + grep for heading levels
pdftotext output/combined.pdf - | grep '^Chapter\|^Section'
```

## Further Reading

- WCAG 2.1 Guidelines (W3C)
- [arXiv accessibility requirements](https://arxiv.org/help/accessibility)
