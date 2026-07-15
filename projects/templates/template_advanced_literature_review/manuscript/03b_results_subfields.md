# Results: Subfield Structure

The subfield taxonomy is defined entirely in configuration; for this instance it spans
{{N_SUBFIELDS}} buckets ({{SUBFIELD_LIST}}). Each record is assigned to the
highest-priority bucket whose keywords it matches, so the distribution reflects the
configured taxonomy rather than a fixed schema. Table 2 (previous section) reports the
counts; the largest bucket is **{{TOP_SUBFIELD}}** ({{TOP_SUBFIELD_PCT}}\%).

## Per-Subfield Characterization

The subfield breakdown reveals the multi-disciplinary nature of the {{SEARCH_TERM}}
literature:

- **Clinical Sleep** dominates at {{TOP_SUBFIELD_PCT}}\%, reflecting the drug's primary
  indication for narcolepsy, shift-work disorder, and obstructive sleep apnea. This
  bucket includes randomized controlled trials, meta-analyses of efficacy, and
  long-term safety studies in sleep-disorder populations.

- **Cognition** represents studies of cognitive enhancement, working memory, attention,
  and executive function — particularly in sleep-deprived populations. This subfield
  has grown with the broader interest in neuroenhancement and "smart drugs."

- **Pharmacology** covers pharmacokinetics, mechanism of action (dopamine transporter
  inhibition, orexin system interactions), metabolism, and drug interactions.

- **Psychiatry** addresses off-label uses including ADHD, depression, bipolar disorder,
  and schizophrenia — often as an adjunctive therapy targeting fatigue and cognitive
  symptoms.

- **Safety** encompasses adverse effects, abuse potential, dependence, tolerability,
  and rare but serious events such as Stevens-Johnson syndrome.

- **Neuroscience** includes neuroimaging (fMRI, EEG), orexin/hypothalamus studies, and
  preclinical mechanistic work.

Because the taxonomy is data, not code, re-targeting the template to another topic — or
refining the buckets for the same topic — changes this section's structure and numbers
without any change to the analysis code. The subfield assignment also feeds the temporal
and citation analyses, allowing per-subfield growth and connectivity to be read off the
same artifacts.
