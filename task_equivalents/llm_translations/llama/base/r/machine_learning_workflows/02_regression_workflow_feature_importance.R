# Install and load necessary libraries
# install.packages(c("readr", "dplyr", "caret", "glmnet", "gbm"))
library(readr)
library(dplyr)
library(caret)
library(glmnet)
library(gbm)

# Load data
Hitters <- read_csv('data/csv/Hitters.csv') %>% 
  drop_na() %>% 
  select(-c(rownames, Player, Name)) %>% 
  mutate(League = ifelse(League == 'A', 0, 1),
         NewLeague = ifelse(NewLeague == 'A', 0, 1),
         Division = ifelse(Division == 'E', 0, 1),
         logSal = log(Salary))

# Split data into training and testing sets
set.seed(1)
trainIndex <- createDataPartition(Hitters$logSal, p = 200/nrow(Hitters), list = FALSE)
xtrain <- Hitters[trainIndex, ] %>% select(-c(Salary, logSal))
ytrain <- Hitters$logSal[trainIndex]
xtest <- Hitters[-trainIndex, ] %>% select(-c(Salary, logSal))
ytest <- Hitters$logSal[-trainIndex]

# Define lambda grid and train MSE
lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- rep(0, 20)
for (i in 1:20) {
  boost <- gbm(ytrain ~ ., data = data.frame(xtrain, ytrain), 
               distribution = "gaussian", n.trees = 1000, shrinkage = lambda_grid[i], 
               cv.folds = 0, keep.data = TRUE)
  train_mse[i] <- mean((ytrain - predict(boost, newdata = data.frame(xtrain), n.trees = 1000))^2)
}

# Lasso model
x_train_matrix <- as.matrix(xtrain)
lasso <- cv.glmnet(x_train_matrix, ytrain, alpha = 1)
lasso_mse <- mean((ytest - predict(lasso, newx = as.matrix(xtest), s = lasso$lambda.min))^2)

# Best lambda and best boost model
best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- gbm(ytrain ~ ., data = data.frame(xtrain, ytrain), 
                  distribution = "gaussian", n.trees = 1000, shrinkage = best_lambda, 
                  cv.folds = 0, keep.data = TRUE)

# Feature importance
feature_importance <- data.frame(summary(best_boost)) %>% 
  arrange(desc(rel.inf)) %>% 
  mutate(rel.inf = rel.inf)
print(feature_importance)