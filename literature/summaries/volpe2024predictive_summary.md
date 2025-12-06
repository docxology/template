# A Predictive Approach for Selecting the Best Quantum Solver for an Optimization Problem

**Authors:** Deborah Volpe, Nils Quetschlich, Mariagrazia Graziano, Giovanna Turvani, Robert Wille

**Year:** 2024

**Source:** arxiv

**Venue:** N/A

**DOI:** 10.1109/QCE60285.2024.00121

**PDF:** [volpe2024predictive.pdf](../pdfs/volpe2024predictive.pdf)

**Generated:** 2025-12-05 10:41:11

---

**Overview/Summary**

The paper proposes a predictive approach for selecting the best quantum solver from a set of available solvers. The authors first review the current state-of-the-art in quantum optimization and then focus on the flow required to solve an optimization problem with quantum computer. They also propose strategies for adjusting solver parameters based on the size and characteristics of the problem, which is not the optimal approach but can be used as a starting point. In this paper, they first review quantum optimization, focusing on solvers and flow required for solving an optimization problem with quantum computers. They also propose strategies for adjusting solver parameters based on the size and characteristics of the problem, which is not the optimal approach but can be used as a starting point. The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors.

**Key Contributions/Findings**

The conducted exploration demonstrates the feasibility of approaching solver selection as a classification task. However, a significant challenge lies in the necessity of a large dataset, which is computationally and economically expensive to obtain, to ensure a reliable prediction. While the dataset dimensions in this manuscript suffice to establish proof of concept, providing encouraging results, more training data are needed to achieve completely satisfactory prediction results. Expanding the dataset poses challenges related to the selection of diverse problems to provide a comprehensive overview of potential scenarios. Furthermore, while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors.

**Methodology/Approach**

The authors first review quantum optimization, focusing on solvers and flow required for solving an optimization problem with quantum computers. They also propose strategies for adjusting solver parameters based on problem size and characteristics. To this end, they first review quantum optimization, focusing on solvers and flow required for solving an optimization problem with quantum computers. They also propose strategies for adjusting solver parameters based on the size and characteristics of the problem, which is not the optimal approach but can be used as a starting point. The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors.

**Results/Data**

The effectiveness of the features reduction technique depends on the type of model. For example, considering the model SVM, Naive Bayes, or Neural Network, they are particularly useful, while in Random Forest, they do not provide benefit. The table shows that Random Forest outperforms other supervised learning models in predicting the expected optimal solver. It achieves the best performance with an accuracy of 73.18% and about 90% rate of predictions providing a solver in the top two. Additionally, the average loss in terms of the probability of obtaining the optimal solution is almost negligible, at just 2.16%. These results have been obtained with the following hyperparameter setting: number of Decision Trees equal to 100; maximal depth equal to 50; minimal samples per leaf equal to 1; and minimal samples per split equal to 2.

**Limitations/Discussion**

The effectiveness of the features reduction technique depends on the type of model. For example, considering the model SVM, Naive Bayes, or Neural Network, they are particularly useful, while in Random Forest, they do not provide benefit. The table shows that Random Forest outperforms other supervised learning models in predicting the expected optimal solver. It achieves the best performance with an accuracy of 73.18% and about 90% rate of predictions providing a solver in the top two. Additionally, the average loss in terms of the probability of obtaining the optimal solution is almost negligible, at just 2.16%. These results have been obtained with the following hyperparameter setting: number of Decision Trees equal to 100; maximal depth equal to 50; minimal samples per leaf equal to 1; and minimal samples per split equal to 2.

**Limitations/Discussion**

The conducted exploration demonstrates the feasibility of approaching solver selection as a classification task. However, a significant challenge lies in the necessity of a large dataset, which is computationally and economically expensive to obtain, to ensure a reliable prediction. While the dataset dimensions in this manuscript suffice to establish proof of concept, providing encouraging results, more training data are needed to achieve completely satisfactory prediction results. Expanding the dataset poses challenges related to the selection of diverse problems to provide a comprehensive overview of potential scenarios. Furthermore, while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors.

**Results/Methodology**

The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Methodology**

The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The authors suggest that while the chosen solvers' settings for dataset creation have demonstrated their reasonableness, relying exclusively on empirical deductions is not the optimal approach. Consequently, there is potential for significant enhancements in the implementation of predictors. The average probability of achieving the expected optimal value (ps) across the dataset's problems is plotted against the number of QUBO variables. The authors choose to present the average loss in success probability rather than those in the overall score because it offers a more explicit interpretation with respect to an abstract score. Furthermore, its range of possible values is problem-independent, unlike the score—dependent on function bounds—, thus simplifying the process of averaging the results.

**Limitations/Results**

The

---

**Summary Statistics:**
- Input: 9,781 words (67,213 chars)
- Output: 1,645 words
- Compression: 0.17x
- Generation: 83.8s (19.6 words/sec)
- Quality Score: 0.40/1.0
- Attempts: 2

**Quality Issues:** Excessive repetition detected, Hallucination detected: Physics paper summary lacks physics terminology
