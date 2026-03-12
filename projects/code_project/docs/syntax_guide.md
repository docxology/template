# Syntax Guide

This document defines the syntax conventions for documentation and markdown inside the `code_project` exemplar.

## 1. Markdown Links

Hyperlinks should be informative and never use placeholder text like "Click here".

- **BAD**: [this link](https://github.com/docxology/template) to see the template.
- **GOOD**: See the [Research Project Template](https://github.com/docxology/template).

## 2. LaTeX Cross-References

Inside `manuscript/` files, use `\ref{}` for explicit cross-referencing. Do not hardcode numbers.

- **BAD**: See Table 1 or Figure 2.
- **GOOD**: See Table `\ref{tab:optimization_results}` or Figure `\ref{fig:convergence}`.

## 3. Variable Injection (Madlibs)

When specifying numeric results in the manuscript, use the `{{VARIABLE_NAME}}` syntax instead of hardcoding numbers. These variables are hydrated dynamically by `scripts/z_generate_manuscript_variables.py`.

- **BAD**: The algorithm took 165 iterations.
- **GOOD**: The algorithm took `{{RESULT_MAX_ITERATIONS}}` iterations.

## 4. Code Blocks

Always tag code blocks securely with their language:

```python
def example():
    return True
```

## 5. Table Captions (Pandoc)

When writing tables in the manuscript, use the Pandoc table caption syntax:

```markdown
| Step Size | Converged |
|-----------|-----------|
| 0.01      | Yes       |

: Optimization convergence results. \label{tab:convergence}
```
