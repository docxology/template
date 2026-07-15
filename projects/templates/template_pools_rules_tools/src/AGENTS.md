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
| `figures.py` | Compatibility façade, shared plots, and the eight manuscript label/filename provenance specs |
| `cover_figure.py` | Cover-art renderer and cover-specific layout helpers |
| `rule_hierarchy_figure.py` | Rule-hierarchy renderer and hierarchy-specific layout helpers |

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
