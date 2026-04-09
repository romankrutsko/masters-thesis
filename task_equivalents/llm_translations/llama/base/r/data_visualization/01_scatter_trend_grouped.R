library(readr)
library(ggplot2)

Auto <- read_csv('data/csv/Auto.csv', na = "?", col_types = cols(.default = "d")) %>%
  drop_na()

X <- Auto$horsepower
Y <- Auto$mpg

model1_fit <- lm(Y ~ X)

a <- coef(model1_fit)[1]
b <- coef(model1_fit)[2]
yfit <- a + b * X

ggplot(Auto, aes(x = X, y = Y)) +
  geom_point() +
  geom_line(aes(x = X, y = yfit), color = "red") +
  labs(x = "horsepower", y = "mpg")