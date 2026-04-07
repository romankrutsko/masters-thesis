library(readr)

Weekly <- read_csv("data/csv/Weekly.csv", show_col_types = FALSE)

x01 <- Weekly[, 3:8, drop = FALSE]
y01 <- ifelse(Weekly$Direction == "Up", 1, 0)

glm0_fit <- glm(y01 ~ ., data = x01, family = binomial())
print(summary(glm0_fit))

prob <- predict(glm0_fit, type = "response")
pred <- ifelse(prob > 0.5, 1, 0)

print(table(y01, pred))
print(mean(pred == y01))