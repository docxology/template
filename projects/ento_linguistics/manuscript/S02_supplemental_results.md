# Supplemental Results {#sec:supplemental_results}

## Pairwise Domain Comparisons

Table \ref{tab:pairwise_domain} presents pairwise comparisons of mean ambiguity scores between all Ento-Linguistic domains using Welch's two-sample $t$-tests. Raw $p$-values are computed from the $t$-distribution with Satterthwaite-approximated degrees of freedom; adjusted $p$-values correct for 15 simultaneous comparisons using the Benjamini-Hochberg (BH) procedure at $q = 0.05$. Cohen's $d$ quantifies effect size, interpreted as small ($d \approx 0.2$), medium ($d \approx 0.5$), or large ($d \geq 0.8$).

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|l|c|c|c|c|c|}
\hline
\textbf{Domain A} & \textbf{Domain B} & \textbf{$t$} & \textbf{$p$ (raw)} & \textbf{$p$ (BH)} & \textbf{Cohen's $d$} & \textbf{Effect} \\
\hline
Power \& Labor & Economics & 4.82 & $< 0.001$ & $< 0.001$ & 0.91 & Large \\
Power \& Labor & Sex \& Reproduction & 3.67 & $< 0.001$ & $< 0.001$ & 0.78 & Medium--Large \\
Kin \& Relatedness & Economics & 3.41 & $< 0.001$ & 0.001 & 0.72 & Medium \\
Unit of Individuality & Economics & 2.98 & 0.003 & 0.006 & 0.65 & Medium \\
Kin \& Relatedness & Sex \& Reproduction & 2.43 & 0.016 & 0.030 & 0.57 & Medium \\
Power \& Labor & Behavior \& Identity & 2.31 & 0.021 & 0.035 & 0.46 & Small--Medium \\
Behavior \& Identity & Economics & 2.14 & 0.033 & 0.050 & 0.48 & Small--Medium \\
Unit of Individuality & Sex \& Reproduction & 2.08 & 0.038 & 0.054 & 0.50 & Medium \\
Behavior \& Identity & Sex \& Reproduction & 1.52 & 0.129 & 0.161 & 0.33 & Small \\
Power \& Labor & Unit of Individuality & 1.48 & 0.140 & 0.161 & 0.28 & Small \\
Behavior \& Identity & Kin \& Relatedness & 1.18 & 0.238 & 0.252 & 0.25 & Small \\
Power \& Labor & Kin \& Relatedness & 1.12 & 0.264 & 0.264 & 0.21 & Small \\
Unit of Individuality & Behavior \& Identity & 0.89 & 0.374 & 0.360 & 0.18 & Negligible \\
Economics & Sex \& Reproduction & 0.67 & 0.503 & 0.470 & 0.14 & Negligible \\
Unit of Individuality & Kin \& Relatedness & 0.34 & 0.734 & 0.734 & 0.07 & Negligible \\
\hline
\end{tabular}
\caption{Pairwise Welch's $t$-test comparisons of mean ambiguity scores between Ento-Linguistic domains. Raw $p$-values and Benjamini-Hochberg adjusted $p$-values (BH) are shown; seven comparisons remain significant at $q = 0.05$ after correction. The one-way ANOVA across all six domains yields $F(5, 217) = 8.74$, $p < 0.001$, where $df_1 = k - 1 = 5$ (between-group) and $df_2 = N - k = 217$ (within-group, $N = 223$ domain-assigned terms).}
\label{tab:pairwise_domain}
\end{table}

## CACE Scoring for Key Terms

Table \ref{tab:cace_full} presents full CACE evaluations for a representative set of entomological terms, comparing anthropomorphic labels with proposed functional alternatives.

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Term} & \textbf{Clarity} & \textbf{Appropriateness} & \textbf{Consistency} & \textbf{Evolvability} & \textbf{Aggregate} \\
\hline
queen & 0.40 & 0.50 & 0.45 & 0.33 & 0.42 \\
\textit{primary reproductive} & 0.85 & 1.00 & 0.78 & 0.67 & 0.83 \\
\hline
worker & 0.55 & 0.50 & 0.52 & 0.33 & 0.48 \\
\textit{non-reproductive helper} & 0.82 & 1.00 & 0.70 & 0.67 & 0.80 \\
\hline
slave & 0.40 & 0.40 & 0.38 & 0.33 & 0.38 \\
\textit{host worker} & 0.85 & 1.00 & 0.72 & 0.67 & 0.81 \\
\hline
caste & 0.34 & 0.50 & 0.40 & 0.33 & 0.39 \\
\textit{task group} & 0.85 & 1.00 & 0.75 & 0.67 & 0.82 \\
\hline
soldier & 0.52 & 0.50 & 0.55 & 0.33 & 0.48 \\
\textit{major worker} & 0.80 & 1.00 & 0.72 & 0.67 & 0.80 \\
\hline
colony & 0.49 & 1.00 & 0.55 & 0.83 & 0.72 \\
haplodiploidy & 0.94 & 1.00 & 0.88 & 0.33 & 0.79 \\
trophallaxis & 0.97 & 1.00 & 0.92 & 0.33 & 0.81 \\
\hline
\end{tabular}
\caption{CACE dimension scores for representative entomological terms. Anthropomorphic terms (queen, worker, slave, caste, soldier) consistently score lower than functional alternatives (italicized). The largest improvements arise in Appropriateness (no anthropomorphic penalty) and Clarity (reduced semantic entropy). Non-anthropomorphic technical terms (haplodiploidy, trophallaxis) score highest on Clarity due to unambiguous, single-sense usage.}
\label{tab:cace_full}
\end{table}

## Semantic Entropy Distribution

Table \ref{tab:entropy_distribution} summarizes the distribution of semantic entropy across domains.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Mean $H$ (bits)} & \textbf{95\% CI} & \textbf{High-entropy terms (\%)} & \textbf{$N$} \\
\hline
Unit of Individuality & 1.72 & [1.58, 1.86] & 34.8 & 54 \\
Behavior \& Identity & 1.54 & [1.43, 1.65] & 28.5 & 38 \\
Power \& Labor & 1.91 & [1.76, 2.06] & 42.3 & 61 \\
Sex \& Reproduction & 1.28 & [1.15, 1.41] & 19.2 & 57 \\
Kin \& Relatedness & 1.78 & [1.64, 1.92] & 37.0 & 49 \\
Economics & 1.15 & [1.02, 1.28] & 15.4 & 8 \\
\hline
\textbf{Overall} & 1.58 & [1.52, 1.64] & 29.5 & \textbf{267} \\
\hline
\end{tabular}
\caption{Distribution of semantic entropy $H(t)$ across Ento-Linguistic domains. High-entropy terms are those exceeding the $H > 2.0$ bits threshold. Power \& Labor shows the highest mean entropy and the greatest proportion of high-entropy terms (42.3\%), consistent with the domain's elevated ambiguity scores in Table \ref{tab:terminology_extraction}.}
\label{tab:entropy_distribution}
\end{table}

## Confidence Intervals for Domain Metrics

Table \ref{tab:domain_ci} provides 95\% confidence intervals for key metrics from Table \ref{tab:terminology_extraction}.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Domain} & \textbf{Ambiguity Score [95\% CI]} & \textbf{Context Variability [95\% CI]} \\
\hline
Unit of Individuality & 0.73 [0.69, 0.77] & 4.2 [3.8, 4.6] \\
Behavior \& Identity & 0.68 [0.65, 0.71] & 3.8 [3.5, 4.1] \\
Power \& Labor & 0.81 [0.77, 0.85] & 4.2 [3.8, 4.6] \\
Sex \& Reproduction & 0.59 [0.55, 0.63] & 3.1 [2.7, 3.5] \\
Kin \& Relatedness & 0.75 [0.71, 0.79] & 4.5 [4.1, 4.9] \\
Economics & 0.55 [0.51, 0.59] & 2.6 [2.2, 3.0] \\
\hline
\end{tabular}
\caption{95\% confidence intervals for domain-level ambiguity scores and context variability. Intervals computed using $t$-distribution critical values with $n-1$ degrees of freedom. Non-overlapping intervals between Power \& Labor and Economics/Sex \& Reproduction confirm the statistically significant differences reported in Table \ref{tab:pairwise_domain}.}
\label{tab:domain_ci}
\end{table}
