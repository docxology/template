# Manuscript Style Guide — Ento-Linguistics

This guide documents the manuscript conventions used in the Ento-Linguistic Domains paper, with examples extracted from the actual manuscript files.

## Section Numbering

### Main Sections (01–06)

| File | Section |
|------|---------|
| `01_abstract.md` | Research overview — terminology networks, six domains, CACE meta-standards |
| `02_introduction.md` | Language–thought entanglement in scientific communication |
| `03_methodology.md` | Mixed-methodology framework (computational + discourse analysis) |
| `04_experimental_results.md` | Domain-by-domain findings with figures and tables |
| `05_discussion.md` | Theoretical implications, limitations, future directions |
| `06_conclusion.md` | Summary, CACE meta-standards proposal |

### Supplemental Sections (S01–S04)

| File | Section |
|------|---------|
| `S01_supplemental_methods.md` | Extended text processing, terminology extraction, performance/scalability |
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
\includegraphics[width=0.9\textwidth]{../output/figures/terminology_network.png}
\caption{Terminology network showing clustering patterns across
Ento-Linguistic domains. Nodes represent terms sized by frequency;
edges indicate co-occurrence strength computed via Jaccard similarity
of shared domain memberships.}
\label{fig:terminology_network}
\end{figure}

Figure \ref{fig:terminology_network} illustrates the terminology network...
```

### Real Figure References Used

| Label | File | Figure |
|-------|------|--------|
| `fig:concept_map` | `02_introduction.md` | Concept map — node sizing by frequency, edges by co-occurrence |
| `fig:terminology_network` | `04_experimental_results.md` | Terminology network across domains |
| `fig:domain_comparison` | `04_experimental_results.md` | 2×2 domain comparison (terms, confidence, frequency, ambiguity) |
| `fig:domain_overlap_heatmap` | `04_experimental_results.md` | Cross-domain term overlap |
| `fig:anthropomorphic_framing` | `04_experimental_results.md` | Anthropomorphic framing analysis |

## Figure Standards

- **Paths**: `../output/figures/filename.png` (relative from `manuscript/`)
- **Sizing**: `width=0.8\textwidth` or `width=0.9\textwidth`
- **Captions**: Descriptive sentences explaining all panels and how to interpret them
- **Labels**: `fig:` prefix matching the filename (e.g., `fig:domain_comparison`)
- **Font floor**: All generated figures enforce 16pt minimum font size

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

% Multiple citations
...drawing on metaphor theory \cite{lakoff1980} and discourse analysis \cite{foucault1972}.
```

## Inline Math

```markdown
The confidence score $c_i \in [0,1]$ measures extraction reliability.
The term frequency $f(t)$ quantifies occurrence across the corpus.
The Jaccard co-occurrence weight $w = |S_1 \cap S_2| / |S_1 \cup S_2|$.
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
```

## Auto-Generated Glossary

`98_symbols_glossary.md` uses HTML comment markers for auto-generation:

```markdown
<!-- BEGIN: AUTO-API-GLOSSARY -->
| Module | Name | Kind | Summary |
|---|---|---|---|
| `term_extraction` | `TerminologyExtractor` | class | Extract terms from scientific corpora |
| `domain_analysis` | `DomainAnalysis` | class | Cross-domain ento-linguistic comparison |
<!-- END: AUTO-API-GLOSSARY -->
```

## See Also

- [validation_guide.md](validation_guide.md) — Manuscript preflight checks
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — Manuscript structure
- [`../manuscript/references.bib`](../manuscript/references.bib) — Full bibliography
