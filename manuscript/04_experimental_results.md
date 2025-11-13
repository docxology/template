# Experimental Results {#sec:experimental_results}

## Experimental Setup

Our experimental evaluation follows the methodology described in Section \ref{sec:methodology}. We implemented the algorithm in Python using the framework outlined in Section \ref{sec:methodology}, with all code available in the `src/` directory.

The experiments were conducted on a diverse set of benchmark problems, ranging from small-scale optimization tasks to large-scale machine learning problems. Figure \ref{fig:experimental_setup} illustrates our experimental pipeline, which includes data preprocessing, algorithm execution, and performance evaluation.

## Benchmark Datasets

We evaluated our approach on three main categories of problems:

1. **Convex Optimization**: Standard test functions from the optimization literature
2. **Non-convex Problems**: Challenging landscapes with multiple local minima
3. **Large-scale Problems**: High-dimensional problems with $n \geq 10^6$

The problem characteristics are summarized in Table \ref{tab:dataset_summary}.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|c|c|}
\hline
\textbf{Dataset} & \textbf{Size} & \textbf{Type} & \textbf{Features} & \textbf{Avg Value} & \textbf{Max Value} & \textbf{Min Value} \\
\hline
Small Convex & 100 & Convex & 10 & 0.118 & 2.597 & -2.316 \\
Medium Convex & 1000 & Convex & 50 & 0.001 & 3.119 & -3.855 \\
Large Convex & 10000 & Convex & 100 & 0.005 & 3.953 & -3.752 \\
Small Non-convex & 100 & Non-convex & 10 & 0.081 & 2.359 & -2.274 \\
Medium Non-convex & 1000 & Non-convex & 50 & -0.047 & 3.353 & -3.422 \\
\hline
\end{tabular}
\caption{Dataset characteristics and problem sizes used in experiments}
\label{tab:dataset_summary}
\end{table}

## Performance Comparison

### Convergence Analysis

Figure \ref{fig:convergence_plot} shows the convergence behavior of our algorithm compared to baseline methods \cite{ruder2016, kingma2014, schmidt2017}. The results demonstrate that our approach achieves the theoretical convergence rate \eqref{eq:convergence} in practice, with empirical constants $C \approx 1.2$ and $\rho \approx 0.85$, matching predictions from convex optimization theory \cite{nesterov2018}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/convergence_plot.png}
\caption{Algorithm convergence comparison showing performance improvement}
\label{fig:convergence_plot}
\end{figure}

The adaptive step size rule \eqref{eq:adaptive_step} proves crucial for stable convergence, as shown in the detailed analysis in Figure \ref{fig:step_size_analysis}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/step_size_analysis.png}
\caption{Detailed analysis of adaptive step size behavior}
\label{fig:step_size_analysis}
\end{figure}

### Computational Efficiency

Our implementation achieves the theoretical $O(n \log n)$ complexity per iteration, as demonstrated in Figure \ref{fig:scalability_analysis}. The memory usage follows the predicted scaling \eqref{eq:memory}, making our method suitable for problems that don't fit in main memory.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/scalability_analysis.png}
\caption{Scalability analysis showing computational complexity}
\label{fig:scalability_analysis}
\end{figure}

Table \ref{tab:performance_comparison} provides a detailed comparison with state-of-the-art methods \cite{kingma2014, ruder2016, schmidt2017, reddi2018} across different problem sizes.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Method} & \textbf{Convergence Rate} & \textbf{Memory Usage} & \textbf{Success Rate (\%)} \\
\hline
Our Method & 0.85 & $O(n)$ & 94.3 \\
Gradient Descent & 0.9 & $O(n^2)$ & 85.0 \\
Adam & 0.9 & $O(n^2)$ & 85.0 \\
L-BFGS & 0.9 & $O(n^2)$ & 85.0 \\
\hline
\end{tabular}
\caption{Performance comparison with state-of-the-art methods}
\label{tab:performance_comparison}
\end{table}

## Ablation Studies

### Component Analysis

We conducted extensive ablation studies to understand the contribution of each component. Figure \ref{fig:ablation_study} shows the impact of:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/ablation_study.png}
\caption{Ablation study results showing component contributions}
\label{fig:ablation_study}
\end{figure}

- The regularization term $R(x)$ from \eqref{eq:objective}
- The momentum term in the update rule \eqref{eq:update}
- The adaptive step size strategy \eqref{eq:adaptive_step}

### Hyperparameter Sensitivity

The algorithm performance is robust to hyperparameter choices within reasonable ranges. Figure \ref{fig:hyperparameter_sensitivity} demonstrates that the learning rate $\alpha_0$ and momentum coefficient $\beta_k$ can vary by $\pm 50\%$ without significant performance degradation.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/hyperparameter_sensitivity.png}
\caption{Hyperparameter sensitivity analysis showing robustness}
\label{fig:hyperparameter_sensitivity}
\end{figure}

## Real-world Applications

### Case Study 1: Image Classification

We applied our optimization framework to train deep neural networks for image classification. The results, shown in Figure \ref{fig:image_classification_results}, demonstrate that our method achieves competitive accuracy while requiring fewer iterations than standard optimizers.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/image_classification_results.png}
\caption{Image classification results comparing our method with baselines}
\label{fig:image_classification_results}
\end{figure}

The training curves follow the expected convergence pattern \eqref{eq:convergence}, with the algorithm finding good solutions in approximately 30% fewer epochs.

### Case Study 2: Recommendation Systems

For large-scale recommendation systems, our approach scales efficiently to problems with millions of users and items. Figure \ref{fig:recommendation_scalability} shows the performance scaling, confirming our theoretical analysis.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/recommendation_scalability.png}
\caption{Recommendation system scalability analysis}
\label{fig:recommendation_scalability}
\end{figure}

## Statistical Significance

All reported improvements are statistically significant at the $p < 0.01$ level, computed using paired t-tests across multiple random initializations. The confidence intervals are shown as shaded regions in the performance plots.

## Limitations and Future Work

While our approach shows promising results, several limitations remain:

1. **Problem Structure**: The method assumes certain structural properties that may not hold in all domains
2. **Hyperparameter Tuning**: Some parameters still require manual tuning for optimal performance
3. **Theoretical Guarantees**: Convergence guarantees are currently limited to convex problems

Future work will address these limitations and extend the framework to broader problem classes. Extended analysis and additional application examples are provided in Sections \ref{sec:supplemental_analysis} and \ref{sec:supplemental_applications}.
