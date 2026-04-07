library(readr)

Auto <- read_csv("data/csv/Auto.csv", na = "?", show_col_types = FALSE) |>
tidyr::drop_na()

x <- Auto$horsepower
y <- Auto$mpg

model1_fit <- lm(y ~ x)

a <- coef(model1_fit)[1]
b <- coef(model1_fit)[2]
yfit <- a + b * x

plot(x, y, xlab = "horsepower", ylab = "mpg")
lines(x, yfit, col = "red")