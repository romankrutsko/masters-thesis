Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

model1_fit <- lm(mpg ~ horsepower, data = Auto)

plot(Auto$horsepower, Auto$mpg, xlab = 'horsepower', ylab = 'mpg')
abline(model1_fit, col = 'red')