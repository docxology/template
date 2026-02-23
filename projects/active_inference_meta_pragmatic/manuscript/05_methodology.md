# Methodology {#sec:methodology}

This paper presents a theoretical framework paper rather than an empirical study. The methodology combines conceptual analysis, mathematical formalization, and computational validation to establish and evaluate the $2 \times 2$ quadrant structure for Active Inference's meta-level operation.

## Theoretical Approach

The research adopts a conceptual-analytic methodology grounded in the Active Inference literature \cite{friston2010free, parr2022active}. The $2 \times 2$ framework was derived by identifying two orthogonal dimensions along which Active Inference's contributions can be organized:

**Data/Meta-Data dimension.** This axis reflects the information hierarchy: *Data* refers to raw sensory observations processed through the generative model's likelihood mapping ($A$ matrix), while *Meta-Data* refers to higher-order information about data quality, reliability, and provenance (confidence scores, temporal stamps, source credibility). The distinction captures the difference between what is observed and what is known about the observation process itself.

**Cognitive/Meta-Cognitive dimension.** This axis reflects the processing level hierarchy, following the meta-cognitive tradition from \cite{flavell1979metacognition} and \cite{nelson1990metamemory}: *Cognitive* processing involves direct transformation of information through belief updating and policy selection, while *Meta-Cognitive* processing involves monitoring, evaluating, and regulating cognitive processes themselves. In Active Inference terms, this distinguishes EFE computation from reasoning about EFE computation.

The cross-product of these dimensions yields four quadrants (Q1--Q4), each representing a distinct mode of cognitive operation with specific mathematical formulations grounded in the EFE framework.

## Mathematical Formalization

Each quadrant is formalized through extensions of the standard EFE formulation (Equation \eqref{eq:efe}):

- **Q1** employs the baseline EFE decomposition into epistemic and pragmatic components.
- **Q2** extends EFE with meta-data weighting parameters ($w_e$, $w_p$, $w_m$) that modulate the relative influence of epistemic, pragmatic, and meta-data-derived value.
- **Q3** introduces hierarchical EFE with a meta-cognitive term $\mathcal{F}_{meta}(\pi)$ weighted by $\lambda$, enabling self-assessment and adaptive strategy selection.
- **Q4** formulates framework-level optimization over the parameter space $\Theta$, with regularization $\mathcal{R}(\Theta)$ ensuring coherence.

All formulations maintain consistency with the variational free energy framework and reduce to standard Active Inference in appropriate limits.

## Computational Validation

The theoretical framework is validated through computational implementations in the project's source modules. Each quadrant is implemented as a testable module with deterministic outputs (fixed random seeds) enabling reproducible validation:

- **Quadrant implementations** (`src/framework/quadrant_framework.py`) instantiate each quadrant's mathematical formulation with concrete matrix specifications.
- **Active inference core** (`src/core/active_inference.py`) implements EFE calculation, policy selection, and belief updating.
- **Meta-cognitive module** (`src/framework/meta_cognition.py`) implements confidence assessment, adaptive attention allocation, and strategy selection.
- **Generative model specification** (`src/core/generative_models.py`) implements $A$, $B$, $C$, $D$ matrix construction and validation.
- **Visualization engine** (`src/visualization/visualization.py`) produces publication-quality figures with programmatic font and layout enforcement.

Validation metrics include decision accuracy under uncertainty, confidence calibration quality, strategy adaptation appropriateness, and framework optimization convergence. Statistical validation employs hypothesis testing (t-tests, ANOVA) with effect sizes reported as Cohen's $d$, as detailed in Appendix \ref{sec:validation_results}.

## Scope and Limitations

As a theoretical framework paper, the methodology is subject to inherent limitations: the quadrant boundaries are analytical constructs that may not correspond to sharp neural or computational distinctions, and the computational validation demonstrates feasibility rather than empirical necessity. We address these limitations explicitly in Section \ref{sec:limitations}.
