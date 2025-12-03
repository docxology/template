# Active Inference for Adaptive BCI: application to the P300 Speller

**Authors:** Jelena Mladenović, Jérémy Frey, Emmanuel Maby, Mateus Joffily, Fabien Lotte, Jeremie Mattout

**Year:** 2018

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [mladenović2018active.pdf](../pdfs/mladenović2018active.pdf)

**Generated:** 2025-12-03 06:28:43

---

**Overview/Summary**

The paper presents a generic Bayesian approach to implement adaptive features in brain-computer interfaces (BCIs) for improving performance. The authors propose using the Active Inference (AI) framework, which tightly couples perception and action, to infer user's intentions or states by accumulating observations (e.g., electrophysiological data) in a flexible manner as well as to act adaptively in a way that optimizes performance. They demonstrate AI applied to BCI using realistic P300-speller simulations. The authors show that AI can implement new features such as optimizing the sequence of flashed letters and yield significant bit rate increases.

**Key Contributions/Findings**

The main contributions are the application of the Active Inference (AI) framework for adaptive BCIs, which is a generic Bayesian approach to infer user's intentions or states by accumulating observations in a flexible manner. The AI can implement new features such as optimizing the sequence of flashed letters and yield significant bit rate increases.

**Methodology/Approach**

The paper uses a probabilistic model that tightly couples perception and action. Key variables include observed data, user hidden states, and machine's actions. The observed data are EEG responses to target, non-target (P300 or not) and feedback stimuli (Error Potentials – ErrPs or not), which allow the machine to infer user's hidden states, here the intention to spell a letter or pause as well as the recognition of a target/non-target or a correct/incorrect feedback. Depending on the hidden states inferred, the computer has possible actions, here to flash in order to accumulate conﬁdence about the target letter, to stop flashing and to display the chosen letter, or to switch off the screen if it infers an idle state of the user, i.e., no P300 response has been observed for some time. The data likelihood matrix can be learned from calibration data. Given the machine's actions, the transitions between hidden states are modeled by a probability (Markov) martix. The authors also predeﬁne the preference over all possible outcomes. Typically, the preferred outcome is to be in the state of observing a correctly spelled letter. Finally, a parameter γ sets the exploration-exploitation tradeoff for action selection.

**Results/Data**

The authors compared AI to two classical approaches: (1) P300- spelling with a fixed number 12 of repetitions and pseudo-random flashing; (2) P300-spelling with pseudo-random flashing but optimal stopping [Mattout et al., 2015]. To do so, the authors used data from 18 subjects from a previous P300-speller experiment [Perrin et al., 2011]. For each algorithm and subject, the authors simulated the spelling of 12000 letters. Furthermore, to demonstrate AI's flexibility, the authors implemented a "LookAway" case, in which the machine would infer the user to be in idle state and would switch the screen off. The authors also simulated an ErrP classiﬁcation enabling the automated detection of a wrongly spelled letter. In case of such detection, AI picks the next most probable letter to spell or choose to continue flashing to strengthen its conﬁdence.

**Limitations/Discussion**

The main findings are that AI outperforms other algorithms while offering a possibility of unifying various adaptive implementations within one generic framework. Thanks to such genericity, with only a few tuning of its parameters, AI can incorporate many features, such as automated correction or accounting for an idle user state. It can adjust to signal variability by inferring about the user, but it can also take into account the inﬂuence of its actions onto the user. This approach lays ground for future co- adaptive systems.

**References**

Friston, K., Kilner, J., and Harrison, L. (2006). A free energy principle for the brain. Journal of Physiology-Paris, 100(1-3):70–87.
Mattout, J., Perrin, M., Bertrand, O., and Maby, E. (2015). Improving bci performance through co-adaptation: Applications to the p300-speller. Annals of physical and rehabilitation medicine, 58(1):23–28.
Mladenovi´c, J., Mattout, J., and Lotte, F. (2017). A generic framework for adaptive EEG-based BCI training and operation. In Nam, C. S., Nijholt, A., and Lotte, F., editors, Brain-Computer Interfaces Handbook: Technological and Theoretical Advances, volume 1 of Brain-Computer Interfaces Handbook: Technological and Theoretical Advances. CRC Press: Taylor & Francis Group.
Perrin, M., Maby, E., Bouet, R., Bertrand, O., and Mattout, J. (2011). Detecting and interpreting responses to feedback in bci. pages 116–119.

**Additional Comments**

The authors used data from 18 subjects from a previous P300-speller experiment [Perrin et al., 2011]. For each algorithm and subject, the authors simulated the spelling of 12000 letters. Furthermore, to demonstrate AI's flexibility, the authors implemented a "LookAway" case, in which the machine would infer the user to be in idle state and would switch the screen off. The authors also simulated an ErrP classiﬁcation enabling the automated detection of a wrongly spelled letter. In case of such detection, AI picks the next most probable letter to spell or choose to continue flashing to strengthen its conﬁdence.

**Acknowledgments**

The authors thank the anonymous reviewers for their helpful comments and suggestions.

**References**

Friston, K., Kilner, J., and Harrison, L. (2006). A free energy principle for the brain. Journal of Physiology-Paris, 100(1-3):70–87.
Mattout, J., Perrin, M., Bertrand, O., and Maby, E. (2015). Improving bci performance through co-adaptation: Applications to the p300-speller. Annals of physical and rehabilitation medicine, 58(1):23–28.
Mladenovi´c, J., Mattout, J., and Lotte, F. (2017). A generic framework for adaptive EEG-based BCI training and operation. In Nam, C. S., Nijholt, A., and Lotte, F., editors, Brain-Computer Interfaces Handbook: Technological and Theoretical Advances, volume 1 of Brain-Computer Interfaces Handbook: Technological and Theoretical Advances. CRC Press: Taylor & Francis Group.
Perrin, M., Maby, E., Bouet, R., Bertrand, O., and Mattout, J. (2011). Detecting and interpreting responses to feedback in bci. pages 116–119.

**Additional Comments**

The authors used data from 18 subjects from a previous P300-speller experiment [Perrin et al., 2011]. For each algorithm and subject, the authors simulated the spelling of 12000 letters. Furthermore, to demonstrate AI's flexibility, the authors implemented a "LookAway" case, in which the machine would infer the user to be in idle state and would switch the screen off. The authors also simulated an ErrP classiﬁcation enabling the automated detection of a wrongly spelled letter. In case of such detection, AI picks the next most probable letter to spell or choose to continue flashing to strengthen its conﬁdence.

**References**

Friston, K., Kilner, J., and Harrison, L. (2006). A free energy principle for the brain. Journal of Physiology-Paris, 100(1-3):70–87.
Mattout, J., Perrin, M., Bertrand, O., and Maby, E. (2015). Improving bci performance through co-adaptation: Applications to the p300-speller. Annals of physical and rehabilitation medicine, 58(1):23–28.
Mladenovi´c, J., Mattout, J., and Lotte, F. (2017). A generic framework for adaptive EEG-based BCI training and operation. In Nam, C. S., Nijholt, A., and Lotte, F., editors, Brain-Computer Interfaces Handbook: Technological and Theoretical Advances, volume 1 of Brain-Computer Interfaces Handbook: Technological and Theoretical Advances. CRC Press: Taylor & Francis Group.
Perrin, M., Maby, E., Bouet, R., Bertrand, O., and Mattout, J. (2011). Detecting and interpreting responses to feedback in bci. pages 116–119.

**Additional Comments**

The authors used data from 18 subjects from a previous P300-speller experiment [Perrin et al., 2011]. For each algorithm and subject, the authors simulated the spelling of 12000 letters. Furthermore, to demonstrate AI's flexibility, the authors implemented a "LookAway" case, in which the machine would infer the user to be in idle state and would switch the screen off. The authors also simulated an ErrP classiﬁcation enabling the automated detection of a wrongly spelled letter. In case of such detection, AI picks the next most probable letter to spell or choose to continue flashing to strengthen its conﬁdence.

**References**

Friston, K., Kilner, J., and Harrison, L. (2006). A free energy principle for the brain. Journal of Physiology-Paris, 100(1-3):70–87.
Mattout, J., Perrin, M., Bertrand, O., and Maby, E. (2015). Improving bci performance through co-adaptation: Applications to the p300-speller. Annals of physical and rehabilitation medicine, 58(

---

**Summary Statistics:**
- Input: 947 words (6,334 chars)
- Output: 1,283 words
- Compression: 1.35x
- Generation: 60.9s (21.1 words/sec)
- Quality Score: 0.90/1.0
- Attempts: 1

**Quality Issues:** Off-topic content: inappropriate content reference
