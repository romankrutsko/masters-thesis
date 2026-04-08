library(gbm)
library(glmnet)

Hitters <- read.csv('data/csv/Hitters.csv')
Hitters <- na.omit(Hitters)
Hitters <- Hitters[, !(names(Hitters) %in% c('rownames', 'Player', 'Name'))]

Hitters$League <- ifelse(Hitters$League == 'A', 0, 1)
Hitters$NewLeague <- ifelse(Hitters$NewLeague == 'A', 0, 1)
Hitters$Division <- ifelse(Hitters$Division == 'E', 0, 1)
Hitters$logSal <- log(Hitters$Salary)

x <- Hitters[, !(names(Hitters) %in% c('Salary', 'logSal'))]
y <- Hitters$logSal

set.seed(1)
train_index <- sample(seq_len(nrow(x)), size = 200)
xtrain <- x[train_index, ]
xtest <- x[-train_index, ]
ytrain <- y[train_index]
ytest <- y[-train_index]

lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(20)

train_data <- cbind(xtrain, logSal = ytrain)

for (i in 1:20) {
  set.seed(2)
  boost <- gbm(logSal ~ ., data = train_data, distribution = "gaussian", 
               n.trees = 1000, shrinkage = lambda_grid[i], interaction.depth = 3)
  train_mse[i] <- mean((ytrain - predict(boost, n.trees = 1000))^2)
}

lasso <- cv.glmnet(as.matrix(xtrain), ytrain, alpha = 1, nfolds = 10)
lasso_mse <- mean((ytest - predict(lasso, s = "lambda.min", newx = as.matrix(xtest)))^2)

best_lambda <- lambda_grid[which.min(train_mse)]
set.seed(2)
best_boost <- gbm(logSal ~ ., data = train_data, distribution = "gaussian", 
                  n.trees = 1000, shrinkage = best_lambda, interaction.depth = 3)

feature_importance <- summary(best_boost, plotit = FALSE)
print(feature_importance)