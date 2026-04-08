Weekly <- read.csv('data/csv/Weekly.csv')

x01 <- Weekly[, 3:8]
y01 <- ifelse(Weekly$Direction == 'Up', 1, 0)

df <- data.frame(y01 = y01, x01)
glm0_fit <- glm(y01 ~ ., data = df, family = binomial)
print(summary(glm0_fit))

prob <- predict(glm0_fit, type = "response")
pred <- ifelse(prob > 0.5, 1, 0)
print(table(y01, pred))
print(mean(pred == y01))