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
train_idx <- sample(seq_len(nrow(Hitters)), size = 200)

xtrain <- x[train_idx, ]
xtest <- x[-train_idx, ]
ytrain <- y[train_idx]
ytest <- y[-train_idx]

lambda_grid <- seq(0.001, 0.201, length.out = 20)
train_mse <- numeric(20)

for (i in seq_along(lambda_grid)) {
boost <- gbm(
formula = logSal ~ .,
data = data.frame(xtrain, logSal = ytrain),
distribution = "gaussian",
n.trees = 1000,
shrinkage = lambda_grid[i],
interaction.depth = 1,
n.minobsinnode = 10,
bag.fraction = 0.5,
train.fraction = 1.0,
verbose = FALSE
)

pred_train <- predict(boost, newdata = xtrain, n.trees = 1000)
train_mse[i] <- mean((ytrain - pred_train)^2)
}

lasso <- cv.glmnet(
x = as.matrix(xtrain),
y = ytrain,
alpha = 1,
nfolds = 10
)

lasso_pred <- predict(lasso, newx = as.matrix(xtest), s = "lambda.min")
lasso_mse <- mean((ytest - lasso_pred)^2)

best_lambda <- lambda_grid[which.min(train_mse)]

best_boost <- gbm(
formula = logSal ~ .,
data = data.frame(xtrain, logSal = ytrain),
distribution = "gaussian",
n.trees = 1000,
shrinkage = best_lambda,
interaction.depth = 1,
n.minobsinnode = 10,
bag.fraction = 0.5,
train.fraction = 1.0,
verbose = FALSE
)

feature_importance <- summary(best_boost, n.trees = 1000, plotit = FALSE)
feature_importance <- feature_importance[order(-feature_importance$rel.inf), ]
print(setNames(feature_importance$rel.inf, feature_importance$var))