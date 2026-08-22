# Validation Package

## Purpose

Validation owns deterministic checks for manuscripts, rendered PDFs, output
trees, documentation, repository health, line-count gates, evidence registries,
and security/plugin guard wrappers. It should report actionable issues without
running project science or rendering stages itself.

## Map

| Area | Files | Role |
| --- | --- | --- |
| Content preflight | `content/prerender.py`, `content/markdown_validator.py`, `content/pdf_validator.py` | Markdown/PDF checks used before or after rendering. |
| Markdown discovery | `content/discovery.py` | Canonical markdown enumeration scopes: `tree`, `repo`, `link_audit`. |
| Output checks | `output/` | Output structure, copied-output parity, artifact manifests, prose-quality integration. |
| Integrity checks | `integrity/` | Hashes, completeness, link extraction, link policies, manifests. |
| Documentation checks | `docs/` | Link, package-count, shell-contract, memory-decision, public-audit, quality checks. |
| Repo audit | `repo/` | Repository scanner and audit orchestration. |
| CLI | `cli/main.py` | `python -m infrastructure.validation.cli ...`. |
| Gates | `line_count.py`, `security_gate.py`, `plugin_export.py` | Shared logic for scripts under `scripts/gates/`. |
| Evidence registry | `evidence_registry.py`, `evidence_registry_collectors.py` | `VerifiedEvidenceRegistry` of project-local facts plus `validate_text_against_registry`; `register_all_project_facts` collects numbers/citations/labels from config, JSON, CSV, claim ledgers, BibTeX, markdown, and output artifacts. Output-derived facts are admitted only through the explicit stable inventory. Public exemplars use Git-shippable mode; lifecycle-aware callers may authorize local mode only for a resolved non-template project. Runtime/build/control and hidden-path files are excluded in both, so they cannot support manuscript claims or perturb the registry. Source paths must exist inside the project or, for shared contracts, inside the repository boundary. Large JSON arrays are treated as raw matrices/corpora and bounded out; scalar summaries and CSV/claim-ledger evidence remain eligible. |
| Claim bindings | `claims.py` | Roster-level `bound` / `not_applicable` / `external_data` inventory, source-derived regression-pin validation, and versioned claim-binding receipts. |
| Publication audit | `publication/` | Composes drift, methods, evidence, figure, artifact, rendered-output, and no-mock checks into a stable public-readiness report. |
| XML parser policy | `xml_parser_policy.py` | `validate_xml_parser_policy`: AST import-level guard forbidding stdlib `xml.*` parsers and `lxml`, requiring `defusedxml` (DEP-DEFUSEDXML-1). |
| Rendered snapshot | `rendered_snapshot/` | Package (`__init__.py` public API + private `_scan.py`/`_records.py`). Commits the current rendered-input and validation-report fingerprints used to detect output drift after a targeted render / validation run (the strict `check_rendered_provenance` snapshot surface). |

## Boundaries

- Do not duplicate markdown file discovery; use `content.discovery`.
- Do not import high-level rendering from validation leaves. Shared pre-render
  logic belongs in validation content leaves that rendering may safely import.
- Do not weaken diagnostic codes. Stable dotted codes are downstream contracts.
- Validation may inspect generated artifacts, but should not hand-edit them.
  Fix the source producer and regenerate.
- New evidence facts derive `checked_at` from the deterministic build epoch;
  preserve existing fact timestamps and carry one `SOURCE_DATE_EPOCH` through
  render and validation.
- Link checks must respect local-only private mirrors and generated-output skip
  policies.

## Public Commands

```bash
uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .
uv run python -m infrastructure.validation.cli integrity projects/templates/template_code_project/output
uv run python -m infrastructure.validation.cli publication-audit --project templates/template_code_project --strict --rendered --format markdown
uv run python scripts/gates/module_line_count_check.py
uv run python scripts/gates/security_scan.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
```

## Tests

```bash
uv run pytest tests/infra_tests/validation -q
uv run pytest tests/infra_tests/project/test_thin_orchestrator_drift.py tests/infra_tests/validation/test_line_count.py -q
```

For output or manuscript behavior, also run the target project validation stage
or project-native validator named by that project’s `AGENTS.md`.

## Change Checklist

- Add or update a focused test for every new validator rule.
- Keep diagnostic messages stable enough for `jq`/`rg` users.
- Update `docs/_generated/COUNTS.md` only through `scripts/docgen/counts.py`
  when counts or gate facts change.
- Run strict drift checks after changing docs/gates:
  `uv run python scripts/audit/check_template_drift.py --strict`.

## See Also

- [`README.md`](README.md)
- [`docs/AGENTS.md`](docs/AGENTS.md)
- [`output/AGENTS.md`](output/AGENTS.md)
- [`../project/AGENTS.md`](../project/AGENTS.md)
