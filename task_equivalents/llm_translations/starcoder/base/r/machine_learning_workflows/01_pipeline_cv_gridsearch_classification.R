library(tidyverse)
library(e1071) # for SVMs

Auto <- read.csv("data/csv/Auto.csv", na.strings="?") %>%
  drop_na() %>%
  mutate(mpg01 = ifelse(mpg > median(mpg), 1, 0)) %>%
  select(-mpg, -name)
var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")
scaled_var <- scale(Auto[, var_to_scale])
df <- cbind(scaled_var, Auto[, var_no_scale])
x <- df[, -ncol(df)]
y <- df[, ncol(df)]
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000))
svm_linear <- tune(svm, train.x=x, train.y=as.factor(y), kernel="linear", ranges=tune_param,
                   cross=5, scale=FALSE)
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000), degree = 2:5)
svm_poly <- tune(svm, train.x=x, train.y=as.factor(y), kernel="polynomial", ranges=tune_param,
                 cross=5, scale=FALSE)
tune_param <- list(C = c(0.01, 0.1, 1, 10, 100, 1000), gamma = c(0.5, 1, 2, 3))
svm_rbf <- tune(svm, train.x=x, train.y=as.factor(y), kernel="radial", ranges=tune_param,
                cross=5, scale=FALSE)
