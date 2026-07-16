# Deep Research Replay

This package provides the advanced exemplar's deterministic Stage 08 path. It
constructs the same provider-neutral request object used by live OpenAI or
Gemini deep-research dispatch, then replays a tracked report instead of making a
network call.

`dispatch_offline_replay(query, output_dir, fixture_path=None)` writes
`deep_research_replay.json` and returns the real request/result models plus the
artifact path. The default fixture is under `fixtures/` and contains a synthetic
demonstration summary with real, metadata-only primary-paper citations. Its
provider is explicitly `curated-fixture`, its job ID is blank, and its trace
labels curation rather than implying a paid provider generated the report.

Run from the template repository root:

```bash
uv run python projects/templates/template_advanced_literature_review/scripts/08_deep_research_dispatch.py
uv run pytest projects/templates/template_advanced_literature_review/tests/test_deep_research_dispatch.py -q
```

This source package never performs live dispatch. A fork that enables paid
providers should expose that behavior through a separate explicit command.
