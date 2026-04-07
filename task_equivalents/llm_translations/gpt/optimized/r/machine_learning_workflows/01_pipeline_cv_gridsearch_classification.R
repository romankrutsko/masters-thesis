library(readr)
library(dplyr)
library(e1071)

Auto <- read_csv("data/csv/Auto.csv", na = "?", show_col_types = FALSE) |>
tidyr::drop_na()

Auto <- Auto |>
mutate(mpg01 = if_else(mpg > median(mpg), 1L, 0L)) |>
select(-mpg, -name)

var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")

scaled_var <- scale(Auto[, var_to_scale])

df <- bind_cols(
as.data.frame(scaled_var),
Auto |> select(all_of(var_no_scale))
)

x <- df[, seq_len(ncol(df) - 1), drop = FALSE]
y <- df$mpg01

linear_tune <- tune(
svm,
train.x = x,
train.y = as.factor(y),
kernel = "linear",
ranges = list(cost = c(0.01, 0.1, 1, 10, 100, 1000)),
tunecontrol = tune.control(cross = 5),
scale = FALSE
)

poly_tune <- tune(
svm,
train.x = x,
train.y = as.factor(y),
kernel = "polynomial",
ranges = list(
cost = c(0.01, 0.1, 1, 10, 100, 1000),
degree = c(2, 3, 4, 5)
),
tunecontrol = tune.control(cross = 5),
scale = FALSE
)

rbf_tune <- tune(
svm,
train.x = x,
train.y = as.factor(y),
kernel = "radial",
ranges = list(
cost = c(0.01, 0.1, 1, 10, 100, 1000),
gamma = c(0.5, 1, 2, 3)
),
tunecontrol = tune.control(cross = 5),
scale = FALSE
)