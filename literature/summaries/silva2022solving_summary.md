# Solving the Job Shop Scheduling Problem with Ant Colony Optimization

**Authors:** Alysson Ribeiro da Silva

**Year:** 2022

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [silva2022solving.pdf](../pdfs/silva2022solving.pdf)

**Generated:** 2025-12-02 08:35:31

---

**Overview/Summary**
The paper presents a technical report on the application of Ant Colony Optimization (ACO) to solve the Job Shop Scheduling Problem (JSSP). The JSSP is an NP-complete problem that involves scheduling jobs in a set of machines. A job can be processed by any machine, but it must be assigned to one machine at a time and each machine can only process one job at a time. The goal is to find the schedule with minimum makespan (total processing time) for all the jobs. The authors use the ACO algorithm to solve this problem.

**Key Contributions/Findings**
The main contribution of the paper is that it uses the ACO to solve the JSSP. The authors show that the ACO can be used to find the optimum or near-optimum solutions for some instances, and it can also achieve good results in harder instances with low standard deviation.

**Methodology/Approach**
The authors use the ACO algorithm to solve the JSSP. The ACO is a metaheuristic inspired by the behavior of ants looking for food sources. It uses the pheromone trails left by the ants as a communication mechanism. In this paper, the authors apply the two-stage ACO to solve the JSSP. The first stage is to generate an initial solution and the second stage is to improve it.

**Results/Data**
The authors evaluate several instances of the JSSP. They use the ACO algorithm to find the best-found solutions for these instances. The results are shown in Table 4, where the algorithm suggests that it can achieve optimum or near-optimum ones for some instances and it can also achieve good results with low standard deviation in harder instances.

**Limitations/Discussion**
The authors show that the ACO is a powerful metaheuristic to solve the JSSP. The parameter selection plays an important role in the algorithm's performance since the algorithm was not able to find the optimum result for all the instances. The evaluation of several other instances from [5] shows that it can also achieve good results with low standard deviation in some scenarios.

**References**
[1] C. Blum and M. Sampels,  “An ant colony optimization algorithm for shop scheduling problems,” Journal of Mathematical Modelling and Algorithms, vol. 3, no. 3, pp. 285–308, Sep 2004. [Online]. Available: https://doi.org/10.1023/B:JMMA.0000038614.39977.6f
[2] A. Puris, R. Bello, Y. Trujillo, A. Nowe, and Y. Mart´ınez,  “Two-stage aco to solve the job shop scheduling problem,” in Progress in Pattern Recognition, Image Analysis and Applications, L. Rueda, D. Mery, and J. Kittler, Eds. Berlin, Heidelberg: Springer Berlin Heidelberg, 2007, pp. 447–456.
[3] C. Turguner and O. K. Sahingoz,  “Solving job shop scheduling problem with ant colony optimization,” in 2014 IEEE 15th International Symposium on Computational Intelligence and Informatics (CINTI), 2014, pp. 385–389.
[4] Zhiqiang Zhang, Jing Zhang, and Shujuan Li,  “A modified ant algorithm for the job shop scheduling problem to minimize makespan,” in 2010 International Conference on Mechanic Automation and Control Engineering, 2010, pp. 3627–3630.
[5] T. Weise,  “jsspinstancesandresults: Results, data, and instances of the job shop scheduling problem,” Hefei, Anhui, China, 2019–2020, a GitHub repository with the common benchmark instances for the Job Shop Scheduling Problem as well as results from the literature, both in form of CSV files as well as R program code to access them. [Online]. Available: https://github.com/thomasWeise/jsspInstancesAndResults

**Limitations/Discussion**
The authors show that the ACO is a powerful metaheuristic to solve the JSSP. The parameter selection plays an important role in the algorithm's performance since for different parameters the algorithm was not able to find the optimum result for all the instances. The evaluation of several other instances from [5] shows that it can also achieve good results with low standard deviation in some scenarios.

**References**
[1] C. Blum and M. Sampels,  “An ant colony optimization algorithm for shop scheduling problems,” Journal of Mathematical Modelling and Algorithms, vol. 3, no. 3, pp. 285–308, Sep 2004. [Online]. Available: https://doi.org/10.1023/B:JMMA.0000038614.39977.6f
[2] A. Puris, R. Bello, Y. Trujillo, A. Nowe, and Y. Mart´ınez,  “Two-stage aco to solve the job shop scheduling problem,” in Progress in Pattern Recognition, Image Analysis and Applications, L. Rueda, D. Mery, and J. Kittler, Eds. Berlin, Heidelberg: Springer Berlin Heidelberg, 2007, pp. 447–456.
[3] C. Turguner and O. K. Sahingoz,  “Solving job shop scheduling problem with ant colony optimization,” in 2014 IEEE 15th International Symposium on Computational Intelligence and Informatics (CINTI), 2014, pp. 385–389.
[4] Zhiqiang Zhang, Jing Zhang, and Shujuan Li,  “A modified ant algorithm for the job shop scheduling problem to minimize makespan,” in 2010 International Conference on Mechanic Automation and Control Engineering, 2010, pp. 3627–3630.
[5] T. Weise,  “jsspinstancesandresults: Results, data, and instances of the job shop scheduling problem,” Hefei, Anhui, China, 2019–2020, a GitHub repository with the common benchmark instances for the Job Shop Scheduling Problem as well as results from the literature, both in form of CSV files as well as R program code to access them. [Online]. Available: https://github.com/thomasWeise/jsspInstancesAndResults

---

**Summary Statistics:**
- Input: 2,662 words (15,609 chars)
- Output: 806 words
- Compression: 0.30x
- Generation: 48.1s (16.7 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
