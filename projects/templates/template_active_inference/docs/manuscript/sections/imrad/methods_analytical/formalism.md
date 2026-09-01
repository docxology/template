The entangled joint over binary policies satisfies

$$
q_\lambda(\pi) \propto E(\pi)\,\exp(\lambda J(\pi)),
$$ {#eq:entangled_joint}

with symmetric Ising coupling $J$ and deformation parameter $\lambda$. Let $\sigma(\lambda)=q_\lambda(\pi_1=\pi_2)$ be the probability that the two streams agree (the diagonal mass of the $2\times2$ joint); by symmetry both marginals are uniform. With binary entropy $H_b(p)=-p\log p-(1-p)\log(1-p)$ in nats, the joint entropy is $H(q_\lambda)=\log 2 + H_b(\sigma(\lambda))$ while each marginal contributes $\log 2$, so the mutual information is

$$
I(\lambda)=\sum_k H(q_k)-H(q_\lambda)=\log 2 - H_b(\sigma(\lambda)),
$$

vanishing at $\lambda=0$ ($\sigma=\tfrac12$, independent streams) and saturating at $\log 2$ as $\lambda\to\infty$ ($\sigma\to1$, perfectly entangled). These symbols are the rows of `analytical_assumption_index.json`, so the derivation is auditable rather than asserted.
