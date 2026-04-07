library(readr)

Auto <- read_csv("data/csv/Auto.csv", na = "?") %>%
na.omit()

X <- Auto$horsepower
Y <- Auto$mpg

model1_fit <- lm(Y ~ X)
print(summary(model1_fit))

xnew <- data.frame(X = 98)

pred_conf <- predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)
print(as.data.frame(pred_conf)[, c("fit", "lwr", "upr")])

pred_pred <- predict(model1_fit, newdata = xnew, interval = "prediction", level = 0.95)
print(as.data.frame(pred_pred)[, c("fit", "lwr", "upr")])