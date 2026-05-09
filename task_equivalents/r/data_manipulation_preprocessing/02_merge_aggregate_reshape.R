# Extracted from Ch06.R (Q9 preprocessing/model matrix)

College = read.csv('data/csv/College.csv', header=TRUE)
rownames(College) = College[,1]
College = College[,-1]

College$Private01 = ifelse(College$Private == 'Yes', 1, 0)
College$Private = NULL

X = as.data.frame(lapply(subset(College, select=-Apps), as.numeric))
Y = College$Apps

set.seed(1)
train    = sample(1:nrow(College), nrow(College)/2)
test     = setdiff(1:nrow(College), train)

xtrain = X[train,]
xtest  = X[test,]
ytrain = Y[train]
ytest  = Y[test]

# Previous version
#
# College = read.csv('data/csv/College.csv', header=TRUE)
# rownames(College) = College[,1]
# College = College[,-1]
#
# set.seed(1)
# train    = sample(1:nrow(College), nrow(College)/2)
# test     = (-train)
# df.train = College[train,]
# df.test  = College[test,]
#
# x.train = model.matrix(Apps~., df.train)[,-1]
# y.train = df.train$Apps
# x.test  = model.matrix(Apps~., df.test)[,-1]
# y.test  = df.test$Apps
