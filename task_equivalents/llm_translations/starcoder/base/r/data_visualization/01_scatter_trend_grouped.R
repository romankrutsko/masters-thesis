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
