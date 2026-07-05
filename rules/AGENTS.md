# AGENTS — Rules Directory

This document tells AI agents how to discover, interpret, and enforce rules
defined in this directory.

---

## Discovery

When entering any project or manuscript context, check for a `rules/` sibling
or parent directory.  Load `rules.yaml` from the most-specific matching
rule set first, then fall back to broader scopes.

```
rules/<project-slug>/rules.yaml   # most specific
rules/templates/<template>/rules.yaml  # fallback exemplar
```

---

## Interpreting Rule Kinds

### Soft rules (`soft/`)

- Treat as **guidelines and preferences**.
- Apply judgment: follow the spirit, not the letter.
- When generating text, code, or reviews, surface any deviation as a
  suggestion, not a blocker.

### Strong rules (`strong/`)

- Treat as **hard constraints**.
- Validate them before marking a task complete.
- If a strong rule is violated, **stop and report** the violation with the
  path of the offending file and the constraint that was broken.
- Do not silently skip strong-rule checks.

---

## Enforcement Workflow

1. Load `rules.yaml` → identify `rule_kinds` present.
2. For each `strong/` schema, run the described validation.
3. For each `soft/` guideline, apply as a prompt constraint during generation.
4. Report results: pass / warn / fail per rule.

---

## Adding New Rules

1. Copy the appropriate template from `rules/templates/`.
2. Update `rules.yaml` metadata (type, description, version, scope).
3. Edit soft guidelines in `soft/`.
4. Edit strong schemas in `strong/`.
5. Bump `version` if any strong constraint changes.

---

## Key Files

| File | Purpose |
|------|---------|
| `rules.yaml` | Machine-readable rule set metadata |
| `soft/*.md`  | Human/agent-readable guideline prose |
| `strong/*.yaml` | Machine-enforceable constraint schemas |
| `README.md`  | Human-readable rule set overview |
| `AGENTS.md`  | This file — agent-facing instructions |
