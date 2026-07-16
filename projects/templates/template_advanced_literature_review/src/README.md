# Source modules

Project-owned business logic for the advanced multi-phase literature-review
exemplar lives here. `multi_phase/` owns phase configuration, filtering,
deduplication, and provenance. `deep_research/` owns deterministic offline
replay dispatch. The remaining analysis packages are standalone-safe mirrors of
the single-term literature implementation. Strict template-drift checks keep
the shared behavior aligned while allowing a clean export to contain no
cross-project symlinks.

Scripts may coordinate these modules, but must not duplicate their decisions.
All standalone-facing imports must work from the project environment created by
the root Stage 01 test runner.
