# Supplement: Limitations and assumptions

This exemplar prioritizes **reproducibility and teachability** over geographic realism. Riverbend is fictional; weights and source labels illustrate schema use, not empirical findings about any jurisdiction.

**No live data.** The pipeline does not call HTTP APIs, scrape documents, or perform NLP on attachments. Every number in the handbook narrative traces to a hand-authored YAML row or to derived metrics computed from those rows.

**Weights are subjective.** Reviewers assign `weight` in $[0,1]$ without a universal rubric. Cross-team calibration is a governance task outside this repository; the code assumes weights are already consensus values.

**Single corpus per build.** The scripts load one fixture path (`data/fixtures/riverbend_area.yaml` in production use of this demo). Merging multiple corpora or federating regions would require new modules and tests, not configuration toggles alone.

**Outline static in code.** `HANDBOOK_TEMPLATE` is Python source, not a per-area YAML file. Customizing chapters without editing code is possible only within the existing section files and themes; adding a ninth scored section demands code and test updates.

**Citation depth.** `source_label` is a short string, not a BibTeX key. Formal citations belong in manuscript markdown using `references.bib`; the corpus stays lean [@bowker2005].

**Threshold semantics.** “Gap” means strictly below threshold, not “close.” Sections barely above the line still pass; policy teams may want stricter thresholds or secondary rules implemented in future metrics fields.
