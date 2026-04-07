library(readr)
library(dplyr)
library(gbm)
library(glmnet)

Hitters <- read_csv("data/csv/Hitters.csv", show_col_types = FALSE) |>
tidyr::drop_na()

drop_cols <- intersect(c("rownames", "Player", "Name"), names(Hitters))
if (length(drop_cols) > 0) {
Hitters <- Hitters |> select(-all_of(drop_cols))
}

Hitters <- Hitters |>
mutate(
League = recode(League, A = 0, N = 1),
NewLeague = recode(NewLeague, A = 0, N = 1),
Division = recode(Division, E = 0, W = 1),
logSal = log(Salary)
)

x <- Hitters |> select(-Salary, -logSal)
y <- Hitters$logSal

set.seed(1)
train_idx <- sample.int(nrow(x), size = 200)
xtrain <- x[train_idx, , drop = FALSE]
xtest <- x[-train_idx, , drop = FALSE]
ytrain <- y[train_idx]
ytest <- y[-train_idx]

lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(length(lambda_grid))

xtrain_mat <- as.matrix(xtrain)
xtest_mat <- as.matrix(xtest)

for (i in seq_along(lambda_grid)) {
boost <- gbm(
formula = ytrain ~ .,
data = data.frame(ytrain = ytrain, xtrain),
distribution = "gaussian",
n.trees = 1000,
interaction.depth = 1,
shrinkage = lambda_grid[i],
bag.fraction = 0.5,
train.fraction = 1,
n.minobsinnode = 10,
verbose = FALSE
)
pred_train <- predict(boost, newdata = xtrain, n.trees = 1000)
train_mse[i] <- mean((ytrain - pred_train)^2)
}

lasso <- cv.glmnet(xtrain_mat, ytrain, alpha = 1, nfolds = 10)
lasso_pred <- predict(lasso, newx = xtest_mat, s = "lambda.min")
lasso_mse <- mean((ytest - lasso_pred)^2)

best_lambda <- lambda_grid[which.min(train_mse)]
best_boost <- gbm(
formula = ytrain ~ .,
data = data.frame(ytrain = ytrain, xtrain),
distribution = "gaussian",
n.trees = 1000,
interaction.depth = 1,
shrinkage = best_lambda,
bag.fraction = 0.5,
train.fraction = 1,
n.minobsinnode = 10,
verbose = FALSE
)

feature_importance <- summary(best_boost, n.trees = 1000, plotit = FALSE)
feature_importance <- setNames(feature_importance$rel.inf, feature_importance$var)
feature_importance <- sort(feature_importance, decreasing = TRUE)
print(feature_importance)