# Reproducibility {#sec:reproducibility}

The bundled `manuscript/config.yaml` is configured for the **strict reproducibility** discipline advocated for computational science by [@peng2011reproducible]:

1. **No network calls.** All analysis is local: prose metrics, structure, quality flags, and bibliography validation are computed from in-repo files only.
2. **Deterministic outputs.** `compute_metrics`, `analyze_structure`, and `analyze_quality` are pure functions over their input strings. The same manuscript text + the same `config.yaml` produces byte-identical JSON artefacts (modulo timestamp metadata in any caches the project later adds).
3. **Threshold transparency.** Every pass/fail decision is recorded in `output/checks.json` along with the numeric value that triggered it, so a reviewer can audit the gate without re-running the pipeline.
4. **No hidden state.** The pipeline does not mutate `manuscript/`; it reads and reports. `manuscript/references.bib` is read-only here (in contrast with the optional search add-on, where it is auto-populated).
5. **Same code, different config.** A reviewer who wants stricter standards edits `manuscript/config.yaml` (`prose.target_grade_level_max: 14.0`, say); no code changes are required.

## Verifying reproducibility locally

```bash
# Run twice; check there are no diffs in the JSON artefacts.
uv run python projects/template_prose_project/scripts/run_prose_pipeline.py
mv projects/template_prose_project/output projects/template_prose_project/output_first
uv run python projects/template_prose_project/scripts/run_prose_pipeline.py
diff -ru \
    projects/template_prose_project/output_first/manuscript_report.json \
    projects/template_prose_project/output/manuscript_report.json
```

The diff should be empty. If it is not, the pipeline has acquired non-determinism — file an issue.

## Determinism guarantees

| Stage | Deterministic? | Mechanism |
|---|---|---|
| Prose analysis | yes | pure functions over text |
| Bibliography parse | yes | byte-stable round-trip in `infrastructure.reference.citation` |
| Check evaluation | yes | pure comparisons |
| Markdown report assembly | yes | sorted file list, fixed output template |
| Figure generation | yes (within Matplotlib version) | fixed palette, no random subsampling |
| Manuscript variables | yes | derived from the deterministic JSON report |
