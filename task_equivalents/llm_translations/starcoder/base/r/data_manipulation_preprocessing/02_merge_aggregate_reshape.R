library(dplyr) # for data manipulation
library(readr) # for reading CSV files
library(caret) # for data splitting
College <- read_csv("data/csv/College.csv")
school_names <- College$X1
rownames(College) <- school_names
College <- select(College, -X1)
College$Private01 <- ifelse(College$Private == "Yes", 1, 0)
College <- select(College, -Private)
X <- select(College, -Apps)
Y <- College$Apps
set.seed(1) # Set a seed for reproducibility
train_index <- sample(1:nrow(X), 0.5 * nrow(X))
xtrain <- X[train_index, ]
ytrain <- Y[train_index]
xtest <- X[-train_index, ]
ytest <- Y[-train_index]
