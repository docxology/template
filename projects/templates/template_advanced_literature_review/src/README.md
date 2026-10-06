# Source modules

Project-owned business logic for the advanced multi-phase literature-review
exemplar lives here. `multi_phase/` owns phase configuration, filtering,
deduplication, and provenance. `deep_research/` owns deterministic offline
replay dispatch. `literature/` owns Advanced's retrieval adapters and sampling.
Scripts import shared analysis, knowledge-graph, reproducibility and figure
methods from the declared `template_literature_meta_analysis` distribution.
The provider's canonical source remains in the Meta project's `src/`; Advanced
does not carry duplicate copies of those packages.

Scripts may coordinate these modules, but must not duplicate their decisions.
Prepare the locked project environment and its declared provider before running
scripts. Installed acceptance binds the genuine provider wheel separately from
Advanced's wheel; a copied Advanced source tree does not establish that boundary.
