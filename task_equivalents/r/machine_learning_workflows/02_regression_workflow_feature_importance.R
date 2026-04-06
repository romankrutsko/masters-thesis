# Extracted from Ch08.R (Q10 boosting/lasso workflow)

library(ISLR)
library(gbm)
library(glmnet)

Hitters = na.omit(Hitters)
Hitters$logSal = log(Hitters$Salary)

set.seed(1)
train    = sample(1:nrow(Hitters), 200)
hit.test = Hitters[-train,'logSal']

j         = 0
train.mse = rep(0, 20)
for (i in seq(0.001, 0.201, 0.01)) {
  j = j + 1
  boost.hit = gbm(logSal~.-Salary, data=Hitters[train,], distribution='gaussian', n.trees=1000, shrinkage=i)
  boost.pred = predict(boost.hit, newdata=Hitters[train,], n.trees=1000, shrinkage=i)
  train.mse[j] = mean((boost.pred - Hitters[train,'logSal'])^2)
}

x.train = model.matrix(logSal~.-Salary, Hitters[train,])[,-1]
y.train = Hitters[train,'logSal']
x.test  = model.matrix(logSal~.-Salary, Hitters[-train,])[,-1]

cv.out     = cv.glmnet(x.train, y.train, alpha=1)
bestlam    = cv.out$lambda.min
lasso.pred = predict(cv.out, s=bestlam, newx=x.test)
lasso.mse  = mean((lasso.pred-hit.test)^2)

best.boost.hit = gbm(logSal~.-Salary, data=Hitters[train,], distribution='gaussian', n.trees=1000, shrinkage=0.011)
summary(best.boost.hit)
