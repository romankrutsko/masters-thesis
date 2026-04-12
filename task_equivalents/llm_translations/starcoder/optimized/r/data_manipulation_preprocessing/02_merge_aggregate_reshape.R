library(dplyr)
library(readr)
library(caTools)

College <- read_csv('data/csv/College.csv')
school_name <- College$X1
College <- rename(College, school_name = X1)
College <- select(College, -school_name)

College$Private01  <- ifelse(College$Private == 'Yes', 1, 0)
College <- select(College, -Private)

X <- select(College, -Apps) %>% as.data.frame()
Y <- College$Apps

set.seed(1) # Set the seed for reproducibility
split <- sample.split(Y, SplitRatio = 0.5)
xtrain <- subset(X, split == TRUE)
xtest <- subset(X, split == FALSE)
ytrain <- subset(Y, split == TRUE)
ytest <- subset(Y, split == FALSE)
