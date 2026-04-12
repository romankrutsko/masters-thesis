library(tidyverse)
library(caret)
library(gbm)

Hitters <- read.csv("data/csv/Hitters.csv") %>%
  drop_na() %>%
  select(-c(rownames, Player, Name)) %>%
  mutate(League = ifelse(League == "A", 0, 1),
         NewLeague = ifelse(NewLeague == "A", 0, 1),
         Division = ifelse(Division == "E", 0, 1))

Hitters <- Hitters %>%
  mutate(logSal = log(Salary))
xtrain <- Hitters %>% select(-c(Salary, logSal))
ytrain <- Hitters$logSal
set.seed(1)
xtest <- xtrain[sample(nrow(xtrain), 20), ]
ytest <- ytrain[as.numeric(rownames(xtest))]
lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- vector("numeric", length = 20)
for (i in seq_along(lambda_grid)) {
  boost <- gbm(logSal ~ .,
               data = Hitters,
               distribution = "gaussian",
               n.trees = 1000,
               interaction.depth = 4,
               shrinkage = lambda_grid[i],
               cv.folds = 5)
  train_mse[i] <- min(boost$cv.error)
}
lasso <- train(xtrain, ytrain, method = "lasso")
lasso_mse <- mean((predict(lasso, xtest) - ytest)^2)
best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- gbm(logSal ~ .,
                  data = Hitters,
                  distribution = "gaussian",
                  n.trees = 1000,
                  interaction.depth = 4,
                  shrinkage = best_lambda)
feature_importance <- summary(best_boost) %>%
  as.data.frame() %>%
  select(var, rel.inf) %>%
  arrange(desc(rel.inf))
print(feature_importance)
