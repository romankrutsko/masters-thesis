Weekly <- read.csv('data/csv/Weekly.csv')

x01 <- Weekly[, 3:8]
y01 <- as.integer(Weekly$Direction == 'Up')

glm0_fit <- glm(y01 ~ ., data = cbind(y01, x01), family = binomial)
print(summary(glm0_fit))

prob <- predict(glm0_fit, type = "response")
pred <- as.integer(prob > 0.5)

print(table(y01, pred))
print(mean(pred == y01))