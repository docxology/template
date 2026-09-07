# src/ — template_pools_rules_tools

Integration readers and appliers for fonds, rules, and tools pools.

| Module | Role |
| --- | --- |
| `type_defs.py` | TypedDict definitions — single source of truth for all return shapes |
| `fonds_reader.py` | Load fonds templates |
| `rules_applier.py` | Apply rules packs |
| `strong_rule_evaluator.py` | Evaluate strong (formal) rule constraints |
| `tools_invoker.py` | Invoke tool templates |
| `integration.py` | End-to-end integration workflow |
| `figure_support.py` | Figure themes, status maps, and the eight manuscript label/filename provenance specs |
| `figures.py` | Compatibility façade and shared plot orchestration; re-exports the figure-support contract |
| `cover_figure.py` | Cover-art renderer and cover-specific layout helpers |
| `rule_hierarchy_figure.py` | Rule-hierarchy renderer and hierarchy-specific layout helpers |

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
