```r
library(stats)
library(dplyr)
library(pscl) # for confusion matrix

Weekly <- read.csv("data/csv/Weekly.csv")
x01 <- cbind(rep(1, nrow(Weekly)), Weekly[, 2:8])
y01 <- ifelse(Weekly$Direction == "Up", 1, 0)
glm0_fit <- glm(y01 ~ x01, family = binomial(link = "logit"))
summary(glm0_fit)
prob <- predict(glm0_fit, type = "response")
pred <- ifelse(prob > 0.5, 1, 0)
confusionMatrix(y01, pred)
mean(pred == y01)
```