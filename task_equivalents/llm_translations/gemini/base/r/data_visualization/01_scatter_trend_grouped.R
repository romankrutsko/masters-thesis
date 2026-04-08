Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

X <- Auto$horsepower
Y <- Auto$mpg
model1_fit <- lm(Y ~ X)

a <- coef(model1_fit)[1]
b <- coef(model1_fit)[2]
yfit <- a + b * X

plot(X, Y, xlab = 'horsepower', ylab = 'mpg')
lines(X, yfit, col = 'red')