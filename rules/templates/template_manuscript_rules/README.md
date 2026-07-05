# template_manuscript_rules

A curated exemplar rule set for **research manuscripts** — papers, reports,
and formal documentation.

This template provides a starting point for governing writing tone, citation
formatting, reference validation, and section structure within a manuscript.

---

## Contents

```
template_manuscript_rules/
├── rules.yaml                  # Machine-readable metadata
├── README.md                   # This file
├── AGENTS.md                   # Agent-facing instructions
├── .gitignore
├── soft/
│   ├── writing-guide.md        # Writing style and tone guidelines
│   └── citation-style.md       # Citation formatting guidelines
└── strong/
    ├── reference-schema.yaml   # Formal reference validation schema
    └── section-schema.yaml     # Formal section structure schema
```

---

## Quick Start

1. Copy this directory into your manuscript's `rules/` folder:
   ```bash
   cp -r rules/templates/template_manuscript_rules/ rules/my-manuscript/
   ```
2. Edit `rules.yaml` — update `description`, `version`, and `scope`.
3. Adjust allowed sections in `strong/section-schema.yaml`.
4. Refine prose in `soft/writing-guide.md` and `soft/citation-style.md`.

---

## Rule Summary

| Rule | Kind | File |
|------|------|------|
| Writing style & tone | Soft | `soft/writing-guide.md` |
| Citation formatting | Soft | `soft/citation-style.md` |
| Reference validation | Strong | `strong/reference-schema.yaml` |
| Section structure | Strong | `strong/section-schema.yaml` |

---

## License

CC0-1.0 — public domain. Copy, adapt, redistribute freely.
