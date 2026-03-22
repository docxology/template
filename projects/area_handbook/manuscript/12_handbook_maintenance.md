# Handbook maintenance

A living handbook requires **three operational habits**:

1. **Version the corpus** when evidence changes materially.
2. **Run analysis scripts** before rendering so figures and JSON match the corpus.
3. **Archive PDFs** with the corpus version in metadata or filename.

The template pipeline encodes steps 2–3; teams adopt step 1 through governance. Optional LLM assists are disabled in `config.yaml` for this exemplar to keep builds deterministic.

**Pull-request discipline.** Treat `riverbend_area.yaml` (or production corpora) like code: require review, run `uv run pytest projects/area_handbook/tests/`, and attach `handbook_report.json` diffs when scores move. Figure regeneration via `scripts/02_generate_handbook_figure.py` updates PNGs and `figure_registry.json`, keeping validation green in `04_validate_output.py`.

**Release artifacts.** Ship three bundles together: the corpus file at a tagged version, `handbook_report.json`, and the combined PDF (or HTML). Consumers can then verify that narrative, metrics, and data describe the same snapshot [@gray2005].

**Threshold policy.** Changing `DEFAULT_GAP_THRESHOLD` in code alters which sections gap without any prose edit. Document threshold policy in steering minutes and prefer explicit `synthesize(..., gap_threshold=...)` in custom scripts if regional policy diverges from repository defaults.

**Supplemental sections.** Files such as `S01_*.md` and `S02_*.md` follow manuscript discovery ordering; add them when limitations or worked examples grow too long for the main chapter flow.

**Slides and web.** The same markdown feeds Beamer slides and static web mirrors; maintenance includes checking relative figure paths after directory moves and confirming browser loads for `output/web/index.html` after each major template upgrade [@template2026].
