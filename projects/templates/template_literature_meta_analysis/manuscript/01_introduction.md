# Introduction

The scholarly literature on any active topic grows faster than any individual can read.
A researcher entering a field needs to know how large it is, how fast it is growing, what
sub-areas compose it, which works anchor its citation structure, what language and
concepts recur, and which claims the field actually tests. Answering those questions by
hand is slow, unrepeatable, and binds no number to evidence. Systematic reviews, while
the gold standard for evidence synthesis, are labour-intensive and become stale between
updates — the Cochrane review cycle, for instance, targets a two-year refresh interval
that many fields outpace [@page2021prisma]. Bibliometric dashboards (Scopus, Web of
Science, Dimensions) offer breadth but no reproducible link from a reported statistic to
a regenerable artifact, and they do not frame or test domain-specific hypotheses.

This project is a **configurable, reproducible meta-analysis template**. It takes one
search term and produces a quantitative portrait of that term's literature, with every
reported number traceable to a committed artifact and regenerable by re-running the
pipeline. The bundled instance targets **{{SEARCH_TERM_TITLE}}**, a wakefulness-promoting
agent with a large, multi-disciplinary literature spanning clinical sleep medicine,
cognitive neuroscience, pharmacology, psychiatry, and safety research; pointing the
configuration at a different term re-targets the whole analysis with no code change.

## Research Questions

The pipeline is designed around four research questions (RQs) that a researcher entering
the field would ask:

1. **RQ1 — Field size and growth.** How large is the literature on {{SEARCH_TERM_TITLE}},
   how fast is it growing, and when did it peak? The corpus of $N = {{CORPUS_SIZE}}$
   records spanning {{YEAR_START}}--{{YEAR_END}} answers this directly, with a compound
   annual growth rate of {{CAGR_PCT}}\% and a peak in {{PEAK_YEAR}}.

2. **RQ2 — Subfield composition.** What sub-areas compose the literature, and what is
   their relative weight? A configurable {{N_SUBFIELDS}}-bucket taxonomy
   ({{SUBFIELD_LIST}}) classifies every record, with **{{TOP_SUBFIELD}}** the largest
   bucket at {{TOP_SUBFIELD_PCT}}\%.

3. **RQ3 — Topical and linguistic structure.** What language and concepts recur, and
   what latent topics cross-cut the keyword taxonomy? TF-IDF over a
   {{NUM_VOCAB_FEATURES}}-feature vocabulary feeds non-negative matrix factorization,
   which extracts {{NUM_TOPICS}} latent topics. The top vocabulary terms are:
   {{TOP_VOCAB_TERMS}}.

4. **RQ4 — Citation geometry and evidence landscape.** Which works anchor the citation
   structure, how self-contained is the retrieved slice, and which claims does the field
   test? The citation network of {{CITATION_NODES}} nodes and {{CITATION_EDGES}} edges
   ({{CITATION_RESOLUTION_PCT}}\% reference resolution rate) exposes hubs, authorities,
   and communities, while {{N_HYPOTHESES}} configured hypotheses frame the evidence
   landscape.

## Contributions

The pipeline contributes an end-to-end, domain-agnostic workflow:

1. **Multiple-engine retrieval with graceful degradation.** Records are gathered from
   {{N_ENGINES}} independent engines ({{ENGINE_LIST}}). An engine with no API key or no
   network reports a *skipped* status; the run completes from whatever engines remain
   plus a committed offline corpus. For this live run, OpenAlex contributed the largest
   share of records, followed by Crossref and PubMed; Semantic Scholar was rate-limited
   (HTTP 429) and returned zero records without aborting the pipeline.

2. **Record de-duplication.** Heterogeneous records are merged by a canonical identifier
   hierarchy, keeping the most complete version of each work. Of {{CORPUS_SIZE}} retrieved
   records, {{DOI_COUNT}} carry DOIs, {{OPENALEX_ID_COUNT}} carry OpenAlex IDs, and
   {{ARXIV_ID_COUNT}} carry arXiv IDs.

3. **Descriptive and bibliometric analysis.** Counts by year, venue, and author; growth
   metrics (CAGR {{CAGR_PCT}}\%, doubling time {{DOUBLING_TIME}} years); a configurable
   {{N_SUBFIELDS}}-bucket subfield classification; topic models; and a citation network
   with {{CITATION_COMMUNITIES}} communities.

4. **Language, entity, and embedding analysis.** Keyphrase and entity extraction and
   offline deterministic document embeddings over titles, abstracts, and full text. The
   TF-IDF vocabulary of {{NUM_VOCAB_FEATURES}} features captures the lexical landscape.

5. **Optional hypothesis evidence.** An LLM-gated knowledge-graph stage scores the
   {{N_HYPOTHESES}} configured hypotheses explored against the corpus.

Because the writing itself is token-injected from configuration and pipeline outputs,
the manuscript is part of the reproducible artifact rather than a separate hand-authored
narrative. Every number, table, and figure reference in this document traces to a
committed, regenerable file under `output/`.
