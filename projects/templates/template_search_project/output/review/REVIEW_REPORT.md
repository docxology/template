# TEMPLATE SEARCH PROJECT — DEEP REVIEW REPORT
**Generated:** 2026-10-30T20:28:00+00:00
**Project root:** `projects/templates/template_search_project`
**Repository root:** `.` (portable report label)
**Review orchestrator:** `scripts/review`
**Purpose:** informational current-source findings; this report is not run or release acceptance.
**Operational completion:** run `scripts/review`; local receipts are separate from this report.
**Configured local summary:** `output/.pipeline/review/summary.json` (not public acceptance)
**Consumed own-source and presence snapshot SHA-256:** `28f5c9ffe789e77041d68ad47e65fc27a73e9672d8694553c0117132f1e4370b`
---------------------------------------------------------------------------
## 1.  PROJECT INVENTORY
  ▸ AGENTS.md  (12537 bytes)
  ▸ CITATION.cff  (620 bytes)
  ▸ LICENSE  (1076 bytes)
  ▸ README.md  (22353 bytes)
  ▸ STANDALONE.md  (4729 bytes)
  ▸ TODO.md  (9180 bytes)
  ▸ codemeta.json  (854 bytes)
  ▸ data/  (4 entries)
  ▸ docs/  (13 entries)
  ▸ domain_profile.yaml  (1659 bytes)
  ▸ experiment_plan.yaml  (1502 bytes)
  ▸ export.toml  (63 bytes)
  ▸ manuscript/  (19 entries)
  ▸ pyproject.toml  (3624 bytes)
  ▸ review_config.yaml  (2366 bytes)
  ▸ scripts/  (12 entries)
  ▸ src/  (5 entries)
  ▸ tests/  (7 entries)
  ▸ uv.lock  (219811 bytes)

**src/ modules**  (5):  AGENTS.md, README.md, __init__.py, template_search_project, template_search_project.egg-info
**tests/ modules** (7):  AGENTS.md, README.md, analysis, conftest.py, pipeline, publish, search
**manuscript/ files** (19):  00_abstract.md, 01_introduction.md, 02_methodology.md, 03_results.md, 04_conclusion.md, 05_pipeline_internals.md, 06_reproducibility.md, 07_deep_search.md, 99_references.md, AGENTS.md, README.md, S01_literature_review.md, SYNTAX.md, config.yaml, config.yaml.example, layer_contract.yaml, preamble.md, references.bib, references_deep.bib
**scripts/ executables** (12):  AGENTS.md, README.md, _run_unpaid_acceptance.py, _search_sdk_bootstrap.py, review, run_deep_search.py, run_search_pipeline.py, s_compose_literature_review.py, y_generate_search_figures.py, z_generate_manuscript_variables.py, zz_generate_review_report.py, zzz_build_dashboard.py

## 2.  DOCUMENTATION COMPLETENESS
**AGENTS.md** sections:
  • Standard pipeline (`run_search_pipeline.py`)
  • Deep search (`run_deep_search.py`)
  • Available stages
  • Custom stages

**README.md** sections:
  • When to use this template
  • Publication and rendering
  • What it does
  • Quick start
  • Configuration
  • Architecture
  • Testing
  • Determinism
  • Review phase
  • Review configuration snapshot
  • Related Documentation
  • Optional hardening

**Internal-anchor validation**
  AGENTS.md anchors broken: 5  ['0f766e', '0f172a', 'fff', '1e3a8a', '7c2d12']
  README.md  anchors broken: 7  ['0f766e', '0f172a', 'fff', 'review-phase', '1e3a8a', 'permanent-canonical-exemplars', '7c2d12']

## 3.  BIBLIOGRAPHY AUDIT
**references.bib** entries: 6
**99_references.md** present (defers to .bib)
**Manuscript inline citations:** 310 unique keys
  [@abrolbekov2026high]
  [@abubaker2022scaling]
  [@abubaker2022scalinga]
  [@afshar2009gradient]
  [@ali2023comparing]
  [@alonso2025mathematics]
  [@alston2020beginners]
  [@amari1993backpropagation]
  [@amor2024realtime]
  [@anon1011171223051015783306294001]
  [@anon1011171225128176013939792001]
  [@anon1011171225259536062680904001]
  [@anon1011171225997446269411057001]
  [@anon1011171226435646314793833112]
  [@anon1011171230261530df877b5f9b8ee11a99dc49c781f4d15]
  [@anon101117123028105e628af96d7c5ee11a99e00505691c5e1]
  [@anon1061686udeac59432]
  [@anon2004approximation]
  [@anon2004convex]
  [@anon2004convexa]
  [@anon2004convexb]
  [@anon2004convexc]
  [@anon2004duality]
  [@anon2004equality]
  [@anon2004geometric]
  [@anon2004introduction]
  [@anon2004mathematical]
  [@anon2004preface]
  [@anon2004references]
  [@anon2004statistical]
  [@anon2004unconstrained]
  [@anon2005connectedness]
  [@anon2011algorithms]
  [@anon2011cones]
  [@anon2011convex]
  [@anon2011largescale]
  [@anon2011tools]
  [@anon2011toolsa]
  [@anon2011weak]
  [@anon2011what]
  [@anon2011whata]
  [@anon20142]
  [@anon20144]
  [@anon20146]
  [@anon2014convergence]
  [@anon2014stochastic]
  [@anon2016reproducible]
  [@anon2016reproduciblea]
  [@anon2017convex]
  [@anon2017fostering]
  [@anon2018implementing]
  [@anon2019eleven]
  [@anon2019introduction]
  [@anon2019replication]
  [@anon2019reproducible]
  [@anon2019tables]
  [@anon2020appendix]
  [@anon2020appendixa]
  [@anon2020testing]
  [@anon2020transparent]
  [@anon2021convex]
  [@anon2021convexa]
  [@anon2021convexb]
  [@anon2021convexc]
  [@anon2021convexd]
  [@anon2021decision]
  [@anon2021ellipsoid]
  [@anon2021generalizations]
  [@anon2021stochastic]
  [@anon2022convex]
  [@anon2025coneconvex]
  [@anon2025convex]
  [@anon2025convexa]
  [@anon2025convexb]
  [@anon2025convexc]
  [@anon2025convexd]
  [@anon2025convexe]
  [@anon2025first]
  [@anon2025firsta]
  [@anon2025minima]
  [@anon2025neural]
  [@anon2025optimality]
  [@anon2025preparing]
  [@anon2025reviewer]
  [@anon2025reviewera]
  [@anon2025separation]
  [@anon2026reviewer]
  [@anon2026reviewera]
  [@anonalgorithm]
  [@anonbackground]
  [@anonconvex]
  [@anonconvexa]
  [@anonduality]
  [@anoneconomics]
  [@anonfigure]
  [@anonglobal]
  [@anonintroduction]
  [@anonninbioinformatics]
  [@anonpreface]
  [@anonreproducible]
  [@anonreverse]
  [@anonsupplemental]
  [@anontable]
  [@anonymous2025noise]
  [@arefin2016minimizing]
  [@ayadi2021stochastic]
  [@azimjonov2023stochastic]
  [@baggerly2024importance]
  [@bahlai2016open]
  [@baker2022reproducible]
  [@bao2020stochastic]
  [@basu2017reproducible]
  [@basu2018reproducible]
  [@basu2021how]
  [@bhardwaj2016practical]
  [@boettiger2019case]
  [@bonnans2019convex]
  [@bottou2010largescale]
  [@bu2026nonstationary]
  [@burgess2018reproducible]
  [@butland2019community]
  [@cacciola2023convergence]
  [@cai2023communicationefficient]
  [@chang2020efficient]
  [@charlton2016how]
  [@chen2012dictionary]
  [@chen2025revisit]
  [@chen2026fractionalorder]
  [@chendistributed]
  [@cheng2019static]
  [@cheng2025convergence]
  [@chow2019reproducible]
  [@christensen2024learning]
  [@cui2019acoustic]
  [@data2020byzantineresilient]
  [@davison2018sumatra]
  [@dragomirescu1992smallest]
  [@dutta2014barrier]
  [@edmunds2014carmen]
  [@edmunds2014carmena]
  [@edmunds2015fermenting]
  [@edmunds2015fermentinga]
  [@edmunds2016reproducible]
  [@edmunds2016reproduciblea]
  [@ferrarotti2019synthesis]
  [@fig:papers_per_source]
  [@fig:score_distribution]
  [@fig:year_histogram]
  [@florenzano2001convex]
  [@floudas1995convex]
  [@fu2025theoretical]
  [@gandrud2013reproducible]
  [@gandrud2018conclusion]
  [@gandrud2018getting]
  [@gandrud2018introducing]
  [@gandrud2018reproducible]
  [@gandrud2020conclusion]
  [@gandrud2020getting]
  [@gandrud2020introducing]
  [@gandrud2020reproducible]
  [@gavel2025ensuring]
  [@geertreproducible]
  [@gong2026comparative]
  [@guo2022variable]
  [@gwozdz2018stochastic]
  [@hafshejani2023fast]
  [@halman2015approximating]
  [@hastings2023ai]
  [@hector2021reproducible]
  [@hediyehzadeh2016computational]
  [@heston2023statistics]
  [@hinsen2012unifying]
  [@hinsen2013platforms]
  [@hinsen2013python]
  [@hinsen2016reproducible]
  [@hinsen2017reproducible]
  [@hinsen2017sustainable]
  [@hoefling2018reproducible]
  [@hrynaszkiewicz2018open]
  [@hu2022efficiency]
  [@hua2023machinelearning]
  [@huadaptive]
  [@ito2026constrained]
  [@iutzeler2024derivatives]
  [@jacobsen2001bb]
  [@jacobsen2008reverse]
  [@jain2025controlling]
  [@jiao2024emergence]
  [@kedron2023reproducible]
  [@ketkar2017stochastic]
  [@key]
  [@kitzes2019basic]
  [@koren2022benign]
  [@kosinski2017coxphsgd]
  [@kour2024stochastic]
  [@koutsibella2020stochastic]
  [@kramerbasis]
  [@kunisato2019introduction]
  [@lam2023resampling]
  [@lan2023stochastic]
  [@lasserre2011convex]
  [@lasserre2014erratum]
  [@lebeau2020reproducible]
  [@lee2017differentially]
  [@li2015convex]
  [@li2021fast]
  [@li2024stochastic]
  [@li2024withdrawn]
  [@li2024withdrawna]
  [@limarereproducible]
  [@liu2024optimizing]
  [@liuautonomous]
  [@livni2024sample]
  [@maerz2024quarto]
  [@marechal2001generating]
  [@marwick2019case]
  [@mattingley2009automatic]
  [@missingvalueplatforms]
  [@missingvaluepractices]
  [@missingvaluetools]
  [@mittal2025explainable]
  [@moresi2018alaska]
  [@moresi2018alaskaa]
  [@mukhopadhyay2020stochastic]
  [@murota2001lconvex]
  [@murota2008lconvex]
  [@murota2024lconvex]
  [@murrayrust2018reproducible]
  [@nesterov2004nonsmooth]
  [@nesterov2004smooth]
  [@nesterov2018nonsmooth]
  [@nesterov2018smooth]
  [@nguyenheavytailed]
  [@ohta2015containerbased]
  [@oktem2017computational]
  [@peng2011reproducible]
  [@peseux2023stochastic]
  [@peypouquet2015convex]
  [@peyrache2025elife]
  [@peyrache2026elife]
  [@pillaudvivienlearning]
  [@poldrack2019case]
  [@preeyanon2018reproducible]
  [@ramos2015hilbert]
  [@ravasi2022multidimensional]
  [@roskar2022renku]
  [@rubsamen2009robust]
  [@schraudolph1999local]
  [@sec:deep_search]
  [@sec:methodology]
  [@sec:pipeline_internals]
  [@sec:reproducibility]
  [@sharma2018guided]
  [@sharma2021guided]
  [@shrimali2023comparative]
  [@singer1980minimization]
  [@singer1999duality]
  [@singer2001duality]
  [@sirignano2017stochastic]
  [@sirignano2020stochastic]
  [@solt2016icpsrdata]
  [@solt2016pewdata]
  [@song2021agsgd]
  [@songanglebased]
  [@srinivasan2026intelligent]
  [@stillwell2019statistical]
  [@stodden2014implementing]
  [@strand2019publishing]
  [@strongin2000global]
  [@suber2008oa]
  [@suber2008open]
  [@suber2009more]
  [@suh20221]
  [@sun2023noisy]
  [@sundecentralized]
  [@t2024hybrid]
  [@tarkhan2020bigsurvsgd]
  [@tbl:determinism]
  [@theodoridis2015stochastic]
  [@theodoridis2020online]
  [@theodoridis2026online]
  [@turali2024optimal]
  [@turek2019case]
  [@turner2009seminar]
  [@turner2009seminara]
  [@turner2010sweave]
  [@turner2010sweavea]
  [@tuy1998convex]
  [@tuy1998convexa]
  [@tuy2016convex]
  [@tuy2016convexa]
  [@tuypartly]
  [@wang2014robust]
  [@wang2018stochastic]
  [@weisbrod2026exampleproject]
  [@white2018software]
  [@wiebels2021leveraging]
  [@wijnhoven2010fast]
  [@williams2022stochastic]
  [@xie2018knitr]
  [@yaghoubi2017hybrid]
  [@yamada2018hyperparameterfree]
  [@yang2001econvex]
  [@yang2022adaptive]
  [@yildiz2023dataintegrated]
  [@youness1999econvex]
  [@zalinescu2024locally]
  [@zamora2016dendrite]
  [@zaslavski2020nonsmooth]
  [@zaslavski2020pdabased]

## 4.  INFRASTRUCTURE UTILISATION AUDIT
**Infrastructure modules imported (by importer count):**
  infrastructure.core.files.secure_write         ← bibliography.py, composition.py, deep_custody.py, deep_search.py, deep_search_cli.py, manuscript_variables.py, pipeline.py, report.py, report_inputs.py, review_execution.py, review_report.py, search_pipeline_cli.py
  infrastructure.search.literature               ← deep_search.py, figures.py, pipeline.py, report.py, synthesis.py
  infrastructure.core.logging.utils              ← composition.py, deep_search_cli.py, llm_runtime.py, search_pipeline_cli.py
  infrastructure.reference.citation              ← bibliography.py, composition.py, deep_search.py, pipeline.py
  infrastructure                                 ← analysis.py, deep_custody.py, provider_paths.py
  infrastructure.core.pipeline.fingerprint_files  ← report_inputs.py
  infrastructure.core.subprocess_policy          ← review_execution.py
  infrastructure.search.literature.live_artifacts  ← live_acceptance.py
  infrastructure.search.literature.live_contract  ← live_acceptance.py
  infrastructure.search.literature.live_providers  ← live_acceptance.py
  infrastructure.search.literature.live_transport  ← live_acceptance.py
  infrastructure.llm                             ← llm_runtime.py
  infrastructure.search.literature.configuration_sources  ← config.py
  infrastructure.reporting.interactive_dashboard  ← dashboard.py
  infrastructure.core.implementation_custody     ← deep_custody.py
  infrastructure.documentation.generated_figure_registry  ← figures.py

## 5.  REVIEW ORCHESTRATION SYSTEM (INSTALLED)

This project has a configurable, multi-stage review system for pre-flight
and post-run quality gates.  It leverages existing infrastructure.cli tools plus
bespoke checks implemented in template_search_project.analysis.

**Artifacts:**
  • review_config.yaml        stage enable/disable configuration
  • scripts/review            unified single-entrypoint orchestrator
  • scripts/zz_generate_review_report.py  informational source/domain reporter
  • src/template_search_project/analysis/           custom-stage functions

**Default enabled stages (when run via scripts/review):**
  1. bibtex_validation         infrastructure.reference.citation.cli validate
  2. bibliography_completeness custom — all [@key]s exist in references.bib
  3. infrastructure_usage      custom — audit src/ import paths
  4. determinism_check          custom — cache/seed + temperature=0

**Disabled by default** (require pipeline completion / dev deps):
  prerender_validation, markdown_links, variables_resolved,
  output_integrity, test_suite_health

**Run:**  uv run python scripts/review   (or add --list, --stage …)
**Operational outputs:** configured output/.pipeline/review/stage_*.json + summary.json (local only)
**Public report:** output/review/REVIEW_REPORT.md (recomputed source/domain findings)


## 6.  CURRENT SOURCE AND DOMAIN FINDINGS
**Bibliography completeness:** passed
**Missing bibliography keys:** 0
**Infrastructure import validity:** passed
**Infrastructure import issues:** 0
**Configured stages (execution results remain local):**
  DISABLED  prerender_validation
  DISABLED  markdown_links
  ENABLED  bibtex_validation
  ENABLED  bibliography_completeness
  DISABLED  variables_resolved
  DISABLED  output_integrity
  DISABLED  test_suite_health
  ENABLED  infrastructure_usage
  ENABLED  determinism_check

## 7.  GAPS & IMMEDIATE RECOMMENDATIONS

| # | Category   | Gap                                          | Recommended Action                    |
|---|------------|----------------------------------------------|---------------------------------------|
| 1 | Bibliography | 99_references.md defers to .bib; 310 inline citation(s) present in manuscript. | Citations present — confirm every key resolves in references.bib (see section 3). |
| 2 | Output artifacts | output/reading_report.md present; final PDF present. | Re-run the top-level PDF-rendering pipeline stage periodically to keep the PDF fresh. |
| 3 | Markdown links | `markdown_links` stage is disabled by default (avoids false positives on infra/external docs). | Enable `markdown_links` once an allowlist covers infra dirs + external docs. |
| 4 | Prerender  | `prerender_validation` stage is disabled by default. | Enable `prerender_validation` once pandoc-crossref labels are allowlisted. |
| 5 | Test suite | `test_suite_health` stage is disabled by default; pytest is available in this environment. | Enable `test_suite_health` to enforce the coverage gate as part of the review run. |


## 8.  NEXT STEPS — ANALYSIS / CODE / MANUSCRIPT
**A.  Bibliography Committee**
  1.  Populate `manuscript/99_references.md` with actual citations or rely on
      `references.bib` exclusively (remove deflective note if not needed).
  2.  Add inline `[@key]` citations in 01-05 sections where prior art is discussed.

**B.  Manuscript Sweep**
  3.  Run:  uv run python scripts/z_generate_manuscript_variables.py
      Substitutes all `{{...}}` placeholders (query, date, tokens, etc.).
  4.  Rerun review with `variables_resolved` enabled to confirm full pass.

**C.  Output Validation**
  5.  Re-enable `output_integrity` once final PDF artefacts exist.
  6.  Run pre-render; check LaTeX warnings / missing refs.

**D.  Analysis + Code Publication**
  7.  `output/reading_report.md` summarises search strategy, backend results, token counts.
  8.  Consider adding `docs/analysis/` linking findings to infrastructure methods.
  9.  Keep thin orchestration — src modules call infra methods; document in AGENTS.md.

**E.  Configuration Hygiene**
 10.  Exclude `.venv/` from link-validation in CI via allowlist, or keep `markdown_links` disabled.

## 9.  INTELLIGENCE AUGMENTATION — FACTS MEMORISED

  • Template_search_project: literature-search exemplar using infrastructure.search
    + infrastructure.reference, orchestrated by thin scripts pipeline.
  • Review system: scripts/review + review_config.yaml + src/template_search_project/analysis.
  • Infra usage (16 module(s)): infrastructure, infrastructure.core.files.secure_write, infrastructure.core.implementation_custody, infrastructure.core.logging.utils, infrastructure.core.pipeline.fingerprint_files, infrastructure.core.subprocess_policy, infrastructure.documentation.generated_figure_registry, infrastructure.llm, infrastructure.reference.citation, infrastructure.reporting.interactive_dashboard, infrastructure.search.literature, infrastructure.search.literature.configuration_sources, infrastructure.search.literature.live_artifacts, infrastructure.search.literature.live_contract, infrastructure.search.literature.live_providers, infrastructure.search.literature.live_transport.
  • Bibliography: 310 inline citation key(s) detected in manuscript (see section 3).
  • Next: run the top-level pipeline's PDF-rendering stage to refresh the combined PDF.
