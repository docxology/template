# Runbook

Run the full deterministic AutoResearch exemplar through the main template
orchestrator:

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
```

The command executes the standard project stages:

1. Project tests validate config parsing, loop generation, manuscript variable
   hydration, and thin scripts.
2. Project analysis runs `scripts/run_autoresearch_loop.py` and
   `scripts/z_generate_manuscript_variables.py`.
3. Rendering consumes generated manuscript variables and resolved manuscript
   files.
4. Output validation includes AutoResearch readiness because
   `autoresearch.yaml` is present.
5. Copy outputs moves final deliverables into the repository-level `output/`
   tree.

## Loop sequence (`src.loop.run_autoresearch_loop`)

1. Compose plan via `build_autoresearch_plan()`.
2. Merge manuscript settings via `build_loop_config()`.
3. Run intrinsic readiness checks (domain profile, experiment plan, pipeline
   contracts, thin orchestrators).
4. Write core artifacts once (plan JSON, loop markdown, stage matrix CSV,
   figure).
5. Run extrinsic readiness checks (evidence registry, artifact manifest,
   required artifacts on disk).
6. Write combined readiness report and refresh the evidence registry snapshot.
7. Build file-backed claims and finalize loop JSON, review packet, summary,
   and manuscript variables.

Targeted checks:

```bash
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
uv run python scripts/02_run_analysis.py --project template_autoresearch_project
uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues
```

Review `output/reports/autoresearch_review_packet.md` before treating the
generated outputs as publication-ready. The exemplar records review readiness;
it does not approve itself.
