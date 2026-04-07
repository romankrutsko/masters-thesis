library(readr)
library(dplyr)
library(glmnet)
library(gbm)

Hitters <- read_csv("data/csv/Hitters.csv") %>%
na.omit()

cols_to_drop <- intersect(c("rownames", "Player", "Name"), names(Hitters))
Hitters <- Hitters %>%
select(-all_of(cols_to_drop))

Hitters <- Hitters %>%
mutate(
League = recode(League, "A" = 0, "N" = 1),
NewLeague = recode(NewLeague, "A" = 0, "N" = 1),
Division = recode(Division, "E" = 0, "W" = 1),
logSal = log(Salary)
)

x <- Hitters %>%
select(-Salary, -logSal)
y <- Hitters$logSal

set.seed(1)
train_idx <- sample(seq_len(nrow(x)), 200)
xtrain <- x[train_idx, ]
xtest <- x[-train_idx, ]
ytrain <- y[train_idx]
ytest <- y[-train_idx]

lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(20)

for (i in seq_along(lambda_grid)) {
boost <- gbm(
formula = ytrain ~ .,
distribution = "gaussian",
data = data.frame(ytrain = ytrain, xtrain),
n.trees = 1000,
interaction.depth = 1,
shrinkage = lambda_grid[i],
bag.fraction = 0.5,
train.fraction = 1.0,
verbose = FALSE
)

pred_train <- predict(boost, newdata = xtrain, n.trees = 1000)
train_mse[i] <- mean((ytrain - pred_train)^2)
}

xtrain_mat <- model.matrix(~ ., data = xtrain)[, -1]
xtest_mat <- model.matrix(~ ., data = xtest)[, -1]

lasso <- cv.glmnet(xtrain_mat, ytrain, alpha = 1, nfolds = 10)
lasso_pred <- predict(lasso, s = "lambda.min", newx = xtest_mat)
lasso_mse <- mean((ytest - lasso_pred)^2)

best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- gbm(
formula = ytrain ~ .,
distribution = "gaussian",
data = data.frame(ytrain = ytrain, xtrain),
n.trees = 1000,
interaction.depth = 1,
shrinkage = best_lambda,
bag.fraction = 0.5,
train.fraction = 1.0,
verbose = FALSE
)

feature_importance <- summary(best_boost, plotit = FALSE)
feature_importance <- feature_importance[order(-feature_importance$rel.inf), ]
print(setNames(feature_importance$rel.inf, feature_importance$var))