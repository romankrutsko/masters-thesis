College <- read.csv('data/csv/College.csv')
rownames(College) <- College[, 1]
College <- College[, -1]

College$Private01 <- ifelse(College$Private == 'Yes', 1, 0)
College$Private <- NULL

X <- College[, names(College) != 'Apps']
X[] <- lapply(X, as.numeric)
Y <- College$Apps

set.seed(1)
train_index <- sample(seq_len(nrow(X)), size = floor(nrow(X) * 0.5))
xtrain <- X[train_index, ]
xtest <- X[-train_index, ]
ytrain <- Y[train_index]
ytest <- Y[-train_index]