# Extracted from Ch08.R (Q10 boosting/lasso workflow)

library(gbm)
library(glmnet)
Hitters = read.csv('data/csv/Hitters.csv', header=TRUE, row.names=1)

Hitters = na.omit(Hitters)
drop_cols = intersect(c('rownames', 'Player', 'Name'), colnames(Hitters))
Hitters = Hitters[, setdiff(colnames(Hitters), drop_cols), drop=FALSE]
Hitters$League = ifelse(Hitters$League == 'A', 0, 1)
Hitters$NewLeague = ifelse(Hitters$NewLeague == 'A', 0, 1)
Hitters$Division = ifelse(Hitters$Division == 'E', 0, 1)
Hitters$logSal = log(Hitters$Salary)

x = subset(Hitters, select=-c(Salary, logSal))
y = Hitters$logSal

set.seed(1)
train = sample(1:nrow(x), 200)
test = setdiff(1:nrow(x), train)
xtrain = x[train,]
xtest = x[test,]
ytrain = y[train]
ytest = y[test]

train.mse = rep(0, 20)
lambda.grid = seq(0.001, 0.201, length.out=20)
for (i in seq_along(lambda.grid)) {
  boost.hit = gbm(ytrain~., data=data.frame(xtrain, ytrain=ytrain), distribution='gaussian', n.trees=1000, shrinkage=lambda.grid[i], verbose=FALSE)
  boost.pred = predict(boost.hit, newdata=xtrain, n.trees=1000)
  train.mse[i] = mean((boost.pred - ytrain)^2)
}

cv.out     = cv.glmnet(as.matrix(xtrain), ytrain, alpha=1, nfolds=10)
bestlam    = cv.out$lambda.min
lasso.pred = predict(cv.out, s=bestlam, newx=as.matrix(xtest))
lasso.mse  = mean((lasso.pred-ytest)^2)

best.lambda = lambda.grid[which.min(train.mse)]
best.boost.hit = gbm(ytrain~., data=data.frame(xtrain, ytrain=ytrain), distribution='gaussian', n.trees=1000, shrinkage=best.lambda, verbose=FALSE)
summary(best.boost.hit)
