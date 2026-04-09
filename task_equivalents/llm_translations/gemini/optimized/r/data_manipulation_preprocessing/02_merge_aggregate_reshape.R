College <- read.csv('data/csv/College.csv', row.names = 1)

College$Private01 <- as.integer(College$Private == 'Yes')
College$Private <- NULL

X <- subset(College, select = -Apps)
X[] <- lapply(X, as.numeric)
Y <- College$Apps

set.seed(1)
train_idx <- sample(seq_len(nrow(X)), size = nrow(X) %/% 2)
xtrain <- X[train_idx, ]
xtest  <- X[-train_idx, ]
ytrain <- Y[train_idx]
ytest  <- Y[-train_idx]