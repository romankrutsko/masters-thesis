library(readr)

Auto <- read_csv("data/csv/Auto.csv", na = "?", show_col_types = FALSE) |>
tidyr::drop_na()

x <- Auto$horsepower
y <- Auto$mpg

model1_fit <- lm(y ~ x)
print(summary(model1_fit))

xnew <- data.frame(x = 98)
pred_conf <- predict(model1_fit, newdata = xnew, interval = "confidence", level = 0.95)
pred_pred <- predict(model1_fit, newdata = xnew, interval = "prediction", level = 0.95)

print(as.data.frame(pred_conf)[, c("fit", "lwr", "upr"), drop = FALSE])
print(as.data.frame(pred_pred)[, c("fit", "lwr", "upr"), drop = FALSE])