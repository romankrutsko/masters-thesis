library(gbm)
library(glmnet)

Hitters <- read.csv('data/csv/Hitters.csv')
Hitters <- na.omit(Hitters)
Hitters <- Hitters[, !(names(Hitters) %in% c('rownames', 'Player', 'Name'))]

Hitters$League <- ifelse(Hitters$League == 'N', 1, 0)
Hitters$NewLeague <- ifelse(Hitters$NewLeague == 'N', 1, 0)
Hitters$Division <- ifelse(Hitters$Division == 'W', 1, 0)
Hitters$logSal <- log(Hitters$Salary)

x <- Hitters[, !(names(Hitters) %in% c('Salary', 'logSal'))]
y <- Hitters$logSal

set.seed(1)
train_idx <- sample(seq_len(nrow(x)), 200)
xtrain <- x[train_idx, ]
xtest  <- x[-train_idx, ]
ytrain <- y[train_idx]
ytest  <- y[-train_idx]

lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(20)
train_data <- cbind(xtrain, logSal = ytrain)

for (i in seq_along(lambda_grid)) {
  set.seed(2)
  boost <- gbm(logSal ~ ., data = train_data, distribution = "gaussian", 
               n.trees = 1000, shrinkage = lambda_grid[i], 
               interaction.depth = 3, bag.fraction = 1)
  
  train_mse[i] <- mean((ytrain - predict(boost, n.trees = 1000))^2)
}

set.seed(1)
lasso <- cv.glmnet(as.matrix(xtrain), ytrain, alpha = 1, nfolds = 10)
lasso_preds <- predict(lasso, s = "lambda.min", newx = as.matrix(xtest))
lasso_mse <- mean((ytest - lasso_preds)^2)

best_lambda <- lambda_grid[which.min(train_mse)]

set.seed(2)
best_boost <- gbm(logSal ~ ., data = train_data, distribution = "gaussian", 
                  n.trees = 1000, shrinkage = best_lambda, 
                  interaction.depth = 3, bag.fraction = 1)

feature_importance <- summary(best_boost, n.trees = 1000, plotit = FALSE)
print(feature_importance)