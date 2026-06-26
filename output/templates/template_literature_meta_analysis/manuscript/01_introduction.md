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
pipeline. The bundled instance targets **Modafinil**, a wakefulness-promoting
agent with a large, multi-disciplinary literature spanning clinical sleep medicine,
cognitive neuroscience, pharmacology, psychiatry, and safety research; pointing the
configuration at a different term re-targets the whole analysis with no code change.

## Research Questions

The pipeline is designed around four research questions (RQs) that a researcher entering
the field would ask:

1. **RQ1 — Field size and growth.** How large is the literature on Modafinil,
   how fast is it growing, and when did it peak? The corpus of $N = 2302$
   records spanning 2000--2026 answers this directly, with a compound
   annual growth rate of 3.45\% and a peak in 2025.

2. **RQ2 — Subfield composition.** What sub-areas compose the literature, and what is
   their relative weight? A configurable 6-bucket taxonomy
   (Clinical Sleep, Cognition, Pharmacology, Psychiatry, Safety, and Neuroscience) classifies every record, with **Clinical Sleep** the largest
   bucket at 64.3\%.

3. **RQ3 — Topical and linguistic structure.** What language and concepts recur, and
   what latent topics cross-cut the keyword taxonomy? TF-IDF over a
   500-feature vocabulary feeds non-negative matrix factorization,
   which extracts 5 latent topics. The top vocabulary terms are:
   modafinil, treatment, study, effects, patients, results, sleep, used, use, drug, studies, clinical, mg, using, placebo, cognitive, associated, effect, however, disorder.

4. **RQ4 — Citation geometry and evidence landscape.** Which works anchor the citation
   structure, how self-contained is the retrieved slice, and which claims does the field
   test? The citation network of 2204 nodes and 8,772 edges
   (22.6\% reference resolution rate) exposes hubs, authorities,
   and communities, while 6 configured hypotheses frame the evidence
   landscape.

## Contributions

The pipeline contributes an end-to-end, domain-agnostic workflow:

1. **Multiple-engine retrieval with graceful degradation.** Records are gathered from
   7 independent engines (arXiv, OpenAlex, Semantic Scholar, Crossref, PubMed, SovietRxiv, and ChinaRxiv). An engine with no API key or no
   network reports a *skipped* status; the run completes from whatever engines remain
   plus a committed offline corpus. For this live run, OpenAlex contributed the largest
   share of records, followed by Crossref and PubMed; Semantic Scholar was rate-limited
   (HTTP 429) and returned zero records without aborting the pipeline.

2. **Record de-duplication.** Heterogeneous records are merged by a canonical identifier
   hierarchy, keeping the most complete version of each work. Of 2302 retrieved
   records, 2248 carry DOIs, 932 carry OpenAlex IDs, and
   1 carry arXiv IDs.

3. **Descriptive and bibliometric analysis.** Counts by year, venue, and author; growth
   metrics (CAGR 3.45\%, doubling time 11.3 years); a configurable
   6-bucket subfield classification; topic models; and a citation network
   with 1377 communities.

4. **Language, entity, and embedding analysis.** Keyphrase and entity extraction and
   offline deterministic document embeddings over titles, abstracts, and full text. The
   TF-IDF vocabulary of 500 features captures the lexical landscape.

5. **Optional hypothesis evidence.** An LLM-gated knowledge-graph stage scores the
   6 configured hypotheses explored against the corpus.

Because the writing itself is token-injected from configuration and pipeline outputs,
the manuscript is part of the reproducible artifact rather than a separate hand-authored
narrative. Every number, table, and figure reference in this document traces to a
committed, regenerable file under `output/`.
