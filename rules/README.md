# Rules

This directory contains **rules** — specifications that govern how projects,
manuscripts, code, and data within this repository should be structured,
written, reviewed, and validated.

Rules come in two kinds:

| Kind   | Description |
|--------|-------------|
| **Soft**   | Prompt-like guidelines (prose, style, review process). Interpreted by humans and AI agents. |
| **Strong** | Formal constraints (YAML schemas, coverage gates, structure invariants). Machine-enforceable. |

---

## Directory Layout

```
rules/
├── README.md          # This file
├── AGENTS.md          # Agent-facing guidance for consuming rules
├── templates/         # Curated, reusable rule-set exemplars
│   ├── template_project_rules/
│   └── template_manuscript_rules/
└── <project-slug>/    # Per-project rule sets (not tracked here)
```

---

## Using a Template

Copy any template under `rules/templates/` into a project:

```bash
cp -r rules/templates/template_project_rules/ rules/my-project/
```

Then edit `rules.yaml`, the soft guidelines, and the strong schemas to match
your project's requirements.

---

## Rule Scopes

| Scope      | Applies to |
|------------|------------|
| `project`  | Source code, CI, testing infrastructure |
| `manuscript` | Research papers, reports, documentation |
| `all`      | Cross-cutting concerns |

---

## Versioning

Each rule set carries a `version` field in its `rules.yaml`.
Increment the version when constraints change in a breaking way.

---

## License

All exemplars in `rules/templates/` are released under **CC0-1.0** (public domain).
