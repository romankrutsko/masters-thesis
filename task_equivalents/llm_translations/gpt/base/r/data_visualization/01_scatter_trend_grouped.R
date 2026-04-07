library(readr)
library(ggplot2)

Auto <- read_csv("data/csv/Auto.csv", na = "?") %>%
na.omit()

n <- nrow(Auto)
X <- matrix(Auto$horsepower, ncol = 1)
Y <- matrix(Auto$mpg, ncol = 1)
X <- cbind(1, X)

model1_fit <- lm(Y ~ X[, 2])

a <- coef(model1_fit)[1]
b <- coef(model1_fit)[2]
yfit <- a + b * X[, 2]

plot(X[, 2], Y,
xlab = "horsepower",
ylab = "mpg",
pch = 16)

lines(X[, 2], yfit, col = "red")