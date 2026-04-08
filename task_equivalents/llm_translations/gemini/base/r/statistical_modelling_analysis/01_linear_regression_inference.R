Auto <- read.csv('data/csv/Auto.csv', na.strings = '?')
Auto <- na.omit(Auto)

model1_fit <- lm(mpg ~ horsepower, data = Auto)
print(summary(model1_fit))

new_data <- data.frame(horsepower = 98)

conf_interval <- predict(model1_fit, new_data, interval = "confidence", level = 0.95)
print(conf_interval)

pred_interval <- predict(model1_fit, new_data, interval = "prediction", level = 0.95)
print(pred_interval)