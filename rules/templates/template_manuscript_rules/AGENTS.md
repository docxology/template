# AGENTS — template_manuscript_rules

This rule set governs **research manuscripts**. Load it when drafting,
reviewing, or editing any manuscript that has adopted these rules.

---

## Soft Rules (guidelines)

### `soft/writing-guide.md`
Apply these preferences during writing and editing:
- Flag passive voice and jargon overuse as suggestions (not blockers).
- Summarise any tone drift at the end of a review pass.

### `soft/citation-style.md`
Follow this guide for all in-text citations and reference lists:
- Apply the citation format defined here consistently.
- Flag any citation that cannot be verified against a DOI or URL.

---

## Strong Rules (hard constraints)

### `strong/reference-schema.yaml`
Before finalising a manuscript:
1. Validate every reference entry against the schema.
2. Ensure all required fields are present and non-empty.
3. Do **not** mark a manuscript complete with invalid references.

### `strong/section-schema.yaml`
When drafting or reviewing section structure:
1. Confirm required sections are present in the correct order.
2. Confirm forbidden section names are absent.
3. Report any violation with the section heading and the violated constraint.

---

## Escalation

If a strong rule cannot be evaluated (e.g., no structured reference data
available), report: `STRONG RULE UNEVALUATED: <rule-name> — <reason>`.
Do not silently pass.
