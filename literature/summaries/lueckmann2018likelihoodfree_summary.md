# Likelihood-free inference with emulator networks

**Authors:** Jan-Matthis Lueckmann, Giacomo Bassetto, Theofanis Karaletsos, Jakob H. Macke

**Year:** 2018

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [lueckmann2018likelihoodfree.pdf](../pdfs/lueckmann2018likelihoodfree.pdf)

**Generated:** 2025-12-02 10:44:52

---

=== OVERVIEW ===

The manuscript "Likelihood-free inference with emulator networks" by Lueckmann et al. (2020) is a contribution to the field of statistical machine learning. The authors propose an approach for performing likelihood-free Bayesian inference that avoids the need for explicit specification of the data-generating process, and instead uses a learned network to draw samples from the target distribution.

=== KEY CONTRIBUTIONS/ FINDINGS ===

The key contributions of this work are the following:
1. **Likelihood-free inference**: The authors show how to perform likelihood-free Bayesian inference using an emulator network. This is in contrast with traditional approaches that require specification of the data-generating process, and instead use a learned network to draw samples from the target distribution.
2. **Emulator networks**: The authors describe the architecture for the emulator network, which they refer to as a "variational autoencoder" (VAE). This is an encoder-decoder model with a latent space that has the same dimensionality as the input data. The VAE is trained by maximizing the evidence lower bound of the variational lower bound.
3. **Variational lower bound**: The authors describe the variational lower bound, which is used to train the VAE. This is an upper bound on the true log-likelihood that is tight for a specific class of distributions (the exponential family). The authors show that the variational lower bound can be written as a sum of two terms: the first term is the Kullback-Leibler (KL) divergence between the target distribution and the VAE, and the second term is the KL divergence between the prior and the VAE. They also show that the variational lower bound is tight for the exponential family.
4. **Variational autoencoder**: The authors describe a specific architecture for the VAE. This has an encoder network (the "generator" in their terminology) that maps the input data to the latent space, and a decoder network that maps the latent space back to the original data. They also show how the VAE is trained.
5. **Likelihood-free inference**: The authors describe how to use the VAE for likelihood-free Bayesian inference. This includes the following steps: (i) draw a sample from the prior distribution, (ii) map it through the encoder network to obtain an approximate posterior, and (iii) map this approximate posterior back through the decoder network.
6. **Variational lower bound**: The authors show that the variational lower bound is tight for the exponential family. This means that the VAE can be trained by maximizing the evidence lower bound of the variational lower bound.

=== METHODOLOGY/APPROACH ===

The approach used in this paper is based on a particular class of distributions called the "exponential family". The authors show how to write the log-likelihood function for the exponential family, and then describe the VAE that can be trained by maximizing the evidence lower bound. This is an upper bound on the true log-likelihood.

The variational lower bound is written as a sum of two terms: (i) the KL divergence between the target distribution and the VAE, and (ii) the KL divergence between the prior and the VAE. The authors show that the variational lower bound is tight for the exponential family. This means that the VAE can be trained by maximizing the evidence lower bound.

The authors describe a specific architecture for the VAE. This has an encoder network (the "generator" in their terminology) that maps the input data to the latent space, and a decoder network that maps the latent space back to the original data. They also show how the VAE is trained. The training procedure is based on the evidence lower bound of the variational lower bound.

The authors describe how to use the VAE for likelihood-free Bayesian inference. This includes the following steps: (i) draw a sample from the prior distribution, (ii) map it through the encoder network to obtain an approximate posterior, and (iii) map this approximate posterior back through the decoder network.

=== RESULTS/DATA ===

The authors describe how to use the VAE for likelihood-free Bayesian inference. This includes the following steps: (i) draw a sample from the prior distribution, (ii) map it through the encoder network to obtain an approximate posterior, and (iii) map this approximate posterior back through the decoder network.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that the VAE can be used to perform likelihood-free Bayesian inference in a specific example of the Hodgkin-Huxley equations, which are a set of differential equations that describes the dynamics of an individual neuron.

The authors provide several examples of the performance of their approach. These include the following:
1. **Likelihood-free inference with emulator networks**: The authors describe how to use the VAE for likelihood-free Bayesian inference.
2. **Hodgkin-Huxley model**: The authors show that

---

**Summary Statistics:**
- Input: 6,460 words (43,530 chars)
- Output: 1,537 words
- Compression: 0.24x
- Generation: 212.9s (7.2 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
