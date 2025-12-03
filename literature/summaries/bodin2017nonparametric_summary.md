# Nonparametric Inference for Auto-Encoding Variational Bayes

**Authors:** Erik Bodin, Iman Malik, Carl Henrik Ek, Neill D. F. Campbell

**Year:** 2017

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [bodin2017nonparametric.pdf](../pdfs/bodin2017nonparametric.pdf)

**Generated:** 2025-12-03 03:40:32

---

**Overview/Summary**
The authors present a novel approach to nonparametric inference for auto-encoding variational Bayes (VAE) models and an associated efficient approximate inference scheme. The VAE is a generative model that learns the underlying distribution of data by mapping it into a latent representation space. The inference takes inspiration from amortized inference and uses a recognition model to parameterize the approximate posterior using a deterministic relationship from the observed data. Rather than using a traditional mean-ﬁeld approximation which forces the latent representation to be independent, they introduce an additional latent representation that models their dependence. Their model results in a signiﬁcantly lower dimensional latent representation allowing them to visualise and generate data in a more intuitive manner without sacriﬁcing the quality of the reconstruction. The authors validate their approach with comparison to a standard VAE by showing data embeddings in the X space and generation of new data.

**Key Contributions/Findings**
The key contributions of this paper are:
1. A hierarchical model for unsupervised learning that is efﬁciently approximated using amortised inference.
2. The authors introduce an additional latent representation to model the dependence between the original latent representations, which results in a lower dimensional latent representation allowing them to visualise and generate data in a more intuitive manner without sacriﬁcing the quality of the reconstruction.

**Methodology/Approach**
The approach is based on amortised inference. The authors use a recognition model to parameterize the approximate posterior using a deterministic relationship from the observed data. Rather than using a traditional mean-ﬁeld approximation which forces the latent representation to be independent, they introduce an additional latent representation that models their dependence. Their model results in a signiﬁcantly lower dimensional latent representation allowing them to visualise and generate data in a more intuitive manner without sacriﬁcing the quality of the reconstruction.

**Results/Data**
The authors present experimental results on the MNIST dataset, which is comprised of 55 000 training examples and 10 000 test examples. The experiment is performed with the decoder and both encoders as Multilayer Perceptrons (MLP) with the same architecture as in the original VAE. They used two hidden layers of 500 units each, mini-batch sizes of 128 and a drop-out probability of 0.9 throughout training. The decoder used was the Bernoulli MLP variant. Furthermore, the ADAM optimiser was used with a learning rate of 10−3. They varied the dimensionality of the inner most layer of the autoencoder (the Z space) for the experiments. They used the MNIST data set from LeCun et al. [1998] comprised of 55 000 training examples and 10 000 test examples of 28 ×28 pixel greyscale images, corresponding to 784 data dimensions.

**Limitations/Discussion**
The authors discuss that their model results in a signiﬁcantly lower dimensional latent representation allowing them to visualise and generate data in a more intuitive manner without sacriﬁcing the quality of the reconstruction. They also show experimental results on how they can retain the representative power of a 500 dimensional model with just a 2 dimensional latent space.

**References**
Diederik P Kingma and Max Welling. Auto-Encoding Variational Bayes. InInternational Conference
on Learning Representations (ICLR), 2014.
Neil D Lawrence. Probabilistic non-linear principal component analysis with Gaussian process latent variable models. Journal of Machine Learning Research, 6:1783–1816, 2005.
Matthew D Hoffman and Matthew J Johnson. ELBO Surgery: Yet Another Way to Carve up the
Variational Evidence Lower Bound. In Workshop in Advances in Approximate Bayesian Inference, NIPS, 2016. (
Jakub M Tomczak and Max Welling. V AE with a VampPrior. arXiv preprint arXiv:1705.07120, 2017.
Xi Chen, Diederik P Kingma, Tim Salimans, Yan Duan, Prafulla Dhariwal, John Schulman, Ilya
Sutskever, and Pieter Abbeel. Variational Lossy Autoencoder. arXiv preprint arXiv:1611.02731, 2016.
Shengjia Zhao, Jiaming Song, and Stefano Ermon. Towards a Deeper Understanding of Variational
Autoencoding Models. arXiv preprint arXiv:1702.08658, 2017.
Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-Base Learning Applied to Document Recognition. Proceedings of the IEEE, 86(11):2278–2323, 1998.

**Word Count:**

---

**Summary Statistics:**
- Input: 2,117 words (13,400 chars)
- Output: 643 words
- Compression: 0.30x
- Generation: 40.1s (16.0 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
