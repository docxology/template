# [chen2026fractionalorder] — Fractional-order dynamics driven stochastic gradient descent method with momentum

_Source keyword: **stochastic gradient descent**_

_2026_  ·  
Yuquan Chen, Hong Wenchao, Mo Xuan, Bing Wang
DOI: <https://doi.org/10.2139/ssrn.6902318>

## Abstract

High-performance optimization algorithms are essential for deep learning,a novel fractional-order stochastic gradient descent with momentum (FOSGDM)optimizer is proposed, which achieves a better performance both inconvergence speed and global search ability. Firstly, existing accelerated optimizationalgorithms are expressed by a closed-loop system with gradientfeedback, where the SGDM optimizer is reconstructed as a second-order dynamicsystem. By replacing integer-order differential operator in the transferfunction of SGDM system with a fractional-order differential operator, theFOSGDM optimizer is then given. Furthermore, a variable order strategy(StepAlpha) is designed to dynamically adjust the fractional order, which effectivelybalances the convergence speed and convergence accuracy. Finally,a semi-implicit Euler discretization is applied to derive a computationallyefficient iterative algorithm. Extensive experiments demonstrate that FOSGDMsignificantly accelerates convergence and improves training accuracywhile maintaining a balanced computational overhead through an optimalmemory truncation strategy.
