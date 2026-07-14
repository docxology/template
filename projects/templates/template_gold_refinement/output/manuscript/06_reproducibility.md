# Reproducibility: Seeded Regeneration {#sec:reproducibility}

Reproduction requires identity, execution, and verification—not merely access to a PDF. Identity fixes the source revision, configuration hash, software release, and environment. Execution rebuilds analysis artifacts before manuscript hydration. Verification checks that registered claims, figures, references, and rendered formats agree with their source owners.

## Deterministic regeneration

The refinery pipeline is fully deterministic. Given the same `manuscript/config.yaml` and `src/` code, every run produces identical output. This is the local version of a reproducible computational research norm: the reader should be able to inspect the source, rerun the workflow, and recover the same derived artifacts [@peng2011reproducible; @sandve2013ten].

Executable-publication scholarship sharpens that norm. Executable research compendia and executable papers treat an article as a package of narrative, code, data, environment, and rendered outputs rather than as a static document with detachable supplements [@nuest2017erc; @lasser2020executable]. The present exemplar is smaller and more template-specific: it does not provide a universal executable-paper format, but it does make the manuscript variables, figures, reports, and rendered PDF/HTML products rebuildable from source-owned inputs.

- **Seed:** 431
- **Config hash:** c7d37fc9538b9677
- **Generation timestamp:** 2026-06-25T00:00:00Z
- **Python version:** 3.12.13

## Replication across technical seeds

Exact replay uses the canonical seed above. Replicability of the token-plan
mechanism is described separately by 1024 technical seed replicates:
the report records 1024 unique plans, mean agreement of
20.62%, and a 95% descriptive
interval of 20.09%–21.14%. This follows the computational
benchmarking principle that performance should be represented over relevant
sources of variation, not only by a single run [@bouthillier2021accounting].
The seed study is not a sample of manuscripts, readers, or scientific claims;
it is a sensitivity analysis of one executable lexical pipeline. The National
Academies distinguish computational reproducibility—recovering results from
the same inputs and procedures—from replicability across changed conditions
[@national_academies_2019_reproducibility]. This project demonstrates the
former directly and explores only one controlled technical variation for the
latter. It does not establish that the seed distribution represents future
software environments or independent research teams.

## Artifact inventory

| Category | Count |
|----------|-------|
| Figures | 28 |
| Data files | 4 |
| Reports | 12 |
| **Total** | 44 |

## Regeneration commands

```bash
# Run the refinery analysis
uv run python projects/templates/template_gold_refinement/scripts/refinement_analysis.py

# Generate manuscript variables
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py

# Full pipeline (from repo root)
./run.sh --project templates/template_gold_refinement --pipeline --core-only
```

A reproduction report should record command exit status, the source revision, `c7d37fc9538b9677`, Python 3.12.13, and whether the generated registries pass. Matching prose alone is insufficient if the token plan, claim registry, or figure registry differs. Conversely, timestamp or renderer metadata differences should be interpreted separately from substantive differences in source-owned values.

## Config ownership

All vocabulary, slots, section conditions, steganography toggles, and optional LLM review gates are declared in `manuscript/config.yaml` under `gold_refinement:`, `steganography:`, and `llm:`. The config is the source of truth; generated prose is disposable.

`src/pipeline_policy.py` turns those policy blocks into an explicit secure-pipeline hook. That keeps the optional hardening path visible before execution instead of burying it in shell glue or prose.

The reproducibility spine uses fact registry and figure registry as generated artifacts rather than reader trust signals. Variable generation records `c7d37fc9538b9677`; analysis writes refinery, token, claim-support, dashboard, and figure artifacts; validation may add the shared evidence registry used by template scientific-integrity checks.

The implementation circuit gives a reproducibility checklist for future forks. A reader should be able to start at any rendered figure or claim, follow it to a generated variable or report, follow that artifact to `src/` or `manuscript/config.yaml`, and rerun the same stage command. If that path is broken, the fork has produced a static illustration rather than a reproducible refinement pipeline.

Metadata is part of that path, not administrative garnish. Work on reproducible computational metadata argues that data, tools, workflows, environments, and reports need machine-readable descriptors before re-execution and reuse can be automated reliably [@chen2021metadata]. Here, the evidence registry, token plan, figure registry, output statistics, and config hash are the local metadata stack. They make the object inspectable, but they remain descriptive: they identify what was generated and from where, not whether a domain conclusion is correct.

The same rule applies to visual polish. The figure registry is source-owned, every registered PNG now has a companion SVG, and `output/reports/figure_quality_report.json` records 13 PNG files, 13 SVG files, and 13 passing visual-quality checks for the current variable pass. A fork should treat [@tbl:figure_quality] as the figure-layer analogue of the claim-support registry: it proves that the visuals are regenerated, present in both raster and vector forms, nonblank, and aligned with the registry before prose promotes them.

## Evidence-registry separation

This exemplar now separates two evidence surfaces. `output/reports/claim_support_registry.json` is the project-local contribution-claim assay consumed by the dashboard and claim-support figure. `output/reports/evidence_registry.json` is reserved for the shared template evidence validator, which registers numbers, citations, equations, sections, figures, tables, generated data, and claim-ledger facts. The split mirrors provenance standards: different entities can be generated by different activities and still belong to one accountable research object [@moreau2013prov; @belhajjame2015ontologies].

The evidence-tier ladder in [@fig:evidence_tier_ladder] is the reproducibility counterpart to that separation. It does not merely count files. It shows which tier owns each support surface, so a future fork can see whether a conclusion rests on config declarations, generated metrics, claim-ledger facts, bibliography records, or rendered artifacts. That distinction matters because only some tiers can support domain truth; others support reproducibility, formatting, or local consistency.
