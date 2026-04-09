Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

model1_fit <- lm(mpg ~ horsepower, data = Auto)
print(summary(model1_fit))

xnew <- data.frame(horsepower = 98)

pred_ci <- predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)
print(pred_ci)

pred_pi <- predict(model1_fit, newdata = xnew, interval = "prediction", level = 0.95)
print(pred_pi)