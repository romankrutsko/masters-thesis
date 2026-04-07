library(readr)
library(dplyr)
library(tibble)
library(caTools)

College <- read_csv("data/csv/College.csv")

school_name <- College[[1]]
College <- College %>%
column_to_rownames(var = names(College)[1])

College <- College %>%
mutate(Private01 = ifelse(Private == "Yes", 1, 0)) %>%
select(-Private)

X <- College %>%
select(-Apps) %>%
mutate(across(everything(), as.numeric))

Y <- College$Apps

set.seed(1)
split <- sample.split(Y, SplitRatio = 0.5)

xtrain <- X[split, ]
xtest <- X[!split, ]
ytrain <- Y[split]
ytest <- Y[!split]