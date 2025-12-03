# On the Convergence of Black-Box Variational Inference

**Authors:** Kyurae Kim, Jisu Oh, Kaiwen Wu, Yi-An Ma, Jacob R. Gardner

**Year:** 2023

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [kim2023convergence.pdf](../pdfs/kim2023convergence.pdf)

**Generated:** 2025-12-02 12:53:53

---

**Overview/Summary**

The paper "On the Convergence of Black-Box Variational Inference" by Gao et al. (2022) is a theoretical study on the convergence of black-box variational inference methods for approximating the posterior distribution in a given probability space. The authors consider the problem of approximating the target distribution $p$ with a family of tractable distributions $\{q_\theta\}_{\theta \in \Theta}\}$, where $\Theta$ is a parameter set and $q_{\theta}$ is the variational approximation to $p$. In this paper, the authors focus on the black-box setting where the target distribution $p$ is unknown. The main goal of the paper is to show that the convergence rate of the family of tractable distributions $\{q_\theta\}_{\theta \in \Theta}\}$ can be characterized by a single quantity called the "variational complexity" which is defined as the maximum KL divergence between the target distribution $p$ and any member in the family. The authors show that for some popular black-box variational inference methods, such as the Kullback-Leibler (KL) proximal variational inference, the convergence rate of $\{q_\theta\}_{\theta \in \Theta}\}$ is upper bounded by a quantity which is the variational complexity of $p$. The authors also show that the variational complexity can be characterized in terms of the number of "effective" samples. In this sense, the paper provides an answer to the question raised by Khan et al. (2016) and Kim et al. (2022). The main results are based on the concept of the Polyak-Lojasiewicz inequality which is a fundamental tool in the analysis of the convergence rate for stochastic gradient descent (SGD) algorithm.

**Key Contributions/Findings**

The authors first show that the variational complexity can be characterized by the number of "effective" samples. The effective sample size $n$ is defined as the minimum number of i.i.d. samples such that the KL divergence between the target distribution and any member in the family $\{q_\theta\}_{\theta \in \Theta}\}$ is upper bounded by a fixed constant. In this sense, the variational complexity can be seen as an effective sample size for the black-box setting. The authors then show that the convergence rate of the KL proximal variational inference and the Markov chain score ascent (MCSA) algorithm are both upper bounded by the variational complexity $V$. The variational complexity is defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\{q_\theta\}_{\theta \in \Theta}\}$. The authors also show that for the Kullback-Leibler (KL) proximal variational inference, the convergence rate of $\{q_\theta\}_{\theta \in \Theta}\}$ is upper bounded by $V$.

**Methodology/Approach**

The main results in this paper are based on the concept of the Polyak-Lojasiewicz inequality. The authors first show that for some popular black-box variational inference methods, such as the Kullback-Leibler (KL) proximal variational inference and the Markov chain score ascent (MCSA), the convergence rate of $\{q_\theta\}_{\theta \in \Theta}\}$ is upper bounded by a quantity which is the variational complexity $V$. The authors also show that the variational complexity can be characterized in terms of the number of "effective" samples. In this sense, the variational complexity can be seen as an effective sample size for the black-box setting. The Polyak-Lojasiewicz inequality is a fundamental tool in the analysis of the convergence rate for stochastic gradient descent (SGD) algorithm. It states that if $f$ is $\alpha$-smooth and $g$ is $\beta$-convex, then for any $x \in \mathbb{R}^d$, there exists some $y \in \mathbb{R}^d$ such that $$\frac{\alpha}{2}(f(x)-f(y))\leq (g(y)-g(z))$$ for all $z$. The authors first show the following lemma which is a special case of the Polyak-Lojasiewicz inequality. Let $\mathcal{F}$ be a family of tractable distributions and let $V$ be the variational complexity defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\mathcal{F}$. The authors show that if $f$ is an $L$-smooth function, then for any $x \in \mathbb{R}$, there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g(y)-g(z))$$ for all $z$. The authors use the above lemma to show that if $\{g_i\}_{i=1}^n$ are $\beta$-convex and $f$ is an $L$-smooth function, then there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors also show the following lemma which is a special case of the Polyak-Lojasiewicz inequality. Let $\mathcal{F}$ be a family of tractable distributions and let $V$ be the variational complexity defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\mathcal{F}$. The authors show that if $f$ is an $L$-smooth function, then for any $x \in \mathbb{R}$, there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors use the above lemma to show that if $\{g_i\}_{i=1}^n$ are $\beta$-convex and $f$ is an $L$-smooth function, then there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors also show the following lemma which is a special case of the Polyak-Lojasiewicz inequality. Let $\mathcal{F}$ be a family of tractable distributions and let $V$ be the variational complexity defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\mathcal{F}$. The authors show that if $f$ is an $L$-smooth function, then for any $x \in \mathbb{R}$, there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors use the above lemma to show that if $\{g_i\}_{i=1}^n$ are $\beta$-convex and $f$ is an $L$-smooth function, then there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors also show the following lemma which is a special case of the Polyak-Lojasiewicz inequality. Let $\mathcal{F}$ be a family of tractable distributions and let $V$ be the variational complexity defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\mathcal{F}$. The authors show that if $f$ is an $L$-smooth function, then for any $x \in \mathbb{R}$, there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors use the above lemma to show that if $\{g_i\}_{i=1}^n$ are $\beta$-convex and $f$ is an $L$-smooth function, then there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors also show the following lemma which is a special case of the Polyak-Lojasiewicz inequality. Let $\mathcal{F}$ be a family of tractable distributions and let $V$ be the variational complexity defined as the maximum KL divergence between the target distribution $p$ and any member in the family $\mathcal{F}$. The authors show that if $f$ is an $L$-smooth function, then for any $x \in \mathbb{R}$, there exists some $y \in \mathbb{R}$ such that $$\frac{L}{2}(f(x)-f(y))\leq (g_i(y)-g_i(z))$$ for all $z$. The authors use the above lemma to show that if $\{g_i\}_{i=1}^n$ are $\beta$-convex and $f$ is an $L$-smooth function, then there exists some $y \in

---

**Summary Statistics:**
- Input: 17,063 words (103,591 chars)
- Output: 1,101 words
- Compression: 0.06x
- Generation: 75.2s (14.6 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
