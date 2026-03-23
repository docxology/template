# docs/ — Traditional Newspaper project documentation

Operational notes for the `traditional_newspaper` exemplar: sixteen core folios, supplemental S01–S03, glossary `98`, tabloid multicolumn PDF via the template pipeline.

**Quick links:** [Agent instructions](agent_instructions.md) · [Architecture](architecture.md) · [Testing](testing_philosophy.md) · [Rendering](rendering_pipeline.md) · [Syntax](syntax_guide.md)

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| [agent_instructions.md](agent_instructions.md) | Constraints before changing code or manuscript | Agents, developers |
| [architecture.md](architecture.md) | `src/newspaper/` → scripts → outputs | Developers |
| [testing_philosophy.md](testing_philosophy.md) | No mocks, subprocess stats, PNG tests | Developers |
| [rendering_pipeline.md](rendering_pipeline.md) | Preamble, figures, combine order | Authors |
| [syntax_guide.md](syntax_guide.md) | Pandoc `{=latex}` and LaTeX-in-markdown | Authors |
| [style_guide.md](style_guide.md) | Pointers to repo standards | Everyone |

## Navigation

- Before editing Python: [agent_instructions.md](agent_instructions.md), then [architecture.md](architecture.md).
- Before editing tests: [testing_philosophy.md](testing_philosophy.md).
- Before editing folios: [rendering_pipeline.md](rendering_pipeline.md), [syntax_guide.md](syntax_guide.md).

## See also

- [../AGENTS.md](../AGENTS.md) — project technical index
- [../README.md](../README.md) — quick start and commands
- [../manuscript/README.md](../manuscript/README.md) — slice list and assets
