# On latent position inference from doubly stochastic messaging activities

**Authors:** Nam H. Lee, Jordan Yoder, Minh Tang, Carey E Priebe

**Year:** 2012

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [lee2012latent.pdf](../pdfs/lee2012latent.pdf)

**Generated:** 2025-12-05 13:16:06

---

**Overview/Summary**
The paper "On latent position inference from doubly stochastic messaging activities" proposes a novel approach for inferring the underlying community structure in a network of interacting agents that communicate through a doubly stochastic process. The doubly stochastic process is a generalization of the stochastic block model, where each agent's activity is determined by both its own state and the states of all other agents. In this paper, the authors assume that the doubly stochastic process is a Markov chain with a finite number of latent positions, and they analyze the asymptotic behavior of the doubly stochastic process in the case where the community starts from no apparent clustering but as time passes, each agent becomes more likely to be attracted to exactly one of the latent positions. The authors' main interest is in the case where the population eventually reaches a total consensus, i.e., all agents are attracted to the same position. They show that if the doubly stochastic process is contracting toward a set of closed convex nonempty disjoint subsets B1 and B2 of [0, 1] such that for some t ∈[0, T], µs(B1 ∪B2) ≥µt(B1 ∪B2) for each s ≥ t and µT([0, 1]) = 1, then the population will eventually reach a total consensus. The authors also show that if the doubly stochastic process is contracting toward two distinct positions, then there are at least three distinct values in [0, 1] separated by at least ∆, to exactly one of which each agent's position is attracted.

**Key Contributions/Findings**
The authors' main contributions are a set of sufficient conditions for the asymptotic total consensus and the partial consensus. The paper also provides an algorithm that can be used to infer the underlying community structure in the case where the population eventually reaches a total consensus. The authors show that if the doubly stochastic process is contracting toward a set of closed convex nonempty disjoint subsets B1 and B2 of [0, 1] such that for some t ∈[0, T], µs(B1 ∪B2) ≥µt(B1 ∪B2) for each s ≥ t and µT([0, 1]) = 1, then the population will eventually reach a total consensus. The authors also show that if the doubly stochastic process is contracting toward two distinct positions, then there are at least three distinct values in [0, 1] separated by at least ∆, to exactly one of which each agent's position is attracted.

**Methodology/Approach**
The paper starts with a quadratic Taylor series approximation for the operator A(µ) in (A.1). The second numerical experiment in Section 6 focuses on the case where the community starts from no apparent clustering but as time passes, each agent becomes more likely to be attracted to exactly one of the latent positions. In this paper, the authors use a model that captures the action in (A.1) up to the second order. To begin, note that
f( z ) = f( x )  + Df( x )  ·(z−x)  +   \frac{1}{2} (z−x)^{\intercal}D^{2}f(x)(z−x)  +  H.O.T.,
where Df( x ) ∈ Rd and Df( x ) ∈ Md×d denote respectively the gradient and the Hessian of f at x, and H.O.T. denotes the higher order terms. Suppose that µt is given. Now, we have
Atf( x ) := A(µt)f( x )
= 2
\int
ψ(y−x)
Df(x)  · (1 −ω)(y−x)\mu_t(y)dy
+   \frac{1}{2}
∫
ψ(y−x)
(1
2(1 −ω)2(y−x)^{\intercal} D^{2}f(x)(y−x)
)
\mu_t(y)dy + H.O.T.
=  ( ∑
k=1
b_{t}(x)\partial k f(x)  +  \sum_{k_{1}}
\sum_{k_{2}}
a_{k_{1},k_{2}}(x)\partial^{2}
k_{1},k_{2} f(x)
)
+ H.O.T.,
where bt(x) ∈ Rd and at(x) ∈ Rd×d are given by the
[... truncated for summarization ...]

**Results/Data**
The authors show that if the doubly stochastic process is contracting toward a set of closed convex nonempty disjoint subsets B1 and B2 of [0, 1] such that for some t ∈[0, T], µs(B1 ∪B2) ≥µt(B1 ∪B2) for each s ≥ t and µT([0, 1]) = 1, then the population will eventually reach a total consensus. The authors also show that if the doubly stochastic process is contracting toward two distinct positions, then there are at least three distinct values in [0, 1] separated by at least ∆, to exactly one of which each agent's position is attracted.

**Limitations/Discussion**
The paper does not discuss any limitations or future work.

---

**Summary Statistics:**
- Input: 13,550 words (73,844 chars)
- Output: 698 words
- Compression: 0.05x
- Generation: 41.7s (16.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
