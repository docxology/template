# validation/docs/ - Quick Reference

Tests for documentation linters under `infrastructure.validation.docs`.

## Run

```bash
uv run pytest tests/infra_tests/validation/docs/ -q
```

## Contents

| File | Purpose |
| --- | --- |
| `test_consistency_lint.py` | Module-count and ghost-project claims |
| `test_cross_link_lint.py` | Relative Markdown link resolution |
| `test_doc_pair_lint.py` | Folder-level AGENTS/README coverage |
| `test_mermaid_lint.py` | Mermaid discovery and `mmdc` rendering |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
