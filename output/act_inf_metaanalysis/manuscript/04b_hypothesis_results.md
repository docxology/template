# Hypothesis Evidence Landscape and Temporal Dynamics \label{sec:hypothesis_results}

The LLM-based extraction pipeline produced a total of 3{,}684 assertions across the eight tracked hypotheses, drawn from the full corpus of $N = 1208$ papers. The distribution of assertion types and the resulting citation-weighted scores reveal a differentiated evidence landscape:

| Hypothesis | Score | Supports | Neutral | Contradicts | Total | Character |
| --- | --- | --- | --- | --- | --- | --- |
| H4: Predictive Coding | $+0.59$ | 837 | 417 | 0 | 1{,}254 | Strong consensus |
| H5: Scalability | $+0.62$ | 142 | 110 | 0 | 252 | Strong consensus |
| H6: Clinical Utility | $+0.41$ | 16 | 29 | 0 | 45 | Moderate, growing |
| H8: Language AIF | $+0.39$ | 54 | 96 | 0 | 150 | Moderate, emerging |
| H7: Morphogenesis | $+0.35$ | 23 | 61 | 1 | 85 | Moderate, emerging |
| H2: AIF Optimality | $+0.22$ | 166 | 569 | 19 | 754 | Weakly contested |
| H1: FEP Universality | $+0.16$ | 297 | 1{,}071 | 2 | 1{,}370 | Broad but diffuse |
| H3: Markov Blanket Realism | $+0.02$ | 14 | 181 | 6 | 201 | Heavily contested |

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/hypothesis_dashboard.png}
\caption{Hypothesis scoring dashboard showing LLM-extracted evidence scores for the eight tracked hypotheses, sorted descending by consensus. Scores range from $-1$ (strong contradicting evidence) to $+1$ (strong supporting evidence).}
\label{fig:hypothesis_dashboard}
\end{figure}

## Interpretation of Evidence Profiles

The eight hypotheses cluster into three distinct tiers. The **consensus tier** (H4, H5) comprises hypotheses with strong positive scores ($> 0.5$) and no contradicting assertions. Predictive coding (H4), the most extensively assessed hypothesis with 1,254 assertions, has accumulated uniformly supportive evidence since the 1970s, reflecting the deep empirical grounding of hierarchical prediction error models in neuroscience. Scalability (H5), while assessed by fewer papers, shows a similarly strong positive trajectory that accelerated after 2017 as deep active inference architectures emerged.

The **moderate tier** (H6, H7, H8) comprises hypotheses with positive but lower scores ($0.3$--$0.4$). Clinical utility (H6) has the smallest evidence base (45 assertions) but shows a temporally increasing trend, consistent with the recent growth of computational psychiatry applications. Language AIF (H8) and morphogenesis (H7) both show moderate support with small contradicting evidence, reflecting their status as active research frontiers where theoretical proposals outpace empirical validation.

The **diffuse or contested tier** (H1, H2, H3) is the most diagnostically informative for understanding the field's intellectual maturation. FEP universality (H1), despite generating the largest raw evidence base (1,370 assertions), achieves a score of only $+0.16$—the vast majority of assessments are strictly neutral, indicating that researchers frequently *invoke* the FEP colloquially without explicitly testing its universality claim. AIF optimality (H2) exhibits the largest volume of contradicting evidence (19 assertions); crucially, its temporal trend reveals a persistent decline from an early peak of $+0.38$ (2012) to its current $+0.22$. This downward trajectory suggests that as the field has transitioned from theory to empirical application, absolute optimality claims have undergone increasingly stringent critical scrutiny. Markov blanket realism (H3) remains the most heavily contested hypothesis, exhibiting a near-zero aggregated score ($+0.02$) with six contradicting assertions effectively neutralizing 14 supporting ones—empirically capturing the intense, ongoing philosophical debate over whether Markov blankets denote real thermodynamic boundaries or merely represent instrumental statistical constructs.

## Temporal Dynamics of Evidence Accumulation

The cumulative evidence timeline (Figure \ref{fig:evidence_timeline}) reveals three temporal patterns. First, **early convergence**: H4 (predictive coding) reached positive territory in the late 1970s and has maintained a stable, high score since, reflecting the mature empirical base in cognitive neuroscience. Second, **recent acceleration**: H5 (scalability) and H6 (clinical utility) show steep upward trends after 2017, tracking the emergence of deep active inference tools and computational psychiatry applications. Third, **persistent contestation**: H3 (Markov blanket realism) has oscillated near zero since 2018, with gains from supporting papers offset by targeted critiques.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/evidence_timeline.png}
\caption{Temporal evolution of cumulative evidence scores by hypothesis. Divergent trajectories around the shaded neutral boundary reveal which hypotheses are gaining or losing support over time.}
\label{fig:evidence_timeline}
\end{figure}

## Assertion Composition and Distribution

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/assertion_breakdown.png}
\caption{Per-hypothesis stacked bar chart decomposing assertions into supports, contradicts, and neutral categories. The composition of evidence varies markedly across hypotheses.}
\label{fig:assertion_breakdown}
\end{figure}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{figures/assertion_summary.png}
\caption{Multi-panel assertion summary: total count, type distribution, and per-hypothesis totals. Provides a single-glance overview of the knowledge graph extraction results.}
\label{fig:assertion_summary}
\end{figure}

## Limitations of the Current Scoring Approach

As noted in Section 2, these results reflect a **tally-based aggregation** of independent LLM-extracted assertions, weighted by citation count and confidence. This approach does not account for evidential dependencies (e.g., papers from the same group testing the same model), does not distinguish between empirical and theoretical evidence, and treats the LLM's confidence scores as calibrated probabilities. The assertion counts are also sensitive to corpus composition: H1's large neutral tally (1,071) partially reflects the keyword classifier's tendency to assign papers to the broad A2 (philosophy) category, where FEP universality is implicitly invoked but rarely explicitly tested. More sophisticated approaches—including hierarchical Bayesian models, causal evidence graphs, and evidential diversity weighting—are discussed as future directions in Section 5.
