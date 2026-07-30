# [srinivasan2026intelligent] — An Intelligent Predictive  CPU Scheduling Algorithm Using Online Multiple Linear Regression and Stochastic Gradient Descent

_Source keyword: **stochastic gradient descent**_

_2026_  ·  
Ashwin  Kumar Srinivasan
DOI: <https://doi.org/10.2139/ssrn.6956552>

## Abstract

Traditional CPU scheduling algorithms — First-Come First-Served (FCFS), Round Robin (RR), and Shortest Job First (SJF) — rely on static heuristics or single-variable exponential smoothing to estimate process burst times. These estimators work reasonably well under stable workloads, but degrade noticeably when process behaviour shifts mid-run, something that is hard to detect until the damage is already in the AWT numbers. This paper describes an alternative: replacing the classical burst-time estimator with an Online Multiple Linear Regression (MLR) model updated via Stochastic Gradient Descent (SGD) after every context switch. The ready queue is sorted by a composite Score-Based Aging function that couples burst prediction with starvation prevention via an aging term. Theoretical analysis gives O(n log n) scheduling complexity with O(k) per-switch learning overhead. We ran some tests using ISO C11 and tried it 15 different times with random settings, and each time we used 30 separate processes to see what would happen, covering CPU-bound, I/O-bound, and mixed workloads — producing a mean aggregate AWT of 268.3 ms. Under these cold-start conditions, MLR+SGD does not outperform SJF with exponential smoothing: the model incurs a 20.5% AWT penalty on CPU-bound workloads. It has a big impact on mixed workloads, with a penalty of 18.3%. But when it comes to short I/O-bound workloads, the deficit is relatively small, at just 2.3%.
