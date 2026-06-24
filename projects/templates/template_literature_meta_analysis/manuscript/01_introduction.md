# Introduction

The scholarly literature on any active topic grows faster than any individual can read.
A researcher entering a field needs to know how large it is, how fast it is growing, what
sub-areas compose it, which works anchor its citation structure, what language and
concepts recur, and which claims the field actually tests. Answering those questions by
hand is slow, unrepeatable, and binds no number to evidence.

This project is a **configurable, reproducible meta-analysis template**. It takes one
search term and produces a quantitative portrait of that term's literature, with every
reported number traceable to a committed artifact and regenerable by re-running the
pipeline. The bundled instance targets **{{SEARCH_TERM_TITLE}}**; pointing the
configuration at a different term re-targets the whole analysis with no code change.

The pipeline contributes an end-to-end, domain-agnostic workflow:

1. **Multiple-engine retrieval with graceful degradation.** Records are gathered from
   {{N_ENGINES}} independent engines ({{ENGINE_LIST}}). An engine with no API key or no
   network reports a *skipped* status; the run completes from whatever engines remain
   plus a committed offline corpus.
2. **Record de-duplication.** Heterogeneous records are merged by a canonical identifier
   hierarchy, keeping the most complete version of each work.
3. **Descriptive and bibliometric analysis.** Counts by year, venue, and author; growth
   metrics; a configurable {{N_SUBFIELDS}}-bucket subfield classification; topic models;
   and a citation network.
4. **Language, entity, and embedding analysis.** Keyphrase and entity extraction and
   offline deterministic document embeddings over titles, abstracts, and full text.
5. **Optional hypothesis evidence.** An LLM-gated knowledge-graph stage scores the
   {{N_HYPOTHESES}} configured hypotheses explored against the corpus.

Because the writing itself is token-injected from configuration and pipeline outputs,
the manuscript is part of the reproducible artifact rather than a separate hand-authored
narrative.
