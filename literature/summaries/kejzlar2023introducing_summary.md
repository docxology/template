# Introducing Variational Inference in Statistics and Data Science Curriculum

**Authors:** Vojtech Kejzlar, Jingchen Hu

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [kejzlar2023introducing.pdf](../pdfs/kejzlar2023introducing.pdf)

**Generated:** 2025-12-05 13:38:02

---

=== PAPER CONTENT  ===

Title: Introducing Variational Inference in Statistics and Data

Abstract:

We introduce a new module for teaching variational inference (VI) to undergraduate statistics students that is designed to be flexible enough to be used in different types of courses. The module is self-contained, so it can be used as an add-on to any course that covers Bayesian inference or regression. This module is based on the idea that VI is a generalization of maximum likelihood estimation and that the posterior distribution is the one that maximizes the expected log-likelihood. We provide a set of activities for students to work in pairs, which are designed to help them understand how the posterior distribution can be used to make predictions about new data. The module also includes a set of R labs that illustrate the use of VI with different types of data and models.

The first part of the paper is an overview of the module. It describes the activities and the R labs, as well as some general tips for teaching statistics students. The second part is the manual of the R shiny app we have developed for the module. The third part is the details of the guided R lab with U.S. women labor participation sample data, presented in Section 4.1 in the main text. The fourth part is the details of the guided R lab of the LDA application to a sample of the Associated Press newspaper articles with VI, presented in Section 4.2 in the main text.

6 Class Activity: Probabilistic Model for Count Data

The goal of this activity is to illustrate variational inference on a simple example of Gamma-Poisson conjugate model, which is a popular model for count data.

6.1 A Motivating Example

Our task is to estimate the average number of active users of a popular massively multiplayer online role- playing game (mmorpg) playing between the peak evening hours 7 pm and 10 pm. This information can help the game developers in allocating server resources and optimizing user experience. To make this estimate, we will consider the following counts (in thousands) of active players collected during the peak evening hours over a two-week period past month.

Sun Mon Tue Wed Thu Fri Sat
Week 1 50 47 46 52 49 55 53
Week 2 48 45 51 50 53 46 47

6.2 Overview of the Gamma-Poisson Model

Sampling density:

Suppose that y = (y1, . . . , yn) represent the observed counts in n time intervals where the counts are independent, then each yi follows a Poisson distribution with rate θ > 0.

yi | θ ∼ Poisson(θ)

• E(yi | θ) = θ

• Var(yi | θ) = θ

Prior distribution:

θ ∼ Gamma(α, β)

• α >0 is the shape parameter

• β >0 is the rate parameter

• E(θ) = α
β

• Var(θ) = α
β2

Posterior distribution:

θ | y1, . . . , yn ∼ Gamma(α + nX i=1 yi, β+ n)

6.3 Exact Inference with the Gamma-Poisson Model

We will start by selecting a prior distribution for the unknown average number of active users. Suppose that we elicit an expert’s advice on the matter, and they tell us that a similar mmorpg has typically about 50,000 users during peak hours. However, they are not too sure about that, so the interval between 45,000 and 55,000 users should have a reasonably high probability. This reasoning leads to a Gamma(100, 2) as a reasonable prior for the average number of active users.

Task 1: Explain the reasoning behind using Gamma (100, 2) as the prior distribution.

Task 2: Use the information above to find the exact posterior distribution for the average number of active users.

Task 3: What are the mean and standard deviation of the posterior distribution that you just obtained? What is your recommendation about the typical number of active users playing the mmorpg between the peak evening hours 7pm and 10pm?

Task 4: Use the sliders in the applet titled Variational Inference with Gamma-Poisson Model for count data to complete the following task. What is your strategy? Task 5: Compare your approximation with a neighbor. Whose approximation is closer to the exact posterior distribution of θ? How are you deciding?

Task 6: Check the Fit a variational approximation box in the applet to find the variational approximation using the gradient ascent algorithm. How close was the variational approximation that you found manually to the one found here?


=== END PAPER CONTENT ===

CRITICAL INSTRUCTIONS:
You are summarizing a scientific research paper. You MUST follow ALL rules below:

1. ONLY use information that appears in the paper text above. Do NOT add external knowledge, assumptions, or invented details.
2. Provide a comprehensive summary that covers the key aspects of the paper. Use section headers that make sense for the content, such as:
    - Overview/Summary  (what the paper is about)
    - Key Contributions/Findings  (main results and advances)
    - Methodology/Approach  (how the research was conducted)
    - Results/Data  (what was found or measured)
    - Limitations/Discussion  (weaknesses and future work)
3. Word count: Aim for 400-700 words of substantive, detailed content. Focus on quality over quantity.
4. CONTENT FOCUS:
    - Emphasize relevance: Explain why this research matters and how it connects to broader scientific questions
    - Be comprehensive: Cover all major aspects mentioned in the paper without leaving out important details
    - Prioritize specificity: Use concrete details, numbers, methods, measurements, and findings from the paper
5. DOMAIN- SPECIFIC EMPHASIS:
    - For PHYSICS papers: Highlight specific equations, experimental parameters, energy scales, detection methods, and statistical significance
    - For COMPUTER SCIENCE papers: Detail algorithms, complexity analysis, dataset characteristics, performance metrics, and comparisons
    - For BIOLOGY papers: Include species, sample sizes, statistical methods, biological mechanisms, and experimental conditions
    - For MATHEMATICS papers: Cover theorems, proofs, mathematical objects, computational complexity, and theoretical implications
6. QUALITY STANDARDS:
    - Be substantive: Provide detailed analysis rather than surface- level descriptions
    - Explain significance: Discuss why methods, results, and contributions matter
    - Maintain coherence: Ensure different sections complement rather than repeat each other
7. ACCURACY REQUIREMENTS:
    - NO HALLUCINATION: Only discuss what the paper explicitly states
    - NO REPETITION: Avoid repeating the same information in multiple places
    - NO META-COMMENTARY: Do not mention being an AI or that this is a summary
8. FLEXIBLE STRUCTURE: Use the section headers that best fit the paper's content. You may use fewer or more sections as appropriate, or even combine related information.

Begin your summary now:

Title: Introducing Variational Inference in Statistics and Data

Abstract:

We introduce a new module for teaching variational inference (VI) to undergraduate statistics students that is designed to be flexible enough to be used in different types of courses. The module is self-contained, so it can be used as an add-on to any course that covers Bayesian inference or regression. This module is based on the idea that VI is a generalization of maximum likelihood estimation and that the posterior distribution is the one that maximizes the expected log-likelihood. We provide a set of activities for students to work in pairs, which are designed to help them understand how the posterior distribution can be used to make predictions about new data. The module also includes a set of R labs that illustrate the use of VI with different types of data and models.

The first part of the paper is an overview of the module. It describes the activities and the R labs, as well as some general tips for teaching statistics students. The second part is the manual of the R shiny app we have developed for the module. The third part is the details of the guided R lab with U.S. women labor participation sample data, presented in Section 4.1 in the main text. The fourth part is the details of the guided R lab of the LDA application to a sample of the Associated Press newspaper articles with VI, presented in Section 4.2 in the main text.

6 Class Activity: Probabilistic Model for Count Data

The goal of this activity is to illustrate variational inference on a simple example of Gamma-Poisson conjugate model, which is a popular model for count data.

6.1 A Motivating Example

Our task is to estimate the average number of active users of a popular massively multiplayer online role- playing game (mmorpg) playing between the peak evening hours 7 pm and 10 pm. This information can help the game developers in allocating server resources and optimizing user experience. To make this estimate, we will consider the following counts (in thousands) of active players collected during the peak evening hours over a two-week period past month.

Sun Mon Tue Wed Thu Fri Sat
Week 1 50 47 46 52 49 55 53
Week 2 48 45 51 50 53 46 47

6.2 Overview of the Gamma-Poisson Model

Sampling density:

Suppose that y = (y1, . . . , yn) represent the observed counts in n time intervals where the counts are independent, then each yi follows a Poisson distribution with rate θ > 0.

yi | θ ∼ Poisson(θ)

• E(yi | θ) = θ

• Var(yi | θ) = θ

Prior distribution:

θ ∼ Gamma

---

**Summary Statistics:**
- Input: 10,714 words (67,824 chars)
- Output: 1,529 words
- Compression: 0.14x
- Generation: 68.1s (22.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
