# Robust Variational Inference

**Authors:** Michael Figurnov, Kirill Struminsky, Dmitry Vetrov

**Year:** 2016

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [figurnov2016robust.pdf](../pdfs/figurnov2016robust.pdf)

**Generated:** 2025-12-02 10:41:19

---

**Overview/Summary**
The paper "Robust Variational Inference" by Michael Figurnov, Kirill Struminsky, and Dmitry Vetrov presents a new variational objective for approximate Bayesian inference that is robust to the presence of uninformative data points in the training set. The authors propose to replace the traditional log-evidence with a robust counterpart that ignores the objects with low evidence values. They also derive a lower bound on the robust model evidence and show that this new objective can be used to successfully train variational autoencoders even when the noise objects comprise the majority of the training dataset. In addition, they compare the proposed robust objective with the traditional non-robust one on the original datasets without synthetic noise. The paper is well-organized and easy to follow.

**Key Contributions/Findings**
The main contributions of this work are two-fold: (1) a new variational lower bound for the robust evidence that also shares the same robustness property as the traditional non-robust one, and (2) the training procedure for the variational autoencoders with the new objective. The authors show that by maximizing the new lower bound they can successfully train the variational autoencoders even in the scenarios where the noise objects comprise the majority of the training dataset.

**Methodology/Approach**
The paper starts off with a parametric latent variable model p(x, z|θ) = p(x|z,θ)p(z) with local latent variables z and parameter θ. The authors derive a lower bound for the robust evidence and study its properties. Finally, following Kingma and Welling (2014), they propose a training procedure for the variational autoencoders with the new objective.

**Results/Data**
The paper presents two experiments to demonstrate the effectiveness of the proposed approach. In the first experiment, the authors compare the robust variational autoencoders with autoencoders on two synthetic datasets. They use MNIST and OMNIGLOT (Lake et al., 2015) as real-world base sets, and then add uninformative data points, i.e. 28 * 28 images with each pixel's intensity equal to the mean pixel intensity of the original dataset. Due to dynamic binarization (Burda et al., 2016), these data points act as noise. The authors vary the relation of the number of the original data points to the number of noise data points from 2:1 to 1:2. To evaluate the models performance, they compute mean log-likelihood estimate over 200 samples on MNIST and OMNIGLOT test sets (without any noise). The range of log α was selected empirically: they started with log α = -50 and then increased it to find the optimal value with respect to the test likelihood. In the second experiment, the authors compare rV AEs and V AEs on datasets without synthetic noise. They use the same network architecture and optimization approach. Test log-likelihoods for MNIST and OMNIGLOT datasets are presented in Figure 2.

**Limitations/Discussion**
The paper does not discuss any limitations or potential future work, but it is a good starting point to further explore this new robust variational inference method.

**References**
Burda, Y., Grosse, R. & Salakhutdinov, R. (2016). Importance weighted autoencoders. ICLR.
He, K., Zhang, X., Ren, S. & Sun, J. (2015). Delving deep into rectifiers: Surpassing human-level performance on imagenet classiﬁcation. CVPR.
Kingma, D. P. & Ba, J. (2015). Adam: A method for stochastic optimization. ICLR.
Kingma, D. P. & Welling, M. (2014). Auto-encoding variational bayes. ICLR.
Lake, B. M., Salakhutdinov, R. & Tenenbaum, J. B. (2015). Human-level concept learning through probabilistic program induction. Science.

**Note**
The paper does not discuss any limitations or potential future work, but it is a good starting point to further explore this new robust variational inference method.

---

**Summary Statistics:**
- Input: 1,609 words (10,288 chars)
- Output: 585 words
- Compression: 0.36x
- Generation: 38.7s (15.1 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
