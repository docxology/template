# Eating Smart: Free-ranging dogs follow an optimal foraging strategy while scavenging in groups

**Authors:** Rohan Sarkar, Sreelekshmi R, Abhijit Nayek, Anirban Bhowmick, Poushali Chakraborty, Rituparna Sonowal, Debsruti Dasgupta, Rounak Banerjee, Aritra Roy, Amartya Baran Mandal, Anindita Bhadra

**Year:** 2022

**Source:** arxiv

**Venue:** N/A

**DOI:** N/A

**PDF:** [sarkar2022eating.pdf](../pdfs/sarkar2022eating.pdf)

**Generated:** 2025-12-05 11:41:50

---

**Overview/Summary**

The study "Eating Smart" investigates the foraging behavior of free-ranging dogs in West Bengal, India. The researchers observed that these dogs eat a variety of food items and found that they tend to eat more chicken than bread. In fact, 77% of the food eaten by the dogs was chicken. This is surprising because it is not common for dogs to be able to access chicken as it is a high-protein food source that is usually reserved for humans. The study also found that the number of dogs in a group affects how much food they eat and this effect varied across different groups. For example, if there was only one dog in a group, then all the food eaten by that dog would be chicken, but if multiple dogs were present, the proportion of bread eaten increased as the number of dogs increased. The study also found that the amount of time spent watching for potential predators (vigilance) was higher when there was only one dog in a group than when multiple dogs were present.

**Key Contributions/Findings**

The main finding is that free-ranging dogs tend to eat more chicken than bread. This is surprising because it is not common for dogs to be able to access high-protein food sources such as chicken, which are usually reserved for humans. The study also found that the number of dogs in a group affects how much food they eat and this effect varied across different groups. For example, if there was only one dog in a group, then all the food eaten by that dog would be chicken, but if multiple dogs were present, the proportion of bread eaten increased as the number of dogs increased. The study also found that the amount of time spent watching for potential predators (vigilance) was higher when there was only one dog in a group than when multiple dogs were present.

**Methodology/Approach**

The researchers conducted this study by observing 15 food items placed at three different locations: Kalyani, Kolkata and Durgapur. The food items were chicken and bread. The number of dogs that ate the food varied from 1 to 12 in a group. The number of food items available was constant across all groups (15). The researchers used a hierarchical model with varying effects for the group nested within place. They also used a zero-inflated binomial distribution to account for the excess zeroes in the data. They used k-fold cross-validation to select the best fitted model amongst the ones they fitted. They reported log odds ratios with 95% credible intervals. The outcome variable was the number of food items eaten per group out of a total of 15, denoted here by trials (n). "foodType" refers to the type of food available to the dog for eating (dummy coded as 0 for bread and 1 for chicken). "participants" denotes the number of dogs eating in a group. The best fitted model was a hierarchical model with "varying" effects of group nested within place. They used a prior beta(2, 2) for "zi" to regularize it towards 0.5. The outcome variable was "Count" which referred to the number of food pieces eaten per group out of a total of 15 pieces, denoted here by trials (n). "foodType" refers to the type of food available to the dog for eating (dummy coded as 0 for bread and 1 for chicken). "participants" denoted the number of dogs eating in a group. 

**Results/Data**

The results of the regression showed that compared to bread, chicken increased the likelihood of proportion of food items being eaten (LOR = 2.54, 95% CI = 1.19, 3.65). The number of participants had a positive effect on the likelihood of food items being eaten (LOR = 1.92, 95%CI = 1.61, 2.27). The density plot of the model parameter estimates have been shown in Supplementary figure 2 below. The density of the group intercept "random effect" (sd_place: group_Intercept) and the random slope of foodType (sd_place : group_foodType) on it are both away from zero validating our choice of including them in the model. Clearly, group has an effect on the likelihood of food eaten and the effect of food type varied between groups. This, as the "participants" parameter shows, is probably because the number of participants in each group is different and groups with larger number of participants eat more food or when only a single member of a group eats during the experiment, it eats only one type of food. Another possibility is that different members eat different food, dependent on availability. The posterior distribution of the place Intercept contained zero, elucidating that it had no effect. 

**Limitations/Discussion**

The study found that the proportion of bread eaten by free-ranging dogs increased as the number of participants in a group increased. This could be because the larger the group size, the more likely it is that different members eat different food items. The study also found that the amount of time spent watching for potential predators (vigilance) was higher when there was only one dog in a group than when multiple dogs were present. 

**Supplementary Materials**

The best fitted model was a hierarchical model with "varying" effects of group nested within place. We used a prior beta(2, 2) for "zi" to regularize it towards 0.5. The outcome variable was "Count" which referred to the number of food pieces eaten per group out of a total of 15 pieces, denoted here by trials (n). "foodType" refers to the type of food available to the dog for eating (dummy coded as 0 for bread and 1 for chicken). "participants" denotes the number of dogs eating in a group. The best fitted model was a hierarchical model with "varying" effects of group nested within place. They also used a zero-inflated binomial distribution to account for the excess zeroes in the data. They used k-fold cross-validation to select the best fitted model amongst the ones they fitted. They reported log odds ratios with 95% credible intervals. The outcome variable was "Count" which referred to the number of food pieces eaten per group out of a total of 15, denoted here by trials (n). "foodType" refers to the type of food available to the dog for eating (dummy coded as 0 for bread and 1 for chicken). "participants" denoted the number of dogs eating in a group. 

**Supplementary Materials**

Food eaten
We carried out a logistic regression with zero-inflated binomial distribution to account for the excess zeroes in the dataset. We used k-fold cross-validation to select the best fitted model amongst the ones we fitted. We reported log odds ratios with 95% credible intervals. The outcome variable was "Count" which referred to the number of food pieces eaten per group out of a total of 15, denoted here by trials (n). "foodType" refers to the type of food available to the dog for eating (dummy coded as 0 for bread and 1 for chicken). "participants" denotes the number of dogs eating in a group. 

**Supplementary Materials**

S_fig 1: Map of India which highlights the area of West Bengal in which the study was conducted:  (a) Kalyani  (b) Kolkata and surrounding suburbs  (c) Durgapur

S_fig 2: Density plot of the model parameter estimates 

**Acknowledgement**

RS would like to thank Dr. Scott Claessens  (School of Psychology, University of Auckland, New Zealand) for his immense help, guidance and mentoring of RS in Bayesian statistics, model building and for providing manuscript inputs. Without his patience and kindness this paper would not have been possible. RS would also like to thank Dr. Satyaki Mazumder  (Department of Mathematics and Statistics, IISER-Kolkata, India) and Narayan Srinivasan  (Department of Mathematics and Statistics, IISER-Kolkata, India) for their valuable inputs. RS would like to express gratitude to Animal Behaviour Collective for their support during the covid pandemic.  

**Funding**

RS was supported by IISER Kolkata Institute fellowship. This work was supported by the Science and Research Board, Department of Science and Technology, Government of India.

**Supplementary Materials**

Supplementary material 1 
S_fig 1: Map of India which highlights the area of West Bengal in which the study was conducted:  (a) Kalyani  (b) Kolkata and surrounding suburbs  (c) Durgapur

Supplementary material 2
Food eaten  We carried out a logistic regression with zero-inflated binomial distribution to account for the excess zeroes in the dataset. We used k-fold cross-validation to select the best fitted model amongst the ones we fitted. We reported log odds ratios with 95% credible intervals. The outcome variable was "Count" which referred to the number of food pieces eaten per group out of a total of 15, denoted here by trials (n).  "foodType" refers to the type of food available to the dog for eating  (dummy coded as 0) for bread,  (1) for chicken).  "participants" denoted the number of dogs eating in a group. 

**Supplementary Materials**

S_fig 2: Density plot of the model parameter estimates 
The results of the regression showed that compared to bread, chicken increased the likelihood  (LOR = 2.54, 95% CI = 1.19, 3.65). The number of participants had a positive effect on the likelihood  (LOR = 1.92, 95%CI = 1.61, 2.27). The density plot of the model parameter estimates have been shown in Supplementary figure 2 below. The density of the

---

**Summary Statistics:**
- Input: 7,827 words (48,964 chars)
- Output: 1,533 words
- Compression: 0.20x
- Generation: 68.1s (22.5 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
