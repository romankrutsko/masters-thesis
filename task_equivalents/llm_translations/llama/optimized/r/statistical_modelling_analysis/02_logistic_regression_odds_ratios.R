library(readr)
library(broom)
library(MASS)

Weekly <- read_csv('data/csv/Weekly.csv')

x01 <- cbind(1, Weekly[, 3:8])
y01 <- ifelse(Weekly$Direction == 'Up', 1, 0)

glm0_fit <- glm(y01 ~ x01 - 1, family = binomial)
print(tidy(glm0_fit))
print(glance(glm0_fit))

prob <- predict(glm0_fit, type = 'response')
pred <- ifelse(prob > 0.5, 1, 0)
print(table(y01, pred))
print(mean(y01 == pred))