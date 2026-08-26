# Repo TO-DO — future cross-cutting work

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests, source-bound evidence, and accurate documentation.

This is the root repository backlog and contains future work only: cross-cutting
infrastructure, CI, documentation, release, security, and reproducibility
improvements. Completed work is preserved in [`CHANGELOG.md`](CHANGELOG.md) or
the dated maintenance records; generated facts remain owned by their
generators; exemplar-specific work belongs in the relevant public
`projects/templates/*/TODO.md`.

Every active row has a stable ID and the complete contract
`ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control`.
Active work is decomposed into Minor or Medium slices. A missing owner,
external receipt, or optional tool is a blocker, never an implicit success.

## Live baseline and constraints

The public roster is authoritative in
[`docs/_generated/active_projects.md`](docs/_generated/active_projects.md), and
measured facts are authoritative in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md). Re-derive them before
editing this file or closing a row.

The deterministic default is offline and one-process-per-project. Network,
LLM, live-data, container, formal-tool, raster, and publication paths are
explicitly opt-in and fail closed when unavailable. Private sidecars,
rotating projects, branch protection, CODEOWNERS review, and owner-authorized
promotion are outside the evidence a local checkout can establish.

## Active root backlog

These are the prioritized scoped improvements and remaining root-level actions, classified by Minor, Medium, and Major categories.

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DOC-LINKS-STANDARDIZE-MIN-1` | completed | Minor | Documentation links, frontmatter schema | Standardize workflow skill frontmatter metadata and fix documentation links / CLI option descriptions. | verified documentation and metadata manifest | `uv run python -m infrastructure.skills check-contracts` | missing or malformed metadata fields must fail contract check |
| `INFRA-MODULES-ENHANCE-MED-1` | completed | Medium | Doctor, Validation, Search, Reference modules | Enhance infrastructure doctor detectors (DOC204 bib/preamble check), search cache query normalization, and reference resolver resilience. | enhanced infra test suite | `uv run pytest tests/infra_tests/doctor tests/infra_tests/search tests/infra_tests/reference -v` | invalid cache payload or broken bibtex must be rejected |
| `PROVENANCE-DAG-HARDEN-MAJ-1` | completed | Medium | Provenance DAG models and store | Implement unified provenance DAG graph integrity validator and cycle / missing reference checks with full CLI interface. | provenance validation test suite | `uv run pytest tests/infra_tests/provenance -v` | circular or dangling edges must fail validation |
| `AUTORESEARCH-ORCHESTRATION-MAJ-1` | completed | Medium | AutoResearch engine, planner, reports | Add AutoResearch multi-phase pipeline orchestration engine with structured phase transitions, budget enforcement, and run ledger logging. | autoresearch orchestration test suite | `uv run pytest tests/infra_tests/autoresearch -v` | budget exhaustion or unapproved publication gates must halt loop |
| `MANUSCRIPT-RENDER-OPTIMIZE-MAJ-1` | completed | Medium | Rendering manager, cache, composition | Add modular manuscript section caching and parallel format dispatch options to optimize multi-format rendering passes. | rendering benchmark report | `uv run pytest tests/infra_tests/rendering -v` | corrupted cache or missing required sections must fail render |
| `EXECUTABLE-BUNDLE-MAJ-1` | partial | Medium | Immutable bundle verifier, pinned runtime, isolated container | Container-build half is now proven on this host (colima; image `template-bundle-verify:2026-08-22` built successfully from the regenerated bundle after fixing the unbuildable default `python3.14` apt request). Remaining: attach a full offline-container verification receipt for the representative bundle run; see `EXECUTABLE-BUNDLE-MAJ-2` for the payload-composition gap discovered during that run. | offline-container verification receipt | `uv run python scripts/runner/bundle_executable.py --project templates/template_code_project` | changed payload, missing lock, private symlink, path escape, or unavailable container must fail/record blocked |
| `CLEAN-CHECKOUT-MAJ-1` | blocked-external | Medium | Local disposable rehearsal and hosted Linux runner | Run two deterministic hosted-Linux rehearsals and attach the owner/platform receipt; local generated render output is restored only inside the disposable clone after path-boundary validation. | clean-checkout rehearsal receipt | `uv run python scripts/maintenance/release_rehearsal.py --execute --receipt /tmp/template-clean-checkout.json` | non-generated mutation, dirty final tree, changed revision, or unequal deterministic runs must fail |
| `ARCHIVAL-TRACKER-MIN-1` | blocked-external | Medium | Credential-free provider evidence and current public roster | Refresh the archival tracker only from current queue/browse evidence and record accepted, pending, verified, unavailable, rate-limited, and excluded states with as-of dates. | archival tracking receipt | `uv run python scripts/runner/archive_publication.py --project templates/template_code_project --providers software_heritage` | missing credential/provider or standalone bundle must never report a completed deposit |
| `SECURITY-OWNERSHIP-1` | blocked-external | Medium | Administrator branch-protection and CODEOWNERS receipt | Obtain administrator evidence for required checks, review, force-push protection, and sensitive-path review; local health must remain distinct from authority. | administrator authority receipt | `uv run python scripts/gates/security_scan.py` | repository files or a green local run must not imply remote protection |
| `SECURITY-PRIVATE-PROMOTION-1` | blocked-external | Medium | Owner authorization, redaction, and export evidence | Obtain an owner-approved private-sidecar promotion record before any promotion; keep the public tree and generated receipts free of private paths and content. | owner promotion receipt | `uv run python scripts/audit/check_tracked_all.py` | private path, sidecar content, credential, or unredacted export must fail public guards |

## Verification order

Run the bounded deterministic gates before any optional authority or provider
work:

```bash
uv run pytest tests/infra_tests/documentation/ tests/infra_tests/publishing/ -q --no-cov --timeout=120
uv run pytest tests/regression/ -q --no-cov --timeout=120
uv run python scripts/audit/check_backlog.py --strict
uv run python scripts/docgen/counts.py --check
uv run python scripts/audit/check_claim_bindings.py --json
uv run python scripts/audit/check_public_template_contract.py --strict
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/check_tracked_secrets.py
```

Then run the isolated public matrix, infrastructure coverage gate, Ruff,
mypy, Bandit, no-mocks, generated-document, manuscript/render, and
accessibility checks. Optional paths must emit `skipped` or `blocked` receipts
when their tools or external authority are unavailable.

## Backlog operating rules

- Re-derive measured facts instead of copying old counts into prose.
- Keep private or rotating project names out of public docs; use the generated roster.
- Prefer real files, subprocesses, deterministic fixtures, and negative controls.
- Keep business logic in `infrastructure/` or project `src/`; scripts remain thin orchestrators.
- Preserve project coverage floors, confidentiality, generated-artifact guards,
  provenance boundaries, and explicit optional-tool skips.
- When an item is complete, move its dated evidence to the changelog or review
  record and remove it from this file in the same change.
