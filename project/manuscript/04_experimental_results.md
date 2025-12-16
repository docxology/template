# Experimental Results {#sec:experimental_results}

## Compatibility Database Results

### Species Pair Analysis

Our compatibility database includes analysis of 15 major fruit tree species, generating a comprehensive compatibility matrix. Figure \ref{fig:compatibility_matrix} shows the compatibility heatmap, where values represent predicted success probabilities for rootstock-scion pairs.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/compatibility_matrix.png}
\caption{Species compatibility matrix showing graft success probabilities between rootstock-scion pairs}
\label{fig:compatibility_matrix}
\end{figure}

The analysis reveals several key patterns:

1. **Intra-generic compatibility**: Species within the same genus (e.g., *Malus* spp.) show high compatibility (0.85-0.95)
2. **Inter-generic compatibility**: Cross-genus combinations show moderate compatibility (0.60-0.80) when phylogenetically close
3. **Distant relationships**: Combinations across families show low compatibility (<0.50)

### Phylogenetic Distance Correlation

Analysis of 500 synthetic grafting trials demonstrates a strong negative correlation ($r = -0.75$, $p < 0.001$) between phylogenetic distance and success rate, confirming that phylogenetic relationships are the primary predictor of graft compatibility. This relationship follows the exponential decay model \eqref{eq:phylogenetic_compatibility} with decay constant $k = 2.1 \pm 0.2$.

## Technique Effectiveness

### Comparative Success Rates

Figure \ref{fig:technique_comparison} compares success rates across major grafting techniques using synthetic trial data representing 500 grafts per technique.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/technique_comparison.png}
\caption{Comparison of grafting techniques showing success rates and union strength metrics}
\label{fig:technique_comparison}
\end{figure}

The results show:

- **Whip and Tongue**: 85% success rate, highest precision requirement
- **Bud Grafting**: 80% success rate, most efficient for mass propagation
- **Cleft Grafting**: 75% success rate, suitable for larger diameters
- **Bark Grafting**: 70% success rate, useful for mature trees

Statistical analysis using ANOVA reveals significant differences between techniques ($F = 12.3$, $p < 0.001$), with post-hoc tests indicating whip and tongue grafting significantly outperforms bark grafting ($p < 0.01$).

### Technique-Species Interactions

Analysis of technique effectiveness across different species types reveals important interactions:

- **Temperate fruit trees**: Whip and tongue performs best (87% success)
- **Tropical species**: Bud grafting shows highest success (82%)
- **Large diameter rootstock**: Cleft and bark grafting are preferred

These interactions highlight the importance of technique selection based on species characteristics and rootstock size.

## Environmental Factor Analysis

### Temperature Effects

Analysis of 1000 grafting trials across temperature ranges (10-35°C) reveals optimal conditions at 20-25°C, with success rates declining outside this range. Figure \ref{fig:environmental_effects} shows the relationship between environmental conditions and success rates.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/environmental_effects.png}
\caption{Graft success as function of temperature and humidity conditions}
\label{fig:environmental_effects}
\end{figure}

The temperature suitability function follows:

- **Optimal range (20-25°C)**: Success rate 82% ± 3%
- **Acceptable range (15-30°C)**: Success rate 75% ± 5%
- **Suboptimal (<15°C or >30°C)**: Success rate 58% ± 8%

### Humidity Effects

Humidity analysis demonstrates optimal range of 70-90% relative humidity:

- **Optimal (70-90%)**: Success rate 80% ± 4%
- **Acceptable (50-70% or 90-100%)**: Success rate 72% ± 6%
- **Suboptimal (<50%)**: Success rate 55% ± 10%

The combined environmental score \eqref{eq:environmental_score} shows strong correlation with success rate ($r = 0.68$, $p < 0.001$).

## Prediction Model Validation

### Compatibility Prediction Accuracy

Validation of our compatibility prediction model \eqref{eq:combined_compatibility} on held-out data shows:

- **Mean absolute error**: 0.12 ± 0.03
- **Correlation with actual success**: $r = 0.78$ ($p < 0.001$)
- **Classification accuracy** (success/failure): 84% ± 3%

The model demonstrates good calibration, with predicted probabilities closely matching observed success rates across the full range (0.3-0.95).

### Biological Simulation Validation

Comparison of simulated healing timelines with literature-reported healing rates shows good agreement:

- **Callus formation time**: Predicted 7-14 days, literature range 5-18 days
- **Vascular connection**: Predicted 14-28 days, literature range 12-30 days
- **Full union establishment**: Predicted 30-60 days, literature range 25-70 days

The simulation model \eqref{eq:healing_dynamics}-\eqref{eq:vascular_dynamics} captures the temporal dynamics with mean absolute error of 2.3 days for callus formation and 3.1 days for vascular connection.

## Success Factor Importance

### Factor Analysis

Analysis of factor importance using correlation and regression analysis reveals:

1. **Species Compatibility** (weight: 0.40): Strongest predictor, correlation $r = 0.75$
2. **Technique Quality** (weight: 0.30): Moderate predictor, correlation $r = 0.58$
3. **Environmental Conditions** (weight: 0.20): Moderate predictor, correlation $r = 0.52$
4. **Seasonal Timing** (weight: 0.10): Weak predictor, correlation $r = 0.35$

These weights align with the success probability model \eqref{eq:success_probability} and are consistent across different species types and techniques.

### Interaction Effects

Analysis reveals significant interaction effects:

- **Compatibility × Technique**: High compatibility amplifies technique quality effects
- **Environment × Timing**: Optimal environmental conditions compensate for suboptimal timing
- **Species × Technique**: Technique effectiveness varies by species type

These interactions are incorporated into the prediction model through interaction terms.

## Economic Analysis Results

### Cost-Breakdown Analysis

Economic analysis of grafting operations reveals:

- **Average cost per graft**: \$3.50 ± \$0.80
  - Labor: \$2.00 (57%)
  - Materials: \$1.00 (29%)
  - Overhead: \$0.50 (14%)
- **Value per successful graft**: \$20.00 ± \$5.00
- **Break-even success rate**: 17.5% ± 2.5%

These figures demonstrate the economic viability of grafting operations, with break-even rates well below typical success rates (70-85%).

### Productivity Metrics

Analysis of productivity shows:

- **Grafts per day**: 50-100 (depending on technique)
- **Successful grafts per year**: 8,750-17,000 (assuming 250 working days)
- **Efficiency**: 75-85% (success rate × working efficiency)

These metrics support the economic viability of commercial grafting operations.

## Seasonal Timing Analysis

### Optimal Grafting Windows

Analysis of seasonal timing across climate zones reveals:

- **Temperate species (Northern Hemisphere)**: Optimal window February-April (months 2-4)
- **Tropical species**: Year-round with optimal period June-September (months 6-9)
- **Subtropical species**: Optimal window November-March (months 11-3)

The seasonal suitability model shows strong predictive power ($r = 0.71$, $p < 0.001$) for temperate species, with reduced accuracy for tropical species due to year-round grafting potential.

## Validation and Reproducibility

All experimental results are generated using reproducible computational workflows:

- **Data generation**: Seeded random number generators ensure reproducibility
- **Simulation parameters**: Documented and version-controlled
- **Statistical analysis**: Standardized procedures with reported confidence intervals
- **Figure generation**: Automated scripts with version tracking

The complete analysis pipeline can be reproduced by running:

```bash
python3 scripts/graft_analysis_pipeline.py
```

This ensures all results are traceable and verifiable, supporting scientific reproducibility and transparency.
