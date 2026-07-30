# [yang2022adaptive] — Adaptive stochastic gradient descent for large-scale learning problems

_Source keyword: **stochastic gradient descent**_

_2022_  ·  
Zhuang Yang, Li Ma
DOI: <https://doi.org/10.21203/rs.3.rs-1066512/v1>

## Abstract

Abstract
        As an effective strategy to enhance stochastic optimization, determining an appropriate step size sequence when performing these algorithms has been warmly encouraged in solving large-scale learning problems. This paper equips stochastic optimization algorithms with an adaptive step size strategy by using the diagonal Barzilai-Borwein (DBB) step size. Specifically, this work proposes a novel stochastic variance reduced algorithm by incorporating DBB into the variance-reduced algorithm, termed mS2GD-DBB. mS2GD-DBB uses a diagonal matrix to approximate the curvature information and accesses to a better curvature information than the conventional BarzilaiBorwein (BB) technique, where the latter works with the scalar approximation of the curvature information. We prove that the proposed algorithm attains a linear convergence rate for strongly convex cases. Moreover, we show that the complexity of the proposed algorithm matches the best known complexity of stochastic optimization algorithms. Numerical experiments suggest that the proposed algorithm shows much promise.
