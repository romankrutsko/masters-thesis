library(readr)
library(dplyr)
library(e1071)

Auto <- read_csv("data/csv/Auto.csv", na = "?") %>%
na.omit()

Auto <- Auto %>%
mutate(mpg01 = ifelse(mpg > median(mpg), 1, 0)) %>%
select(-mpg, -name)

var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")

scaled_var <- scale(Auto[, var_to_scale])

df <- bind_cols(
as.data.frame(scaled_var) %>% setNames(var_to_scale),
Auto[, var_no_scale]
)

x <- df[, 1:(ncol(df) - 1)]
y <- as.factor(df$mpg01)

tune_param <- list(cost = c(0.01, 0.1, 1, 10, 100, 1000))
tune(svm, mpg01 ~ ., data = data.frame(x, mpg01 = y), kernel = "linear",
ranges = tune_param, tunecontrol = tune.control(cross = 5))

tune_param <- list(cost = c(0.01, 0.1, 1, 10, 100, 1000),
degree = c(2, 3, 4, 5))
tune(svm, mpg01 ~ ., data = data.frame(x, mpg01 = y), kernel = "polynomial",
ranges = tune_param, tunecontrol = tune.control(cross = 5))

tune_param <- list(cost = c(0.01, 0.1, 1, 10, 100, 1000),
gamma = c(0.5, 1, 2, 3))
tune(svm, mpg01 ~ ., data = data.frame(x, mpg01 = y), kernel = "radial",
ranges = tune_param, tunecontrol = tune.control(cross = 5))