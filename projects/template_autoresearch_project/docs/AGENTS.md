# Agent Notes

`projects/template_autoresearch_project/docs/` is documentation only. Keep
business logic in `../src/`, orchestration in `../scripts/`, and generated
artifacts under `../output/`.

When adding a configurable loop feature, update:

- `../autoresearch.yaml` for readiness controls and required artifacts.
- `../manuscript/config.yaml` for project-local research questions and loop
  stages.
- [configuration.md](configuration.md) and [outputs.md](outputs.md) for the
  public contract.
- Project tests under `../tests/` and the root public-project contract tests.

Do not add network calls, LLM calls, autonomous approval loops, or generated
code execution to this exemplar. Human review remains an explicit report
packet, not an automated decision.

