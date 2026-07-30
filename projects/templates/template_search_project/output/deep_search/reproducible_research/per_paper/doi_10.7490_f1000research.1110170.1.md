# [ohta2015containerbased] — Container-based sequence data analysis workflow for reproducible research

_Source keyword: **reproducible research**_

_2015_  ·  
Tazro Ohta, Osamu Ogasawara
DOI: <https://doi.org/10.7490/f1000research.1110170.1>

## Abstract

Publishing raw data on public repository enabled researchers to reuse data and reproduce the published results. Most of the data analysis methods which connect raw data and published results, however, are described in natural language in the section of materials and methods in published articles that often has a lack of information to execute the analysis workflow exactly same as done in the original study. To achieve more accurate description and sharing of data analysis workflow for the reproducible research, we developed a framework based on Docker, the container- based virtual environment, and the several analysis workflow of high-throughput sequencing data are converted into the sets of docker container to be executed on the developed framework. Apache Mesos is also introduced on our large scale computing infrastructure as a resource manager, and we developed job schedular which communicates with Mesos to execute containers successively. This framework works on any kind of computational environment where docker and Mesos run, and supports users to manage, share, and re-execute their tools and workflows. We will provide the results of framework design and the challenges to better reproducible research environment for all the computational biology.​
