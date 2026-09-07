# tests/

No-mocks test suite for `src/`, 90%+ coverage required.

| File | Covers |
|------|--------|
| `test_paths.py` | Repo-root discovery |
| `test_deck_tokens.py` | Live repo-fact sourcing |
| `test_token_resolution.py` | `{{TOKEN}}` substitution + raise-on-missing |
| `test_cliche_lint.py` | Word-boundary cliché denylist |
| `test_content_loader.py` | YAML → `DeckContent` token resolution plus budget-bound authored counts and a source-bound roster split derived from the exact live public scope |
| `test_deck_audit.py` | Shared token+cliche audit |
| `test_diligence_audit.py` | Fact-token → citation coverage |
| `test_render_orchestration.py` | Real end-to-end render (writes real PDF/PPTX) |
| `test_chart_rendering.py` | three real matplotlib charts write distinct image bytes; real donut wedge/text artists select black/white at ≥4.5:1 and fail closed for an unreadable theme |
| `test_coverage_chart_data.py` | `src/coverage_chart_data.py` parses real per-exemplar coverage rows from `docs/_generated/COUNTS.md`, sorted and validated |
| `test_infra_facts.py` | `src/infra_facts.py`'s live `infrastructure/` subpackage/file introspection and token reconciliation against a real git checkout |
| `test_standalone_slides.py` | `src/standalone_slides.py`'s per-slide standalone Markdown pages, QR-URL attachment, and path-traversal rejection |

`conftest.py` puts this project's `src/` and the monorepo root on
`sys.path` regardless of which `pyproject.toml` pytest resolves as its
rootdir/configfile for a given invocation.
