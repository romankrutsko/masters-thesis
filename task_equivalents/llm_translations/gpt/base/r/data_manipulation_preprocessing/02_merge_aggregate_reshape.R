library(readr)
library(dplyr)

College <- read_csv("data/csv/College.csv")

school_name <- College[[1]]
rownames(College) <- school_name
College <- College[, -1]

College <- College %>%
mutate(Private01 = ifelse(Private == "Yes", 1, 0)) %>%
select(-Private)

X <- College %>%
select(-Apps) %>%
mutate(across(everything(), as.numeric))

Y <- College$Apps

set.seed(1)
train_idx <- sample(seq_len(nrow(College)), size = floor(0.5 * nrow(College)))

xtrain <- X[train_idx, ]
xtest <- X[-train_idx, ]
ytrain <- Y[train_idx]
ytest <- Y[-train_idx]