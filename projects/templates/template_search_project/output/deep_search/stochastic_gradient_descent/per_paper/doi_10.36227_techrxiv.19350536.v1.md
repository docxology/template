# [abubaker2022scaling] — Scaling Stratified Stochastic Gradient Descent for Distributed Matrix Completion

_Source keyword: **stochastic gradient descent**_

_2022_  ·  
Nabil Abubaker, M. Ozan Karsavuran, Cevdet Aykanat
DOI: <https://doi.org/10.36227/techrxiv.19350536.v1>

## Abstract

Stratified SGD (SSGD) is the primary approach for achieving serializable
parallel SGD for matrix completion. State-of-the-art parallelizations of
SSGD fail to scale due to huge communication overhead. During an SGD
epoch, these methods send data proportional to one of the dimensions of
the rating matrix. We propose a framework for scalable SSGD through
significantly reducing the communication overhead via exchanging
point-to-point messages utilizing the sparsity of the input matrix. We
provide formulas to represent the essential communication for correctly
performing parallel SSGD and we propose a dynamic programming algorithm
for efficiently computing them to establish the point-to-point message
schedules. This scheme, however, significantly increases the number of
messages sent by a processor per epoch from O(K) to O(K^2) for a
K-processor system which might limit the scalability. To remedy this, we
propose a Hold-and-Combine strategy to limit the upper-bound on the
number of messages sent per processor to O(KlgK). We also propose a
hypergraph partitioning model that correctly encapsulates reducing the
communication volume. Experimental results show that the framework
successfully achieves a scalable distributed SSGD through significantly
reducing the communication overhead. Our code is publicly available at:
github.com/nfabubaker/CESSGD
