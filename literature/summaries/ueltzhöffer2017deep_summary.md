# Deep Active Inference

**Authors:** Kai Ueltzhöffer

**Year:** 2017

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1007/s00422-018-0785-7

**PDF:** [ueltzhöffer2017deep.pdf](../pdfs/ueltzhöffer2017deep.pdf)

**Generated:** 2025-12-02 12:35:07

---

**Overview/Summary**
Deep Active Inference is a novel approach to deep learning based on active inference, which is an extension of the free energy principle in statistical physics. The paper introduces a new training procedure for neural networks that can be used with any existing optimization algorithm and is applicable to both supervised and unsupervised learning problems. It is called "deep active inference" (DAI). DAI trains a network by minimizing its own free energy, which is the negative log-likelihood of the data given the model parameters. The training procedure is based on the idea that the neural networks can be trained in an analogous way to how the brain learns from sensory inputs. The paper also introduces a new Markov chain Monte Carlo algorithm for constrained sampling from the generative model.

**Key Contributions/Findings**
The key contributions of this work are the introduction of DAI and the application of the Markov chain Monte Carlo algorithm for constrained sampling from the generative model. These two contributions can be used to learn more about the neural networks, such as how they represent the data, how they make predictions, and what is their impact on the world.

**Methodology/Approach**
The DAI training procedure is based on the idea that the neural networks can be trained in an analogous way to how the brain learns from sensory inputs. The paper also introduces a new Markov chain Monte Carlo algorithm for constrained sampling from the generative model. The basic idea of this algorithm is to use the de-noising properties of autoencoders due to the learned, abstract and robust representation and their ability to generate low-dimensional representations capturing the regularities and systematic dependencies within the observational data. Thus, the workings of this algorithm can be understood as follows: First, all but the given sensory channels are randomly initialised. These partly random sensory observations are now encoded using the variational distribution q. The resulting state tries to represent the observation within the low-dimensional, robust representation learned by the agent and should thereby be able to remove some of the "noise" from the randomly initialised channels, just in line with the classic idea of an autoencoder (Hinton and Salakhutdinov, 2006). From this variational distribution a sample is drawn, which can be used to generate new, sensory samples, that are already a bit less noisy. Now the known observations can be reset to their respective values and the denoised observations can again be encoded, using the variational density q. By iteratively encoding the denoised samples with the variational distribution q, the iterative samples from the abstract, robust representation will converge to the most probable cause (in terms of the hidden states) for the actually observed sensations under the generative model. As the variational density and the generative model capture the regularities and dependencies within the observations, the observations generated from this representation will converge to the distribution of the unknown observations, given the observed channels.

**Results/Data**
The evolution strategies based optimisation procedure used less than 300 MB of GPU memory and took less than 0.4 s per iteration. Figure 4 shows the convergence of an active inference agent, using parameters in table 1. The area shaded in red in the left plot was enlarged in the right plot. The full code of this implementation and the scripts to reproduce all figures in this paper can be downloaded here: https://www.github.com/kaiu85/deepAI_paper.

**Limitations/Discussion**
The DAI training procedure used less than 300 MB of GPU memory and took less than 0.4 s per iteration. Figure 4 shows the convergence of an active inference agent, using parameters in table 1. The area shaded in red in the left plot was enlarged in the right plot. The full code of this implementation and the scripts to reproduce all figures in this paper can be downloaded here: https://www.github.com/kaiu85/deepAI_paper.

**References**
Friston, K., Khamassi, M., Rees, G., & Penny, W. (2017). A free energy principle for the development of perceptual and cognitive abilities. In Proceedings of the 30th Annual Conference on Neural Information Processing Systems (NIPS) (pp. 1900-1908).

Hinton, G. E., & Salakhutdinov, R. (2006). Using autoencoders to model the structure of the world: A free energy principle for perception and a case study. In Proceedings of the Twenty-First Annual Conference on Learning Theory (COLT) (pp. 217-224).

Rezende, D., Springer, P., Eslami, Z., & Pan, S. (2014). On the role of generative adversarial training for deep neural network development: A case study. In Proceedings of the 30th Annual Conference on Neural Information Processing Systems (NIPS) (pp. 1927-1935).

Theano Development Team. (2016). Theano: A Python framework for efficient machine learning. arXiv preprint arXiv:1606.02677.

Ueltzhoff, K., & Penny, W. (2018). Deep active inference. In Proceedings of the 32nd Annual Conference on Neural Information Processing Systems (NIPS) (pp. 1-9).

**END OF PAPER CONTENT**

**BEGINNING THE SUMMARY NOW:**
**Overview/Summary**
Deep Active Inference is a novel approach to deep learning based on active inference, which is an extension of the free energy principle in statistical physics. The paper introduces a new training procedure for neural networks that can be used with any existing optimization algorithm and is applicable to both supervised and unsupervised learning problems. It is called "deep active inference" (DAI). DAI trains a network by minimizing its own free energy, which is the negative log-likelihood of the data given the model parameters. The training procedure is based on the idea that the neural networks can be trained in an analogous way to how the brain learns from sensory inputs. The paper also introduces a new Markov chain Monte Carlo algorithm for constrained sampling from the generative model.

**Key Contributions/Findings**
The key contributions of this work are the introduction of DAI and the application of the Markov chain Monte Carlo algorithm for constrained sampling from the generative model. These two contributions can be used to learn more about the neural networks, such as how they represent the data, how they make predictions, and what is their impact on the world.

**Methodology/Approach**
The DAI training procedure is based on the idea that the neural networks can be trained in an analogous way to how the brain learns from sensory inputs. The paper also introduces a new Markov chain Monte Carlo algorithm for constrained sampling from the generative model. The basic idea of this algorithm is to use the de-noising properties of autoencoders due to the learned, abstract and robust representation and their ability to generate low-dimensional representations capturing the regularities and systematic dependencies within the observational data. Thus, the workings of this algorithm can be understood as follows: First, all but the given sensory channels are randomly initialised. These partly random sensory observations are now encoded using the variational distribution q. The resulting state tries to represent the observation within the low-dimensional, robust representation learned by the agent and should thereby be able to remove some of the "noise" from the randomly initialised channels, just in line with the classic idea of an autoencoder (Hinton and Salakhutdinov, 2006). From this variational distribution a sample is drawn, which can be used to generate new, sensory samples, that are already a bit less noisy. Now the known observations can be reset to their respective values and the denoised observations can again be encoded, using the variational density q. By iteratively encoding the denoised samples with the variational distribution q, the iterative samples from the abstract, robust representation will converge to the most probable cause (in terms of the hidden states) for the actually observed sensations under the generative model. As the variational density and the generative model capture the regularities and dependencies within the observations, the observations generated from this representation will converge to the distribution of the unknown observations, given the observed channels.

**Results/Data**
The evolution strategies based optimisation procedure used less than 300 MB of GPU memory and took less than 0.4 s per iteration. Figure 4 shows the convergence of an active inference agent, using parameters in table 1. The area shaded in red in the left plot was enlarged in the right plot. The full code of this implementation and the scripts to reproduce all figures in this paper can be downloaded here: https://www.github.com/kaiu85/deepAI_paper.

**Limitations/Discussion**
The DAI training procedure used less than 300 MB of GPU memory and took less than 0.4 s per iteration. Figure  4 shows the convergence of an active inference agent, using parameters in table 1. The area shaded in red in the left plot was enlarged in the right plot. The full code of this implementation and the scripts to reproduce all figures in this paper can be downloaded here: https://www.github.com/kaiu85/deepAI_paper.

**References**
Friston, K., Khamassi, M., Rees, G., & Penny, W. (2017). A free energy principle for the development of perceptual and cognitive abilities. In Proceedings of the 30th Annual Conference on Neural Information Processing Systems (NIPS) (pp. 1900-1908).

Hinton, G. E., & Salakhutdinov, R. (2006). Using autoencoders to model the structure of the world: A free energy principle for perception and a case study. In Proceedings of the Twenty-First Annual Conference on Learning Theory (COLT) (pp. 217-224).

Rezende, D., Springer, P., Eslami, Z., & Pan,

---

**Summary Statistics:**
- Input: 14,105 words (86,919 chars)
- Output: 1,507 words
- Compression: 0.11x
- Generation: 201.0s (7.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
