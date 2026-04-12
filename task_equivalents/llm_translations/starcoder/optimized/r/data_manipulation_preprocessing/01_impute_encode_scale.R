library(dplyr)
library(tidyr)
library(caret)
Auto <- read.csv("data/csv/Auto.csv", na.strings="?") %>%
  drop_na() %>%
  mutate(mpg01 = ifelse(mpg > median(mpg), 1, 0)) %>%
  select(-mpg, -name)
var_no_scale <- c("cylinders", "year", "origin", "mpg01")
var_to_scale <- c("displacement", "horsepower", "weight", "acceleration")
scaled_var <- scale(Auto[, var_to_scale])
df <- cbind(scaled_var, Auto[, var_no_scale])
x <- df[, -ncol(df)]
y <- df[, ncol(df)]
