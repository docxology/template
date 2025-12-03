# Location Inference from Tweets using Grid-based Classification

**Authors:** Oluwaseun Ajao, Deepak P, Jun Hong

**Year:** 2017

**Source:** arxiv

**Venue:** arXiv

**DOI:** N/A

**PDF:** [ajao2017location.pdf](../pdfs/ajao2017location.pdf)

**Generated:** 2025-12-03 04:12:00

---

**Overview/Summary**

The paper "Location Inference from Tweets using Grid-based Classification" is a study on inferring the location of a Twitter user based on their tweets. The authors propose a grid-based classification method for this task, which outperforms the existing methods in city-level location inference on Twitter. They use four different radii (120, 100, 60, and 30 miles) to classify the tweets into different grids, and then apply various machine learning models to predict the user's location based on their tweets.

**Key Contributions/Findings**

The main contributions of this paper are the grid-based classification method and the results obtained by using the proposed method. The authors use four different radii (120, 100, 60, and 30 miles) to classify the tweets into different grids. They then apply various machine learning models such as Naive Bayes, Random Forest, Support Vector Machine, Gradient Boosting, and Logistic Regression to predict the user's location based on their tweets. The results of the four different radii are presented in Table 2. The continental United States has a total geographic area of 6,110,264 square miles (Agency, 2013) gridding of the datasets translated into four (4) variants of radius in miles (120, 100, 60, and 30). The results for each grid type, location, and classification are presented in Table 2. The continental United States has a total geographic area of 6,110,264 square miles (Agency, 2013) gridding of the datasets translated into four (4) variants of radius in miles (120, 100, 60, and 30). The results for each grid type, location, and classification are presented in Table 2. At a radius of 100 miles as show in Table 2 we achieve an accuracy of 57% as opposed to the 51% accuracy achieved by Cheng et al. (2010) representing a 10% improvement. Sizes of the lattices can be modiﬁed for accuracy and level of granularity or location detail required.

**Methodology/Approach**

The cleaning of the tweets followed the standard natural language processing pipeline while the Scikit-learn machine learning module in Python for implementing the classiﬁcations

**Results/Data**

Summary results for each grid type, location, and classiﬁcation are presented in Table 2. The continental United States has a total geographic area of 6,110,264 square miles (Agency, 2013) gridding of the datasets translated into four (4) variants of radius in miles (120, 100, 60, and 30). The results for each grid type, location, and classiﬁcation are presented in Table 2. At a radius of 100 miles as show in Table 2 we achieve an accuracy of 57% as opposed to the 51% accuracy achieved by Cheng et al. (2010) representing a 10% improvement. Sizes of the lattices can be modiﬁed for accuracy and level of granularity or location detail required.

**Limitations/Discussion**

The result of the grid classiﬁcation shows an improvement over the existing baseline in city-level location inference on Twitter as our method clearly outperforms the existing works. At a radius of 100 miles as show in Table 2 we achieve an accuracy of 57% as opposed to the 51% accuracy achieved by Cheng et al. (2010) representing a 10% improvement. Sizes of the lattices can be modiﬁed for accuracy and level of granularity or location detail required

**References**

[Agency2013] Central Intelligence Agency. 2013. The world factbook: United States. https://www.cia.gov/library/publications/the-world-factbook/geos/us.html. Accessed: 2016/12/05.
[Ajao et al.2015] Oluwaseun Ajao, Jun Hong, and Weiru Liu. 2015. A survey of location inference techniques on twitter. Journal of Information Science, 41(6):855–864.
[Cha et al.2015] Miriam Cha, Youngjune Gwon, and HT Kung. 2015. Twitter geolocation and regional classiﬁcation via sparse coding. In Proceedings of the 9th International Conference on Weblogs and Social Media (ICWSM), pages 582–585.
[Chang et al.2012] Hau-chen Chang, Dongwon Lee, Mohammed Eltaher, and Jeongkyu Lee. 2012. @ phillies tweeting from philly? pre-dicting twitter user locations with spatial word usage. In Proceedings of the 2012 International Conference on Advances in Social Networks Analysis and Mining (ASONAM), pages 111–118. IEEE Computer Society.
[Cheng et al.2010] Zhiyuan Cheng, James Caver-lee, and Kyumin Lee. 2010. You are where you tweet: a content-based approach to geo-locating twitter users. In Proceedings of the 19th ACM international conference on Information and knowledge management, pages 759–768. ACM.
[Compton et al.2014] Ryan Compton, David Jurgens, and David Allen. 2014. Geotagging one hundred million twitter accounts with total variation minimization. In Big Data (Big Data), 2014 IEEE International Conference on, pages 393–401. IEEE.
[Han et al.2014] Bo Han, Paul Cook, and Timothy Baldwin. 2014. Text-based twitter user ge-location prediction. Journal of Artificial Intelligence Research, 49:451–500.
[Han et al.2016] Bo Han, Afshin Rahimi, Leon Derczynski, and Timothy Baldwin. 2016. Twitter geolocation prediction shared task of the 2016 workshop on noisy user-generated text. In Proceedings of the W-NUT Workshop.
[Ikawa et al.2012] Yohei Ikawa, Miki Enoki, and Michiaki Tatsubori. 2012. Location inference using microblog messages. In Proceedings of the 21st International Conference on World Wide Web, pages 687–690. ACM.
[Jurgens et al.2015] David Jurgens, Tyler Finethy, James McCorriston, Yi Tian Xu, and Derek Ruths. 2015. Geolocation prediction in twitter using social networks: A critical analysis and review of current practice. In Proceedings of the 9th International AAAI Conference on Weblogs and Social Media (ICWSM).
[Jurgens2013] David Jurgens. 2013. That’s what friends are for: Inferring location in online so- cial media platforms based on social relationships. ICWSM, 13:273–282.
[Mahmud et al.2014] Jalal Mahmud, Jeffrey Nichols, and Clemens Drews. 2014. Home location identiﬁcation of twitter users. ACM Transactions on Intelligent Systems and Technology (TIST), 5(3):47.
[Ritter et al.2011] Alan Ritter, Sam Clark, Mausam, and Oren Etzioni. 2011. Named entity recognition in tweets: An experimental study. In EMNLP.
[US Census Bureau2016] Population Department US Census Bureau. 2016. Annual estimates of resident population change for incorporated places of 50,000 or more in 2014, ranked by percent change: July 1, 2014 to july 1, 2015. http://factfinder.census.gov/ faces/tableservices/jsf/pages/productview.xhtml?src= bkmk. Ac-cessed: 2016/12/05.
[Yamaguchi et al.2014] Yuto Yamaguchi, Toshiyuki Amagasa, Hiroyuki Kitagawa, and Yohei Ikawa. 2014. Online user location inference exploiting spatiotemporal correlations in social streams. In Proceedings of the 23rd ACM International Conference on Conference on Information and Knowledge Management, pages 1139–1148. ACM.

=== END OF PAPER SUMMARY ===

---

**Summary Statistics:**
- Input: 2,239 words (14,179 chars)
- Output: 1,001 words
- Compression: 0.45x
- Generation: 59.1s (16.9 words/sec)
- Quality Score: 1.00/1.0
- Attempts: 1

**Quality Check:** Passed
