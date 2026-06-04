# Test Support Helpers

> Shared scaffold factories imported by the infrastructure test suites

**Quick Reference:** [projects.py](projects.py) | [Test Suite](../README.md) | [Infra Tests](../infra_tests/README.md)

## Directory Structure

| Module | Description |
|--------|-------------|
| [`projects.py`](projects.py) | `make_project` / `make_repo` / `write_doc` — build minimum-valid synthetic project trees under `tmp_path` for discovery, rendering, and orchestration tests |

## Key Conventions

- Synthetic projects live under `tmp_path` only — **never** under the real `projects/` tree.
- Default slug is `template_test`: a stable, readable stand-in that does not couple tests to the six public exemplars.
- Pass `program="templates"` to nest under `projects/templates/<name>/` so discovery yields the qualified name `templates/<name>`.

## See Also

- [AGENTS.md](AGENTS.md) — Technical guide
- [Test Suite](../README.md) — Full test documentation
- [Infrastructure Tests](../infra_tests/README.md) — Primary consumer of these helpers
