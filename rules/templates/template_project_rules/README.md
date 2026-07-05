# template_project_rules

A curated exemplar rule set for **software projects**.

This template provides a starting point for governing source code, CI pipelines,
testing infrastructure, and module structure within a project.

---

## Contents

```
template_project_rules/
├── rules.yaml                  # Machine-readable metadata
├── README.md                   # This file
├── AGENTS.md                   # Agent-facing instructions
├── .gitignore
├── soft/
│   ├── style-guide.md          # Prose and code style guidelines
│   └── review-process.md       # Review workflow guidelines
└── strong/
    ├── coverage-gate.yaml      # Formal test coverage thresholds
    └── module-structure.yaml   # Formal module structure constraints
```

---

## Quick Start

1. Copy this directory into your project's `rules/` folder:
   ```bash
   cp -r rules/templates/template_project_rules/ rules/my-project/
   ```
2. Edit `rules.yaml` — update `description`, `version`, and `scope`.
3. Adjust thresholds in `strong/coverage-gate.yaml`.
4. Refine prose in `soft/style-guide.md` and `soft/review-process.md`.

---

## Rule Summary

| Rule | Kind | File |
|------|------|------|
| Code style & prose | Soft | `soft/style-guide.md` |
| Review workflow | Soft | `soft/review-process.md` |
| Coverage thresholds | Strong | `strong/coverage-gate.yaml` |
| Module structure | Strong | `strong/module-structure.yaml` |

---

## License

CC0-1.0 — public domain. Copy, adapt, redistribute freely.
