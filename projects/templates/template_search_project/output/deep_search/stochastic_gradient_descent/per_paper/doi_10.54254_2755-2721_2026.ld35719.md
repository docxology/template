# [gong2026comparative] — A Comparative Study of Gradient Descent and Stochastic Gradient Descent in Neural Network Function Approximation

_Source keyword: **stochastic gradient descent**_

_2026_  ·  
Pu Gong
DOI: <https://doi.org/10.54254/2755-2721/2026.ld35719>

## Abstract

Neural networks are often employed in artificial intelligence because they are capable of learning patterns and approximating nonlinear functions from input data. But the performance of a neural network is not only decided by the model structure, but also by the optimization technique utilized in the training process. In this research, we compare full-batch Gradient Descent versus mini-batch Stochastic Gradient Descent in a neural network function approximation problem. A tiny feedforward neural network is trained to approximate the nonlinear function. The experiment is implemented in Python and the comparison is made based on training loss curves, final training means squared error, final test mean squared error and prediction visualization. The results reveal that the full-batch Gradient Descent gives a smoother loss curve since in each update the entire training dataset is used. Mini-batch Stochastic Gradient Descent on the other hand shows more noticeable oscillations but reaches a lower ultimate training MSE and test MSE in this experimental context. This implies that stochastic updates can be less stable at each step but can still assist the model in achieving greater approximation performance in the same number of epochs. The study shows how optimization techniques influence neural network training behavior and it combines mathematical optimization theory with real model performance.
