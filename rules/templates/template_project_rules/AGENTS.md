# AGENTS — template_project_rules

This rule set governs **software projects**. Load it when working in any
project context that has adopted these rules.

---

## Soft Rules (guidelines)

### `soft/style-guide.md`
Apply these preferences during code generation and review:
- Flag deviations as suggestions (not blockers).
- Summarise any style drift at the end of a review pass.

### `soft/review-process.md`
Follow this workflow when performing or requesting code reviews:
- Use the stage labels defined in the guide.
- Do not skip the "security scan" stage for changes touching auth, crypto,
  or network code.

---

## Strong Rules (hard constraints)

### `strong/coverage-gate.yaml`
Before marking any PR or task complete:
1. Confirm test coverage meets or exceeds the thresholds.
2. If coverage data is unavailable, surface a warning and halt.
3. Do **not** bypass this gate.

### `strong/module-structure.yaml`
When creating or refactoring modules:
1. Verify the directory layout matches the required pattern.
2. Confirm forbidden patterns are absent.
3. Report any violation with the exact path and the violated constraint.

---

## Escalation

If a strong rule cannot be evaluated (e.g., no test runner present),
report: `STRONG RULE UNEVALUATED: <rule-name> — <reason>`.
Do not silently pass.
