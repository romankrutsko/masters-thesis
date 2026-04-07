library(readr)

Auto <- read_csv("data/csv/Auto.csv", na = "?") %>%
na.omit()

n <- nrow(Auto)
X <- matrix(Auto$horsepower, ncol = 1)
Y <- matrix(Auto$mpg, ncol = 1)

model1_fit <- lm(Y ~ X[, 1])
summary(model1_fit)

xnew <- data.frame(X[, 1] = 98)
predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)