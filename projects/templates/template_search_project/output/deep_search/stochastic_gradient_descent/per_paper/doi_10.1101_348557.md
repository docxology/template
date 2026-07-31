# [yamada2018hyperparameterfree] — Hyperparameter-free optimizer of stochastic gradient descent that incorporates unit correction and moment estimation

_Source keyword: **stochastic gradient descent**_

_2018_  ·  
Kazunori D Yamada
DOI: <https://doi.org/10.1101/348557>

## Abstract

ABSTRACT
                In the deep learning era, stochastic gradient descent is the most common method used for optimizing neural network parameters. Among the various mathematical optimization methods, the gradient descent method is the most naive. Adjustment of learning rate is necessary for quick convergence, which is normally done manually with gradient descent. Many optimizers have been developed to control the learning rate and increase convergence speed. Generally, these optimizers adjust the learning rate automatically in response to learning status. These optimizers were gradually improved by incorporating the effective aspects of earlier methods. In this study, we developed a new optimizer: YamAdam. Our optimizer is based on Adam, which utilizes the first and second moments of previous gradients. In addition to the moment estimation system, we incorporated an advantageous part of AdaDelta, namely a unit correction system, into YamAdam. According to benchmark tests on some common datasets, our optimizer showed similar or faster convergent performance compared to the existing methods. YamAdam is an option as an alternative optimizer for deep learning.
