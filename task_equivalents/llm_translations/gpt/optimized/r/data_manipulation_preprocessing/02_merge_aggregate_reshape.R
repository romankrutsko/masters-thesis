library(readr)
library(dplyr)

College <- read_csv("data/csv/College.csv", show_col_types = FALSE)

school_name <- College[[1]]
College <- College |>
tibble::column_to_rownames(var = names(College)[1])

College <- College |>
mutate(Private01 = if_else(Private == "Yes", 1, 0)) |>
select(-Private)

X <- College |>
select(-Apps) |>
mutate(across(everything(), as.double))

Y <- College$Apps

set.seed(1)
train_idx <- sample.int(nrow(College), size = floor(0.5 * nrow(College)))
xtrain <- X[train_idx, , drop = FALSE]
xtest <- X[-train_idx, , drop = FALSE]
ytrain <- Y[train_idx]
ytest <- Y[-train_idx]