# Resolving uncertainty on the fly: Modeling adaptive driving behavior as active inference

**Authors:** Johan Engström, Ran Wei, Anthony McDonald, Alfredo Garcia, Matt O'Kelly, Leif Johnson

**Year:** 2023

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [engström2023resolving.pdf](../pdfs/engström2023resolving.pdf)

**Generated:** 2025-12-05 13:01:49

---

**Overview/Summary**
The paper presents a new approach to modeling driver behavior in a visual time-sharing scenario where drivers are performing a secondary task that requires looking away from the road. The authors propose an active inference model that represents the driver's uncertainty about their own vehicle position and heading angle, as well as their uncertainty about the presence of other road users. They also represent the driver's motivation to perform the secondary task in terms of a preference for on-road versus off-road glances. The approach is based on the concept of "uncertainty on the fly" where the model can update its beliefs and make decisions without requiring an explicit reset or reinitialization at each time step, as opposed to traditional approaches that require the driver's uncertainty to be reset at the start of a new episode. The authors use this approach to predict the frequency and duration of off-road glances in a driving simulator experiment.

**Key Contributions/Findings**
The main contribution of the paper is the development of an active inference model for visual time sharing, which is based on the concept of "uncertainty on the fly". This allows the driver's uncertainty about their own vehicle position and heading angle to be updated without requiring an explicit reset or reinitialization at each time step. The authors use this approach to predict the frequency and duration of off-road glances in a driving simulator experiment. The results from the model are compared with human data, which is collected using a similar experimental paradigm.

**Methodology/Approach**
The visual time sharing model builds on the model described under Scenario 1 and, unless otherwise stated, uses the same parameters and values. In this scenario, the authors replaced the point mass vehicle dynamics model in the previous scenario with a kinematic bicycle model to more accurately capture the vehicle motion constraints [46]. To generate uncertainty in the ego vehicle's actual position on the road we introduce a small steering noise (0.001 rad/s) to represent the disturbance caused by uncontrollable environment effects such as uneven road surface or wind gusts. The driver's generative model matched the generative process, and since the road ahead was always empty, the authors here only address the second source of uncertainty proposed by Senders et al [18] related to vehicle position in the lane. However, the model could be extended to incorporate other sources of uncertainty, for example, related to the behavior of other road users (the first type of uncertainty in [18]). The driver's state is represented as a vector that contains the kinematic state of the vehicle in lane coordinates sego  = [x, y, θ, δ, v, a, w], two binary variables Cl and Cr for whether the vehicle has crossed the left or right lane boundary, and a binary variable I for the driver's gaze direction (i.e., off-road or on-road). The model makes decisions about two types of actions: the kinematic control of the vehicle acontrol, and the gaze action, aI, which represents a deterministic transition of the corresponding gaze state. The authors use this approach to predict the frequency and duration of off-road glances in a driving simulator experiment.

**Results/Data**
The visual time sharing model builds on the model described under Scenario 1 and, unless otherwise stated, uses the same parameters and values. In this scenario, we replaced the point mass vehicle dynamics model in the previous scenario with a kinematic bicycle model to more accurately capture the vehicle motion constraints [46]. To generate uncertainty in the ego vehicle's actual position on the road we introduce a small steering noise (0.001 rad/s) to represent the disturbance caused by uncontrollable environment effects such as uneven road surface or wind gusts. We model the state of the driver-vehicle system using the kinematic state of the vehicle in lane coordinates sego  = [x, y, θ, δ, v, a, w], two binary variables Cl and Cr for whether the vehicle has crossed the left or right lane boundary, and a binary variable I for the driver's gaze direction (i.e., off-road or on-road). The model makes decisions about two types of actions: the kinematic control of the vehicle acontrol, and the gaze action, aI, which represents a deterministic transition of the corresponding gaze state. All Scenario 2 simulations were performed for a segment of 30 seconds. Each scenario was run for 10 times and the time series plots below show one randomly selected run. However, the results from all 10 runs were used to compute summary statistical metrics for comparison with human data.

**Limitations/Discussion**
The authors note that the model could be extended to incorporate other sources of uncertainty, for example, related to the behavior of other road users (the first type of uncertainty in [18]). The paper does not discuss the limitations of the approach or future work.

---

**Summary Statistics:**
- Input: 14,998 words (96,418 chars)
- Output: 794 words
- Compression: 0.05x
- Generation: 38.0s (20.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
