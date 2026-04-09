library(readr)
library(broom)

Auto <- read_csv('data/csv/Auto.csv', na = c("?", "NA")) %>%
  drop_na()

X <- cbind(1, Auto$horsepower)
Y <- Auto$mpg

model1_fit <- lm(Y ~ X[, 2])
summary_model <- tidy(summary(model1_fit))
print(summary(model1_fit))

xnew <- data.frame(horsepower = 98)
pred <- predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)
print(data.frame(mean = pred[, 1], mean_ci_lower = pred[, 2], mean_ci_upper = pred[, 3]))

pred <- predict(model1_fit, newdata = xnew, interval = "prediction", level = 0.95)
print(data.frame(mean = pred[, 1], obs_ci_lower = pred[, 2], obs_ci_upper = pred[, 3]))