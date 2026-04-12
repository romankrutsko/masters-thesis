library(readr)
library(dplyr)
library(broom)
library(ggplot2)
Auto <- read_csv('data/csv/Auto.csv', na = '?') %>% drop_na()
n  = nrow(Auto)
X  = matrix(Auto$horsepower, ncol = 1)
Y  = matrix(Auto$mpg, ncol = 1)
X  = cbind(rep(1, n), X)
model1_fit  = lm(Y ~ X[, 2])
a  = coef(model1_fit)[1]
b  = coef(model1_fit)[2]
yfit  = a + b * X[, 2]
ggplot(Auto, aes(x = horsepower, y = mpg)) +
  geom_point() +
  geom_line(aes(y = yfit), color = 'red') +
  xlab('horsepower') +
  ylab('mpg')
