# Deep Active Inference for Partially Observable MDPs

**Authors:** Otto van der Himst, Pablo Lanillos

**Year:** 2020

**Source:** arxiv

**Venue:** arXiv

**DOI:** 10.1007/978-3-030-64919-7_8

**PDF:** [himst2020deep.pdf](../pdfs/himst2020deep.pdf)

**Generated:** 2025-12-02 09:45:51

---

**Overview/Summary**

The paper "Deep Active Inference for Partially Observable MDPs" by O. van der Himst and P. Lanillos presents a novel approach to the problem of learning in partially observable Markov decision processes (POMDPs). The authors propose a new algorithm called Deep Active Inference (DAI) that combines the benefits of active inference with deep reinforcement learning. The key contribution is the use of variational autoencoders as a probabilistic model for the POMDP, which allows the DAI to learn from high-dimensional observations in an end-to-end manner. The authors also show how this approach can be used to solve more complex problems such as learning to control robots.

**Key Contributions/Findings**

The main contribution of the paper is the use of a variational autoencoder (VAE) for the POMDP, which allows the DAI to learn from high-dimensional observations in an end-to-end manner. The authors also show how this approach can be used to solve more complex problems such as learning to control robots. The key finding is that the DAI with the VAE model outperforms a baseline DAI using a Gaussian state space and achieves similar performance to the best known deep reinforcement learning algorithm for POMDPs.

**Methodology/Approach**

The authors use the variational autoencoder (VAE) as a probabilistic model for the POMDP. The VAE is used in the DAI to learn from high-dimensional observations, which allows the DAI to learn from raw sensor data without any pre-processing or feature extraction. The authors also compare their algorithm with a baseline that uses a Gaussian state space and an actor-critic method. The VAE model is learned using a variational loss function. The learning process of the DAI is based on the free energy principle, which is used to guide the search for the optimal policy in the POMDP.

**Results/Data**

The authors compare their algorithm with a baseline that uses a Gaussian state space and an actor-critic method. The VAE model is learned using a variational loss function. The learning process of the DAI is based on the free energy principle, which is used to guide the search for the optimal policy in the POMDP. The authors also show how this approach can be used to solve more complex problems such as learning to control robots.

**Limitations/Discussion**

The main limitation of the paper is that it only compares their algorithm with a baseline using a Gaussian state space and an actor-critic method, which may not be the best known deep reinforcement learning algorithm for POMDPs. The authors also do not provide any theoretical guarantees about the convergence or optimality of the DAI. The authors suggest that future work could include the use of a more complex VAE model such as a hierarchical one and the use of the DAI in more complex problems.

**References**

1. Ueltzhöfer, K.: Deep active inference. Biological Cybernetics 112(6), 547–573 (Oct 2018). https://doi.org/10.1007/s00422-018-0785-7
2. Sancaktar, C., Lanillos, P.: End-to-end pixel-based deep active inference for body perception and action. arXiv preprint arXiv:2001.05847 (2019)
3. Millidge, B.: Deep active inference as variational policy gradients. Journal of Mathematical Psychology 96, 102348 (2020). https://doi.org/10.1016/j.jmp.2020.102348
4. Tschantz, A., Baltieri, M., Seth, A.K., Buckley, C.L.: Scaling active inference. arXiv Prepr. arXiv:1911.10601v1 (2019)
5. Câtal, O., Wauthier, S., Verbelen, T., Boom, C.D., Dhoedt, B.: Deep active inference for autonomous robot navigation. arXiv Prepr. arXiv:2003.03220v1 (2020)
6. Fountas, Z., Sajid, N., Mediano, P.A.M., Friston, K.: Deep active inference agents using monte-carlo methods. arXiv Prepr. arXiv:2006.04176v1 (2020)
7. Mnih, V., Kavukcuoglu, K., Silver, D., Graves, A., Antonoglou, I., Wierstra, D., Riedmiller, M.: Playing atari with deep reinforcement learning. arXiv Prepr. arXiv:1312.5602v1 (2013)
8. Arulkumaran, K., Deisenroth, M.P., Brundage, M., Bharath, A.A.: Deep reinforcement learning: A brief survey. IEEE Signal Processing Magazine 34(6), 26–38 (2017)
9. Friston, K.J.: The free-energ principle: a uniﬁed brain theory? Nature11, 127–138 (2010). https://doi.org/https://doi.org/10.1038/nrn2787
10. Friston, K., Daunizeau, J., Kilner, J., Kiebel, S.J.: Action and behavior: a free-energ formulation. Biol Cybern 102, 227–260 (2010). https://doi.org/https://doi.org/10.1007/s00422-010-0364-z
11. Adams, R.A., Shipp, S., Friston, K.: Predictions not commands: active inference in the motor system. Brain Struct Funct. 218(3), 611–643 (2012). https://doi.org/doi:10.1007/s00429-012-0475-5
12. Lanillos, P., Pages, J., Cheng, G.: Robot self/other distinction: active inference meets neural networks learning in a mirror. In: Proceedings of the 24th European Conference on Artiﬁcial Intelligence (ECAI). pp. 2410–2416 (2020). https://doi.org/10.3233/FAIA200372
13. Rood, T., van Gerven, M., Lanillos, P.: A deep active inference model of the rubber-hand illusion. arXiv Prepr. arXiv:2008.07408 (2020)
14. Oliver, G., Lanillos, P., Cheng, G.: Active inference body perception and action for humanoid robots. arXiv Prepr. arXiv:1906.03022v3 (2019)
15. Friston, K.J.: The free-energ principle: a uniﬁed brain theory? Nature11, 127–138 (2010). https://doi.org/https://doi.org/10.1038/nrn2787
16. Parr, T., Friston, K.: Generalised free energy and active inference. Biol Cybern 113, 495–513 (2019). https://doi. org/doi:10.1007/s00422-019-00805-w
17. Adams, R.A., Shipp, S., Friston, K.: Predictions not commands: active inference in the motor system. Brain Struct Funct. 218(3), 611–643 (2012). https://doi.org/doi:10.1007/s00429-012-0475-5
18. Lanillos, P., Pages, J., Cheng, G.: Robot self/other distinction: active inference meets neural networks learning in a mirror. In: Proceedings of the 24th European Conference on Artiﬁcial Intelligence (ECAI). pp. 2410–2416 (2020). https://doi.org/10.3233/FAIA200372
19. Rood, T., van Gerven, M., Lanillos, P.: A deep active inference model of the rubber-hand illusion. arXiv Prepr. arXiv:2008.07408 (2020)
20. Oliver, G., Lanillos, P., Cheng, G.: Active inference body perception and action for humanoid robots. arXiv Prepr. arXiv:1906.03022v3 (2019)
21. Friston, K.J.: The free-energ principle: a uniﬁed brain theory? Nature11, 127–138 (2010). https://doi.org/https://doi.org/10.1038/nrn2787
22. Parr, T., Friston, K.: Generalised free energy and active inference. Biol Cybern 106, 523–541 (2012).
23. Friston, K.J.: The free-energ principle: a uniﬁed brain theory? Nature11, 127–138 (2010). https://doi.org/https://doi.org/10.1038/nrn2787
24. Adams, R.A., Shipp, S., Friston, K.: Predictions not commands: active inference in the motor system. Brain Struct Funct. 218(3), 611–643 (2012). https://doi.org/doi:10.1007/s00429-012-0475-5
25. Lanillos, P., Pages, J., Cheng, G.: Robot self/other distinction: active inference meets neural networks learning in a mirror. In: Proceedings of the 24th European Conference on Artiﬁcial Intelligence (ECAI). pp. 2410–2416 (2020). https://doi.org/10.323

---

**Summary Statistics:**
- Input: 3,503 words (22,375 chars)
- Output: 976 words
- Compression: 0.28x
- Generation: 83.0s (11.8 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
