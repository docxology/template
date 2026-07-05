# Style Guide

These are **soft** guidelines — apply them with judgment. Surface deviations
as suggestions, not hard blockers.

---

## Code Style

### General
- Prefer clarity over cleverness. A reader should understand a function
  without reading its callees.
- Keep functions short: aim for ≤ 40 lines of logic per function.
- One responsibility per module. If a module name requires "and", split it.

### Naming
- Use descriptive names; avoid single-letter variables outside list
  comprehensions and well-known loop indices (`i`, `j`, `k`).
- Boolean variables and functions should read as statements: `is_valid`,
  `has_errors`, `can_retry`.
- Constants: `UPPER_SNAKE_CASE`. Classes: `PascalCase`. Functions/variables:
  `snake_case`.

### Comments & Docstrings
- Write docstrings for all public functions, classes, and modules.
- Comments explain *why*, not *what*. Code should be self-explanatory for
  the *what*.
- Avoid commented-out dead code in main branches; use version control instead.

---

## Documentation Style

### Prose
- Use active voice. Prefer "The function returns X" over "X is returned by
  the function".
- Keep sentences short (target ≤ 25 words).
- Use present tense for descriptions ("This module handles…").

### Headings
- Use sentence case for headings ("Getting started", not "Getting Started").
- Only one H1 (`#`) per document.

### Code Blocks
- Always specify the language for fenced code blocks (` ```python `).
- Show realistic examples; avoid `foo` / `bar` unless illustrating syntax only.

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

---

## Deviation Handling

If following a guideline would significantly harm readability or correctness
in a specific context, deviate and leave a comment explaining the exception.
