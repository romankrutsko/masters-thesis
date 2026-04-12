library(MASS)
library(tidyverse)
library(caret)
Hitters <- read_csv('data/csv/Hitters.csv') %>% drop_na()
Hitters <- Hitters %>% select(-rownames, -Player, -Name)
Hitters <- Hitters %>% mutate(League = ifelse(League == "A", 0, 1), NewLeague = ifelse(NewLeague == "A", 0, 1), Division = ifelse(Division == "E", 0, 1))
Hitters <- Hitters %>% mutate(logSal = log(Salary))

x <- Hitters %>% select(-Salary, -logSal)
y <- Hitters$logSal
train_idx <- createDataPartition(y, p=200/nrow(Hitters), list=FALSE)
xtrain <- x[train_idx, ]
ytrain <- y[train_idx]
xtest <- x[-train_idx, ]
ytest <- y[-train_idx]
lambda_grid <- seq(0.001, 0.201, length.out=20)
train_mse <- rep(0, 20)
for (i in 1:20) {
  boost <- train(xtrain, ytrain, method="gbm", trControl=trainControl(method="none"), tuneGrid=data.frame(n.trees=1000, interaction.depth=1, shrinkage=lambda_grid[i], n.minobsinnode=10))
  train_mse[i] <- mean((ytrain - predict(boost, xtrain))^2)
}
lasso <- train(xtrain, ytrain, method="lasso", trControl=trainControl(method="cv", number=10))
lasso_mse <- mean((ytest - predict(lasso, xtest))^2)
best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- train(xtrain, ytrain, method="gbm", trControl=trainControl(method="none"), tuneGrid=data.frame(n.trees=1000, interaction.depth=1, shrinkage=best_lambda, n.minobsinnode=10))
feature_importance <- varImp(best_boost)$importance %>% rownames_to_column("Variable") %>% arrange(desc(Overall))
print(feature_importance)
