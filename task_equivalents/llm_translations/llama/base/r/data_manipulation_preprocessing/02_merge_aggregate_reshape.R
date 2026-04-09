library(readr)
library(dplyr)

College <- read_csv('data/csv/College.csv')
school_name <- College[, 1]
rownames(College) <- school_name
College <- College[, -1]

College <- College %>% 
  mutate(Private01 = ifelse(Private == 'Yes', 1, 0)) %>% 
  select(-Private)

X <- College %>% 
  select(-Apps) %>% 
  mutate(across(everything(), as.numeric))
Y <- College$Apps

set.seed(1)
train_index <- sample(nrow(X), nrow(X) / 2)
xtrain <- X[train_index, ]
xtest <- X[-train_index, ]
ytrain <- Y[train_index]
ytest <- Y[-train_index]