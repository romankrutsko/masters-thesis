# Extracted from Ch06.R (Q9 ridge/lasso CV workflow)

library(glmnet)

College = read.csv("C:\\Users\\Carol\\Desktop\\College.csv", header=T)
rownames(College) = College[,1]
College = College[,-1]

set.seed(1)
train    = sample(1:nrow(College), nrow(College)/2)
test     = (-train)
df.train = College[train,]
df.test  = College[test,]

x.train = model.matrix(Apps~., df.train)[,-1]
y.train = df.train$Apps
x.test  = model.matrix(Apps~., df.test)[,-1]
y.test  = df.test$Apps

set.seed(1)
cv.out  = cv.glmnet(x.train, y.train, alpha=0)
plot(cv.out)
bestlam = cv.out$lambda.min

ridge.pred = predict(cv.out, s=bestlam, newx=x.test)
ridge.err  = mean((ridge.pred-y.test)^2)

set.seed(1)
cv.out  = cv.glmnet(x.train, y.train, alpha=1)
plot(cv.out)
bestlam = cv.out$lambda.min

lasso.pred = predict(cv.out, s=bestlam, newx=x.test)
lasso.err  = mean((lasso.pred-y.test)^2)
