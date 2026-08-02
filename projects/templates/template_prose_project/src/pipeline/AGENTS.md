# `template_prose_project/src/pipeline/` - agent guide

## Purpose

Project-specific check orchestration over a pre-analysed
`ManuscriptReportLike`. `src/pipeline/` itself imports no `infrastructure`
modules — the thin `scripts/` layer calls
`infrastructure.prose.analyze_manuscript` and hands the report in.

## Rules

- Put `run_prose_pipeline` orchestration in `__init__.py`.
- Put configured check logic in `checks.py`.
- Add or change a check by updating `CHECK_REGISTRY` and covering both pass and
  fail cases in `tests/test_pipeline.py`.
- Keep scripts as CLI shims around this package.

## See Also

- [`README.md`](README.md) - quick reference
- [`../AGENTS.md`](../AGENTS.md) - source-layer contract
