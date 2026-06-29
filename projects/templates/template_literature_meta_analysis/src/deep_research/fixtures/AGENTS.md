# src/deep_research/fixtures/

`recorded_report.json` is a synthetic, serialized `DeepResearchResult` (provider,
job_id, status, output_text, citations, trace, raw, plus the originating
request) consumed by `replay_recorded_report()`. Shape mirrors
`infrastructure.search.deep_research.artifacts._format_json_report`. Replay fails
closed if this file is missing — never fabricate it at runtime.
