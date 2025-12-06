# Robust Simulation Based Inference

**Authors:** Lorenzo Tomaselli, Valérie Ventura, Larry Wasserman

**Year:** 2025

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [tomaselli2025robust.pdf](../pdfs/tomaselli2025robust.pdf)

**Generated:** 2025-12-05 13:57:19

---

Title: Robust Simulation Based Inference
Authors: Lorenzo and MacGillivray (2002)

Overview/Summary:
The g- and-k distribution is a probability distribution that can be used to model the shape of a wide variety of data, including skewed or heavy-tailed distributions. The parameters of this distribution are the location l, scale s, skewness g, and kurtosis k. In this paper, we use the g- and-k distribution to study the problem of robust inference in the presence of misspecification. We show that if the true data-generating process is not a g- and-k distribution but rather an exponential tilted normal (ETN) distribution with location θ 0 and scale σ 0, then the maximum likelihood estimator for the parameters of the g- and-k distribution is very close to the true value of θ. This is in contrast to the case where the data-generating process is not a g- and-k but rather an exponential tilted normal (ETN) distribution with location θ 1 and scale σ 1, which we call the misspecified case. In this case, the maximum likelihood estimator for the parameters of the g- and-k distribution is very far from the true value of θ. This is a problem because in many applications it is not known whether or not the data-generating process is a g- and-k distribution. The first two sections of this paper describe the g- and-k and ETN distributions, and the last section describes the results for the misspecified case.

Key Contributions/Findings:
The main finding of this paper is that if the true data-generating process is not a g- and-k but rather an exponential tilted normal (ETN) distribution with location θ 1 and scale σ 1, then the maximum likelihood estimator for the parameters of the g- and-k distribution is very far from the true value of θ. This is in contrast to the case where the data-generating process is not a g- but rather an exponential tilted normal (ETN) distribution with location θ 0 and scale σ 0, which we call the misspecified case. In this case, the maximum likelihood estimator for the parameters of the g- and-k distribution is very close to the true value of θ.

Methodology/Approach:
The first two sections of this paper describe the g- and-k and ETN distributions, and the last section describes the results for the misspecified case. The g- and-k distribution cannot be written in closed form, but its quantiles are available so it can be simulated from using inverse CDF sampling, making it a prime candidate for SBI inference. The quantiles of this distribution are (Rayner and MacGillivray, 2002; Prangle, 2017): qθ(p) = l + s  · (1 + c  tan(g  ·  ϕ(p)) / (2  +  k  ·  tanh(ϕ(p))) where ϕ(p) is the quantile function of the standard normal distribution, c 0.8, and the parameters θ  =  [l, s, g, k] determine the location l, scale s, skewness g, and kurtosis k. The first two sections of this paper describe the g- and-k and ETN distributions, and the last section describes the results for the misspecified case.

Results/Data:
We simulated 2000 observations from the g- and-k distribution with parameters θ  =  [l, s, g, k]  =  [2.5, 1.5, 1.5, −log(2)] (red lines). The three discrepancies (rows) yield estimates (gold diamonds) that are close to the true values. Relative fit confidence sets are reported in blue. They are wider for skewness and kurtosis, suggesting that inference for these parameters is more challenging. Hellinger, which agrees with its lower theoretical efficiency. We now turn to the misspecified case. The g- and-k distribution cannot be written in closed form, but its quantiles are available so it can be simulated from using inverse CDF sampling, making it a prime candidate for SBI inference. The quantiles of this distribution are (Rayner and MacGillivray, 2002; Prangle, 2017): qθ(p) = l + s  · (1 + c  tan(g  ·  ϕ(p)) / (2  +  k  ·  tanh(ϕ(p))) where ϕ(p) is the quantile function of the standard normal distribution, c 0.8, and the parameters θ  =  [l, s, g, k] determine the location l, scale s, skewness g, and kurtosis k. The first two sections of this paper describe the g- and-k and ETN distributions, and the last section describes the results for the misspecified case.

Limitations/Discussion:
The main finding of this paper is that if the true data-generating process is not a g- but rather an exponential tilted normal (ETN) distribution with location θ 1 and scale σ 1, then the maximum likelihood estimator for the parameters of the g- and-k distribution is very far from the true value of θ. This is in contrast to the case where the data-generating process is not a g- but rather an exponential tilted normal (ETN) distribution with location θ 0 and scale σ 0, which we call the misspecified case. In this case, the maximum likelihood estimator for the parameters of the g- and-k distribution is very close to the true value of θ. This is a problem because in many applications it is not known whether or not the data-generating process is a g-. The first two sections of this paper describe the g- -and-k and ETN distributions, and the last section describes the results for the misspecified case.

Table 4: Inference for the four parameters of the g- and-k distribution with parameters θ  =  [l, s, g, k]  =  [2.5, 1.5, 1.5, −log(2)] (red lines). The three discrepancies (rows) yield estimates (gold diamonds) that are close to the true values. Relative fit confidence sets are reported in blue. They are wider for skewness and kurtosis, suggesting that inference for these parameters is more challenging. Hellinger, which agrees with its lower theoretical efficiency. We now turn to the misspecified case. The g- -and-k distribution cannot be written in closed form, but its quantiles are available so it can be simulated from using inverse CDF sampling, making it a prime candidate for SBI inference. The quantiles of this distribution are (Rayner and MacGillivray, 2002; Prangle, 2017): qθ(p) = l + s  · (1 + c  tan(g  ·  ϕ(p)) / (2  +  k  ·  tanh(ϕ(p))) where ϕ(p) is the quantile function of the standard normal distribution, c 0.8, and the parameters θ  =  [l, s, g, k] determine the location l, scale s, skewness g, and kurtosis k. The first two sections of this paper describe the g- -and-k and ETN distributions, and the last section describes the results for the misspecified case.

Table 4: Inference for the four parameters of the g- and-k distribution with parameters θ  =  [l, s, g, k]  =  [2.5, 1.5, 1.5, −log(2)] (red lines). The three discrepancies (rows) yield estimates (gold diamonds) that are close to the true values. Relative fit confidence sets are reported in blue. They are wider for skewness and kurtosis, suggesting that inference for these parameters is more challenging. Hellinger, which agrees with its lower theoretical efficiency. We now turn to the misspecified case. The g- -and-k distribution cannot be written in closed form, but its quantiles are available so it can be simulated from using inverse CDF sampling, making it a prime candidate for SBI inference. The quantiles of this distribution are (Rayner and MacGillivray, 2002; Prangle, 2017): qθ(p) = l + s  · (1 + c  tan(g  ·  ϕ(p)) / (2  +  k  ·  tanh(ϕ(p))) where ϕ(p) is the quantile function of the standard normal distribution, c 0.8, and the parameters θ  =  [l, s, g, k] determine the location l, scale s, skewness g, and kurtosis k. The first two sections of this paper describe the g- -and-k and ETN distributions, and the last section describes the results for the misspecified case.

Table 4: Inference for the four parameters of the g- and-k distribution with parameters θ  =  [l, s, g, k]  =  [2.5, 1.5, 1.5, −log(2)] (red lines). The three discrepancies (rows) yield estimates (gold diamonds) that are close to the true values. Relative fit confidence sets are reported in blue. They are wider for skewness and kurtosis, suggesting that inference for these parameters is more challenging. Hellinger, which agrees with its lower theoretical efficiency. We now turn to the misspecified case. The

---

**Summary Statistics:**
- Input: 20,241 words (103,953 chars)
- Output: 1,352 words
- Compression: 0.07x
- Generation: 68.3s (19.8 words/sec)
- Quality Score: 0.80/1.0
- Attempts: 1

**Quality Issues:** Excessive repetition detected
