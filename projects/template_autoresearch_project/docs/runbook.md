# Runbook

Run the full deterministic AutoResearch exemplar through the main template
orchestrator:

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
```

The command executes the standard project stages:

1. Project tests validate config parsing, deterministic ML-task behavior, loop
   generation, manuscript variable hydration, and thin scripts.
2. Project analysis runs `scripts/run_autoresearch_loop.py` and
   `scripts/z_generate_manuscript_variables.py`.
3. Rendering consumes generated manuscript variables and resolved manuscript
   files.
4. Output validation includes AutoResearch readiness because
   `autoresearch.yaml` is present.
5. Copy outputs moves final deliverables into the repository-level `output/`
   tree.

## Loop sequence (`src.loop.run_autoresearch_loop`)

1. Compose plan via `build_autoresearch_plan()` and merge manuscript settings
   via `build_loop_config()`.
2. Run intrinsic readiness checks (domain profile, experiment plan, pipeline
   contracts, thin orchestrators).
3. Write core artifacts (plan JSON, loop markdown, stage matrix CSV, figure).
4. Write the first evidence registry snapshot from on-disk artifacts.
5. Run the bounded local MNIST neural-network task and write resolved config,
   results, candidate ledger, confusion matrix, training history, error
   examples, probability records, classification diagnostics, calibration
   report, candidate accuracy intervals, class-balance counts, robustness
   report, probability diagnostics, bootstrap intervals, paired baseline
   comparison, statistical summary, training diagnostics, report, benchmark
   score, candidate-selection audit, diagnostic-boundary report, and
   candidate-score figure.
6. Build file-backed claims and finalize loop JSON, review packet, summary, and
   manuscript variables.
7. Write method-contract artifacts: research program, idea ledger, run ledger,
   deferred review decisions, benchmark grading report, and benchmark scores.
8. Refresh loop payloads provisionally (`readiness_valid=False`) and write the
   first local security artifacts plus the first artifact manifest.
9. Run extrinsic readiness checks (evidence registry, artifact manifest,
   required artifacts, method ledgers, review gates, benchmark outputs, and
   enabled security artifacts).
10. Write the combined intrinsic + extrinsic readiness report.
11. Rebuild claims after readiness reports exist and refresh loop payloads with
   final `readiness_valid` and output paths.
12. Regenerate final figures and figure registry captions from the final loop
   state, including candidate scores, confusion matrix, per-class accuracy,
   learning curves, complexity/accuracy, error examples, calibration,
   classification metrics, confusion pairs, generalization gaps, robustness
   matrix, probability and margin distributions, bootstrap intervals, paired
   correctness, selective accuracy, probability quality, training dynamics,
   candidate lifecycle, local class balance, local data contact sheet,
   readiness matrix, closure flow, security-control matrix, and integrity
   chain.
13. Write manuscript variables, registry-backed figure blocks, and variable
   provenance sidecars.
14. Rewrite the evidence registry, security artifacts, and artifact manifest.

Targeted checks:

```bash
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
uv run python scripts/02_run_analysis.py --project template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli plan --project template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli benchmark --project template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues
```

Review `output/reports/autoresearch_review_packet.md` before treating the
generated outputs as publication-ready. The exemplar records review readiness;
it does not approve itself.
Also review `output/reports/autoresearch_security_review.md`; it is local
artifact-integrity evidence, not an external security certification.

## Fixture maintenance

The default pipeline uses the checked-in `data/mnist_small.npz` fixture and does
not download MNIST. To intentionally rebuild that fixture, run the manual
maintenance utility:

```bash
uv run python projects/template_autoresearch_project/scripts/regenerate_mnist_fixture.py
```

Do not wire this script into project tests, analysis, rendering, validation, or
CI. The maintenance path verifies the fixed HTTPS source URL, file sizes, and
SHA-256 hashes before rewriting the fixture and provenance files.
