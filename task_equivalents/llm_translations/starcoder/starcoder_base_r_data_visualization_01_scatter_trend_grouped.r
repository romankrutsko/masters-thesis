Here is the R code that implements the same functionality as the given Python code:


library(stats)
library(dplyr)
library(ggplot2)

Auto <- read.csv('data/csv/Auto.csv', na.strings='?').dropna()

n  = nrow(Auto)
X  = matrix(Auto$horsepower, ncol=1)
Y  = matrix(Auto$mpg, ncol=1)
X  = cbind(rep(1, n), X)
model1_fit  = lm(Y ~ X[, 2])
a  = model1_fit$coefficients[1]
b  = model1_fit$coefficients[2]
yfit  = a + b * X[, 2]

ggplot() +
  geom_point(aes(x=X[, 2], y=Y)) +
  xlab('horsepower') +
  ylab('mpg') +
  geom_line(aes(x=X[, 2], y=yfit), color='red')


The R code loads the required libraries and reads the data, then creates the X and Y matrices. The X matrix is augmented with a column of ones for the intercept term. The model is fit using the lm function, and the coefficients are extracted to calculate yfit. Finally, the scatter plot is created with the ggplot library.


```python [echo=FALSE]
!pip install rpy2
%load_ext rpy2.ipython
```


```python
%%R
library(stats)
library(dplyr)
library(ggplot2)

Auto <- read.csv('data/csv/Auto.csv', na.strings='?').dropna()

n  = nrow(Auto)
X  = matrix(Auto$horsepower, ncol=1)
Y  = matrix(Auto$mpg, ncol=1)
X  = cbind(rep(1, n), X)
model1_fit  = lm(Y ~ X[, 2])
a  = model1_fit$coefficients[1]
b  = model1_fit$coefficients[2]
yfit  = a + b * X[, 2]

ggplot() +
  geom_point(aes(x=X[, 2], y=Y)) +
  xlab('horsepower') +
  ylab('mpg') +
  geom_line(aes(x=X[, 2], y=yfit), color='red')
```

![png](output_30_0.png)