# Manuscript Style Guide — Ento-Linguistics

This guide documents the manuscript conventions used in the Ento-Linguistic Domains paper, with examples extracted from the actual manuscript files.

## Section Numbering

### Main Sections (01–06)

| File | Section |
|------|---------|
| `01_abstract.md` | Research overview — terminology networks, six domains, CACE meta-standards |
| `02_introduction.md` | Language–thought entanglement in scientific communication |
| `03_methodology.md` | Mixed-methodology framework (computational + discourse analysis), 8 numbered subsections |
| `04_experimental_results.md` | Domain-by-domain findings with all 11 figures and tables |
| `05_discussion.md` | Theoretical implications, limitations, future directions |
| `06_conclusion.md` | Summary, CACE meta-standards proposal |

### Supplemental Sections (S01–S04)

| File | Section |
|------|---------|
| `S01_supplemental_methods.md` | Full src/ module API — all 37 Python files, method signatures, parameters, real corpus stats |
| `S02_supplemental_results.md` | Additional analysis tables and domain-specific details |
| `S03_supplemental_analysis.md` | Extended theoretical analysis and complexity |
| `S04_supplemental_applications.md` | Additional application examples |

### Reference Sections (98–99)

| File | Section |
|------|---------|
| `98_symbols_glossary.md` | Auto-generated API glossary from `src/` |
| `99_references.md` | Bibliography (`\bibliography{references}`) |

## Cross-Referencing

### Section References

```markdown
# Methodology {#sec:methodology}

As discussed in Section \ref{sec:methodology}...
```

### Figure References

```markdown
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/domain_comparison.png}
\caption{Six-panel domain comparison showing term counts, confidence scores, total
frequencies, semantic entropy distributions, bridging term counts, and CACE aggregate
scores across all six Ento-Linguistic domains.}
\label{fig:domain_comparison}
\end{figure}

Figure \ref{fig:domain_comparison} illustrates the domain comparison...
```

### Real Figure References Used (11 figures)

| Label | File | Figure |
|-------|------|--------|
| `fig:concept_map` | `02_introduction.md` | Concept map — node sizing by frequency, edges by co-occurrence |
| `fig:terminology_network` | `04_experimental_results.md` | Terminology network across domains (Jaccard similarity) |
| `fig:domain_comparison` | `04_experimental_results.md` | 6-panel domain comparison (terms/confidence/frequency/entropy/bridging/CACE) |
| `fig:domain_overlap_heatmap` | `04_experimental_results.md` | Cross-domain term overlap heatmap |
| `fig:anthropomorphic_framing` | `04_experimental_results.md` | Anthropomorphic framing analysis (LinguisticFeatureExtractor) |
| `fig:concept_hierarchy` | `04_experimental_results.md` | Concept network centrality — NetworkX degree/betweenness/eigenvector |
| `fig:domain_overview_grid` | `04_experimental_results.md` | 6-panel top-10 terms per domain, coloured by entropy |
| `fig:domain_patterns_grid` | `04_experimental_results.md` | 6-panel POS composition donut charts per domain |
| `fig:power_and_labor_ambiguities` | `S02_supplemental_results.md` | Power & Labor domain: ambiguity distribution |
| `fig:power_and_labor_term_frequencies` | `S02_supplemental_results.md` | Power & Labor domain: term frequency distribution |
| `fig:unit_of_individuality_patterns` | `S02_supplemental_results.md` | Unit of Individuality: term pattern breakdown |

## Figure Standards

- **Paths**: `../output/figures/filename.png` (relative from `manuscript/`)
- **Sizing**: `width=0.8\textwidth` or `width=0.9\textwidth`
- **Captions**: Descriptive sentences explaining all panels and how to interpret them
- **Labels**: `fig:` prefix matching the filename (e.g., `fig:domain_comparison`)
- **Font floor**: All generated figures enforce 16pt minimum font size
- **Regeneration**: `uv run python scripts/02_generate_figures.py` (clean-slate rebuild)

## Equations

### Semantic Entropy (§3.3)

```markdown
$$H(t) = -\sum_{i=1}^{k} p_i \log_2 p_i$$
```

Where $p_i$ is the empirical proportion of usage contexts in cluster $i$, with $k = \min(5, |C_t|)$ KMeans clusters.

### CACE Clarity Score (§3.7)

```markdown
$$\text{Clarity}(t) = \max\!\left(0,\, 1 - \frac{H(t)}{H_{\max}}\right), \quad H_{\max} = \log_2 5 \approx 2.32$$
```

### Jaccard Co-occurrence Weight (concept map edges)

```markdown
$$w = \frac{|A \cap B|}{\min(|A|, |B|)}$$
```

### Composite CACE Relationship Strength

```markdown
$$\text{strength} = 0.4 \cdot w_\text{base} + 0.3 \cdot r_\text{term} + 0.2 \cdot r_\text{domain} + 0.1 \cdot \mathbb{1}_\text{hierarchical}$$
```

### Inline Math

```markdown
The confidence score $c_i \in [0,1]$ measures extraction reliability.
The type–token ratio $\text{TTR} = V / N$ (vocabulary / tokens) = 0.144 for this corpus.
Semantic entropy threshold $H^* = 2.0$ bits (calibrated to 4 equiprobable senses).
```

## Citations

### Bibliography Entries

From `references.bib`:

```bibtex
@book{hölldobler1990,
  title={The Ants},
  author={Hölldobler, Bert and Wilson, Edward O.},
  year={1990},
  publisher={Harvard University Press}
}

@book{foucault1972,
  title={The Archaeology of Knowledge},
  author={Foucault, Michel},
  year={1972},
  publisher={Pantheon Books}
}

@book{lakoff1980,
  title={Metaphors We Live By},
  author={Lakoff, George and Johnson, Mark},
  year={1980},
  publisher={University of Chicago Press}
}
```

### Citation Patterns

```markdown
% Single citation
...as described by \cite{hölldobler1990}.

% Author-year (natbib)
\citet{herbers2006} proposed alternatives...

% Parenthetical
\citep{lakoff1980, foucault1972}

% Author only
\citeauthor{herbers2006}'s proposed alternatives...
```

## Configuration

From `config.yaml`:

```yaml
paper:
  title: "Ento-Linguistic Domains: Language, Ambiguity, and Scientific Communication in Entomology"
  subtitle: "How Terminology Networks Shape Understanding of Insect Biology (And Vice-Versa)"
  version: "1.0"

authors:
  - name: "Daniel Ari Friedman"
    orcid: "0000-0001-6232-9096"
    email: "daniel@activeinference.institute"
    affiliation: "Active Inference Institute"
    corresponding: true

keywords:
  - "entomology"
  - "scientific terminology"
  - "language analysis"
  - "discourse analysis"
  - "ant biology"
  - "eusociality"
  - "conceptual frameworks"
  - "active inference"
  - "terminology networks"
```

## Auto-Generated Glossary

`98_symbols_glossary.md` uses HTML comment markers for auto-generation:

```markdown
<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `term_extraction` | `TerminologyExtractor` | class | Extract terms from scientific corpora |
| `analysis.semantic_entropy` | `calculate_semantic_entropy` | function | Shannon H(t) via TF-IDF + KMeans |
| `analysis.cace_scoring` | `evaluate_term_cace` | function | CACE 4-dimension scoring per term |
| `domain_analysis` | `DomainAnalyzer` | class | Cross-domain ento-linguistic analysis |
<!-- END: AUTO-API-GLOSSARY -->
```

## See Also

- [validation_guide.md](validation_guide.md) — Manuscript preflight checks
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
- [`../manuscript/references.bib`](../manuscript/references.bib) — Full bibliography
