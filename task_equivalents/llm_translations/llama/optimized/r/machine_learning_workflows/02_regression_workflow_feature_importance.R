# Load necessary libraries
library(readr)
library(dplyr)
library(caret)
library(glmnet)
library(gbm)

# Load data and preprocess
Hitters <- read_csv('data/csv/Hitters.csv') %>%
  drop_na() %>%
  select(-c(rownames, Player, Name)) %>%
  mutate(
    League = ifelse(League == 'A', 0, 1),
    NewLeague = ifelse(NewLeague == 'A', 0, 1),
    Division = ifelse(Division == 'E', 0, 1),
    logSal = log(Salary)
  )

# Split data into features and target
x <- Hitters %>% select(-c(Salary, logSal))
y <- Hitters$logSal

# Split data into training and testing sets
set.seed(1)
train_index <- createDataPartition(y, p = 200 / nrow(Hitters), list = FALSE)
xtrain <- x[train_index, ]
xtest <- x[-train_index, ]
ytrain <- y[train_index]
ytest <- y[-train_index]

# Define lambda grid and train boosting models
lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(20)
for (i in seq_along(lambda_grid)) {
  boost <- gbm(
    formula = logSal ~ .,
    data = data.frame(xtrain, logSal = ytrain),
    distribution = 'gaussian',
    n.trees = 1000,
    shrinkage = lambda_grid[i],
    verbose = FALSE
  )
  train_mse[i] <- mean((ytrain - predict(boost, newdata = xtrain, n.trees = 1000))^2)
}

# Train lasso model
x_train_matrix <- as.matrix(xtrain)
lasso <- cv.glmnet(x_train_matrix, ytrain, alpha = 1)
lasso_mse <- mean((ytest - predict(lasso, newx = as.matrix(xtest), s = lasso$lambda.min))^2)

# Find best lambda and retrain best boosting model
best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- gbm(
  formula = logSal ~ .,
  data = data.frame(xtrain, logSal = ytrain),
  distribution = 'gaussian',
  n.trees = 1000,
  shrinkage = best_lambda,
  verbose = FALSE
)

# Calculate feature importance
feature_importance <- data.frame(
  feature = names(xtrain),
  importance = summary(best_boost)$rel.inf
) %>%
  arrange(desc(importance))
print(feature_importance)