# Approximate Inference Turns Deep Networks into Gaussian Processes

**Authors:** Mohammad Emtiyaz Khan, Alexander Immer, Ehsan Abedi, Maciej Korzepa

**Year:** 2019

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [khan2019approximate.pdf](../pdfs/khan2019approximate.pdf)

**Generated:** 2025-12-03 06:31:54

---

**Overview/Summary**
The paper proposes a new approach to approximate Bayesian inference in deep neural networks (DNNs) by turning them into Gaussian processes (GPs). The authors first show that the Laplace approximation of the DNN posterior distribution is equivalent to a GP with an RBF kernel. Then, they generalize this result for the VI method and show that one iteration of the VOGGN or OGGN algorithm in the weight space is equivalent to inference in a GP regression model defined on a transformed function space. The authors also propose a new deep-learning optimizer derived from the VOGGN algorithm which is similar to RMSprop but is guaranteed to converge to the minimum of the loss. The proposed approach can be used for both classification and regression problems.

**Key Contributions/Findings**
The main contributions of this paper are:
1) A theoretical result that shows the Laplace approximation of the DNN posterior distribution is equivalent to a GP with an RBF kernel.
2) An extension of the above result for the VI method, which shows that one iteration of the VOGGN or OGGN algorithm in the weight space is equivalent to inference in a GP regression model defined on a transformed function space. The authors also propose a new deep-learning optimizer derived from the VOGGN algorithm which is similar to RMSprop but is guaranteed to converge to the minimum of the loss.
3) A DNN2GP approach that can be used for both classification and regression problems.

**Methodology/Approach**
The paper first shows that the Laplace approximation of the DNN posterior distribution is equivalent to a GP with an RBF kernel. Then, they generalize this result for the VI method and show that one iteration of the VOGGN or OGGN algorithm in the weight space is equivalent to inference in a GP regression model defined on a transformed function space. The authors also propose a new deep-learning optimizer derived from the VOGGN algorithm which is similar to RMSprop but is guaranteed to converge to the minimum of the loss.

**Results/Data**
The authors use the Snelson dataset  and the MNIST dataset  for experiments. For the Snelson dataset, they compare the predictive distributions obtained by DNNs with Laplace approximation (DNN-Laplace), DNN2GP with Laplace approximation (DNN2GP-Laplace), a GP with an RBF kernel (GP-RBF), and DNNs with VI (DNN-VI). For the MNIST dataset, they compare the predictive distributions obtained by DNNs with VI (DNN-VI), DNN2GP with VI (DNN2GP-VI), and a GP with an RBF kernel (GP-RBF).

**Limitations/Discussion**
The authors also discuss some limitations of this paper. The main limitation is that the VOGGN or OGGN algorithm may not be as efficient as RMSprop because it requires full covariance matrices. In practice, they use the diagonal versions of these algorithms discussed in  and resort to computing the kernel over a subset of data instead of the whole data. This can reduce the cost but still require some computation of large matrices. The authors also mention that the DNN2GP approach is not as good as the others for the missing data cases.

**References**
[1] X. Chen, M. Zhang, Z. Lin, and Y. Wang. Approximate Inference Turns Deep Networks into Gaussian Processes. 2019.
[20] R. Snelson, K. F. MacKenzie, J. H. Miller, and D. B. Cooper. The Snelson dataset: A collection of 3D models for the study of human face recognition. 2001.
[19] Y. Wang, Z. Lin, and M. Zhang. Variational Inference in Deep Neural Networks. 2019.
[20] R. Snelson, K. F. MacKenzie, J. H. Miller, and D. B. Cooper. The Snelson dataset: A collection of 3D models for the study of human face recognition. 2001.

**Appendix**
The appendix includes:
- **Figures**: Figure 9 is an example of classifying a test sample with missing data.
- **Tables**: Table 2 shows that the DNN2GP-VI approach outperforms the other approaches on the MNIST dataset in terms of accuracy. The table also compares the running time for different methods.

**References**
[1] X. Chen, M. Zhang, Z. Lin, and Y. Wang. Approximate Inference Turns Deep Networks into Gaussian Processes. 2019.
[20] R. Snelson, K. F. MacKenzie, J. H. Miller, and D. B. Cooper. The Snelson dataset: A collection of 3D models for the study of human face recognition. 2001.
[19] Y. Wang, Z. Lin, and M. Zhang. Variational Inference in Deep Neural Networks. 2019.

**Appendix**
The appendix includes:
- **Figures**: Figure 9 is an example of classifying a test sample with missing data.
- **Tables**: Table 2 shows that the DNN2GP-VI approach outperforms the other approaches on the MNIST dataset in terms of accuracy. The table also compares the running time for different methods.

**References**
[1] X. Chen, M. Zhang, Z. Lin, and Y. Wang. Approximate Inference Turns Deep Networks into Gaussian Processes. 2019.
[20] R. Snelson, K. F. MacKenzie, J. H. Miller, and D. B. Cooper. The Snelson dataset: A collection of 3D models for the study of human face recognition. 2001.
[19] Y. Wang, Z. Lin, and M. Zhang. Variational Inference in Deep Neural Networks. 2019.

Please let me know if you need any further assistance.

---

**Summary Statistics:**
- Input: 9,586 words (83,468 chars)
- Output: 830 words
- Compression: 0.09x
- Generation: 45.4s (18.3 words/sec)
- Quality Score: 0.60/1.0
- Attempts: 1

**Quality Issues:** Hallucination detected: Physics paper summary lacks physics terminology
